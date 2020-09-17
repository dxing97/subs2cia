from subs2cia.argparser import get_args_subzipper
from subs2cia.sources import is_language

import logging
from pathlib import Path
import pycountry
from pprint import pprint


def start():
    args = get_args_subzipper()
    args = vars(args)

    if args['verbose']:
        # if args['debug']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    # elif args['debug']:
    #     logging.basicConfig(level=logging.DEBUG)

    logging.debug(f"Start arguments: {args}")

    subfiles = args['subfiles']
    reffiles = args['reffiles']

    if len(subfiles) != len(reffiles):
        logging.warning(f"Mismatched number of subtitle and reference files! Got {len(subfiles)} subtitle files and "
                        f"{len(reffiles)} reference files.")
        logging.warning(f"Will only process the first "
                        f"{len(subfiles) if len(subfiles) < len(reffiles) else len(reffiles)} "
                        f"reference-subtitle pairs.")
        # exit(1)

    # subfiles = [Path(s).absolute() for s in subfiles]
    # reffiles = [Path(r).absolute() for r in reffiles]
    subfiles = [Path(s) for s in subfiles]
    reffiles = [Path(r) for r in reffiles]

    lang = None
    if args['lang'] is not None:
        if is_language(args['lang']):
            lang = pycountry.languages.lookup(args['lang'])
            lang = lang.alpha_3
            logging.info(f'Appending language code {lang}')
        else:
            logging.error(f"Language lookup failure: {args['lang']} is not a ISO recognized language")

    if args['no_sort']:
        logging.info("Not sorting inputs alphabetically, using as-is.")
    else:
        subfiles.sort(key=lambda x: str(x))
        reffiles.sort(key=lambda x: str(x))

    for s, r in zip(subfiles, reffiles):
        newpath = r.parent / (r.stem + ('' if lang is None else f'.{lang}') + s.suffix)
        logging.info(f"Will rename {s} to {newpath}")

        if not s.exists():
            logging.critical(f"Subtitle file doesn't exist: {s}")
            exit(1)
        if not r.exists():
            logging.warning(f"Reference file doesn't exist: {r}")
        if newpath == r:
            logging.critical(f"Renaming subtitle to {newpath} will overwrite the reference file!")
            exit(1)
        if newpath.exists():
            logging.critical(f"Renaming subtitle to {newpath} will overwrite an existing file!")
            exit(1)

    # todo: user-interactive question here
    if args['dry_run']:
        logging.info("Dry run mode, not writing changes.")
        return

    for s, r in zip(subfiles, reffiles):
        newpath = r.parent / (r.stem + ('' if lang is None else f'.{lang}') + s.suffix)
        logging.info(f"Renaming {s} to {newpath}...")
        s.rename(newpath)
        logging.info(f"...done")


if __name__ == '__main__':
    start()
