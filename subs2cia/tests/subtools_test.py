import argparse
import logging
from pathlib import Path
from subs2cia.subtools import SubtitleManipulator

def get_args():
    parser = argparse.ArgumentParser(description=f'subtools manual testing')

    parser.add_argument('-s', '--subtitle', metavar='<input file>', dest='subfile', default=None, required=True,
                        type=str,
                        help='Subtitle file')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    # parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False,
    #                     help='Verbose and debug output if set')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    sub_obj = SubtitleManipulator(subpath=Path(args.subfile), threshold=1500, padding=200)
    sub_obj.load(include_all=False, regex=None)
    print(sub_obj)
    sub_obj.merge_groups()
    sub_obj.condense()
    sub_obj.condensed_ssadata.save(args.subfile + ".condensed.ass", encoding=u'utf-8')
    print(sub_obj)

