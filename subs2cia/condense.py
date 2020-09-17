from subs2cia.sources import AVSFile
from subs2cia.pickers import picker
from subs2cia.sources import Stream
import subs2cia.subtools as subtools
from subs2cia.ffmpeg_tools import export_condensed_audio, export_condensed_video

import logging
from collections import defaultdict
from pathlib import Path


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


class SubCondensed:
    def __init__(self, sources: [AVSFile], outdir: Path, condensed_video: bool, threshold: int, padding: int,
                 partition: int, split: int, demux_overwrite_existing: bool, overwrite_existing_generated: bool,
                 keep_temporaries: bool, target_lang: str, out_audioext: str, minimum_compression_ratio: float,
                 use_all_subs: bool, subtitle_regex_filter: str, audio_stream_index: int, subtitle_stream_index: int):
        r"""

        :param sources: List of AVSFile objects, each representing one input file
        :param outdir: Output directory to save to. Default is the directory of the first source file in *sources*
        :param condensed_video: If set, generates condensed video as well
        :param threshold:
        :param padding:
        :param partition:
        :param split:
        :param demux_overwrite_existing: If set, demuxing operations will overwrite existing files on disk
        :param overwrite_existing_generated: If set, generation operations will overwrite existing files on disk
        :param keep_temporaries: If set, will not delete demuxed files on cleanup
        :param target_lang: Target language for audio AND subtitles
        :param out_audioext: Output audio extension
        :param minimum_compression_ratio: Chosen subtitle stream must yield generated audio at least this percent long of audio file
        """

        if outdir is None:
            self.outdir = sources[0].filepath.parent
        else:
            self.outdir = outdir
        self.outstem = sources[0].filepath.stem
        self.sources = sources
        self.out_audioext = out_audioext
        self.out_vidoeext = '.mkv'
        self.out_subext = None  # extensions must contain dot

        # logging.debug(f'Will save a file with stem "{self.outstem}" to directory "{self.outdir}"')
        logging.info(f"Mapping input file(s) {sources} to one output file")

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

        self.target_lang = target_lang
        # following indices overrides target_lang, is overridden by standalone input audio/subtitle files
        self.audio_stream_index = audio_stream_index
        self.subtitle_stream_index = subtitle_stream_index

        self.padding = padding
        self.threshold = threshold
        self.partition = partition
        self.split = split

        self.dialogue_times = None
        self.minimum_compression_ratio = minimum_compression_ratio

        self.demux_overwrite_existing = demux_overwrite_existing
        self.overwrite_existing_generated = overwrite_existing_generated
        self.keep_temporaries = keep_temporaries

        self.condensed_audio = True  # can be exposed later if needed
        self.condensed_video = condensed_video
        self.condensed_subtitles = True  # can be exposed later if needed

        self.use_all_subs = use_all_subs
        self.subtitle_regex_filter = subtitle_regex_filter

        self.insufficient = False
        self.subtitle_outfile = None

    # go through source files and count how many subtitle and audio streams we have
    def get_and_partition_streams(self):
        for sourcefile in self.sources:
            if sourcefile.type == 'video':
                # dig into streams
                for idx, stream_info in enumerate(sourcefile.info['streams']):
                    stype = stream_info['codec_type']
                    self.partitioned_streams[stype].append(Stream(file=sourcefile, type=stype,
                                                                  index=idx, stream_info=stream_info))
                continue
            self.partitioned_streams[sourcefile.type].append(Stream(file=sourcefile, type=sourcefile.type,
                                                                    stream_info=sourcefile.info,
                                                                    index=None))
            # for stream in sourcefile
        for k in self.partitioned_streams:
            logging.info(f"Found {len(self.partitioned_streams[k])} {k} input streams")
            # logging.debug(f"Streams found: {self.partitioned_streams[k]}")

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

    def choose_streams(self):
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
                        logging.critical("Input streams for this group are invalid for condensing")
                        self.insufficient = True
                        return
            for k in ['audio', 'subtitle', 'video']:
                # validate picked streams

                # todo: spin off into its own function at a later step
                if k == 'audio':
                    afile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
                    if afile is None:
                        self.picked_streams[k] = None

                if k == 'subtitle':
                    subfile = self.picked_streams[k].demux(
                        overwrite_existing=self.demux_overwrite_existing)  # type AVSFile
                    if subfile is None:
                        self.picked_streams[k] = None
                        continue
                    # times = subtools.load_subtitle_times(subfile.filepath, include_all_lines=self.use_all_subs)
                    subdata = subtools.SubtitleManipulator(subfile.filepath,
                                                           threshold=self.threshold, padding=self.padding)
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
                    audiolength = subtools.get_audiofile_duration(
                        self.picked_streams['audio'].demux_file.filepath)
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

    def process_subtitles(self):
        if self.picked_streams['subtitle'] is None:
            logging.error(f'No subtitle stream to process for output stem {self.outstem}')
            return
        if self.insufficient:
            return
        logging.debug("process_subtitles merged into choose_streams")
        # subfile = self.picked_streams['subtitle'].demux(overwrite_existing=self.demux_overwrite_existing)
        # times = subtools.load_subtitle_times(subfile.filepath)
        # times = subtools.merge_times(times, threshold=self.threshold, padding=self.padding)
        # self.dialogue_times = subtools.partition_and_split(sub_times=times, partition_size=1000*self.partition,
        #                                                    split_size=1000*self.split)

    def export_subtitles(self):
        if self.picked_streams['subtitle'] is None:
            logging.info(f'No subtitle stream to process for output stem {self.outstem}')
            return
        subpath = self.picked_streams['subtitle'].get_data_path()
        subext = subpath.suffix
        subdata = subtools.SubtitleManipulator(subpath, threshold=self.threshold, padding=self.padding)
        subdata.load(include_all=self.use_all_subs, regex=self.subtitle_regex_filter)
        subdata.merge_groups()
        subdata.condense()

        self.subtitle_outfile = Path(self.outdir) / (
                    self.outstem + f'.condensed{self.out_subext if self.out_subext is not None else subext}')
        subdata.condensed_ssadata.save(self.subtitle_outfile, encoding=u'utf-8')

    def export_audio(self):
        if self.picked_streams['audio'] is None:
            logging.error(f'No audio stream to process for output stem {self.outstem}')
            return
        outfile = Path(self.outdir) / (self.outstem + f'.{self.out_audioext}')
        # logging.info(f"exporting condensed audio to {outfile}")  # todo: fix output naming
        if outfile.exists() and not self.overwrite_existing_generated:
            logging.warning(f"Can't write to {outfile}: file exists and not set to overwrite")
            return
        export_condensed_audio(self.dialogue_times, audiofile=self.picked_streams['audio'].get_data_path(),
                               outfile=outfile)

    def export_video(self):
        if self.picked_streams['video'] is None:
            logging.error(f'No video stream to process for output stem {self.outstem}')
            return

        outfile = Path(self.outdir) / (self.outstem + '.mkv')
        logging.info(f"exporting condensed video to {outfile}")
        if outfile.exists() and not self.overwrite_existing_generated:
            logging.warning(f"Can't write to {outfile}: file exists and not set to overwrite")
            return
        export_condensed_video(self.dialogue_times, audiofile=self.picked_streams['audio'].get_data_path(),
                               subfile=self.subtitle_outfile,
                               videofile=self.picked_streams['video'].get_data_path(),
                               outfile=outfile)
        return

    def export(self):
        if self.insufficient:
            return
        subtools.get_compression_ratio(self.dialogue_times, self.picked_streams['audio'].demux_file.filepath)
        if self.condensed_subtitles:
            self.export_subtitles()
        if self.condensed_audio:
            self.export_audio()
        if self.condensed_video:
            self.export_video()

    def cleanup(self):
        if self.keep_temporaries:
            return
        for k in ['audio', 'video', 'subtitle']:
            if len(self.partitioned_streams) == 0:
                continue
            for s in self.partitioned_streams[k]:
                s.cleanup_demux()
