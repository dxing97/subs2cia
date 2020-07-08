import ffmpeg
import logging
from pathlib import Path


# given a stream in the input file, demux the stream and save it into the outfile with some type
def ffmpeg_demux(infile: Path, stream_idx: int, outfile: Path):
    # output format is specified via extention on outfile
    video = ffmpeg.input(infile)
    stream = video[str(stream_idx)]  # don't need 0
    stream = ffmpeg.output(stream, outfile)
    stream = ffmpeg.overwrite_output(stream)  # todo: add option to not force overwrite
    ffmpeg.run(stream, quiet=logging.getLogger().getEffectiveLevel() < logging.WARNING)  # verbose only
    return outfile
