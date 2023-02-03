#!/usr/bin/env python3
import os
import sys
import shutil
import glob

# this line is for when main.py is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subs2cia.argparser import get_args_subs2cia
from subs2cia.sources import AVSFile, group_files
from subs2cia.condense import Condense
from subs2cia.CardExport import CardExport

from pathlib import Path
import logging
from colorlog import ColoredFormatter
from pprint import pprint
from typing import Union, List
import tqdm

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


# https://stackoverflow.com/a/38739634
class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            tqdm.tqdm.write(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def condense_start(args, groups: List[List[AVSFile]]):
    condense_args = {key: args[key] for key in
                     ['outdir', 'outstem', 'condensed_video', 'padding', 'threshold', 'partition', 'split',
                      'demux_overwrite_existing', 'overwrite_existing_generated', 'keep_temporaries',
                      'target_lang', 'out_audioext', 'minimum_compression_ratio', 'use_all_subs',
                      'subtitle_regex_filter',
                      'subtitle_regex_substrfilter', 'subtitle_regex_substrfilter_nokeep',
                      'audio_stream_index', 'subtitle_stream_index', 'ignore_range', 'ignore_chapters',
                      'bitrate', 'mono_channel', 'interactive', 'no_condensed_subtitles', 'out_audiocodec']}

    condensed_files = [Condense(g, **condense_args) for g in groups]
    if logging.root.isEnabledFor(logging.INFO):
        logging.info("Input/output file mapping:")
        for cgroup in condensed_files:
            logging.info(f"{cgroup.outstem}")
            for cfile in cgroup.sources:
                logging.info(f"    {cfile.filepath}")

    # logging.root.addHandler(TqdmLoggingHandler())

    i = condensed_files
    # if logging.root.level == logging.INFO:
    #     # logging level of WARNING means quiet output
    #     # debug is too noisy for a progress bar to be _that_ useful
    #     i = tqdm.tqdm(condensed_files, position=0)

    for idx, c in enumerate(i):
        # if logging.root.level == logging.INFO:
        #     i.set_postfix_str(f"{c.outstem}")
        #     i.update(0)
        logging.info(f"({idx + 1}/{len(i)}): {c.outstem}")
        c.get_and_partition_streams()
        c.initialize_pickers()
        if args['dry_run']:
            continue
        if args['list_streams']:
            c.list_streams()
            continue
        c.choose_streams()
        c.export()
        c.cleanup()


def srs_export_start(args, groups: List[List[AVSFile]]):
    srs_args = {key: args[key] for key in
                ['outdir', 'outstem', 'condensed_video', 'padding', 'demux_overwrite_existing',
                 'overwrite_existing_generated', 'keep_temporaries', 'target_lang', 'out_audioext', 'use_all_subs',
                 'subtitle_regex_filter', 'audio_stream_index', 'subtitle_stream_index', 'ignore_range',
                 'ignore_chapters',
                 'bitrate', 'mono_channel', 'interactive', 'normalize_audio', "out_audiocodec"]
                }

    cardexport_group = [CardExport(g, **srs_args) for g in groups]

    for c in cardexport_group:
        c.get_and_partition_streams()
        c.initialize_pickers()
        if args['dry_run']:
            continue
        if args['list_streams']:
            c.list_streams()
            continue
        c.choose_streams()
        c.export()
        c.cleanup()


def start():
    if not shutil.which('ffmpeg'):
        logging.warning(f"Couldn't find ffmpeg in PATH, things may break.")

    args = get_args_subs2cia()
    args = vars(args)

    logconfig = False
    ch = logging.StreamHandler()
    level = logging.NOTSET
    if args['debug']:
        level = logging.DEBUG
        logconfig = True
    if not logconfig and args['quiet']:
        level = logging.WARNING
        logconfig = True
    if not logconfig:
        level = logging.INFO
        logconfig = True

    if level == logging.DEBUG:
        format = "subs2cia:%(log_color)s%(levelname)s%(reset)s:%(message_log_color)s%(message)s [%(module)s.py:%(funcName)s():%(lineno)d]"
    else:
        format = "subs2cia:%(log_color)s%(levelname)s%(reset)s:%(message_log_color)s%(message)s"

    ch.setLevel(level)
    ch.setFormatter(ColoredFormatter(format, log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red,bg_white',
    }, secondary_log_colors={
        'message': {
            'ERROR': 'red',
            'CRITICAL': 'bold_red'
        }
    }))
    logging.root.setLevel(level)
    logging.root.addHandler(ch)

    from subs2cia import __version__
    logging.info(f"subs2cia version {__version__}")
    logging.debug(f"Start arguments: {args}")

    if args['list_presets']:  # todo: user-defined presets
        list_presets()
        return

    if args['preset'] is not None:
        if abs(args['preset']) >= len(presets):
            logging.critical(f"Preset {args['preset']} does not exist")
            exit(0)
        logging.info(f"Using preset {args['preset']}")
        for key, val in presets[args['preset']].items():
            if key in args.keys() and ((args[key] == False) or (args[key] is None)):  # override presets
                args[key] = val

    if args['infiles'] is None:
        logging.warning("No input files given, nothing to do.")
        exit(0)

    infiles = _resolve(args['infiles'])

    # convert to Path objects and see if any input files are actually directories
    # for the moment, don't support processing entire directories.
    # point users to globbing and asterisks if they want to process an entire directory
    infiles = [Path(file) for file in infiles]
    for file in infiles:
        if file.is_dir():
            logging.error(f'Input file "{file}" is actually a directory, aborting.\n'
                          f'If you want to process all files in this directory, use "{file}/*" instead.')
            exit(2)

    if args['absolute_paths']:
        sources = [AVSFile(Path(file).absolute()) for file in infiles]
    else:
        sources = [AVSFile(Path(file)) for file in infiles]

    for s in sources:
        s.probe()
        s.get_type()

    if args['batch']:
        args['outstem'] = None
        logging.info(f"Running in batch mode, attempting to group similarly named files together.")
        groups = list(group_files(sources))
    else:
        if len(sources) > 2:
            logging.warning(f"Redundant input files detected. Got {len(sources)} "
                            f"input files to process and not running "
                            f"in batch mode. Only one output "
                            f"will be generated. ")
        groups = [list(sources)]
    logging.debug(f"Have {len(groups)} group(s) to process.")

    commands = {
        'condense': condense_start,
        'srs': srs_export_start
    }
    commands[args['command']](args, groups)


def _resolve(files):
    resolved = []

    for f in files:
        if '*' in f or '?' in f:
            globbed = glob.glob(f)
            if len(globbed) > 0:
                resolved += globbed
            else:
                resolved.append(f)
        else:
            resolved.append(f)

    return resolved


if __name__ == '__main__':
    start()
