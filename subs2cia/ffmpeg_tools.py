from __future__ import unicode_literals, print_function
import logging
from pathlib import Path
import subprocess
from typing import List, Union
import gevent, gevent.monkey
from tqdm import tqdm, TqdmWarning

import warnings
warnings.filterwarnings("ignore", category=TqdmWarning)

import contextlib
import ffmpeg
import gevent
import gevent.monkey; gevent.monkey.patch_all(thread=False)
import os
import shutil
import socket
import sys
import tempfile
import textwrap

import json


@contextlib.contextmanager
def _tmpdir_scope():
    tmpdir = tempfile.mkdtemp()
    try:
        yield tmpdir
    finally:
        shutil.rmtree(tmpdir)


def _do_watch_progress(filename, sock, handler):
    """Function to run in a separate gevent greenlet to read progress
    events from a unix-domain socket."""
    connection, client_address = sock.accept()
    data = b''
    try:
        while True:
            more_data = connection.recv(16)
            if not more_data:
                break
            data += more_data
            lines = data.split(b'\n')
            for line in lines[:-1]:
                line = line.decode()
                parts = line.split('=')
                key = parts[0] if len(parts) > 0 else None
                value = parts[1] if len(parts) > 1 else None
                handler(key, value)
            data = lines[-1]
    finally:
        connection.close()


@contextlib.contextmanager
def _watch_progress(handler):
    """Context manager for creating a unix-domain socket and listen for
    ffmpeg progress events.
    The socket filename is yielded from the context manager and the
    socket is closed when the context manager is exited.
    Args:
        handler: a function to be called when progress events are
            received; receives a ``key`` argument and ``value``
            argument. (The example ``show_progress`` below uses tqdm)
    Yields:
        socket_filename: the name of the socket file.
    """
    with _tmpdir_scope() as tmpdir:
        socket_filename = os.path.join(tmpdir, 'sock')
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        with contextlib.closing(sock):
            sock.bind(socket_filename)
            sock.listen(1)
            child = gevent.spawn(_do_watch_progress, socket_filename, sock, handler)
            try:
                yield socket_filename
            except:
                gevent.kill(child)
                raise



@contextlib.contextmanager
def show_progress(total_duration, desc):
    """Create a unix-domain socket to watch progress and render tqdm
    progress bar."""
    with tqdm(total=round(total_duration, 2), position=0, unit='sec', desc=desc) as bar:
        def handler(key, value):
            if key == 'out_time_ms':
                time = round(float(value) / 1000000., 2)
                bar.update(time - bar.n)
            elif key == 'progress' and value == 'end':
                bar.update(bar.total - bar.n)
        with _watch_progress(handler) as socket_filename:
            yield socket_filename


# given a stream in the input file, demux the stream and save it into the outfile with some type
def ffmpeg_demux(infile: Path, stream_idx: int, outfile: Path):
    # output format is specified via extention on outfile
    logging.debug(f"demuxing stream {stream_idx} from file {infile} to {outfile}")
    video = ffmpeg.input(str(infile))
    stream = video[str(stream_idx)]  # don't need 0
    stream = ffmpeg.output(stream, str(outfile))
    stream = ffmpeg.overwrite_output(stream)
    logging.debug(f"ffmpeg arguments: {ffmpeg.get_args(stream)}")

    quiet = not logging.root.isEnabledFor(logging.DEBUG)

    try:
        ffmpeg.run(stream, quiet=quiet)  # verbose only
    except ffmpeg.Error as e:
        if e.stderr is None:
            logging.warning(
                f"Couldn't demux stream {stream_idx} from {infile}, skipping.")
            return None
        logging.warning(
            f"Couldn't demux stream {stream_idx} from {infile}, skipping. ffmpeg output: \n" + e.stderr.decode("utf-8"))
        return None
    return outfile


