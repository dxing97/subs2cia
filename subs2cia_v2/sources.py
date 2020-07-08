# each output has a set of possible input files
# all source_files does is take all of the input files and partitons them into three lists:

from pathlib import Path
import logging
import ffmpeg
from collections import defaultdict




class AVSFile:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.info = None
        self.type = None
    # returns string-encoded type (subtitle, audio, video)
    # determining type may just be as simple as reading the extension
    # but sometimes its better to use a parser and make sure the extension is correct
    def probe(self):
        try:
            self.info = ffmpeg.probe(self.filepath, cmd='ffprobe')
        except ffmpeg.Error as e:
            logging.warning(f"Couldn't probe file, skipping {str(self.filepath)}. ffmpeg output: \n" + e.stderr.decode("utf-8"))

        logging.debug(f"ffmpeg probe results: {self.info}")

    def get_type(self):
        if 'streams' not in self.info:
            logging.warning(f"Unexpected ffmpeg.probe output, ignoring file {str(self.filepath)}")
            logging.debug(self.info)
            self.type = None
            return
        if len(self.info['streams']) > 1:
            self.type = 'video'  # video files are treated as multi-stream objects
            return
        stream = self.info['streams'][0]
        if stream['codec_type'] == 'video':
            logging.info(f"File {str(self.filepath)} contains no audio or subtitle tracks!")
        self.type = stream['codec_type']


# single ffmpeg stream
class Stream:
    index = None

    def __init__(self, file: AVSFile, index=None):
        self.file = file
        self.index = index
        # index of None indicates that demuxing with ffmpeg is not nessecary to extract data

    def is_standalone(self):
        if self.index is None:
            return True
        return False

    def get_language(self):  # TODO
        pass

def common_count(t0, t1):
    # returns the length of the longest common prefix
    i = 0
    for i, pair in enumerate(zip(t0, t1)):
        if pair[0] != pair[1]:
            return i
    return i


def group_by_longest_prefix(sources: [AVSFile]):
    files = sources
    out = []
    longest = 0
    for f in files:
        splits = str(f.filepath.name).split('.')
        if out:
            common = common_count(splits, str(out[-1].filepath.name).split('.'))
            if common <= longest:
                yield out
                longest = 0
                out = []
                # otherwise, just update the target prefix length
            else:
                longest = common

                # add the current entry to the group
        out.append(f)

    # return remaining entries as the last group
    if out:
        yield out


def group_files(sources: [AVSFile]):
    file_groups = list(group_by_longest_prefix(sources))
    logging.debug(f"groups: {[[f.filepath for f in g] for g in file_groups]}")
    return file_groups