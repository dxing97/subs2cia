import argparse
import sys
import re
from pysubs2.time import make_time


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


# taken from pysubs2:cli.py
def time(s):
    d = {}
    # all = re.findall(r"(\+?|-?|^$)(\d*\.?\d*)(ms|m|s|h)", s)
    sign = s[0] if s[0] == 'e' or s[0] == '+' else ''
    for v, k in re.findall(r"(\d*\.?\d*)(ms|m|s|h)", s):
        d[k] = float(v)
    return sign, make_time(**d)


def get_args_subs2cia():
    from subs2cia import __version__
    parser = argparse.ArgumentParser(description=f'subs2cia {__version__}: Extract subtitled dialogue from audiovisual media for use '
                                                 f'in language acquisition')

    subparsers = parser.add_subparsers(title='subcommands', help="subcommand help", dest="command")
    parent_parser = argparse.ArgumentParser(add_help=False)

    parent_parser.add_argument('-Q', '--quiet', action='store_true', dest='quiet', default=False, required=False,
                               help='Will only report warning and errors if set.')

    parent_parser.add_argument('-vv', '--debug', action='store_true', dest='debug', default=False, required=False,
                               help='Verbose and debug output if set')

    # todo: implement directory parsing
    # if directory is an input, batch mode must be specified
    parent_parser.add_argument('-i', '--inputs', metavar='<input files>', dest='infiles', default=None, required=False,
                               type=str, nargs='+',
                               help='Paths to input files or a single path to a directory of input files.')

    parent_parser.add_argument('-si', '--subtitle-index', metavar='<index>', dest='subtitle_stream_index', default=None,
                               type=int,
                               help='Force a certain subtitle stream to use. '
                                    'Takes precedence over --target-language option.'
                                    'If any input files are standalone subtitle files, they will be used first. '
                                    'Use --list-streams for a list of available streams and their indices.')

    parent_parser.add_argument('-ai', '--audio-index', metavar='<index>', dest='audio_stream_index', default=None,
                               type=int,
                               help='Force a certain subtitle audio to use. '
                                    'Takes precedence over --target-language option.'
                                    'If any input files are standalone audio files, they will be used first. '
                                    'Use --list-streams for a list of available streams and their indices.')

    parent_parser.add_argument('-b', '--batch', action='store_true', dest='batch', default=False,
                               help='If set, attempts to split input files into groups, one set of outputs per group. '
                                    'Groups are determined by file names. If two files share the same root name, such as '
                                    '"video0.mkv" and "video0.srt", then they are part of the same group. '
                                    'If file names contain a language code as a suffix, '
                                    'then the suffix will also be ignored (e.g. "video1.eng.flac" and "video1.ja.srt" '
                                    'will be grouped together under "video1")')

    parent_parser.add_argument('-u', '--dry-run', action='store_true', dest='dry_run', default=False,
                               help="If set, will analyze input files but won't demux or generate any output files")

    parent_parser.add_argument('-o', '--output-name', metavar='<name>', dest='outstem', default=None,
                               type=str,
                               help='Output file name to save to, without the extension '
                                    '(specify extension using -ae or -ve). '
                                    'By default, uses the file name of the first '
                                    'input file with the input extension removed '
                                    'and "condensed.{output extension} added. \n'
                                    'Ignored if batch mode is enabled.')

    parent_parser.add_argument('-d', '--output-dir', metavar='/path/to/directory', dest='outdir', default=None,
                               type=str,
                               help='Output directory to save to. Default is the directory the input files reside in.')

    parent_parser.add_argument('-ae', '--audio-extension', metavar='<audio extension>', dest='out_audioext',
                               default='mp3',
                               type=str,
                               help='Output audio extension to save as (without the dot). '
                                    'Default is mp3.')

    parent_parser.add_argument('-ac', '--audio-codec', metavar='<audio codec>', dest='out_audiocodec',
                               default='',
                               type=str,
                               help='Output audio codec to use on export. '
                                    'Default is to let ffmpeg choose based on the audio file extension.')

    parent_parser.add_argument('-q', '--bitrate', metavar='<bitrate in kbps>', dest='bitrate', default=320,
                               type=int,
                               help='Output audio bitrate in kbps, lower bitrates result in smaller files and lower '
                                    'fidelity. Ignored if the output audio file extension and audio codec is not mp3. '
                                    'Default is 320 kbps. '
                                    'Bitrates below 64 kbps are not recommended. ')

    parent_parser.add_argument('-M', '--mono', dest='mono_channel', default=False,
                               action="store_true",
                               help='If set, mixes audio channels to a single channel, primarily to save space.')
    # todo: dot stripper, output naming
    parent_parser.add_argument('-m', '--gen-video', action='store_true', dest='condensed_video', default=False,
                               help='If set, generates condensed video along with condensed audio and subtitles. '
                                    'Subtitles are muxed in to video file. '
                                    'WARNING: VERY CPU INTENSIVE AND SLOW.')

    parent_parser.add_argument('--overwrite-on-demux', action='store_true', dest='demux_overwrite_existing',
                               default=False,
                               help='If set, will overwrite existing files when demuxing temporary files.')

    parent_parser.add_argument('--keep-temporaries', action='store_true', dest='keep_temporaries', default=False,
                               help='If set, will not delete any demuxed temporary files.')

    parent_parser.add_argument('--no-overwrite-on-generation', action='store_false',
                               dest='overwrite_existing_generated',
                               default=True,
                               help='If set, will not overwrite existing files when generating output media.')

    parent_parser.add_argument('-ni', '--ignore-none', action='store_true', dest='use_all_subs',
                               default=False,
                               help='If set, will not use internal heuristics to remove non-dialogue '
                                    'lines from the subtitle. Ignored if -R is set.')

    parent_parser.add_argument('-R', '--sub-regex-filter', metavar='<regular expression>', dest='subtitle_regex_filter',
                               default=None,
                               type=str,
                               help='For filtering non-dialogue subtitles. Lines that match given regex are IGNORED '
                                    'during subtitle processing and will not influence condensed audio or be included in output cards. '
                                    'Ignored lines may still be included in condensed subtitles if they overlap with non-ignored subtitles. '
                                    'This option will override the internal subs2cia non-dialogue filter.')

    # parent_parser.add_argument('-RR', '--sub-regex-substrfilter', metavar='<regular expression>',
    #                            dest='subtitle_regex_substrfilter', default=None,
    #                            type=str,
    #                            help='Searches subtitle lines and removes all substrings that match this regular '
    #                                 'expression. If the resulting subtitle line becomes empty, contains only spaces, '
    #                                 'or contains only punctuation as a result, the entire subtitle line is '
    #                                 'removed and will not be present in the output unless -RRnk is set. Internal '
    #                                 'dialogue detection method is still active unless -ni is set.')
    #
    # parent_parser.add_argument('-RRnk', '--sub-regex-substrfilter-nokeepchanges', action='store_true', dest='subtitle_regex_substrfilter_nokeep',
    #                            default=False,
    #                            help='If set, the modified subtitle text created by -RR will not be passed to the '
    #                                 'output subtitles/cards. Any empty filtered lines will be marked as non-dialogue '
    #                                 'instead of being removed entirely from the output. '
    #                                 'Useful for implementing custom dialogue-ignoring ')

    parent_parser.add_argument('-I', '--ignore-range', metavar="<prefix>timestamp", dest="ignore_range", default=None,
                               type=time, nargs=2, action="append",
                               help="Time range to ignore when condensing, specified using two timestamps. "
                                    "Useful for removing openings and endings of shows. \n"
                                    "Time formatting example: '2h30m2s100ms', '10m20s', etc. \n"
                                    "Subtitles that fall into an ignored range before padding are trimmed so that they "
                                    "do not overlap with the ignore range. "
                                    "Timestamps can measured from the start of the audio (no prefix), end of the audio (using the 'e' prefix), or relative to "
                                    "another timestamp (using the '+' prefix). "
                               # "Examples: \n"
                               #     "\t-I 1m 2m30s  # ignore subtitles that exist between 01:00 and 02:30\n"
                               #     "\t-I 1m12s +1m30s  # ignore subtitiles in the 1m30s after 01:12\n"
                               #     "\t-I -3m -1ms  # ignore subtitles that exist between 3 minutes from end of audio and 1 minute from end of audio"
                               #     "\t-I -2m +1m30s  # ignore subtitles that exist in the first 1m30s of the last 2 minutes of audio"
                                    "If batch mode is enabled, the same ranges are applied to ALL outputs."
                                    "Multiple ranges can be specified like so: -I 2m 3m30s -I 20m 21m. ")

    parent_parser.add_argument('-Ic', '--ignore-chapter', metavar="<chapter name>", dest="ignore_chapters",
                               default=None,
                               type=str, action="append",
                               help="Chapter titles to ignore, case sensitive. Use -ls to get chapter titles. "
                                    "Can be used in addition to --ignore-range to ignore sections of the stream. "
                                    "Useful for ignoring chaptered intros and endings. "
                                    "Use --list-streams to get a list of chapter titles.")

    parent_parser.add_argument('-p', '--padding', metavar='msecs', dest='padding', default=0,
                               type=int,
                               help='Adds this many milliseconds of audio before and after every subtitle. '
                                    'Overlaps with adjacent subtitles are merged automatically.')

    parent_parser.add_argument('-tl', '--target-language', metavar='ISO_code', dest='target_lang', default=None,
                               type=str,
                               help='If set, attempts to use audio and subtitle files that are in this language first. '
                                    'Input should be an ISO 639-3 language code.')

    parent_parser.add_argument('-ls', '--list-streams', dest='list_streams', action='store_true', default=False,
                               help='Lists all audio, subtitle, and video streams as well as chapters '
                                    'found in given input files and exits.')

    parent_parser.add_argument('--preset', metavar='preset#', dest='preset', type=int, default=None,
                               help='If set, uses a given preset. User arguments will override presets.')
    # todo: consider listing presets somewhere else
    parent_parser.add_argument('-lp', '--list-presets', dest='list_presets', action='store_true', default=False,
                               help='Lists all available built-in presets and exits.')

    # todo: consider depreciating this option, it's not really _that_ useful aside from user debugging
    parent_parser.add_argument('-a', '--absolute-paths', action='store_true', dest='absolute_paths', default=False,
                               help='Prints absolute paths from the root directory instead of given paths.')

    parent_parser.add_argument('-ma', '--interactive', action='store_true', dest='interactive', default=False,
                               help='If set, will enable interactive stream picking. Overrides -ai, -si, -tl.')

    cia_parser = subparsers.add_parser('condense', parents=[parent_parser],
                                       help="Compress input audio/video into a shorter file",
                                       description="Compress input audio/video into a shorter file")
    srs_parser = subparsers.add_parser('srs', parents=[parent_parser],
                                       help="(Experimental) Snip input media and import into spaced-repetition software via a TSV file.",
                                       description="(Experimental) Snip input media line by line and export to a Anki-compatible "
                                                   "TSV file. The output TSV columns are:"+ """

1:\tSubtitle text;
2:\tTime range of subtitle in milliseconds, formatted as start-end;
3:\tAudio, formatted as [sound:media_start-end.mp3];
4:\tScreenshot, HTML formatted as <img src='media_start-end.jpg'>;
5:\tVideo clip (currently disabled);
6:\tComma-seperated list of input files used
""" )

    srs_parser.add_argument('-N', '--normalize', action='store_true', dest='normalize_audio', default=False,
                            help="If set, normalizes volume of audio clips to the same loudness. YMMV.")

    cia_parser.add_argument('-t', '--threshold', metavar='msecs', dest='threshold', default=0,
                            type=int,
                            help="If two subtitles start and end within (threshold + 2*padding) "
                                 "milliseconds of each other, they will be merged. "
                                 "Useful for preserving silences between "
                                 "subtitle lines.")

    cia_parser.add_argument('-r', '--partition', metavar='secs', dest='partition', default=0,
                            type=int,
                            help="If set, attempts to partition the input audio into "
                                 "seperate blocks of this size seconds BEFORE condensing. Partitions and splits respect "
                                 "subtitle boundaries and will not split a single subtitle across two output files."
                                 " 0 partition length is ignored. For example, if the partition size is 60 seconds and the "
                                 "input media is 180 seconds long, then there will be three output files. The first output "
                                 "file will contain condensed media from the first 60 seconds of the source material, "
                                 "the second output file will contain the next 60 seconds of input media, and so on.")

    cia_parser.add_argument('-s', '--split', metavar='secs', dest='split', default=0,
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

    cia_parser.add_argument('-c', '--minimum-compression-ratio', metavar='<ratio>', dest='minimum_compression_ratio',
                            default=0.2, type=float,
                            help="Will only generate from subtitle files that are this fraction long of the selected audio "
                                 "file. Default is 0.2, meaning the output condensed file must be at least 20 percent as long as "
                                 "the chosen audio stream. If the output doesn't reach this minimum, then a different "
                                 "subtitle file will be chosen, if available. Used for ignoring subtitles that contain only "
                                 "signs and songs.")

    cia_parser.add_argument('--no-gen-subtitle', action='store_true', dest='no_condensed_subtitles', default=False,
                            help="If set, won't output a condensed subtitle file. Useful for reducing file clutter.")

    args = parser.parse_args()

    # temporary patch until this feature is ready
    args.subtitle_regex_substrfilter = None
    args.subtitle_regex_substrfilter_nokeep = False

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    return args
