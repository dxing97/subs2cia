from subs2cia.sources import Stream
import pycountry
import logging


def picker(streams: [Stream], target_lang: str = None, forced_stream: int = None):
    r"""
    Returns streams by priority. Streams which are not part of a container are preferred first,
    followed by manually specified stream indices, then streams which match a specified language, finally followed
    by the remaining streams.
    :param streams: List of Stream objects
    :param target_lang: Target language
    :param forced_stream:
    :return:
    """
    for s in streams:
        if s.is_standalone():
            yield s

    if forced_stream is not None:
        yield streams[forced_stream]

    if target_lang is not None:
        target_lang = pycountry.languages.lookup(target_lang)
        target_lang = target_lang.alpha_3

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
