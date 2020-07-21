from subs2cia.sources import Stream
import pycountry

def picker(streams: [Stream], target_lang=None):
    if target_lang is not None:
        target_lang = pycountry.languages.lookup(target_lang)
        target_lang = target_lang.alpha_2
    for s in streams:
        if s.is_standalone():
            yield s
    for s in streams:
        if s.is_standalone():
            continue
        if s.get_language() == target_lang:
            yield s

    for s in streams:
        if s.is_standalone():
            continue
        if s.get_language == target_lang:
            continue
        yield s