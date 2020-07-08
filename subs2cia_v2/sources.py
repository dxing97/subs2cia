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
            logging.warning(f"Couldn't probe file, skipping {str(f)}. ffmpeg output: \n" + e.stderr.decode("utf-8"))

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



class SourceFiles:
    def __init__(self, infiles: [Path]):


        for f in infiles:
            if f.is_dir():
                # todo: batchng with directories
                logging.debug("is dir")

        for f in infiles:
            if not f.exists():
                raise AssertionError(f"File {str(f)} doesn't exist")

        infiles.sort()

        pretty = ['\n'] + ['\t' + str(file) + '\n' for file in infiles]
        logging.info(f"Input files: {''.join(pretty)}")

        self.infiles = [AVSFile(f) for f in infiles]


    # for each input file, determine if its a video, subtitle, or audio file by reading their info
    def probe_files(self):
        for f in self.infiles:
            f.probe()

    def determine_types(self):
        for f in self.infiles:
            f.get_type()

    def bin_by_type(self):
        ret = defaultdict(list)
        for f in self.infiles:
            if f.type is not None:
                ret[f.type].append(f)
        return ret
"""
for each input file, determine their type
figure out how many output files to write (may need to be interactive)
    what inputs get mapped to which outputs?
    
do output files
"""