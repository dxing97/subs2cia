# each output has a set of possible input files
# all source_files does is take all of the input files and partitons them into three lists:

from subs2cia.ffmpeg_tools import ffmpeg_demux

from pathlib import Path
import logging
import ffmpeg
import pycountry
from typing import List, Union
from collections import defaultdict



class AVSFile:
    def __init__(self, filepath: Path):
        if not filepath.exists():
            raise AssertionError(f"File {filepath} does not exist")
        # don't handle directories here
        self.filepath = filepath
        self.info = None
        self.type = None

    # returns string-encoded type (subtitle, audio, video)
    # determining type may just be as simple as reading the extension
    # but sometimes its better to use a parser and make sure the extension is correct
    def probe(self):
        logging.debug(f"Probing {self.filepath}")
        try:
            self.info = ffmpeg.probe(str(self.filepath), 'ffprobe', **{'show_chapters': None})
        except ffmpeg.Error as e:
            logging.warning(
                f"Couldn't probe file, skipping {str(self.filepath)}. ffmpeg output: \n" + e.stderr.decode("utf-8"))

        logging.debug(f"ffprobe results: {self.info}")

    def get_type(self):
        if self.info is None:  # ffprobe probably failed for some reason
            self.type = 'unknown'
            return
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
            logging.warning(f"File {str(self.filepath)} contains no audio or subtitle tracks!")
        self.type = stream['codec_type']

    def __str__(self):
        return f"{str(self.filepath)} ({self.type})"

    def __repr__(self):
        return f"AVSFile(filepath={self.filepath.__repr__()})"


# single ffmpeg stream
class Stream:
    index = None

    def __init__(self, file: AVSFile, type, stream_info, index=None, ):
        self.file = file
        self.index = index
        self.type = type
        # index of None indicates that demuxing with ffmpeg is not nessecary to extract data
        self.demux_file = None
        self.lang = 'unknownlang'
        self.stream_info = stream_info

        self.get_language()

    def is_standalone(self):
        if self.index is None:
            return True
        return False

    def __str__(self):
        if self.is_standalone():
            return f"standalone {self.stream_info['codec_name']} {self.type} at {str(self.file)}"
        else:
            return f"stream {self.index} ({self.type}, {f'{self.lang.name}, ' if self.lang != 'unknownlang' else ''}{self.stream_info['codec_name']}) in {self.file}"

    def __repr__(self):
        return f"Stream(file={self.file.__repr__()}, type={self.type}, index={self.index})"

    def get_language(self):
        if self.lang != 'unknownlang':
            return self.lang.alpha_3
        if self.is_standalone():
            # no metadata to analyze, look in suffixes for language codes
            suffixes = self.file.filepath.suffixes
            if len(suffixes) >= 2:
                if suffixes[-2] != '.forced':
                    self.lang = suffixes[-2][1:]
                elif len(suffixes) != 2:
                    self.lang = suffixes[-3][1:]
            if self.lang == 'unknownlang':
                return self.lang
            try:
                lang = pycountry.languages.lookup(self.lang)
            except:
                logging.warning(f"{self.lang} is not a language, treating {self.file.filepath} as unknown language")
                self.lang = 'unknownlang'
                return self.lang
            self.lang = lang
            return self.lang.alpha_3
        # look at metadata for language codes
        if 'tags' not in self.file.info['streams'][self.index]:
            return self.lang
        if 'language' not in self.file.info['streams'][self.index]['tags']:
            return self.lang
        try:
            self.lang = pycountry.languages.lookup(self.file.info['streams'][self.index]['tags']['language'])
        except LookupError as e:
            logging.warning(f"{self} language {self.file.info['streams'][self.index]['tags']['language']} is not a "
                            f"proper language code, setting to unknown language.")
            self.lang = 'unknownlang'
            return self.lang
        return self.lang.alpha_3

    def demux(self, overwrite_existing: bool):
        if self.demux_file is not None:
            return self.demux_file
        demux_path = self.file.filepath
        if not self.is_standalone():
            if self.type == 'subtitle':
                subtitle_mapping = {
                    'subrip': 'srt',
                    'ass': 'ass'
                }
                # todo: bitmap subtitles
                if self.stream_info is not None and 'codec_name' in self.stream_info:
                    if self.stream_info['codec_name'] not in subtitle_mapping:
                        extension = 'ass'
                        logging.warning(f"Unknown subtitle type {self.stream_info['codec_name']} found, "
                                     f"will attempt to convert to .ass")
                    else:
                        extension = subtitle_mapping[self.stream_info['codec_name']]

            if self.type == 'audio':
                # we could change what type to demux as similarly to subtitles,
                # but it may cause compatability issues down the road so let's
                # keep it as flac for now
                extension = 'flac'
            demux_path = self.file.filepath.parent / Path(
                f'{self.file.filepath.name}.stream{self.index}.{self.type}.{self.get_language()}.{extension}')

            if overwrite_existing or not demux_path.exists() or demux_path.stat().st_size == 0:
                demux_path = ffmpeg_demux(self.file.filepath, self.index, demux_path)
                if demux_path is None:
                    logging.error(
                        f"Couldn't demux stream {self.index} from {str(self.file.filepath)} (type={self.type})")
                    return None
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
    return i + 1


def is_language(s):
    try:
        pycountry.languages.lookup(s)
        return True
    except:
        return False


# Strip extensions and language info from local assets, Plex style.
# see https://support.plex.tv/articles/200471133-adding-local-subtitles-to-your-media/
def strip_extensions(p: Path) -> Path:
    if len(p.suffixes) <= 1:
        return p.with_suffix('')
    p = p.with_suffix('')
    if len(p.suffixes) >= 1:
        if p.suffixes[-1] == '.forced':
            p = p.with_suffix('')
    if len(p.suffixes) >= 1:
        lcode = p.suffixes[-1]
        lcode = lcode.replace('.', '')
        if is_language(lcode):
            return p.with_suffix('')
        # return p
    return p


def group_names_better(sources: List[AVSFile]) -> List[List[AVSFile]]:
    all_groups = []
    while(len(sources) > 0):
        group = [sources.pop(0)]
        to_remove = []
        for f in sources:
            if strip_extensions(f.filepath) == strip_extensions(group[0].filepath):
                group.append(f)
                to_remove.append(f)
        for f in to_remove:
            sources.remove(f)
        all_groups.append(group)
    return all_groups


def group_files(sources: [AVSFile]):
    file_groups = group_names_better(sources)
    logging.debug(f"groups: {[[f.filepath for f in g] for g in file_groups]}")
    return file_groups


def get_and_partition_streams(sources: List[AVSFile]):
    partitioned_streams = defaultdict(list)
    for sourcefile in sources:
        if sourcefile.type == 'video':
            # dig into streams
            for idx, stream_info in enumerate(sourcefile.info['streams']):
                stype = stream_info['codec_type']
                partitioned_streams[stype].append(Stream(file=sourcefile, type=stype,
                                                              index=idx, stream_info=stream_info))
            continue
        if sourcefile.info is None:
            # ffmpeg couldn't probe this, so skip it
            logging.info(f'Skipping input file "{sourcefile.filepath}": ffmpeg couldn\'t probe')
            continue
        partitioned_streams[sourcefile.type].append(Stream(file=sourcefile, type=sourcefile.type,
                                                                stream_info=sourcefile.info['streams'][0],
                                                                index=None))
        # for stream in sourcefile
    for k in partitioned_streams:
        # logging.debug(f"Found {len(partitioned_streams[k])} {k} input streams")
        logging.debug(f"{k} streams found: {partitioned_streams[k]}")
    return partitioned_streams
