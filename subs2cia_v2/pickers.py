from subs2cia_v2.sources import Stream

def picker(streams: [Stream], target_lang=None):
    for s in streams:
        if s.is_standalone():
            yield s
    for s in streams:
        if s.is_standalone():
            continue
        if s.get_language == target_lang:
            yield s

    for s in streams:
        if s.is_standalone():
            continue
        if s.get_language == target_lang:
            continue
        yield s