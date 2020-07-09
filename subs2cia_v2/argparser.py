import argparse
from pathlib import Path


def get_args():
    parser = argparse.ArgumentParser(description='subs2cia: subtitle-based condensed audio generator')

    parser.add_argument('-i', '--inputs', metavar='<input files>', dest='infiles', default=None, required=True,
                        type=str, nargs='+',
                        help='Paths to input files or a single path to a directory of input files')

    parser.add_argument('-o', '--output-dir', metavar='/path/to/directory', dest='outdir', default=None,
                        type=str,
                        help='Output directory to save to. Default is the directory the input files reside in.')

    parser.add_argument('-ea', '--audio-extension', metavar='<audio extension>', dest='out_audioext', default='mp3',
                        type=str,
                        help='Condensed audio output type to save to. Default is mp3.')

    parser.add_argument('-m', '--gen-video', action='store_true', dest='condensed_video', default=False,
                        help='If set, generates condensed video along with condensed audio.')

    parser.add_argument('--overwrite-on-demux', action='store_true', dest='demux_overwrite_existing', default=False,
                        help='If set, will overwrite existing files when demuxing temporary files.')

    parser.add_argument('--keep-temporaries', action='store_true', dest='keep_temporaries', default=False,
                        help='If set, will not delete any demuxed temporary files.')

    parser.add_argument('--no-overwrite-on-generation', action='store_false', dest='overwrite_existing_generated', default=True,
                        help='If set, will not overwrite existing files when generating condensed media.')

    parser.add_argument('-p', '--padding', metavar='msecs', dest='padding', default=0,
                        type=int,
                        help='Adds this many milliseconds of audio before and after every subtitle. '
                             'Overlaps with adjacent subtitles are merged.')

    parser.add_argument('-t', '--threshold', metavar='msecs', dest='threshold', default=0,
                        type=int,
                        help="If there's a subtitle that's threshold+padding msec away, "
                             "adds the intervening audio into the condensed audio.")

    parser.add_argument('-r', '--partition', metavar='secs', dest='partition', default=0,
                        type=int,
                        help="If set, attempts to partition the input audio into"
                             "seperate blocks of this size BEFORE condensing. 0"
                             "partition length is ignored.")

    parser.add_argument('-s', '--split', metavar='secs', dest='split', default=0,
                        type=int,
                        help="If set, attempts to split the condensed audio into"
                             "seperate blocks of this size AFTER condensing. 0"
                             "split length is ignored.")

    parser.add_argument('-tl', '--target-language', metavar='ISO_code', dest='target_lang', default=None,
                        type=str,
                        help='If set, attempts to use audio and subtitle files that are in this language first.')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False,
                        help='Verbose and debug output if set')

    parser.add_argument('--preset', metavar='preset#', dest='preset', type=int, default=None,
                        help='If set, uses a given preset. User arguments will override presets.')
    parser.add_argument('-lp', '--list-presets', dest='list_presets', action='store_true', default=False,
                        help='Lists all available presets.')

    args = parser.parse_args()
    return args