# from ffmpeg-python _run.py
class Error(Exception):
    def __init__(self, cmd, stdout, stderr: bytes):
        super(Error, self).__init__(
            '{} error (see stderr output for detail)'.format(cmd)
        )
        self.stdout = stdout
        self.stderr = stderr


def ffmpeg_condense_audio(audiofile, sub_times, quality: Union[int, None], to_mono: bool, outfile=None, codec=''):
    if outfile is None:
        outfile = "condensed.flac"
    # logging.info(f"saving condensed audio to {outfile}")

    # get samples in audio file
    # prefer codec_time_base because some files will have different values for each, and codec_time_base seems to be the
    #  most accurate
    audio_info = ffmpeg.probe(audiofile, cmd='ffprobe')
    if 'codec_time_base' in audio_info['streams'][0]:
        # audio samples per second, inverse of sampling frequency
        sps = int(
            audio_info['streams'][0]['codec_time_base'].split('/')[1])
    elif 'time_base' in audio_info['streams'][0]:
        # audio samples per second, inverse of sampling frequency
        sps = int(
            audio_info['streams'][0]['time_base'].split('/')[
                1])
    else:
        info = json.dumps(audio_info['streams'][0])
        logging.error("ffprobe couldn't determine audio time_base, can't condense")
        raise Error("", '', info.encode('utf-8'))
    # samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track
    # duration_ts uses time_base, not codec_time_base

    stream = ffmpeg.input(audiofile)

    clips = list()
    for time in sub_times:  # times are in milliseconds
        start = int(time[0] * sps / 1000)  # convert to sample index
        end = int(time[1] * sps / 1000)
        # use start_pts for sample/millisecond level precision
        clips.append(stream.audio.filter('atrim', start_pts=start, end_pts=end).filter('asetpts', 'PTS-STARTPTS'))
    combined = ffmpeg.concat(*clips, a=1, v=0)

    kwargs = {}

    if codec:
        kwargs['acodec'] = codec

    if Path(outfile).suffix.lower() == ".mp3" or codec == 'mp3':
        if quality is None:
            kwargs['audio_bitrate'] = "320k"
        else:
            kwargs['audio_bitrate'] = f"{quality}k"
    if to_mono:
        kwargs['ac'] = 1

    combined = ffmpeg.output(combined, outfile, **kwargs)
    combined = ffmpeg.overwrite_output(combined)

    if logging.root.isEnabledFor(logging.DEBUG):
        logging.debug(f"ffmpeg_condense_audio: ffmpeg arguments: {' '.join(ffmpeg.get_args(combined))}")

    duration = sum([end - start for start, end in sub_times]) / 1000
    ffmpeg_exec(duration, outfile, combined)


def export_condensed_audio(divided_times, audiofile: Path, quality: Union[int, None], to_mono: bool, outfile=None,
                           use_absolute_numbering=False, codec=''):
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
            if use_absolute_numbering:  # todo: remove outfile naming from this function
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
            try:
                ffmpeg_condense_audio(audiofile=audiofile, sub_times=split, outfile=outfilesplit, quality=quality,
                                      to_mono=to_mono, codec=codec)
                logging.info(f"Wrote condensed audio to {outfilesplit}")
            except Error as e:
                logging.error(
                    f"ffmpeg couldn't export audio. ffmpeg output: \n" + e.stderr.decode("utf-8"))


def export_condensed_video(divided_times, audiofile: Path, subfile: Path, videofile: Path, outfile=None,
                           use_absolute_numbering=False):
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
            # todo: need to split subfiles with partition, split options
            try:
                ffmpeg_condense_video(audiofile=audiofile, videofile=str(videofile), subfile=str(subfile),
                                      sub_times=split, outfile=outfilesplit)
            except Error as e:
                logging.error(
                    f"ffmpeg couldn't export video. ffmpeg output: \n" + e.stderr.decode("utf-8"))


