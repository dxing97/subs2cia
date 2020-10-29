from subs2cia.sources import AVSFile

from typing import List, Union
from pathlib import Path


class Common:
    def __init__(self, sources: List[AVSFile], outdir: Union[Path, None], condensed_video: bool, padding: int,
                 demux_overwrite_existing: bool, overwrite_existing_generated: bool,
                 keep_temporaries: bool, target_lang: str, out_audioext: str,
                 use_all_subs: bool, subtitle_regex_filter: str, audio_stream_index: int, subtitle_stream_index: int,
                 ignore_range: Union[List[List[int]], None]):
        if outdir is None:
            self.outdir = sources[0].filepath.parent
        else:
            self.outdir = outdir

        self.sources = sources
        self.outstem = sources[0].filepath.stem

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
