from subs2cia.sources import *
from pathlib import Path
from pprint import pprint

# Step 1: strip extension,
#   strip 'forced' if present,
#   strip language code if present

def main():
    input_files = [
        'testfile.mkv',
        'video.s01e01.ja.srt',
        'testfile.en.srt',
        'video.s01e01.mkv',
        'test.mkv',
        'video02.ja.ass',
        'test.en.forced.srt',
        'video02.mp4',
        'video02.forced.srt',
        'video.condensed.mp3',
        'video.condensed.ja.srt',
        'nullfile'
    ]
    # for f in input_files:
    #     Path(f).touch(exist_ok=True)
    input_files = [Path(f) for f in input_files]
    pprint(input_files)

    pprint([strip_extensions(f) for f in input_files])

    all_groups = []
    while(len(input_files) > 0):
        group = [input_files.pop(0)]
        to_remove = []
        for f in input_files:
            if strip_extensions(f) == strip_extensions(group[0]):
                group.append(f)
                to_remove.append(f)
        for f in to_remove:
            input_files.remove(f)
        all_groups.append(group)

    pprint(all_groups)
if __name__ == '__main__':
    main()