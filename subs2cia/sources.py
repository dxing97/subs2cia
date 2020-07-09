# each output has a set of possible input files
# all source_files does is take all of the input files and partitons them into three lists:

from pathlib import Path
import logging
import ffmpeg
from collections import defaultdict
from subs2cia.ffmpeg_tools import ffmpeg_demux
import pycountry



class AVSFile:
    def __init__(self, filepath: Path):
        if not filepath.exists():
            raise AssertionError(f"File {filepath} does not exist")
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

    def __init__(self, file: AVSFile, type, index=None):
        self.file = file
        self.index = index
        self.type = type
        # index of None indicates that demuxing with ffmpeg is not nessecary to extract data
        self.demux_file = None
        self.lang = 'unknownlang'
    def is_standalone(self):
        if self.index is None:
            return True
        return False

    def get_language(self):
        if self.lang != 'unknownlang':
            return self.lang.alpha_2
        if self.is_standalone():
            # no metadata to analyze, look in suffixes for language codes
            suffixes = self.file.filepath.suffixes
            if len(suffixes) >= 2:
                if suffixes[-2] != 'forced':
                    self.lang = suffixes[-2]
                elif len(suffixes) != 2:
                    self.lang = suffixes[-3]
            if self.lang == 'unknownlang':
                return self.lang
            try:
                lang = pycountry.languages.lookup(self.lang)
            except:
                logging.warning(f"{self.lang} is not a language, treating {self.file.filepath} as unknown language")
                self.lang = 'unknownlang'
                return self.lang
            self.lang = lang
            return self.lang.alpha_2
        # look at metadata for language codes
        if 'tags' not in self.file.info['streams'][self.index]:
            return self.lang
        if 'language' not in self.file.info['streams'][self.index]['tags']:
            return self.lang
        self.lang = pycountry.languages.lookup(self.file.info['streams'][self.index]['tags']['language'])
        # todo: catch exceptions here
        return self.lang.alpha_2


    def demux(self, overwrite_existing: bool):
        demux_path = self.file.filepath
        if not self.is_standalone():
            if self.type == 'subtitle':
                # demux_path = self.file.filepath.parent / Path(f'{self.file.filepath.name}.stream{self.index}.{self.type}.{self.get_language()}.srt')
                # todo: bitmap subtitles
                extension = 'ass'

            if self.type == 'audio':
                # todo: demux file type picker
                extension = 'flac'
            demux_path = self.file.filepath.parent / Path(f'{self.file.filepath.name}.stream{self.index}.{self.type}.{self.get_language()}.{extension}')

            if overwrite_existing or not demux_path.exists():
                demux_path = ffmpeg_demux(self.file.filepath, self.index, demux_path)
                if demux_path is None:
                    logging.error(f"Couldn't demux stream {self.index} from {str(self.file.filepath)} (type={self.type})")
                    return
        self.demux_file = AVSFile(demux_path)
        self.demux_file.probe()
        self.demux_file.get_type()
        return self.demux_file

    def cleanup_demux(self):
        if self.demux_file is not None and self.index is not None:
            logging.info(f"Deleting temporary file {str(self.demux_file.filepath)}")
            self.demux_file.filepath.unlink()

    # return a readable path to the data
    def get_data_path(self) -> Path:
        if self.is_standalone() or self.type == 'video':
            return self.file.filepath
        else:
            return self.demux_file.filepath

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
            if common < longest:
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