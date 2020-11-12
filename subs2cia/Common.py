from subs2cia.sources import AVSFile
from subs2cia.pickers import picker
from subs2cia.sources import Stream, get_and_partition_streams
import subs2cia.subtools as subtools
from subs2cia.ffmpeg_tools import export_condensed_audio, export_condensed_video

from typing import List, Union, Dict
from collections import defaultdict
from pathlib import Path

import logging


def picked_sources_are_insufficient(d: dict):
    for k in d:
        if d[k] == 'retry':
            return True
    if d['subtitle'] is None:
        return True
    if d['audio'] is None:
        return True
    return False


def insufficient_source_streams(d: dict):
    if len(d['subtitle']) == 0:
        return True
    if len(d['audio']) == 0:
        return True
    return False


def chapter_timestamps(sourcefile: AVSFile, ignore_chapters: List[str]):
    if len(ignore_chapters) == 0:
        return []

    chapters = sourcefile.info['chapters'] or []

    if len(chapters) == 0:
        return []

    chapters_by_title = {c['tags']['title']: c for c in chapters}
    timestamps = []

    for title in ignore_chapters:
        if title in chapters_by_title:
            chapter = chapters_by_title[title]
            timestamps.append([('', 1000 * int(float((chapter['start_time'])))), ('', 1000 * int(float(chapter['end_time'])))])
        else:
            logging.warning(f"Chapter '{title}' was specified to be ignored, but it was not found")

    return timestamps

def interactive_picker(sources: List[AVSFile], partitioned_streams: Dict[str, Stream], media_type: str):
    print("Input files:")
    for avsf in sources:
        print(f"\t{avsf}")
    print(f"Found the following {media_type} streams:")
    for idx, stream in enumerate(partitioned_streams[media_type]):
        desc_str = ''
        if "codec_name" in stream.stream_info:
            desc_str = desc_str + "codec: " + stream.stream_info['codec_name'] + ", "
        if media_type == 'video':
            if 'width' in stream.stream_info and 'height' in stream.stream_info:
                desc_str = desc_str + f"{stream.stream_info['width']}x{stream.stream_info['height']}, "
        if media_type == 'audio':
            if "tags" in stream.stream_info:
                tags = stream.stream_info['tags']
                if "language" in tags:
                    desc_str = desc_str + "lang_code: " + tags['language'] + ", "
                if "title" in tags:
                    desc_str = desc_str + "title: " + tags['title'] + ", "
        if desc_str == '':
            desc_str = f"\tStream {idx: 3}: no information found, "
        else:
            desc_str = f"\tStream {idx: 3}: {desc_str}"
        desc_str += f"file: {str(stream.file)}"
        print(desc_str)
    print("")
    idx = int(input("Which stream to use?"))
    return partitioned_streams[media_type][idx]


