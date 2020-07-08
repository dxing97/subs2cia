from subs2cia_v2.sources import AVSFile
from subs2cia_v2.pickers import picker
from subs2cia_v2.sources import Stream

import subs2cia_v2.subtools as subtools
from subs2cia_v2.sources import common_count
from subs2cia_v2.ffmpeg_tools import export_condensed_audio
import logging
from collections import defaultdict


def picked_sources_are_insufficient(d: dict):
    for k in d:
        if d[k] == 'retry':
            return True
    if d['subtitle'] is None:
        return True
    if d['audio'] is None:
        return True
    return False

class SubCondensed:
    def __init__(self, sources: [AVSFile], outdir=None, condensed_video=False, threshold=0, padding=0,
                 partition=0, split=0, demux_overwrite_existing=False, target_lang=None):
        if len(sources) == 1:
            outstem = sources[0].filepath.stem
        else:
            outstem = sources[0].filepath.name[0:1+common_count(sources[0].filepath.stem, sources[1].filepath.stem)]

        if outdir is None:
            self.outdir = sources[0].filepath.parent
        else:
            self.outdir = outdir
        self.outstem = outstem
        self.sources = sources

        logging.debug(f'Will save a file with stem "{self.outstem}" to directory "{self.outdir}"')

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

        self.padding = padding
        self.threshold = threshold
        self.partition = partition
        self.split = split

        self.dialogue_times = None

        self.demux_overwrite_existing = demux_overwrite_existing

    # go through source files and count how many subtitle and audio streams we have
    def get_and_partition_streams(self):
        for sourcefile in self.sources:
            if sourcefile.type == 'video':
                # dig into streams
                for idx, st in enumerate(sourcefile.info['streams']):
                    stype = st['codec_type']
                    self.partitioned_streams[stype].append(Stream(sourcefile, stype, idx))
                continue
            self.partitioned_streams[sourcefile.type].append(Stream(sourcefile, sourcefile.type, None))
            # for stream in sourcefile

    def initialize_pickers(self):
        for k in self.pickers:
            self.pickers[k] = picker(self.partitioned_streams[k], target_lang=self.target_lang)

    def choose_streams(self):
        while picked_sources_are_insufficient(self.picked_streams):
            for k in self.picked_streams:
                if len(self.partitioned_streams[k]) == 0:
                    # list is empty, nothing to pick
                    continue
                if self.picked_streams[k] is None:
                    self.picked_streams[k] = next(self.pickers[k])

                # validate picked stream
                if k == 'subtitle':
                    subfile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)  # type AVSFile
                    times = subtools.load_subtitle_times(subfile.filepath)
                    if times is None:
                        self.picked_streams[k] = 'retry'

                if k == 'audio':
                    afile = self.picked_streams[k].demux(overwrite_existing=self.demux_overwrite_existing)
                    if afile is None:
                        self.picked_streams[k] = 'retry'


                if k == 'video':
                    pass

    def process_subtitles(self):
        subfile = self.picked_streams['subtitle'].demux(overwrite_existing=self.demux_overwrite_existing)
        times = subtools.load_subtitle_times(subfile.filepath)
        times = subtools.merge_times(times, threshold=self.threshold, padding=self.padding)
        self.dialogue_times = subtools.partition_and_split(sub_times=times, partition_size=1000*self.partition,
                                                           split_size=1000*self.split)

    def export(self):
        export_condensed_audio(self.dialogue_times, audiofile=self.picked_streams['audio'].get_data_path(),
                               outfile=self.outdir / (self.outstem + '.mp3'))

    def cleanup(self, keep_demux=False):
        if keep_demux == True:
            return
        for k in ['audio', 'video', 'subtitle']:
            if len(self.partitioned_streams) == 0:
                continue
            for s in self.partitioned_streams[k]:
                s.cleanup_demux()





