# Condensed Immersion Audio Generator

import pysubs2 as ps2  # for reading in subtitles
import ffmpeg  # using ffmpeg-python
import argparse
import os
import pycountry
from datetime import timedelta
from pprint import pprint

# also installed SoX, ffmpeg, libav (for pydub)


verbose = False


# given raw subtitle timing data, merge overlaps and perform padding and merging
def merge_times(times, threshold=0, padding=0):
    # padding: time to add to the beginning and end of each subtitle. Resulting overlaps are removed.
    # threshold: if two subtitles are within this distance apart, they will be merged in the audio track

    print("merging times")
    times.sort(key=lambda x: x[0])  # sort by first value in tuple

    initial = len(times)
    if padding > 0:
        for time in times:
            time[0] -= padding
            time[1] += padding

    # even if threshold is 0 any added padding may cause overlaps, which the code below will also merge
    idx = 0
    while idx < len(times) - 1:
        if times[idx + 1][0] < times[idx][1] + threshold:
            # if the next subtitle starts within 3 seconds of the current subtitle finishing, merge them
            times[idx][1] = times[idx + 1][1]
            del times[idx + 1]
            if idx < len(times) - 1:
                continue
        idx += 1

    print(f"merged {initial} subtitles into {len(times)} audio snippets\n")
    return times


# examine a subtitle's text and determine if it contains text or just signs/song styling
# could be much more robust, by including regexes
def is_spoken_dialogue(line, include_all=False):
    if include_all:  # ignore filtering
        return True
    if line.type != "Dialogue":
        return False
    if len(line.text) == 0:
        return False
    if line.text[0] == '{':
        return False

    # list of characters that, if present anywhere in the subtitle text, means that the subtitle is not dialogue
    globally_invalid = ["♪", "♪"]
    if any(invalid in line.text for invalid in globally_invalid):
        return False
    return True


# given a path to a subtitle file, load it in and strip it of non-dialogue text
# keyword arguments are filter options that are passed to is_spoken_dialogue for filtering configuration
def load_subtitle_times(subfile, **kwargs):
    print("loading", subfile)
    subs = ps2.load(subfile)
    print(subs)
    print("loaded subtitles\n")

    times = list()
    count = 0
    for idx, line in enumerate(subs):
        # print(line)
        if is_spoken_dialogue(line, **kwargs):
            # print(line)
            times.append([line.start, line.end])
        else:
            # print(f"ignoring {line.text}, probably not spoken dialogue")
            count += 1
            pass
    print(f"ignored {count} lines")  # number of subtitles that looked like they didn't contain dialogue

    # print(times)
    if len(times) == 0:
        print("warning: got 0 dialogue lines from subtitle")
    return times


