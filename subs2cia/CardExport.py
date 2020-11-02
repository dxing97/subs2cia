from subs2cia.sources import AVSFile
from subs2cia.Common import Common, interactive_picker

from typing import List, Union
from pathlib import Path
import logging

class CardExport(Common):
    def __init__(self, sources: List[AVSFile], outdir: Path, outstem: Union[str, None], condensed_video: bool, padding: int,
                 demux_overwrite_existing: bool, overwrite_existing_generated: bool,
                 keep_temporaries: bool, target_lang: str, out_audioext: str,
                 use_all_subs: bool, subtitle_regex_filter: str, audio_stream_index: int, subtitle_stream_index: int,
                 ignore_range: Union[List[List[int]], None], bitrate: Union[int, None], mono_channel: bool):
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
            bitrate=bitrate,
            mono_channel=mono_channel
        )

        self.insufficient = False

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
            if subfile is None:
                logging.warning(f"Error while demuxing {self.picked_streams[k]}")
                self.picked_streams[k] = None

    def export(self):
        pass
