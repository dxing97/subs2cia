import argparse
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(description='subs2cia: subtitle-based condensed audio generator')

    parser.add_argument('-i', '--inputs', metavar='<input files>', dest='infiles', default=None, required=True,
                        type=str, nargs='+',
                        help='Paths to input files or a single path to a directory of input files')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False,
                        help='Verbose and debug output if set')

    args = parser.parse_args()
    return args
