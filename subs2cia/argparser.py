import argparse
from pathlib import Path
import sys


def get_args_subzipper():
    parser = argparse.ArgumentParser(description=f'SubZipper: Map video files to subtitle files')

    parser.add_argument('-s', '--subtitle', metavar='<input files>', dest='subfiles', default=None, required=True,
                        type=str, nargs='+',
                        help='List of subtitle files. Number of subtitle files should equal number of reference files.')

    parser.add_argument('-r', '--reference', metavar='<input files>', dest='reffiles', default=None, required=True,
                        type=str, nargs='+',
                        help='List of reference files, typically video files. '
                             'Number of subtitle files should equal number of reference files. ')

    parser.add_argument('-l', '--language', metavar='ISO_LANG_CODE', dest='lang', default=None, required=False,
                        type=str,
                        help='Language code to append to end of subtitle file. Optional. '
                             'If set, will be checked for validity.')

    parser.add_argument('-ns', '--no-sort', action='store_true', dest='no_sort', default=False,
                        help="If set, will not sort input files alphabetically.")

    parser.add_argument('-d', '--dry-run', action='store_true', dest='dry_run', default=False,
                        help="If set, will print out mappings but will not write any changes to disk.")

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    # parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False,
    #                     help='Verbose and debug output if set')

    args = parser.parse_args()
    return args


