from subs2cia.sources import AVSFile
from subs2cia.Common import Common, interactive_picker, chapter_timestamps
import subs2cia.subtools as subtools
from subs2cia.ffmpeg_tools import ffmpeg_trim_audio_clip_atrim_encode, ffmpeg_get_frame_fast, ffmpeg_trim_video_clip_directcopy

from typing import List, Union
from pathlib import Path
import logging
import tqdm
import pandas as pd


class CardExport(Common):
    def __init__(self, sources: List[AVSFile], outdir: Path, outstem: Union[str, None], condensed_video: bool, padding: int,
                 demux_overwrite_existing: bool, overwrite_existing_generated: bool,
                 keep_temporaries: bool, target_lang: str, out_audioext: str,
                 use_all_subs: bool, subtitle_regex_filter: str, audio_stream_index: int, subtitle_stream_index: int,
                 ignore_range: Union[List[List[int]], None], ignore_chapters: Union[List[str], None],
                 bitrate: Union[int, None], mono_channel: bool, interactive: bool, normalize_audio: bool):
        super(CardExport, self).__init__(
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
            audio_stream_index=audio_stream_index,
            subtitle_stream_index=subtitle_stream_index,
            ignore_range=ignore_range,
            ignore_chapters=ignore_chapters,
            bitrate=bitrate,
            mono_channel=mono_channel,
            interactive=interactive
        )

        self.insufficient = False

        self.normalize_audio = normalize_audio

        self.subdata = None

    def choose_subtitle(self, interactive):
        if len(self.partitioned_streams['subtitle']) == 0:
            logging.warning(f"Couldn't find audio streams in input files")
            return
        if interactive and len(self.partitioned_streams['subtitle']) > 1:
            self.picked_streams['subtitle'] = interactive_picker(self.sources, self.partitioned_streams, 'subtitle')
            return

        k = 'subtitle'
        while self.picked_streams[k] is None:
            try:
                self.picked_streams[k] = next(self.pickers[k])
            except StopIteration as s:
                logging.critical(f"Input files {self.sources} don't contain usable subtitles")
                self.insufficient = True
                return
            subfile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
            ignore_range = (self.ignore_range or []) + chapter_timestamps(self.picked_streams[k].file, self.ignore_chapters or [])
            if subfile is None:
                logging.warning(f"Error while demuxing {self.picked_streams[k]}")
                self.picked_streams[k] = None

            audiolength = subtools.get_audiofile_duration(self.picked_streams['audio'].demux_file.filepath)
            subdata = subtools.SubtitleManipulator(subfile.filepath,
                                                   threshold=0, padding=self.padding,
                                                   ignore_range=ignore_range, audio_length=audiolength)
            subdata.load(include_all=self.use_all_subs, regex=self.subtitle_regex_filter)
            if subdata.ssadata is None:
                logging.warning(f"Problem loading subtitle data from {self.picked_streams[k]}")
                self.picked_streams[k] = None
                continue

            self.subdata = subdata

    def export(self):
        # expose these as options at some point
        export_audio = True
        export_screenshot = True
        export_video = False
        lbda = 0.0
        w = -1
        h = -1
        columns = ['text', 'timestamps', 'audioclip', 'screenclip', 'videoclip', 'sources']
        exported = pd.DataFrame(columns=columns)
        for group in tqdm.tqdm(self.subdata.groups):
            # since subdata.merge_groups hasn't been called, each group only contains one SSAevent

            if group.contains_only_ephemeral:
                continue
            row = {'text': group.events[0].plaintext,
                   'timestamps': f"{group.group_range[0]}-{group.group_range[1]}",
                   'audioclip': None,
                   'screenclip': None,
                   'videoclip': None,
                   'sources': f"{self.sources}"[1:-1]}
            if export_audio:
                outpath = self.outdir / (self.outstem + f"({group.group_range[0]}-{group.group_range[1]}).mp3")
                row['audioclip'] = f"[sound:{outpath.name}]"
                ffmpeg_trim_audio_clip_atrim_encode(input_file=self.picked_streams['audio'].demux_file,
                                                    stream_index=0,
                                                    timestamp_start=group.group_range[0],
                                                    timestamp_end=group.group_range[1], quality=self.quality,
                                                    to_mono=self.to_mono, normalize_audio=self.normalize_audio,
                                                    outpath=outpath)
            if export_screenshot:
                outpath = self.outdir / (self.outstem + f"[{group.group_range[0]}-{group.group_range[1]}].jpg")
                row['screenclip'] = f"<img src='{outpath.name}' />"
                timestamp = (1-lbda) * group.group_range[0] + lbda * group.group_range[1]
                ffmpeg_get_frame_fast(self.picked_streams['video'].file,
                                      timestamp=timestamp, outpath=outpath, w=w, h=h)
            if export_video:
                outpath = self.outdir / (self.outstem + f"_{group.group_range[0]}_{group.group_range[1]}.mp4")
                row['videoclip'] = f"[sound:{outpath.name}]"
                ffmpeg_trim_video_clip_directcopy(self.picked_streams['video'].file, timestamp_start=group.group_range[0],
                                                    timestamp_end=group.group_range[1], quality=None, outpath=outpath)
            exported = exported.append([row], ignore_index=True)
        # print(exported)
        outpath = self.outdir / (self.outstem + ".tsv")
        exported.to_csv(outpath, sep='\t')
