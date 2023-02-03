from subs2cia.sources import Stream
from subs2cia.ffmpeg_tools import ffmpeg_demux, ffmpeg_trim_audio_clip_atrim_encode, ffmpeg_get_frame_fast

import logging
import pysubs2 as ps2  # for reading in subtitles
from pathlib import Path
from datetime import timedelta
import ffmpeg
import re
import copy
import sys
import unicodedata

codepoints = range(sys.maxunicode + 1)
punct_tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                      if unicodedata.category(chr(i)).startswith('P') or unicodedata.category(chr(i)).startswith('S'))

from typing import List, Union


def overlap_range(range1: List[int], range2: List[int]):
    assert len(range1) == len(range2) == 2
    if range1[0] < range2[0] < range1[1] or range1[0] < range2[1] < range1[1] or range2[0] < range1[0] < range2[1] or \
        range2[0] < range1[1] < range2[1]:
        return True
    return False


def ssaevent_trim(event: ps2.SSAEvent, ir: List[int]):
    r"""
    Given an event that overlaps with ir
    if subtitle is only on one side of IR
        trim subtitle to not overlap IR
    if subtitle is on both sides of IR
        split subtitle into two and trim each
    if subtitle is entirely inside IR
        drop it
    :param event: SSAEvent to trim/split+trim/drop
    :param ir: Ignore range, two integers representing milliseconds
    :return: List of trimmed events. There may be zero, one, or two events returned
    """

    assert len(ir) == 2
    trimmed = []
    if ir[0] <= event.start < ir[1] and ir[0] < event.end <= ir[1]:
        # event falls completely inside an ignore range
        return trimmed
    if ir[0] <= event.start < ir[1] and ir[1] < event.end:
        # event starts inside ignore range, ends outside of it
        event.start = ir[1]
        trimmed.append(event)
        return trimmed
    if event.start < ir[0] and ir[0] < event.end <= ir[1]:
        # event starts outside of ignore range, ends inside of it
        event.end = ir[0]
        trimmed.append(event)
        return trimmed
    if event.start < ir[0] and ir[1] < event.end:
        # split into two pieces
        event2 = copy.deepcopy(event)
        event.end = ir[0]
        trimmed.append(event)
        event2.start = ir[1]
        trimmed.append(event2)
        return trimmed
    # should never get here
    assert False


def ignore_nibble(ignore_ranges: List[List[int]], e: ps2.SSAEvent):
    r"""
    Given a set of ignore_ranges and a SSAEvent, determine if the event falls in an IR and if it does, trim it
    :param ignore_ranges: List of IRs
    :param e: SSAEvent of interest
    :return: List of SSAEvents
    """
    for ir in ignore_ranges:
        assert len(ir) == 2
        if overlap_range(ir, [e.start, e.end]):
            trimmed = ssaevent_trim(e, ir)
            # assert(trimmed is not None)
            return trimmed
    return [e]


class SubGroup:
    def __init__(self, events: [ps2.SSAEvent], ephemeral: bool, threshold: int, padding: int):
        self.contains_only_ephemeral = ephemeral  # if true, won't affect merging/splitting
        self.events = events
        self.ephemeral_events = []  # not empty only when mixing ephemeral and dialogue events

        self.threshold = threshold
        self.padding = padding

    @property
    def events_start(self):
        lowest = float('inf')
        for e in self.events:  # there may be 0 events
            if e.start < lowest:
                lowest = e.start
        return lowest

    @property
    def events_end(self):
        highest = 0
        for e in self.events:  # there may be 0 events
            if e.end > highest:
                highest = e.end
        return highest

    @property
    def group_range(self):
        r"""
        Subtitle group start, end with padding
        :return: [range_start, range_end]
        """
        if self.contains_only_ephemeral:
            return [self.events_start, self.events_end]
        grange = self.padding
        return [self.events_start - grange if self.events_start - grange > 0 else 0, self.events_end + grange]

    @property
    def group_limits(self):
        r"""
        Subtitle group start/end extended with padding and threshold
        :return: [limit_start, limit_end]
        """
        if self.contains_only_ephemeral:
            return [self.events_start, self.events_end]
        limit = self.threshold/2 + self.padding  # divide by two: threshold is distance to next group
        return [self.events_start - limit if self.events_start - limit > 0 else 0, self.events_end + limit]

    def __repr__(self):
        s = f"<SubGroup |{self.group_limits[0]} {self.group_range[0]} {(self.events_start, self.events_end)} {self.group_range[1]} {self.group_limits[1]}|>"
        return s


