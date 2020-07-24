from subs2cia.sources import Stream
from subs2cia.ffmpeg_tools import ffmpeg_demux

import logging
import pysubs2 as ps2  # for reading in subtitles
from pathlib import Path
from datetime import timedelta
import ffmpeg
import re

# TODO
# take a subfile (or SSAFile) and concatenate times down such that it can be muxed into condensed video
# good opportunity to add crude shifts/retiming here
def condense_subtitle():
    pass


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

    logging.info(f"merged {initial} subtitles into {len(times)} audio snippets\n")
    return times


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
    if line.type != "Dialogue":
        return False
    if len(line.text) == 0:
        return False
    if '{' == line.text[0]:
        return False

    # list of characters that, if present anywhere in the subtitle text, means that the subtitle is not dialogue
    globally_invalid = ["♪", "♪"]
    if any(invalid in line.text for invalid in globally_invalid):
        return False
    return True


# given a path to a subtitle file, load it in and strip it of non-dialogue text
# keyword arguments are filter options that are passed to is_spoken_dialogue for filtering configuration
def load_subtitle_times(subfile: Path, include_all_lines=False):
    # if dry_run:
    #     print("dry_run: will load", subfile)
    #     if os.path.isfile(subfile) is False:
    #         print(f"note: {subfile} doesn't exist yet, skipping subtitle loading")
    #         return [[0, 0], ]  # might just be a demuxed file that hasn't been demuxed yet
    logging.info(f"loading {subfile}")
    subs = ps2.load(str(subfile))
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
    audio_info = ffmpeg.probe(str(audiofile), cmd='ffprobe')
    sps = int(
        audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
    samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track
    audio_total = samples / sps * 1000
    return audio_total


def get_compression_ratio(sub_times, audiofile: Path, print=True):
    # audio_info = ffmpeg.probe(str(audiofile), cmd='ffprobe')
    # sps = int(
    #     audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
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
    if print:
        logging.info(f"will condense {str(timedelta(milliseconds=audio_total)).split('.')[0]} of source audio to "
                     f"{str(timedelta(milliseconds=subs_total)).split('.')[0]} "
                     f"({round(subs_total / audio_total * 100, 1)}% compression ratio) of condensed audio")
    return subs_total / audio_total

class Subtitle:
    def __init__(self, stream: Stream, threshold=0, padding=0, include_all_lines=False):
        self.stream = stream
        self.subs = None
        self.include_all_lines = include_all_lines
        self.threshold = threshold
        self.padding = padding

    def load_subs(self):
        if self.stream.index is None:
            self.subs = load_subtitle_times(self.stream.file.filepath, include_all_lines=self.include_all_lines)
        else:
            ffmpeg_demux(self.stream.file)

    def merge(self):
        self.subs = merge_times(self.subs, threshold=self.threshold, padding=self.padding)

    def write_subs(self):
        pass


