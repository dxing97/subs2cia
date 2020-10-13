import argparse
import logging
from pathlib import Path
from subs2cia.ffmpeg_tools import ffmpeg_get_frames

def get_args():
    parser = argparse.ArgumentParser(description=f'subtools manual testing')

    parser.add_argument('-V', '--video', metavar='<input file>', dest='videofile', default=None, required=True,
                        type=str,
                        help='Video file')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    parser.add_argument('-t', '--timestamps', type=int, nargs='+', dest='timestamps', required=True,
                        help='Timestamps to grab in milliseconds')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    ffmpeg_get_frames(Path(args.videofile), args.timestamps, Path("output.png"))