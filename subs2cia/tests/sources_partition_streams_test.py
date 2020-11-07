import argparse
import logging
from pathlib import Path
from subs2cia.sources import get_and_partition_streams, AVSFile, Stream
from pprint import pprint


def get_args():
    parser = argparse.ArgumentParser(description=f'frame capture manual testing')

    parser.add_argument('-V', '--video', metavar='<input file>', dest='infiles', default=None, required=True,
                        nargs='+', type=str, help='Input files to probe')

    parser.add_argument('-v', '--verbose', action='store_true', dest='verbose', default=False,
                        help='Verbose output if set.')

    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = get_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    sources = [AVSFile(Path(source)) for source in args.infiles]
    for s in sources:
        s.probe()  # run ffprobe
        s.get_type()  # determine filetype from ffprobe results (video, audio, subtitle, unknown)
    pprint(sources)

    partitioned_streams = get_and_partition_streams(sources)  # dict of lists of Streams
    pprint(partitioned_streams)

    for k in ['subtitle', 'audio', 'video']:
        print(f"Available {k} streams:")
        for idx, stream in enumerate(partitioned_streams[k]):
            desc_str = ''
            if "codec_name" in stream.stream_info:
                desc_str = desc_str + "codec: " + stream.stream_info['codec_name'] + ", "
            if "tags" in stream.stream_info:
                tags = stream.stream_info['tags']
                if "language" in tags:
                    desc_str = desc_str + "lang_code: " + tags['language'] + ", "
                if "title" in tags:
                    desc_str = desc_str + "title: " + tags['title'] + ", "
            if desc_str == '':
                desc_str = f"Stream {idx: 3}: no information found"
            else:
                desc_str = f"Stream {idx: 3}: {desc_str}"
            print(desc_str)
        print("")
