from subs2cia_v2.sources import AVSFile
from subs2cia_v2.pickers import picker
from subs2cia_v2.streams import Stream

import subs2cia_v2.subtools as subtools
from subs2cia_v2.sources import common_count

import logging
from collections import defaultdict


def dict_has_none(d: dict):
    for k in d:
        if d[k] is None:
            return True
    return False


class Condensed:
    def __init__(self, sources: [AVSFile], outdir=None, condensed_video=False, threshold=0, padding=0,
                 target_lang=None):
        if len(sources) == 1:
            outstem = sources[0].filepath.stem
        else:
            outstem = sources[0].filepath.name[0:common_count(sources[0].filepath.stem, sources[1].filepath.stem)]

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

    # go through source files and count how many subtitle and audio streams we have
    def get_and_partition_streams(self):
        for sourcefile in self.sources:
            if sourcefile.type == 'video':
                # dig into streams
                for idx, st in enumerate(sourcefile.info['streams']):
                    stype = st['codec_type']
                    self.partitioned_streams[stype].append(Stream(sourcefile, idx))
                continue
            self.partitioned_streams[sourcefile.type].append(Stream(sourcefile, None))
            # for stream in sourcefile

    def initialize_pickers(self):
        for k in self.pickers:
            self.pickers[k] = picker(self.partitioned_streams[k], target_lang=self.target_lang)

    def choose_streams(self):
        while dict_has_none(self.picked_streams):
            for k in self.picked_streams:
                if self.picked_streams[k] is None:
                    self.picked_streams[k] = next(self.pickers[k])