def trim(input_path, output_path, start=30, end=60):
    input_stream = ffmpeg.input(input_path)

    vid = (
        input_stream.video
            .trim(start=start, end=end)
            .setpts('PTS-STARTPTS')
    )
    aud = (
        input_stream.audio
            .filter_('atrim', start=start, end=end)
            .filter_('asetpts', 'PTS-STARTPTS')
    )

    joined = ffmpeg.concat(vid, aud, v=1, a=1).node
    output = ffmpeg.output(joined[0], joined[1], output_path)
    output.run()


def ffmpeg_exec(duration: float, outfile: str, combined):
    def run(combined):
        args = ffmpeg.get_args(combined)

        if len("ffmpeg " + " ".join(args)) > 30000:
            # logging.info("Arguments passed to ffmpeg exceeds 32767 characters while running on a Windows system. "
            #              "Will try using a temporary file to pass filter_complex arguments to ffmpeg.")
            logging.debug("ffmpeg command length exceeds 30000, will try writing to a temporary file")
            idx = args.index("-filter_complex") + 1
            complex_filter = str(args[idx])
            # write complex_filter to a temporary file
            fp = tempfile.NamedTemporaryFile(
                delete=False)  # don't delete b/c can't open file again when it's already open in windows
            fp.write(complex_filter.encode(encoding="utf-8"))
            fp.close()
            logging.debug(f"using temporary file {fp.name}")
            args[idx] = fp.name
            args[idx - 1] = "-filter_complex_script"
        args = ["ffmpeg"] + args  # + ['-progress', 'unix://{}'.format(socket_filename)]

        # ffmpeg.run(combined, quiet=logging.getLogger().getEffectiveLevel() >= logging.WARNING)

        pipe_stdin = False
        pipe_stdout = True
        pipe_stderr = True
        quiet = not logging.root.isEnabledFor(logging.DEBUG)

        stdin_stream = subprocess.PIPE if pipe_stdin else None
        stdout_stream = subprocess.PIPE if pipe_stdout or quiet else None
        stderr_stream = subprocess.PIPE if pipe_stderr or quiet else None
        process = subprocess.Popen(
            args, stdin=stdin_stream, stdout=stdout_stream, stderr=stderr_stream
        )
        out, err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise Error('ffmpeg', out, err)

    # if os.name == 'posix':
    if hasattr(socket, 'AF_UNIX') and logging.root.level <= logging.INFO:
        with show_progress(total_duration=duration, desc=outfile) as socket_filename:
            combined = combined.global_args('-progress', 'unix://{}'.format(socket_filename))
            run(combined)
    else:
        run(combined)


def ffmpeg_condense_video(audiofile: str, videofile: str, subfile: str, sub_times, outfile):
    # logging.info(f"saving condensed video to {outfile}")

    # get samples in audio file
    audio_info = ffmpeg.probe(audiofile, cmd='ffprobe')
    sps = int(
        audio_info['streams'][0]['time_base'].split('/')[1])  # audio samples per second, inverse of sampling frequency
    # samples = audio_info['streams'][0]['duration_ts']  # total samples in audio track

    audiostream = ffmpeg.input(audiofile)
    videostream = ffmpeg.input(videofile)
    substream = ffmpeg.input(subfile)
    vid = videostream.video.filter_multi_output('split')
    # sub = videostream['s'].filter_multi_output('split')
    aud = audiostream.audio.filter_multi_output('asplit')

    clips = []
    for idx, time in enumerate(sub_times):  # times are in milliseconds
        # start = int(time[0] * sps / 1000)  # convert to sample index
        # end = int(time[1] * sps / 1000)
        start = time[0] / 1000
        end = time[1] / 1000
        # use start_pts for sample/millisecond level precision

        a = aud[idx].filter('atrim', start=start, end=end).filter('asetpts', expr='PTS-STARTPTS')
        v = vid[idx].trim(start=start, end=end).setpts('PTS-STARTPTS')
        # s = sub[idx].trim(start=start, end=end).setpts('PTS-STARTPTS')
        clips.extend((v, a))

    out = ffmpeg.concat(
        *clips,
        v=1,
        a=1
    ).output(substream, outfile)

    # output = ffmpeg.output(joined[0], joined[1], outfile)
    out = ffmpeg.overwrite_output(out)
    if logging.root.isEnabledFor(logging.DEBUG):
        logging.debug(f"ffmpeg_condense_video: ffmpeg arguments: {' '.join(ffmpeg.get_args(out))}")

    duration = sum([end - start for start, end in sub_times]) / 1000
    ffmpeg_exec(duration, outfile, out)