class SubtitleManipulator:
    def __init__(self, subpath: Path, threshold: int, padding: int, ignore_range: Union[List[List[int]], None], audio_length: int):
        r"""
        Class for subtitle manipulation
        :param subpath: Path to pysubs2-compatible subtitle file
        :param threshold: in milliseconds
        :param padding: in milliseconds
        :param ignore_range: list of ranges. each range is a list of two tuples. each tuple contains two values, a "sign" and a "duration".
        :param audio_length: How long the audio is in milliseconds.
        """
        self.subpath = subpath
        self.ssadata = None
        self.condensed_ssadata = None
        self.ssa_events = None
        self.groups = None
        self.ephemeral = None

        self.threshold = threshold
        self.padding = padding

        self.audio_length = audio_length

        self.ignore_range = None
        if ignore_range is not None:
            self.ignore_range = []
            for irange in ignore_range:
                assert(len(irange) == 2)
                to_append = []
                for idx, (sign, duration) in enumerate(irange):
                    if sign == "+":
                        if idx == 0:
                            raise AssertionError("Can't have duration '+' as first range value, "
                                                 "must be second range value "
                                                 "(e.g. -I 1m +1m30s)")
                        to_append.append(to_append[0] + duration)
                    elif sign == "e":
                        to_append.append(int(self.audio_length - duration))
                    elif sign == "":
                        to_append.append(duration)
                    else:
                        # shouldn't get here, re.findall should strip anything unexpected out
                        raise AssertionError(f"SubtitleManipulator received unexpected sign ({sign})")
                if not to_append[0] < to_append[1]:
                    raise AssertionError(f"Ignore range '{irange[0][0]}{irange[0][1]}ms {irange[1][0]}{irange[1][1]}ms'"
                                         f" is invalid: end of range "
                                         f"({to_append[1]}ms) is before start of range ({to_append[0]}ms)")
                self.ignore_range.append(to_append)

    def load(self, include_all: bool, regex: str, substrreplace_regex: str, substrreplace_nokeepchanges: bool):
        if not self.subpath.exists():
            logging.warning(f"Subtitle file {self.subpath} does not exist")
            return

        logging.debug(f"Loading subtitles at {self.subpath}")
        try:
            self.ssadata = ps2.load(str(self.subpath))
        except (ps2.FormatAutodetectionError) as e:
            # retry by forcing format
            logger = logging.getLogger(__name__)
            logger.exception(e)
            logging.warning(f"Subtitle file format not recognized by pysubs2, will try forcing extension {self.subpath.suffix[1:]} as format ({self.subpath})")
            try:
                self.ssadata = ps2.load(str(self.subpath), format_=self.subpath.suffix[1:])
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.exception(e)
                logging.warning(f"pysubs2 enountered error loading subtitle file {self.subpath}")
                self.ssadata = None
                return
        except (ValueError, AttributeError) as e:
            logger = logging.getLogger(__name__)
            logger.exception(e)
            logging.warning(f"pysubs2 enountered error loading subtitle file {self.subpath}")
            self.ssadata = None
            return
        logging.debug(f"Loaded {self.ssadata}")

        self.ssa_events = self.ssadata.events
        self.ssa_events.sort(key=lambda x: x.start)

        pool = self.ssa_events
        self.groups = []
        while len(pool) > 0:
            e = pool.pop(0)
            ignored = False
            if substrreplace_regex:
                new_subtitle_line = re.sub(substrreplace_regex, '', e.plaintext)
                if new_subtitle_line == e.plaintext:
                    pass
                else:
                    logging.debug(f"substrfilter: modified line:\nold line: {e.plaintext}\nnew line: {new_subtitle_line}")
                    # is the line now empty or contains only spaces or punctuation/symbols
                    if len(new_subtitle_line) == 0 or \
                       new_subtitle_line.isspace() or \
                       len(new_subtitle_line.translate(punct_tbl)) == 0:
                        if substrreplace_nokeepchanges:
                            # mark as non-dialogue
                            ignored = True
                        else:
                            # remove entirely
                            continue
                    # do we want to use the original e.plaintext or the stripped and non-empty new_subtitle_line?
                    if not substrreplace_nokeepchanges:
                        e.plaintext = new_subtitle_line
            if self.ignore_range is not None:
                if any([overlap_range(ir, [e.start, e.end]) for ir in self.ignore_range]):
                    trimmed = ignore_nibble(self.ignore_range, e)
                    pool = trimmed + pool
                    continue  # trimmed events may still overlap other ranges, will need to retest
            self.groups.append(SubGroup([e], ephemeral=ignored or not is_dialogue(e, include_all, regex),
                                        threshold=self.threshold,
                                        padding=self.padding))

    def merge_groups(self):
        merged = []
        self.ephemeral = []
        for group in self.groups:
            # ephermal groups are not merged with any other groups so they can be dealt with seperately
            if group.contains_only_ephemeral:
                self.ephemeral.append(group)
                continue
            if len(merged) == 0:  # first group
                merged.append(group)
                continue
            if merged[-1].group_limits[1] > group.group_limits[0]:
                merged[-1].events += group.events
            else:
                merged.append(group)
        self.groups = merged
        logging.debug(f"Merged groups {merged}")
        # add ephemeral groups back into rest of groups
        for egroup in self.ephemeral:  # assuming each egroup contains one ssaevent
            for group in self.groups:
                # if egroup is valid inside group range
                    # create a new ssaevent from egroup that fits inside group
                if group.group_range[0] < egroup.events_start < group.group_range[1] or \
                group.group_range[0] < egroup.events_end < group.group_range[1]:
                    new_event = egroup.events[0].copy()
                    new_event.start = new_event.start if new_event.start > group.group_range[0] else group.group_range[0]
                    new_event.end = new_event.end if new_event.end < group.group_range[1] else group.group_range[1]
                    group.ephemeral_events.append(new_event)
        logging.debug("Inserted ephemeral events")

    def get_times(self):
        # returns list of tuples of group ranges
        times = []
        for g in self.groups:
            times.append(g.group_range)
        return times

    def condense(self):
        r"""
        laststart = 0
        for each group g
            shift all event times in g back by g.group_range[0] - laststart milliseconds
        :return:
        """
        laststart = 0
        groups = copy.deepcopy(self.groups)
        for g in groups:
            shift = g.group_range[0] - laststart
            for e in g.events:
                e.start -= shift
                e.end -= shift
            for e in g.ephemeral_events:
                e.start -= shift
                e.end -= shift
            laststart = g.group_range[1]
        logging.debug("Shifted subtitle groups")
        # extract shifted SSAevents
        condensed_events = []
        for g in groups:
            for e in g.events:
                condensed_events.append(e)
            for e in g.ephemeral_events:
                condensed_events.append(e)
        self.condensed_ssadata = copy.copy(self.ssadata)
        self.condensed_ssadata.events = condensed_events


