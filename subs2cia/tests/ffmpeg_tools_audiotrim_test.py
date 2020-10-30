import argparse
import logging
from pathlib import Path
from subs2cia.ffmpeg_tools import *

def get_args():
    parser = argparse.ArgumentParser(description=f'audio trimming manual testing')

    parser.add_argument('-V', '--video', metavar='<input file>', dest='videofile', default=None, required=True,
                        type=str,
                        help='Video file')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    # parser.add_argument('-t', '--timestamps', type=int, nargs='+', dest='timestamps', required=True,
    #                     help='Timestamps to grab in milliseconds')

    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    args.timestamps = [0, 1000, 2000, 30000, 600000, 700000]
    # ffmpeg_trim_audio_clip_directcopy(Path(args.videofile), timestamp_start=10000, timestamp_end=20000,
    #                        outpath=Path("output.eac3"))

    ffmpeg_trim_audio_clip_encode(Path(args.videofile), stream_index=2, timestamp_start=40000, timestamp_end=50000, quality=None,
                           to_mono=True, outpath=Path("output.mp3"))

    ffmpeg_trim_audio_clip_atrim_encode(Path(args.videofile), stream_index=2, timestamp_start=40000, timestamp_end=50000, quality=None,
                           to_mono=True, normalize_audio=True, outpath=Path("output_normalized.mp3"))