class Common:
    def __init__(self, sources: List[AVSFile], outdir: Union[Path, None], outstem: Union[str, None],
                 condensed_video: bool, padding: int,
                 demux_overwrite_existing: bool, overwrite_existing_generated: bool,
                 keep_temporaries: bool, target_lang: str, out_audioext: str,
                 use_all_subs: bool, subtitle_regex_filter: str, audio_stream_index: int, subtitle_stream_index: int,
                 ignore_range: Union[List[List[int]], None], ignore_chapters: Union[List[str], None],
                 bitrate: Union[int, None], mono_channel: bool, interactive: bool):
        if outdir is None:
            self.outdir = sources[0].filepath.parent
        else:
            self.outdir = outdir

        self.sources = sources
        if outstem is not None:
            self.outstem = outstem
        else:
            self.outstem = sources[0].filepath.stem

        self.partitioned_streams = defaultdict(list)

        self.picked_streams = {
            'audio': None,
            'subtitle': None,
            'video': None
        }

        self.pickers = {
            'audio': None,
            'subtitle': None,
            'video': None
        }

        self.quality = bitrate
        self.to_mono = mono_channel

        self.export_video = condensed_video
        self.padding = padding
        self.demux_overwrite_existing = demux_overwrite_existing
        self.overwrite_existing_generated = overwrite_existing_generated
        self.keep_temporaries = keep_temporaries
        self.target_lang = target_lang

        self.out_audioext = out_audioext
        self.out_videoext = '.mp4'


        self.use_all_subs = use_all_subs
        self.subtitle_regex_filter = subtitle_regex_filter
        self.audio_stream_index = audio_stream_index
        self.subtitle_stream_index = subtitle_stream_index
        # todo: verify ignore_range, make sure start is after end
        self.ignore_range = ignore_range
        self.ignore_chapters = ignore_chapters

        self.insufficient = False

        self.interactive = interactive

    # go through source files and count how many subtitle and audio streams we have
    def get_and_partition_streams(self):
        self.partitioned_streams = get_and_partition_streams(self.sources)
        # for sourcefile in self.sources:
        #     if sourcefile.type == 'video':
        #         # dig into streams
        #         for idx, stream_info in enumerate(sourcefile.info['streams']):
        #             stype = stream_info['codec_type']
        #             self.partitioned_streams[stype].append(Stream(file=sourcefile, type=stype,
        #                                                           index=idx, stream_info=stream_info))
        #         continue
        #     self.partitioned_streams[sourcefile.type].append(Stream(file=sourcefile, type=sourcefile.type,
        #                                                             stream_info=sourcefile.info,
        #                                                             index=None))
        #     # for stream in sourcefile
        # for k in self.partitioned_streams:
        #     logging.info(f"Found {len(self.partitioned_streams[k])} {k} input streams")
        #     # logging.debug(f"Streams found: {self.partitioned_streams[k]}")

    def initialize_pickers(self):
        for k in self.pickers:
            idx = None
            if k == 'audio':
                idx = self.audio_stream_index
            if k == 'subtitle':
                idx = self.subtitle_stream_index
            self.pickers[k] = picker(self.partitioned_streams[k], target_lang=self.target_lang, forced_stream=idx)

    def list_streams(self):
        print(f"Listing streams found in {self.sources}")
        for k in ['subtitle', 'audio', 'video']:
            print(f"Available {k} streams:")
            for idx, stream in enumerate(self.partitioned_streams[k]):
                desc_str = ''
                if "codec_name" in stream.stream_info:
                    desc_str = desc_str + "codec: " + stream.stream_info['codec_name'] + ", "
                if "tags" in stream.stream_info:
                    tags = stream.stream_info['tags']
                    if "language" in tags:
                        desc_str = desc_str + "lang_code: " + tags['language'] + ", "
                    if "title" in tags:
                        desc_str = desc_str + "title: " + tags['title'] + ", "
                if desc_str == '':
                    desc_str = f"Stream {idx: 3}: no information found"
                else:
                    desc_str = f"Stream {idx: 3}: {desc_str}"
                print(desc_str)
            print("")

    def choose_audio(self, interactive: bool):
        r"""
        Picks an audio stream to use. If there are multiple audio streams, prioritizes the following:
            * CLI-specified stream index
            * target language
            * order of appearance
        :param interactive: if true, prompts user about which audio stream to use
        :return:
        """
        if len(self.partitioned_streams['audio']) == 0:
            logging.warning(f"Couldn't find audio streams in input files")
            return
        if interactive and len(self.partitioned_streams['audio']) > 1:
            self.picked_streams['audio'] = interactive_picker(self.sources, self.partitioned_streams, 'audio')
            return

        k = 'audio'
        while self.picked_streams[k] is None:
            try:
                self.picked_streams[k] = next(self.pickers[k])
            except StopIteration as s:
                logging.critical("Inputs don't contain usable audio")
                self.insufficient = True
                return
            afile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
            if afile is None:
                logging.warning(f"Error while demuxing {self.picked_streams[k]}")
                self.picked_streams[k] = None

    def choose_subtitle(self, interactive: bool):
        # pass
        raise NotImplementedError("Child classes must implement choose_subtitles")

    def choose_video(self, interactive: bool):
        if len(self.partitioned_streams['video']) == 0:
            logging.info(f"Couldn't find video streams in input files")
            return
        if interactive and len(self.partitioned_streams['audio']) > 1:
            self.picked_streams['audio'] = interactive_picker(self.sources, self.partitioned_streams, 'video')
            return
        k = 'video'
        while self.picked_streams[k] is None:
            try:
                self.picked_streams[k] = next(self.pickers[k])
            except StopIteration as s:
                logging.critical("Inputs don't contain usable audio")
                self.insufficient = True
                return
            # afile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
            # if afile is None:
            #     logging.warning(f"Error while demuxing {self.picked_streams[k]}")
            #     self.picked_streams[k] = None

    def choose_streams(self):
        if insufficient_source_streams(self.partitioned_streams):
            logging.error(f"Not enough input sources to generate condensed output for output stem {self.outstem} "
                          f"(missing audio and/or subtitles)")
            self.insufficient = True
            return
        self.choose_audio(interactive=self.interactive)
        self.choose_subtitle(interactive=self.interactive)
        self.choose_video(interactive=self.interactive)

        logging.info(f"Picked audio stream:    {self.picked_streams['audio']}")
        logging.info(f"Picked subtitle stream: {self.picked_streams['subtitle']}")
        logging.info(f"Picked video stream:    {self.picked_streams['video']}")

    def choose_streams_old(self):
        if insufficient_source_streams(self.partitioned_streams):
            logging.error(f"Not enough input sources to generate condensed output for output stem {self.outstem}")
            self.insufficient = True
            return
        while picked_sources_are_insufficient(self.picked_streams):
            for k in ['audio', 'video', 'subtitle']:
                if len(self.partitioned_streams[k]) == 0:
                    logging.debug(f"no input streams of type {k}")
                    continue
                if self.picked_streams[k] is None:
                    try:
                        self.picked_streams[k] = next(self.pickers[k])
                    except StopIteration as s:
                        logging.critical("Input streams for this input group are invalid for condensing "
                                         "(missing audio or subtitles)")
                        self.insufficient = True
                        return
            for k in ['audio', 'subtitle', 'video']:
                # validate picked streams


                if k == 'audio':
                    afile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
                    if afile is None:
                        self.picked_streams[k] = None

                # todo: maybe move this back into Condense, split/threshold is a cia thing, not a srs thing,
                #  or have seperate functions for video, audio, and subtitles
                if k == 'subtitle':
                    subfile = self.picked_streams[k].demux(
                        overwrite_existing=self.demux_overwrite_existing)  # type AVSFile
                    if subfile is None:
                        self.picked_streams[k] = None
                        continue
                    # times = subtools.load_subtitle_times(subfile.filepath, include_all_lines=self.use_all_subs)
                    audiolength = subtools.get_audiofile_duration(
                        self.picked_streams['audio'].demux_file.filepath)
                    subdata = subtools.SubtitleManipulator(subfile.filepath,
                                                           threshold=self.threshold, padding=self.padding,
                                                           ignore_range=self.ignore_range, audio_length=audiolength)
                    subdata.load(include_all=self.use_all_subs, regex=self.subtitle_regex_filter)
                    if subdata.ssadata is None:
                        self.picked_streams[k] = None
                        continue
                    if self.picked_streams['audio'] is None:
                        # can't verify subtitle validity until audio candidate is found
                        continue
                    # times = subtools.merge_times(times, threshold=self.threshold, padding=self.padding)
                    subdata.merge_groups()
                    times = subdata.get_times()
                    ps_times = subtools.partition_and_split(times, self.partition, self.split)

                    sublength = subtools.get_partitioned_and_split_times_duration(ps_times)

                    compression_ratio = sublength / audiolength
                    if compression_ratio < self.minimum_compression_ratio:
                        logging.info(f"got compression ratio of {compression_ratio}, which is smaller than the minimum"
                                     f" ratio of {self.minimum_compression_ratio}, retrying wth different subtitle "
                                     f"file. If too many subtitles are being ignored, try -ni or -R. If the minimum "
                                     f"ratio is too high, try -c.")
                        self.picked_streams[k] = None
                        continue
                    self.dialogue_times = subtools.partition_and_split(sub_times=times,
                                                                       partition_size=1000 * self.partition,
                                                                       split_size=1000 * self.split)
                if k == 'video':
                    pass
        logging.info(f"Picked {self.picked_streams['audio']} to use for condensing")
        logging.info(f"Picked {self.picked_streams['video']} to use for condensing")
        logging.info(f"Picked {self.picked_streams['subtitle']} to use for condensing")

    def cleanup(self):
        if self.keep_temporaries:
            return
        for k in ['audio', 'video', 'subtitle']:
            if len(self.partitioned_streams) == 0:
                continue
            for s in self.partitioned_streams[k]:
                s.cleanup_demux()
