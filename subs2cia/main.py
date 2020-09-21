import os
import sys
import shutil

# this line is for when main.py is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subs2cia.argparser import get_args_subs2cia
from subs2cia.sources import AVSFile, group_files
from subs2cia.condense import SubCondensed
__version__ = 'v0.2.4'

from pathlib import Path
import logging
from pprint import pprint

presets = [
    {  # preset 0
        'preset_description': "Padded and merged Japanese condensed audio",
        'threshold': 1500,
        'padding': 200,
        # 'partition_size': 1800,  # 30 minutes, for long movies
        'target_lang': 'ja',
    },
    {  # preset 1
        'preset_description': "Unpadded Japanese condensed audio",
        'threshold': 0,  # note: default is 0
        'padding': 0,  # note: default is 0
        # 'partition': 1800,  # 30 minutes, for long movies
        'target_lang': 'ja',
    },
]


def list_presets():
    for idx, preset in enumerate(presets):
        print(f"Preset {idx}")
        pprint(preset)


def start():
    if not shutil.which('ffmpeg'):
        logging.warning(f"Couldn't find ffmpeg in PATH, things may break.")

    args = get_args_subs2cia()
    args = vars(args)

    if args['verbose']:
        if args['debug']:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    elif args['debug']:
        logging.basicConfig(level=logging.DEBUG)

    logging.info(f"subs2cia version {__version__}")
    logging.debug(f"Start arguments: {args}")

    if args['list_presets']:
        list_presets()
        return

    if args['preset'] is not None:
        if abs(args['preset']) >= len(presets):
            logging.critical(f"Preset {args['preset']} does not exist")
            exit(0)
        logging.info(f"using preset {args['preset']}")
        for key, val in presets[args['preset']].items():
            if key in args.keys() and ((args[key] == False) or (args[key] is None)):  # override presets
                args[key] = val

    SubC_args = {key: args[key] for key in
                 ['outdir', 'condensed_video', 'padding', 'threshold', 'partition', 'split',
                  'demux_overwrite_existing', 'overwrite_existing_generated', 'keep_temporaries',
                  'target_lang', 'out_audioext', 'minimum_compression_ratio', 'use_all_subs', 'subtitle_regex_filter',
                  'audio_stream_index', 'subtitle_stream_index']}

    if args['infiles'] is None:
        logging.info("No input files given, nothing to do.")
        exit(0)

    args['infiles'].sort()

    if args['absolute_paths']:
        sources = [AVSFile(Path(file).absolute()) for file in args['infiles']]
    else:
        sources = [AVSFile(Path(file)) for file in args['infiles']]

    for s in sources:
        s.probe()
        s.get_type()

    if args['batch']:
        logging.info(f"Running in batch mode, attempting to group input files together.")
        groups = list(group_files(sources))
    else:
        if len(sources) > 2:
            logging.warning(f"Redundant input files detected. Got {len(sources)} "
                            f"input files to process and not running "
                            f"in batch mode. Only one output "
                            f"will be generated. ")
        groups = [list(sources)]
    logging.info(f"Have {len(groups)} group(s) to process.")

    condensed_files = [SubCondensed(g, **SubC_args) for g in groups]
    for c in condensed_files:
        c.get_and_partition_streams()
        c.initialize_pickers()
        if args['dry_run']:
            continue
        if args['list_streams']:
            c.list_streams()
            continue
        c.choose_streams()
        c.process_subtitles()
        c.export()
        c.cleanup()


if __name__ == '__main__':
    start()
