from subs2cia_v2.streams import Stream
from subs2cia_v2.ffmpeg_tools import ffmpeg_demux
import logging
import pysubs2 as ps2  # for reading in subtitles
from pathlib import Path


# given raw subtitle timing data, merge overlaps and perform padding and merging
def merge_times(times, threshold=0, padding=0):
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

    print(f"merged {initial} subtitles into {len(times)} audio snippets\n")
    return times


# examine a subtitle's text and determine if it contains text or just signs/song styling
# could be much more robust, by including regexes
def is_not_dialogue(line, include_all=False):
    if include_all:  # ignore filtering
        return True
    if line.type != "Dialogue":
        return False
    if len(line.text) == 0:
        return False
    if line.text[0] == '{':
        return False

    # list of characters that, if present anywhere in the subtitle text, means that the subtitle is not dialogue
    globally_invalid = ["♪", "♪"]
    if any(invalid in line.text for invalid in globally_invalid):
        return False
    return True


# given a path to a subtitle file, load it in and strip it of non-dialogue text
# keyword arguments are filter options that are passed to is_spoken_dialogue for filtering configuration
# todo: rewrite this to keep text information while merging, so subs can be loaded for condensed video
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
        if is_not_dialogue(line, include_all=include_all_lines):
            # print(line)
            times.append([line.start, line.end])
        else:
            # print(f"ignoring {line.text}, probably not spoken dialogue")
            count += 1
            pass
    logging.info(f"ignored {count} lines")  # number of subtitles that looked like they didn't contain dialogue

    # print(times)
    if len(times) == 0:
        print("warning: got 0 dialogue lines from subtitle")
    return times


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