# uses ffmpeg to
def ffmpeg_condense_audio(audiofile, sub_times, outfile=None):
    if outfile is None:
        outfile = "condensed.flac"
    print("saving audio to", outfile)

    # get samples in audio file
    audio_info = ffmpeg.probe(audiofile, cmd='ffprobe')
    sps = int(
        audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
    # samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track

    stream = ffmpeg.input(audiofile)
    clips = list()
    for time in sub_times:  # times are in milliseconds
        start = int(time[0] * sps / 1000)  # convert to sample index
        end = int(time[1] * sps / 1000)
        # use start_pts for sample/millisecond level precision
        clips.append(stream.audio.filter('atrim', start_pts=start, end_pts=end).filter('asetpts', 'PTS-STARTPTS'))
    combined = ffmpeg.concat(*clips, a=1, v=0)
    if os.path.splitext(outfile)[1] == ".mp3":
        combined = ffmpeg.output(combined, outfile, audio_bitrate='320k')  # todo: make this user-settable
    else:
        combined = ffmpeg.output(combined, outfile)
    combined = ffmpeg.overwrite_output(combined)
    ffmpeg.run(combined, quiet=not verbose)


# figure out what files we were given to work with
def probe_sources(subfile=None, audiofile=None, videofile=None):
    if (audiofile or videofile) is None:
        print("missing audio")
        return None
    if (subfile or videofile) is None:
        print("missing subtitles")
        return None
    sources = dict(audio=[], subtitles=[])

    if subfile is not None:  # manually specified subtitle files come first
        sources["subtitles"].append(subfile)

    if audiofile is not None:  # manually specified audio files come first
        audio_info = ffmpeg.probe(audiofile, cmd='ffprobe')
        # print(audio_info)
        if audio_info['streams'][0]['codec_type'] == 'audio':  # make sure it's an audio file
            sources["audio"].append(audiofile)
        else:
            print(
                f"WARNING: {audiofile} doesn't contain any ffmpeg-readable audio. "
                f"Will try to fall back to video source.")

    if videofile is not None:
        video_info = ffmpeg.probe(videofile, cmd='ffprobe')
        # print(video_info)
        for idx, stream in enumerate(video_info['streams']):
            if stream['codec_type'] == 'audio':
                # print(stream)
                sources['audio'].append((video_info, stream))
            elif stream['codec_type'] == 'subtitle':
                # print(stream)
                sources['subtitles'].append((video_info, stream))

    if len(sources['audio']) == 0:
        print("no audio found, exiting")
        exit()
    if len(sources['subtitles']) == 0:
        print("WARNING: no subtitles found, can't condense audio. will attempt to demux.")
    print(f"found {len(sources['audio'])} audio source(s) and {len(sources['subtitles'])} subtitle source(s)")
    return sources


def pick_audio_source(sources,
                      alang=None,
                      force_audio=0):
    audio_idx = 0  # default is first track, be it user specified or automatically found
    if force_audio != 0:
        # get ffmpeg stream with force_audio index and save its sources idx to audio_idx
        if isinstance(sources['audio'][0], str):
            print(f"ignoring force_audio, using {sources['audio'][0]}")
        elif force_audio > len(sources['audio']):
            print(
                f"WARNING: can't force audio stream #{force_audio}, "
                f"there are only {len(sources['audio'])} audio streams")
        else:
            audio_idx = force_audio - 1
            return audio_idx

    if alang is not None:
        for idx, item in enumerate(sources["audio"]):
            if not isinstance(item,
                              str):  # raw audio/subtitle files don't contain language information most of the time
                (parent, stream) = item
                if pycountry.languages.lookup(stream['tags']['language']) == pycountry.languages.lookup(alang):
                    # found a match
                    print(f"found {stream['tags']['language']} audio in video file")
                    audio_idx = idx
                    break
            else:
                print("using given audio file, ignoring video audio tracks")
                audio_idx = idx
                break
    return audio_idx


def pick_subtitle_source(sources,
                         slang=None,
                         force_subtitles=0):
    sub_idx = 0  # default: use first subtitle source
    if force_subtitles != 0:
        # get ffmpeg stream with force_subtitle index and save its sources idx to audio_idx
        if isinstance(sources['subtitles'][0], str):
            print(f"ignoring force_subtitles, using {sources['subtitles'][0]}")
        elif force_subtitles > len(sources['subtitles']):
            print(
                f"WARNING: can't force subtitle stream #{force_subtitles}, "
                f"there are only {len(sources['subtitles'])} subtitle streams")
        else:
            sub_idx = force_subtitles - 1
            return sub_idx

    if slang is not None:
        for idx, item in enumerate(sources["subtitles"]):
            if not isinstance(item,
                              str):
                (parent, stream) = item
                if pycountry.languages.lookup(stream['tags']['language']) == pycountry.languages.lookup(slang):
                    # found a match
                    print(f"found {stream['tags']['language']} subtitles in video file")
                    sub_idx = idx
                    break
            else:
                print("using given subtitle file, ignoring video subtitles")
                sub_idx = idx
                break
        if sub_idx == -1:
            _, stream = sources['subtitles'][0]
            print(f"didn't find a {slang} subtitle track , using first subtitle track ({stream['tags']['language']})")
            sub_idx = 0
    return sub_idx


# pick subtitles, audio to condense based on language or stream options
def pick_sources(sources,  # dict of audio and subtitle sources that have been found
                 alang=None, slang=None,  # languages to prefer as ISO language codes (NOT country codes)
                 force_audio=0, force_subtitles=0
                 # if set, will choose these audio/subtitle streams regardless of language setting
                 ):
    sub_idx = pick_subtitle_source(sources, slang=slang, force_subtitles=force_subtitles)
    print(f"using subtitle source {sub_idx}")  # ({sources['subtitles'][sub_idx]})")
    audio_idx = pick_audio_source(sources, alang, force_audio=force_audio)
    print(f"using audio source {audio_idx}")  # ({sources['audio'][sub_idx]})")
    return sub_idx, audio_idx  # sources dict entires


# given a stream in the input file, demux the stream and save it into the outfile with some type
def demux(infile, stream_idx, outfile):
    # output format is specified via extention on outfile
    video = ffmpeg.input(infile)
    stream = video[str(stream_idx)]  # don't need 0
    stream = ffmpeg.output(stream, outfile)
    stream = ffmpeg.overwrite_output(stream)  # todo: add option to not force overwrite
    ffmpeg.run(stream, quiet=not verbose)
    return outfile


def demux_audio(videofile, sources, audio_idx):
    if not isinstance(sources["audio"][audio_idx], str):  # if not manually specified audio file
        # input file: /original/path/video.file.mkv
        # output file: /original/path/video.file.languagecode.flac
        language = sources['audio'][audio_idx][1]['tags']['language']
        stream_idx = sources['audio'][audio_idx][1]['index']
        audiofile = os.path.splitext(videofile)[0] + f".audio{audio_idx + 1}.{language}.flac"
        if not os.path.exists(audiofile):  # don't overwrite previosly existing file
            audiofile = demux(infile=videofile, stream_idx=stream_idx, outfile=audiofile)
        print(f"demuxed stream {stream_idx} ({language}) audio track to {audiofile}")
        return audiofile
    return sources['audio'][0]


def demux_subtitles(videofile, sources, sub_idx):
    if not isinstance(sources["subtitles"][sub_idx], str):  # if subtitle file not specified
        # demux subtitles from video file
        language = sources['subtitles'][sub_idx][1]['tags']['language']
        stream_idx = sources['subtitles'][sub_idx][1]['index']
        subfile = os.path.splitext(videofile)[
                      0] + f".subtitle{sub_idx + 1}.{language}.ass"  # todo: probe subtitle type and save to the appropriate extension
        if not os.path.exists(subfile):  # don't overwrite existing file
            subfile = demux(infile=videofile, stream_idx=stream_idx, outfile=subfile)
        print(f"demuxed stream {stream_idx} ({language}) subtitle track to {subfile}")
        return subfile
    return sources['subtitles'][0]


def decide_partitions(sub_times, partition=0):
    if partition == 0:
        return [(0, len(sub_times)), ]

    partitions = list()
    current_partition = 0
    start = 0
    idx = 0
    for idx, t in enumerate(sub_times):
        current_partition_boundary = (current_partition + 1) * partition
        if t[1] > current_partition_boundary:
            if abs(t[1] - current_partition_boundary) < abs(sub_times[idx - 1][1] - current_partition_boundary):
                end = idx + 1
            else:
                end = idx
            partitions.append((start, end))
            current_partition += 1
            start = end
    end = idx + 1
    partitions.append((start, end))
    return partitions


def split_times(sub_times, partition_indicies, splitsize=0):
    partition_times = sub_times[partition_indicies[0]:partition_indicies[1]]
    if splitsize == 0:
        return [partition_times, ]

    prev = 0
    for idx, time in enumerate(sub_times):
        time.append(time[1] - time[0] + prev)
        prev = time[2]

    start = 0
    idx = 0
    splits = list()
    current_split = 0
    for idx, t in enumerate(partition_times):
        current_partition_boundary = (current_split + 1) * splitsize
        if t[2] > current_partition_boundary:
            if abs(t[2] - current_partition_boundary) < abs(partition_times[idx - 1][2] - current_partition_boundary):
                end = idx + 1
            else:
                end = idx
            splits.append((start, end))
            current_split += 1
            start = end
    end = idx + 1
    splits.append((start, end))
    splittimes = list()
    for split in splits:
        tmp = partition_times[split[0]:split[1]]
        tmp = [[x[0], x[1]] for x in tmp]
        splittimes.append(tmp)
    return splittimes


# todo: remove ffmpeg_condense_audio from this part
def partition_and_split(sub_times, partition_size=0, split_size=0):
    # returns a list tuple index pairs in [start, end) format for sub_times
    partitions = decide_partitions(sub_times,
                                   partition=partition_size)
    """
    partition1
        split1
            time1
                start
                end
            time2
                ...
        split2
            time1
        split3
        split4...
    partition2
        split1
            time1
            time2...
    """
    divided_times = list()
    for p, partition_size in enumerate(partitions):
        # returns list of list of times in milliseconds, can feed into condense_audio
        times = split_times(sub_times, partition_size,
                            splitsize=split_size)
        divided_times.append(times)

    return divided_times


def export_condensed_audio(divided_times, audiofile, outfile, use_absolute_numbering=False):
    # outfile is full path with extension
    if outfile is None:  # no output path given, use audiofile path
        outfile = audiofile
    elif outfile[0] == '.' and outfile[1:].isalnum():  # outfile is just an extension, use audiofile for path
        # extension = outfile
        outfile = os.path.splitext(audiofile)[0] + outfile
    else:  # outfile is already full path with extension
        pass
    idx = 0
    for p, partition in enumerate(divided_times):
        if len(partition) == 0:
            continue
        for s, split in enumerate(partition):
            if len(split) == 0:
                continue
            idx += 1
            if use_absolute_numbering:
                outfile = os.path.splitext(outfile)[0] + \
                          f".pt{idx}" + \
                          ".condensed" + \
                          os.path.splitext(outfile)[1]
            else:
                outfile = os.path.splitext(outfile)[0] + \
                          (f".p{p + 1}" if len(divided_times) != 1 else "") + \
                          (f".s{s + 1}" if len(partition) != 1 else "") + \
                          ".condensed" + \
                          os.path.splitext(outfile)[1]

            ffmpeg_condense_audio(audiofile=audiofile, sub_times=split, outfile=outfile)


def print_compression_ratio(sub_times, audiofile):
    audio_info = ffmpeg.probe(audiofile, cmd='ffprobe')
    sps = int(
        audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
    samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track

    audio_total = samples / sps * 1000
    subs_total = sum([x2 - x1 for x1, x2 in sub_times])  # in ms
    print(f"will condense {str(timedelta(milliseconds=audio_total)).split('.')[0]} of source audio into "
          f"{str(timedelta(milliseconds=subs_total)).split('.')[0]} ({round(subs_total / audio_total * 100, 1)}% compression ratio)")


def test(audiofile=None, subfile=None, videofile=None, outfile="condensed.flac", dry_run=False, threshold=0, padding=0,
         partition_size=0, split_size=0, alang=None, slang=None, force_audio=0, force_subtitles=0, no_retry=False,
         absolute_numbering=False, **kwargs):
    sources = probe_sources(subfile=subfile, audiofile=audiofile, videofile=videofile)
    if sources is None:
        print("not enough sources")
        return

    (sub_idx, audio_idx) = pick_sources(sources=sources, alang=alang, slang=slang, force_audio=force_audio,
                                        force_subtitles=force_subtitles)
    # if needed, demux audio/subtitles from video

    valid = False
    tries = 0
    sub_times = list()
    while valid is False:
        subfile = demux_subtitles(videofile=videofile, sources=sources, sub_idx=sub_idx)
        ## subtitle file might be a signs/songs track, so it won't contain any dialogue lines. we can try a different sub track in that case
        sub_times = load_subtitle_times(subfile)
        if len(sub_times) == 0:  # todo: what if there's an anomolous amount of subtitles? (requires more testing)
            # didn't find any subtitles, try a different subtitle track
            tries += 1
            if no_retry:
                print(f"subtitle file {subfile} doesn't contain valid dialogue lines, not going to retry")
                exit(1)
            elif tries < len(sources['subtitles']):
                sub_idx += 1 % len(sources['subtitles'])
                print(f"trying subtitle track {sub_idx}")
            else:
                print("no subtitle files contain valid dialogue lines")
                sub_idx = -1
        else:
            valid = True

    audiofile = demux_audio(videofile=videofile, sources=sources, audio_idx=audio_idx)
    if sub_idx == -1:
        # no good subtitle found, demux only
        print(f"no valid subtitle source found, demuxing only")
        return

    sub_times = merge_times(times=sub_times, threshold=threshold, padding=padding)

    print_compression_ratio(sub_times=sub_times, audiofile=audiofile)

    divided_times = partition_and_split(sub_times=sub_times, partition_size=partition_size * 1000,
                                        split_size=split_size * 1000)

    export_condensed_audio(divided_times=divided_times, audiofile=audiofile, outfile=outfile,
                           use_absolute_numbering=absolute_numbering)


def get_args():
    parser = argparse.ArgumentParser(description='subs2cia: subtitle-based condensed audio generator')
    parser.add_argument('-a', '--audio', metavar='path/to/audio', dest='audiofile', required=False, type=str,
                        help='Path to audio file. Supported types: any type ffmpeg supports.')  # todo: automagically find audio files in wd
    parser.add_argument('-s', '--subtitles', metavar='path/to/subtitles', dest='subfile', required=False, type=str,
                        help='Path to subtitle file. Supported types: .ass, .srt. Unsupported types: .sup, PGS')  # todo: automagically find subtitles in wd
    parser.add_argument('-i', '--video', metavar='path/to/video', dest='videofile', required=False, type=str,
                        help='Path to video file containing audio and subtitles that can be demuxed. Tracks from video sources are ignored if -a or -s is present. . Supported containers: any type ffmpeg supports.')
    parser.add_argument('-o', '--output', metavar='path/to/outputfile.flac', dest='outfile', type=str,
                        help='Path to output condensed audio to (audio codec assumed from extension). Default is to use the audio or video file name and extension (usually flac). '
                             'You can also specify just the output file type by using an extension, e.g. for .mp3, use -o ".mp3"')

    parser.add_argument('-d', '--dry-run', action='store_true', dest='dry_run', default=False,
                        help='If nonzero, reads inputs, processes them, but does not demux or write output(s) to disk')
    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    parser.add_argument('-t', '--threshold', metavar='msecs', dest='threshold', type=int, default=0,
                        help='maximum distance between subtitles before splitting the audio snippet')
    parser.add_argument('-p', '--padding', metavar='msecs', dest='padding', type=int, default=0,
                        help='default padding added to both ends of a subtitle interval')

    parser.add_argument('-P', '--partition', metavar='secs', dest='partition_size', type=int, default=0,
                        help='If set, attempts to partition the input audio into seperate blocks of this size before condensing. 0 partition length is ignored.')
    parser.add_argument('-S', '--split', metavar='secs', dest='split_size', type=int, default=0,
                        help='If set, attempts to split the condensed audio into seperate parts that do not exceed this size. 0 split size is ignored.')
    parser.add_argument('--use-absolute-numbering', dest='absolute_numbering', action='store_true', default=False,
                        help='If set, names partitions/splits as "pt1, pt2, ...", instead of "p1s1, p1s2, p2s1, ..."')

    parser.add_argument('-al', '--audio-language', metavar='ISO_code', dest='alang', type=str,
                        help='If set, and given a video file, attempts to use audio from the video that is in this language. Expects ISO language code.')
    parser.add_argument('-sl', '--subtitle-language', metavar='ISO_code', dest='slang', type=str,
                        help='If set, and given a video file, attempts to use subtitles from the video that is in this language. Expects ISO language code.')

    parser.add_argument('-fs', '--force-subtitle-stream', metavar='stream#', dest='force_subtitles', type=int,
                        default=0,
                        help='If set, and given a video file, attempts to use the stream# subtitle stream from the video file for subtitles. Default is to use the first subtitle track. Ignored if -s is present. 1-indexed.')
    parser.add_argument('-fa', '--force-audio-stream', metavar='stream#', dest='force_audio', type=int, default=0,
                        help='If set, and given a video file, attempts to use the stream# audio stream from the video file for audio. Default is to use the first audio track. Ignored if -a is present. 1-indexed')
    parser.add_argument('-N', '--no-retry', dest='no_retry', action='store_true', default=False,
                        help='If set, makes no attempt to retry different audio/subtitle tracks if anything is wrong with an audio/subtitle file.')

    parser.add_argument('--preset', metavar='preset#', dest='preset', type=int, default=None,
                        help='If set, uses a given preset. Will override user arguments.')
    parser.add_argument('-lp', '--list-presets', dest='list_presets', action='store_true', default=False,
                        help='If set, uses a given preset. Will override user arguments.')
    args = parser.parse_args()
    return args


presets = [
    {  # preset 0
        'preset_description': "Padded and merged Japanese condensed audio",
        'outfile': '.mp3',
        'threshold': 1500,
        'padding': 200,
        'partition_size': 1800,  # 30 minutes, for long movies
        'alang': 'ja',
    },
    {  # preset 1
        'preset_description': "Unpadded Japanese condensed audio",
        'outfile': '.mp3',
        'threshold': 0,  # note: default is 0
        'padding': 0,  # note: default is 0
        'partition_size': 1800,  # 30 minutes, for long movies
        'alang': 'ja',
    },
]


def list_presets():
    for idx, preset in enumerate(presets):
        print(f"Preset {idx}")
        pprint(preset)


if __name__ == "__main__":
    args = get_args()

    if args.list_presets:
        list_presets()

    verbose = args.verbose
    if verbose:
        print("running in verbose mode")

    args = vars(args)
    if args['preset'] is not None:
        if abs(args['preset']) >= len(presets):
            print(f"Preset {args['preset']} does not exist")
            exit(0)
        print(f"using preset {args['preset']}")
        for key, val in presets[args['preset']].items():
            args[key] = val
    test(**args)
    print("done")