def get_args_subs2cia():
    parser = argparse.ArgumentParser(description=f'subs2cia: Extract subtitled dialogue from audiovisual media for use '
                                                 f'in language acquisition ')

    # todo: implement directory parsing
    parser.add_argument('-i', '--inputs', metavar='<input files>', dest='infiles', default=None, required=False,
                        type=str, nargs='+',
                        help='Paths to input files or a single path to a directory of input files.')


    parser.add_argument('-si', '--subtitle-index',  metavar='<index>', dest='subtitle_stream_index', default=None,
                        type=int,
                        help='Force a certain subtitle stream to use. Takes precedence over --target-language option.'
                             'If any input files are standalone subtitle files, they will be used first. '
                             'Use --list-streams for a list of available streams and their indices.')

    parser.add_argument('-ai', '--audio-index',  metavar='<index>', dest='audio_stream_index', default=None,
                        type=int,
                        help='Force a certain subtitle audio to use. Takes precedence over --target-language option.'
                             'If any input files are standalone audio files, they will be used first. '
                             'Use --list-streams for a list of available streams and their indices.')

    parser.add_argument('-b', '--batch', action='store_true', dest='batch', default=False,
                        help='If set, attempts to split input files into groups, one output file per group. '
                             'Groups are determined by file names. If two files share the same root name, such as '
                             '"video0.mkv" and "video0.srt", then they are part of the same group.')

    parser.add_argument('-u', '--dry-run', action='store_true', dest='dry_run', default=False,
                        help="If set, will analyze input files but won't demux or generate any condensed files")

    parser.add_argument('-o', '--output-name', metavar='<name>', dest='outstem', default=None,
                        type=str,
                        help='Output file name to save to, without the extension (specify extension using -ae or -ve). '
                             'By default, uses the file name of the first input file with the input extension removed '
                             'and "condensed.{output extension} added. \n'
                             'Ignored if batch mode is enabled.')

    parser.add_argument('-d', '--output-dir', metavar='/path/to/directory', dest='outdir', default=None,
                        type=str,
                        help='Output directory to save to. Default is the directory the input files reside in.')

    parser.add_argument('-ae', '--audio-extension', metavar='<audio extension>', dest='out_audioext', default='mp3',
                        type=str,
                        help='Condensed audio extension to save as (without the dot). '
                             'Default is mp3, flac has been tested to work.')
    # todo: dot stripper, output naming
    parser.add_argument('-m', '--gen-video', action='store_true', dest='condensed_video', default=False,
                        help='If set, generates condensed video along with condensed audio and subtitles. '
                             'Subtitles are muxed in to video file. '
                             'WARNING: VERY CPU INTENSIVE).')

    parser.add_argument('--overwrite-on-demux', action='store_true', dest='demux_overwrite_existing', default=False,
                        help='If set, will overwrite existing files when demuxing temporary files.')

    parser.add_argument('--keep-temporaries', action='store_true', dest='keep_temporaries', default=False,
                        help='If set, will not delete any demuxed temporary files.')

    parser.add_argument('--no-overwrite-on-generation', action='store_false', dest='overwrite_existing_generated',
                        default=True,
                        help='If set, will not overwrite existing files when generating condensed media.')

    parser.add_argument('-ni', '--ignore-none', action='store_true', dest='use_all_subs',
                        default=False,
                        help='If set, will not use internal heuristics to remove non-dialogue lines from the subtitle. '
                             'Overridden by -R.')

    parser.add_argument('-R', '--sref', metavar='<regular expression>', dest='subtitle_regex_filter', default=None,
                        type=str,
                        help='For filtering non-dialogue subtitles. Lines that match given regex are IGNORED '
                             'during subtitle processing and will not influence condensed audio. '
                             'Ignored lines may be included in condensed subtitles. This option will override the '
                             'internal subs2cia non-dialogue filter.')

    parser.add_argument('-p', '--padding', metavar='msecs', dest='padding', default=0,
                        type=int,
                        help='Adds this many milliseconds of audio before and after every subtitle. '
                             'Overlaps with adjacent subtitles are merged automatically.')

    parser.add_argument('-t', '--threshold', metavar='msecs', dest='threshold', default=0,
                        type=int,
                        help="If two subtitles start and end within (threshold + 2*padding) "
                             "milliseconds of each other, they will be merged. Useful for preserving silences between "
                             "subtitle lines.")

    parser.add_argument('-r', '--partition', metavar='secs', dest='partition', default=0,
                        type=int,
                        help="If set, attempts to partition the input audio into "
                             "seperate blocks of this size seconds BEFORE condensing. Partitions and splits respect "
                             "subtitle boundaries and will not split a single subtitle across two output files."
                             " 0 partition length is ignored. For example, if the partition size is 60 seconds and the "
                             "input media is 180 seconds long, then there will be three output files. The first output "
                             "file will contain condensed media from the first 60 seconds of the source material, "
                             "the second output file will contain the next 60 seconds of input media, and so on.")

    parser.add_argument('-s', '--split', metavar='secs', dest='split', default=0,
                        type=int,
                        help="If set, attempts to split the condensed audio into "
                             "seperate blocks of this size AFTER condensing. 0 "
                             "split length is ignored. "
                             "Partitions and splits respect subtitle boundaries and will not split a single subtitle "
                             "across two output files. "
                             "Done within a partition. For example, say the split length is "
                             "60 seconds and the condensed audio length of a input partition is 150 seconds. "
                             "The output file will be split into three files, the first two ~60 seconds long and the "
                             "last ~30 seconds long.")

    parser.add_argument('-c', '--minimum-compression-ratio', metavar='<ratio>', dest='minimum_compression_ratio',
                        default=0.2, type=float,
                        help="Will only generate from subtitle files that are this fraction long of the selected audio "
                             "file. Default is 0.2, meaning the output condensed file must be at least 20% as long as "
                             "the chosen audio stream. If the output doesn't reach this minimum, then a different "
                             "subtitle file will be chosen, if available. Used to ignore subtitles that contain only"
                             "signs and songs.")

    parser.add_argument('-tl', '--target-language', metavar='ISO_code', dest='target_lang', default=None,
                        type=str,
                        help='If set, attempts to use audio and subtitle files that are in this language first. '
                             'Should follow ISO language codes. ')

    # todo: consider depreciating this option
    parser.add_argument('-a', '--absolute-paths', action='store_true', dest='absolute_paths', default=False,
                        help='Prints absolute paths from the root directory instead of given paths.')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False,
                        help='Verbose and debug output if set')

    parser.add_argument('--preset', metavar='preset#', dest='preset', type=int, default=None,
                        help='If set, uses a given preset. User arguments will override presets.')
    parser.add_argument('-lp', '--list-presets', dest='list_presets', action='store_true', default=False,
                        help='Lists all available built-in presets and exits.')
    parser.add_argument('-ls', '--list-streams', dest='list_streams', action='store_true', default=False,
                        help='Lists all audio, subtitle, and video streams found in given input files and exits.')
    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return args
