from subs2cia_v2.sources import SourceFiles, AVSFile
from subs2cia_v2.pickers import pick_audio, pick_subtitle
from subs2cia_v2.streams import Stream

import subs2cia_v2.subtools as subtools

import logging
from collections import defaultdict


def common_count(t0, t1):
    # returns the length of the longest common prefix
    i = 0
    for i, pair in enumerate(zip(t0, t1)):
        if pair[0] != pair[1]:
            return i
    return i


def group_by_longest_prefix(sources: SourceFiles):
    files = sources.infiles
    out = []
    longest = 0
    for f in files:
        splits = str(f.filepath.name).split('.')
        if out:
            common = common_count(splits, str(out[-1].filepath.name).split('.'))
            if common <= longest:
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


def group_files(sources: SourceFiles):
    file_groups = list(group_by_longest_prefix(sources))
    logging.debug(f"groups: {[[f.filepath for f in g] for g in file_groups]}")
    return file_groups



class Condensed:
    def __init__(self, sources: [AVSFile], outdir=None, condensed_video=False, threshold=0, padding=0):
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
        # note: the only dict keys we'll use are "video", "audio", and "subtitle".
        # Other types like "attachment" are ignored
        self.audio_stream_idx_picker = None
        self.subtitle_stream_idx_picker = None
        self.video_stream_idx_picker = None

        self.audio_stream_idx = None
        self.subtitle_stream_idx = None
        self.video_stream_idx = None

        self.subtitles = None

        self.threshold = threshold
        self.padding = padding

    # go through source files and count how many subtitle and audio streams we have
    def partition_sources(self):
        for sourcefile in self.sources:
            if sourcefile.type == 'video':
                # dig into streams
                for idx, st in enumerate(sourcefile.info['streams']):
                    stype = st['codec_type']
                    self.partitioned_streams[stype].append(Stream(sourcefile, idx))
                continue
            self.partitioned_streams[sourcefile.type].append(Stream(sourcefile, None))
            # for stream in sourcefile

    # default behaviour is to pick the first Stream with a None index
    def pick_audio(self):
        if self.audio_stream_idx_picker is None:
            self.audio_stream_idx_picker = pick_audio(self.partitioned_streams['audio'])
        self.audio_stream_idx = next(self.audio_stream_idx_picker)

    def pick_subtitle(self):
        if self.subtitle_stream_idx_picker is None:
            self.subtitle_stream_idx_picker = pick_subtitle(self.partitioned_streams['subtitle'])

        while self.subtitles is None:
            self.subtitle_stream_idx = next(self.subtitle_stream_idx_picker)
            substream = self.partitioned_streams['subtitle'][self.subtitle_stream_idx]
            subs = subtools.Subtitle(stream=substream, threshold=self.threshold, padding=self.padding)
            subs.load_subs()


    def pick_video(self):
        if self.video_stream_idx_picker is None:
            self.video_stream_idx_picker = pick_subtitle(self.partitioned_streams['video'])
        self.video_stream_idx = next(self.video_stream_idx_picker)




