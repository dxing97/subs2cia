from subs2cia.Common import Common, interactive_picker, chapter_timestamps
from subs2cia.sources import AVSFile
from subs2cia.pickers import picker
from subs2cia.sources import Stream
import subs2cia.subtools as subtools
from subs2cia.ffmpeg_tools import export_condensed_audio, export_condensed_video

import logging
from collections import defaultdict
from pathlib import Path
from typing import Union, List


class Condense(Common):
    # todo: shouldn't we just use **kwargs here?
    def __init__(self, sources: [AVSFile], outdir: Path, outstem: Union[str, None], condensed_video: bool,
                 threshold: int, padding: int, partition: int, split: int, demux_overwrite_existing: bool,
                 overwrite_existing_generated: bool, keep_temporaries: bool, target_lang: str, out_audioext: str,
                 minimum_compression_ratio: float, use_all_subs: bool, subtitle_regex_filter: str,
                 subtitle_regex_substrfilter: str, subtitle_regex_substrfilter_nokeep: bool,
                 audio_stream_index: int, subtitle_stream_index: int, ignore_range: Union[List[List[int]], None],
                 ignore_chapters: Union[List[str], None], bitrate: Union[int, None], mono_channel: bool,
                 interactive: bool, no_condensed_subtitles: bool, out_audiocodec: str):
        super(Condense, self).__init__(
            sources=sources,
            outdir=outdir,
            outstem=outstem,
            condensed_video=condensed_video,
            padding=padding,
            demux_overwrite_existing=demux_overwrite_existing,
            overwrite_existing_generated=overwrite_existing_generated,
            keep_temporaries=keep_temporaries,
            target_lang=target_lang,
            out_audioext=out_audioext,
            use_all_subs=use_all_subs,
            subtitle_regex_filter=subtitle_regex_filter,
            # subtitle_regex_substrfilter=subtitle_regex_substrfilter,
            # subtitle_regex_substrfilter_nokeep=subtitle_regex_substrfilter_nokeep,
            audio_stream_index=audio_stream_index,
            subtitle_stream_index=subtitle_stream_index,
            ignore_range=ignore_range,
            ignore_chapters=ignore_chapters,
            bitrate=bitrate,
            mono_channel=mono_channel,
            interactive=interactive,
            out_audiocodec=out_audiocodec
        )
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

        self.out_subext = None  # extensions must contain dot

        logging.debug(f"Mapping input file(s) {sources} to one output file")

        self.threshold = threshold
        self.partition = partition
        self.split = split

        self.subdata = None
        self.dialogue_times = None
        self.minimum_compression_ratio = minimum_compression_ratio

        self.condensed_audio = True  # can be exposed later if needed
        self.condensed_video = condensed_video
        self.condensed_subtitles = not no_condensed_subtitles  # can be exposed later if needed

        self.subtitle_outfile = None

    def choose_subtitle(self, interactive: bool):
        if len(self.partitioned_streams['subtitle']) == 0:
            logging.warning(f"Couldn't find audio streams in input files")
            return
        k = 'subtitle'
        while True:
            if interactive and len(self.partitioned_streams['subtitle']) > 1:
                self.picked_streams['subtitle'] = interactive_picker(self.sources, self.partitioned_streams, 'subtitle')
            else:

                k = 'subtitle'
                try:
                    self.picked_streams[k] = next(self.pickers[k])
                except StopIteration as s:
                    logging.critical(f"Input files {self.sources} don't contain usable subtitles")
                    self.insufficient = True
                    return
            subfile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
            if subfile is None:
                logging.warning(f"Error while demuxing {self.picked_streams[k]}")
                self.picked_streams[k] = None
                continue

            assert(self.picked_streams['audio'] is not None)  # must call choose_audio first
            ignore_range = (self.ignore_range or []) + chapter_timestamps(self.picked_streams['audio'].file, self.ignore_chapters or [])
            audiolength = subtools.get_audiofile_duration(self.picked_streams['audio'].demux_file.filepath)
            subdata = subtools.SubtitleManipulator(subfile.filepath,
                                                   threshold=self.threshold, padding=self.padding,
                                                   ignore_range=ignore_range, audio_length=audiolength)
            subdata.load(include_all=self.use_all_subs, regex=self.subtitle_regex_filter,
                         substrreplace_regex='',
                         substrreplace_nokeepchanges=False)
                         # substrreplace_regex=self.subtitle_regex_substrfilter, substrreplace_nokeepchanges=self.subtitle_regex_substrfilter_nokeep)
            if subdata.ssadata is None:
                logging.warning(f"Problem loading subtitle data from {self.picked_streams[k]}")
                self.picked_streams[k] = None
                continue
            subdata.merge_groups()
            times = subdata.get_times()
            ps_times = subtools.partition_and_split(times, self.partition, self.split)

            sublength = subtools.get_partitioned_and_split_times_duration(ps_times)

            compression_ratio = sublength / audiolength
            if compression_ratio < self.minimum_compression_ratio:
                if interactive:
                    resp = input(f"Got compression ratio of {compression_ratio} (ratio of dialogue to total audio), "
                                 f"which is smaller than the minimum"
                                 f" ratio of {self.minimum_compression_ratio}. Continue with picked subtitles? (y/N)")
                    if resp != 'y':
                        continue

                else:
                    logging.warning(f"Got compression ratio of {compression_ratio}, which is smaller than the minimum"
                                 f" ratio of {self.minimum_compression_ratio}"
                                 f"retrying wth different subtitle "
                                 f"file. If too many subtitles are being ignored, try -ni or -R. If the minimum "
                                 f"ratio is too high, try -c.")
                    self.picked_streams[k] = None
                    continue
            self.subdata = subdata
            self.dialogue_times = subtools.partition_and_split(sub_times=times,
                                                               partition_size=1000 * self.partition,
                                                               split_size=1000 * self.split)
            break


    # def process_subtitles(self):
    #     if self.picked_streams['subtitle'] is None:
    #         logging.error(f'No subtitle stream to process for output stem {self.outstem}')
    #         return
    #     if self.insufficient:
    #         return

    def export_subtitles(self):
        if self.picked_streams['subtitle'] is None:
            logging.info(f'No subtitles to process for output {self.outstem}')
            return
        subpath = self.picked_streams['subtitle'].get_data_path()
        subext = subpath.suffix
        self.subdata.condense()

        self.subtitle_outfile = Path(self.outdir) / (
                    self.outstem + f'.condensed{self.out_subext if self.out_subext is not None else subext}')
        self.subdata.condensed_ssadata.save(str(self.subtitle_outfile), encoding=u'utf-8')
        logging.info(f"Wrote condensed subtitles to {self.subtitle_outfile}")

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
                               outfile=outfile, to_mono=self.to_mono, quality=self.quality, codec=self.out_audiocodec)
        # logging.info(f"Wrote condensed audio to {outfile}")

    def export_video(self):
        if self.picked_streams['video'] is None:
            logging.error(f'No video stream to process for output stem {self.outstem}')
            return

        outfile = Path(self.outdir) / (self.outstem + '.mkv')
        # logging.info(f"exporting condensed video to {outfile}")
        if outfile.exists() and not self.overwrite_existing_generated:
            logging.warning(f"Can't write to {outfile}: file exists and not set to overwrite")
            return
        export_condensed_video(self.dialogue_times, audiofile=self.picked_streams['audio'].get_data_path(),
                               subfile=self.subtitle_outfile,
                               videofile=self.picked_streams['video'].get_data_path(),
                               outfile=outfile)
        logging.info(f"Wrote condensed video to {outfile}")
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