def ffmpeg_get_frames(videofile: Path, timestamps: List[int], outdir: Path, outstem: str, outext: str, w: int, h: int):
    r"""

    :param videofile:
    :param timestamps:
    :param outdir:
    :param outstem:
    :param outext: image extension. Should include dot.
    :return:
    """
    # todo: make async if needed
    for idx, timestamp in enumerate(timestamps):
        outname = outstem + f"_{idx}_{timestamp}" + outext
        ffmpeg_get_frame_fast(videofile, timestamp, outdir / outname, w, h)


# too slow, not used
def ffmpeg_get_frame(videofile: Path, timestamp: int, outpath: Path):
    # logging.debug(f"Saving frame from {videofile} at {timestamp}ms to {outpath}")
    videostream = ffmpeg.input(str(videofile))

    # from https://superuser.com/a/1330042
    # this method will probably need the windows long-argument fix as well
    # it's also relatively slow
    videostream = videostream.video.filter('select', f"lt(prev_pts*TB,{timestamp/1000})*gte(pts*TB,{timestamp/1000})")

    # from https://stackoverflow.com/a/28321986
    # TODO: compare speed of this and the other method

    videostream = ffmpeg.output(videostream, str(outpath), vsync='drop')
    args = videostream.get_args()
    logging.debug(f"ffmpeg_get_frame: args: {args}")
    ffmpeg.run(videostream)


def ffmpeg_get_frame_fast(videofile: Path, timestamp: int, outpath: Path, w: int, h: int,
                          format: Union[str, None] = None, capture_stdout: bool = False, silent: bool = True):
    r"""
    Gets a screenshot from a video file
    :param videofile: Path to input file containing a video stream
    :param timestamp: Timestamp to get in milliseconds
    :param outpath: Output path to save to. If set to 'pipe:', will instead pipe to stdout.
    :param w: Width in pixels. -1 preserves aspect ratio.
    :param h: Height in pixels. -1 preserves aspect ratio.
    :param format: Output format (e.g. mjpeg for JPG, image2 for PNG, etc), required if outpath is missing/misleading an extension.
    :param capture_stdout: If set to true, captures ffmpeg's stdout and returns as raw bytestream.
            Otherwise prints to stdout.
    :param silent: Suppresses stderr from printing if set. Useful for exporting many frames at a time.
    :return:
    """

    # from https://stackoverflow.com/a/28321986
    videostream = ffmpeg.input(str(videofile), ss=timestamp/1000)
    if w == -1 and h == -1:
        pass
    else:
        videostream = videostream.video.filter('scale', w, h)

    kwargs = {'vframes': 1}
    if format is not None:
        kwargs['format'] = format

    videostream = ffmpeg.output(videostream, str(outpath), **kwargs)
    videostream = ffmpeg.overwrite_output(videostream)
    args = videostream.get_args()
    logging.debug(f"ffmpeg_get_frame_fast: args: {args}")
    stdout, stderr = ffmpeg.run(videostream, capture_stdout=capture_stdout, capture_stderr=silent)

    return stdout