def decide_partitions(sub_times, partition=0):
    if partition == 0:
        return [(0, len(sub_times)), ]

    partitions = list()
    current_partition = 0
    start = 0
    idx = 0
    for idx, t in enumerate(sub_times):
        current_partition_boundary = (current_partition + 1) * partition
        if t[1] > current_partition_boundary:
            if abs(t[1] - current_partition_boundary) < abs(sub_times[idx - 1][1] - current_partition_boundary):
                end = idx + 1
            else:
                end = idx
            partitions.append((start, end))
            current_partition += 1
            start = end
    end = idx + 1
    partitions.append((start, end))
    return partitions


def split_times(sub_times, partition_indicies, splitsize=0):
    partition_times = sub_times[partition_indicies[0]:partition_indicies[1]]
    if splitsize == 0:
        return [partition_times, ]

    prev = 0
    for idx, time in enumerate(sub_times):
        time.append(time[1] - time[0] + prev)
        prev = time[2]

    start = 0
    idx = 0
    splits = list()
    current_split = 0
    for idx, t in enumerate(partition_times):
        current_partition_boundary = (current_split + 1) * splitsize
        if t[2] > current_partition_boundary:
            if abs(t[2] - current_partition_boundary) < abs(partition_times[idx - 1][2] - current_partition_boundary):
                end = idx + 1
            else:
                end = idx
            splits.append((start, end))
            current_split += 1
            start = end
    end = idx + 1
    splits.append((start, end))
    splittimes = list()
    for split in splits:
        tmp = partition_times[split[0]:split[1]]
        tmp = [[x[0], x[1]] for x in tmp]
        splittimes.append(tmp)
    return splittimes


def partition_and_split(sub_times, partition_size=0, split_size=0):
    # returns a list tuple index pairs in [start, end) format for sub_times
    partitions = decide_partitions(sub_times,
                                   partition=partition_size)
    """
    partition1
        split1
            time1
                start
                end
            time2
                ...
        split2
            time1
        split3
        split4...
    partition2
        split1
            time1
            time2...
    """
    divided_times = list()
    for p, partition_size in enumerate(partitions):
        # returns list of list of times in milliseconds, can feed into condense_audio
        times = split_times(sub_times, partition_size,
                            splitsize=split_size)
        divided_times.append(times)

    return divided_times


# given raw subtitle timing data, merge overlaps and perform padding and merging
# DEPRECIATED
def merge_times(times: [], threshold=0, padding=0):
    # padding: time to add to the beginning and end of each subtitle. Resulting overlaps are removed.
    # threshold: if two subtitles are within this distance apart, they will be merged in the audio track
    times.sort(key=lambda x: x[0])  # sort by first value in tuple

    initial = len(times)
    if padding > 0:
        for time in times:
            time[0] -= padding
            time[1] += padding

    # even if threshold is 0 any added padding may cause overlaps, which the code below will also merge
    idx = 0
    while idx < len(times) - 1:
        if times[idx + 1][0] < times[idx][1] + threshold:
            # if the next subtitle starts within 3 seconds of the current subtitle finishing, merge them
            times[idx][1] = times[idx + 1][1]
            del times[idx + 1]
            if idx < len(times) - 1:
                continue
        idx += 1

    logging.info(f"Merged {initial} subtitles into {len(times)} audio snippets\n")
    logging.debug(f"Merged times: {times}")
    return times

