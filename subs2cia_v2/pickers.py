from subs2cia_v2.streams import Stream


def pick_audio(streams: [Stream], target_lang=None):
    for idx, s in enumerate(streams):
        if s.index is None:
            # raw file, no useful metadata to examine
            yield idx
    # None indices have been exhausted, go through rest of streams
    for idx, s in enumerate(streams):
        if s.index is not None:
            yield idx
            # todo: metadata analysis
    # stream contains metadata we can examine (probably)


def pick_subtitle(streams: [Stream], target_lang=None):
    for idx, s in enumerate(streams):
        if s.index is None:
            # raw file, no useful metadata to examine
            yield idx
    # None indices have been exhausted, go through rest of streams
    for idx, s in enumerate(streams):
        if s.index is None:
            continue
    # examine metadata


def pick_video(streams: [Stream]):
    for idx, s in enumerate(streams):
        if s.index is None:
            # raw file, no useful metadata to examine
            yield idx
    # None indices have been exhausted, go through rest of streams
    for idx, s in enumerate(streams):
        if s.index is None:
            continue
    # examine metadata
