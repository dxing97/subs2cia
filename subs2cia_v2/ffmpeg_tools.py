import ffmpeg
import logging
from pathlib import Path
import os


# given a stream in the input file, demux the stream and save it into the outfile with some type
def ffmpeg_demux(infile: Path, stream_idx: int, outfile: Path):
    # output format is specified via extention on outfile
    logging.debug(f"demuxing stream {stream_idx} from file {infile} to {outfile}")
    video = ffmpeg.input(infile)
    stream = video[str(stream_idx)]  # don't need 0
    stream = ffmpeg.output(stream, str(outfile))
    stream = ffmpeg.overwrite_output(stream)  # todo: add option to not force overwrite
    logging.debug(f"ffmpeg arguments: {ffmpeg.get_args(stream)}")
    try:
        ffmpeg.run(stream, quiet=logging.getLogger().getEffectiveLevel() >= logging.WARNING)  # verbose only
    except ffmpeg.Error as e:
        logging.warning(
            f"Couldn't demux file, skipping. ffmpeg output: \n" + e.stderr.decode("utf-8"))
        return None
    return outfile


def ffmpeg_condense_audio(audiofile, sub_times, outfile=None):
    if outfile is None:
        outfile = "condensed.flac"
    logging.info(f"saving condensed audio to {outfile}")  # todo: print input/output files at top of start()

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
    logging.debug(f"ffmpeg arguments: {ffmpeg.get_args(combined)}")
    ffmpeg.run(combined, quiet=logging.getLogger().getEffectiveLevel() >= logging.WARNING)


def export_condensed_audio(divided_times, audiofile: Path, outfile=None, use_absolute_numbering=False):
    # outfile is full path with extension
    audiofile = str(audiofile)
    if outfile is not None:
        outfile = str(outfile)

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
                outfilesplit = os.path.splitext(outfile)[0] + \
                               f".pt{idx}" + \
                               ".condensed" + \
                               os.path.splitext(outfile)[1]
            else:
                outfilesplit = os.path.splitext(outfile)[0] + \
                               (f".p{p + 1}" if len(divided_times) != 1 else "") + \
                               (f".s{s + 1}" if len(partition) != 1 else "") + \
                               ".condensed" + \
                               os.path.splitext(outfile)[1]

            ffmpeg_condense_audio(audiofile=audiofile, sub_times=split, outfile=outfilesplit)