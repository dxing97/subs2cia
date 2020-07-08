from subs2cia_v2.argparser import get_args
from subs2cia_v2.sources import AVSFile, group_files
from subs2cia_v2.condense import Condensed
import logging



def start():
    args = get_args()
    args = vars(args)

    if args['verbose']:
        logging.basicConfig(level=logging.INFO)
    if args['debug']:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug(f"Start arguments: {args}")

    sources = [AVSFile(file) for file in args['infiles']]

    for s in sources:
        s.probe()
        s.get_type()

    groups = list(group_files(sources))
    # condensed_files = []
    # for g in groups:
    #     condensed_files.append(Condensed(g))
    condensed_files = [Condensed(g) for g in groups]

    for c in condensed_files:
        c.get_and_partition_streams()
        c.initialize_pickers()
        c.choose_streams()









    # bin_dict = sources.bin_by_type()

    # at this point we do Plex-style matching of input files
    # for every input file, we strip all suffixes off of filenames (like .mkv, .ja.srt, etc)
    # and see if there are any other files with the same base name
    # if the base names are the same, they're treated as a single file name

if __name__ == '__main__':
    start()