_alignment_re = re.compile(r"{\\an?\d+?}")

# examine a subtitle's text and determine if it contains text or just signs/song styling
# could be much more robust, by including regexes
def is_dialogue(line, include_all=False, regex=None):
    if regex is not None:
        p = re.compile(regex)
        logging.debug(f"using regex {regex} for subtitle search")
        m = p.findall(line.text)
        if len(m) >= 1:
            logging.debug(f'Regex {regex} found match(s) in "{line.text}": {m}')
            return False
        return True
    if include_all:  # ignore filtering
        return True

    # list of characters that, if present anywhere in the subtitle text, means that the subtitle is not dialogue
    globally_invalid = ["♪", "♪"]
    if any(invalid in line.text for invalid in globally_invalid):
        return False

    if line.type != "Dialogue":
        return False
    if len(line.text) == 0:
        return False
    if '{' == line.text[0]:
        return bool(_alignment_re.search(line.text))
    if '（' == line.text[0] and '）' == line.text[-1]:
        return False

    return True


# given a path to a subtitle file, load it in and strip it of non-dialogue text
# keyword arguments are filter options that are passed to is_spoken_dialogue for filtering configuration
# DEPRECIATED
def load_subtitle_times(subfile: Path, include_all_lines=False):
    # if dry_run:
    #     print("dry_run: will load", subfile)
    #     if os.path.isfile(subfile) is False:
    #         print(f"note: {subfile} doesn't exist yet, skipping subtitle loading")
    #         return [[0, 0], ]  # might just be a demuxed file that hasn't been demuxed yet
    logging.info(f"loading {subfile}")
    try:
        subs = ps2.load(str(subfile))
    except (ValueError, AttributeError) as e:
        logger = logging.getLogger(__name__)
        logger.exception(e)
        logging.warning(f"pysub2 enountered error loading subtitle file {subfile}, trying a different subtitle file...")
        return None
    logging.info(subs)

    times = list()
    count = 0
    for idx, line in enumerate(subs):
        # print(line)
        if is_dialogue(line, include_all=include_all_lines):
            # print(line)
            times.append([line.start, line.end])
        else:
            logging.debug(f"ignoring {line.text}, probably not spoken dialogue")
            count += 1
            pass
    logging.info(f"ignored {count} lines")  # number of subtitles that looked like they didn't contain dialogue

    # print(times)
    if len(times) == 0:
        logging.warning(f"warning: got 0 dialogue lines from subtitle file {subfile}")
        return None
    return times


def get_partitioned_and_split_times_duration(sub_times):
    r"""
    Calculates the total amount of condensed audio to be generated from the subtitle times, in milliseconds
    :param sub_times:
    :return: time in milliseconds
    """
    total = list()
    for split in sub_times:
        for partition in split:
            for x1, x2 in partition:
                total.append(x2 - x1)
    subs_total = sum(total)
    return subs_total


# don't use: not reliable
# def get_audiostream_duration(stream_info):
#     sps = int(
#         stream_info['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
#     samples = stream_info['duration_ts']  # total samples in audio track
#     audio_total = samples / sps * 1000
#     return audio_total


def get_audiofile_duration(audiofile: Path):
    stream_idx = 0
    audio_info = ffmpeg.probe(str(audiofile), cmd='ffprobe')
    sps = int(
        audio_info['streams'][stream_idx]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
    samples = audio_info['streams'][stream_idx]['duration_ts']  # total samples in audio track
    audio_total = samples / sps * 1000
    return audio_total


def get_compression_ratio(sub_times, audiofile: Path, verbose=True):
    # audio_info = ffmpeg.probe(str(audiofile), cmd='ffprobe')
    # sps = int(
    #     audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling freq
    # samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track
    # audio_total = samples / sps * 1000
    audio_total = get_audiofile_duration(audiofile)
    # total = list()
    # for split in sub_times:
    #     for partition in split:
    #         for x1, x2 in partition:
    #             total.append(x2-x1)
    # subs_total = sum(total)
    subs_total = get_partitioned_and_split_times_duration(sub_times)
    if verbose:
        logging.info(f"will condense {str(timedelta(milliseconds=audio_total)).split('.')[0]} of source audio to "
                     f"{str(timedelta(milliseconds=subs_total)).split('.')[0]} "
                     f"({round(subs_total / audio_total * 100, 1)}% compression ratio) of condensed audio")
    return subs_total / audio_total