def ffmpeg_trim_audio_clip_directcopy(videofile: Path, stream_index: int, timestamp_start: int, timestamp_end: int, outpath: Path):
    videostream = ffmpeg.input(str(videofile))
    # outpath extension must be a container format (mp4, mkv) or the same type as the audio (.mp3, .eac3, .flac, etc)
    # todo: may need to use AVSfile to specify audio stream/direct demux
    videostream = ffmpeg.output(videostream[str(stream_index)], str(outpath), ss=timestamp_start/1000, to=timestamp_end/1000, c="copy")

    videostream = ffmpeg.overwrite_output(videostream)
    args = videostream.get_args()
    logging.debug(f"ffmpeg_trim_audio_clip: args: {args}")
    ffmpeg.run(videostream)


def ffmpeg_trim_audio_clip_atrim_encode(input_file: Path, stream_index: int, timestamp_start: int, timestamp_end: int,
                                        quality: Union[int, None], to_mono: bool, normalize_audio: bool,
                                        outpath: Path, format: str = None, capture_stdout: bool = False,
                                        silent: bool = True):
    r"""
    Take media file and export a trimmed audio file.
    :param stream_index: FFmpeg stream index. If input is not a container format, 0 should be used.
    :param capture_stdout: If true, returns stdout. Used in conjunction with outpath="pipe:" and format option.
    :param input_file: Path to video/audio file to clip from.
    :param timestamp_start: Start time in milliseconds.
    :param timestamp_end: End time in milliseconds.
    :param quality: If output extension is .mp3, this is the bitrate in kbps. Ignored otherwise.
    :param to_mono: If set, mixes all input channels to mono to save space
    :param normalize_audio: If set, attempts to normalize loudness of output audio. YMMV.
    :param outpath: Path to save to.
    :param format: Output format (e.g. mp3, flac, etc), required if extension of outpath is missing/not the intended
                    format. Required if outpath is "pipe:" since there is no output extension to infer from.
    :param silent: If set, suppresses stderr.
    :return: FFmpeg stdout data if capture_stdout is set
    """
    input_stream = ffmpeg.input(str(input_file))
    input_stream = input_stream[str(stream_index)]

    input_stream = input_stream.filter("atrim",
                                     start=timestamp_start/1000,
                                     end=timestamp_end/1000).filter("asetpts", "PTS-STARTPTS")

    if normalize_audio:
        input_stream = input_stream.filter("loudnorm", print_format="summary")

    kwargs = {}

    if outpath.suffix.lower() == ".mp3":
        if quality is not None:
            kwargs['audio_bitrate'] = f'{quality}k'
        else:
            kwargs['audio_bitrate'] = '320k'

    if to_mono:
        kwargs['ac'] = 1  # audio channels

    if format is not None:
        kwargs['format'] = format
    input_stream = ffmpeg.output(input_stream, str(outpath), **kwargs)


    input_stream = ffmpeg.overwrite_output(input_stream)
    args = input_stream.get_args()
    # logging.debug(f"ffmpeg_trim_audio_clip: args: {args}")
    try:
        stdout, stderr = ffmpeg.run(input_stream, capture_stdout=capture_stdout, capture_stderr=silent)
    except Exception as e:
        logging.error(
            f"ffmpeg couldn't trim audio clip. ffmpeg output: \n" + e.stderr.decode("utf-8"))
        raise e
    # return stdout


# buggy, dont use
def ffmpeg_trim_video_clip_directcopy(videofile: Path, timestamp_start: int, timestamp_end: int, quality, outpath: Path,
                                      quiet: bool=True):
    videostream = ffmpeg.input(str(videofile))

    videostream = ffmpeg.output(videostream, str(outpath), ss=timestamp_start/1000, to=timestamp_end/1000, c="copy")

    videostream = ffmpeg.overwrite_output(videostream)
    # args = videostream.get_args()
    # logging.debug(f"ffmpeg_trim_audio_clip: args: {args}")
    try:
        stdout, stderr = ffmpeg.run(videostream, capture_stderr=quiet)
    except ffmpeg._run.Error as e:
        print(e.stderr.decode("utf-8"))
        raise e


# todo: only first audio stream is saved, just want target audio, nothing else
#  https://video.stackexchange.com/a/21738
def ffmpeg_clip_video():
    pass
