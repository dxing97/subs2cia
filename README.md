# subs2cia

A subtitled media to condensed immersion audio converter.

Inspired by a script demoed [here](https://www.youtube.com/watch?v=QOLTeO-uCYU) that takes audio snippets played during 
subtitles and concatenates them together to make one large audio file that should contain just spoken audio. 
However, the quality of the snippets you use directly influences the quality of the final condensed audio, and subtitle 
timing information isn't taken into account when generating the final condensed audio, potentially resulting in 
stutters, repeated audio, and dialogue with little to no space between each sentence.

This script aims to fix these issues, as well as allow users the flexibility to choose how the audio is generated. 

## Installation
Clone the repository, and run 

```pip3 install .```

in the subs2cia root folder. A PyPi package is in the works. If you prefer, you can also run ``subs2cia/main.py`` directly.

## Usage
```
$ sub2cia -h
usage: main.py [-h] [-i <input files> [<input files> ...]] [-b] [-u]
               [-o <name>] [-d /path/to/directory] [-ae <audio extension>]
               [-m] [--overwrite-on-demux] [--keep-temporaries]
               [--no-overwrite-on-generation] [-p msecs] [-t msecs] [-r secs]
               [-s secs] [-tl ISO_code] [-v] [-vv] [--preset preset#] [-lp]

subs2cia: subtitle-based condensed audio generator

optional arguments:
  -h, --help            show this help message and exit
  -i <input files> [<input files> ...], --inputs <input files> [<input files> ...]
                        Paths to input files or a single path to a directory
                        of input files.
  -b, --batch           If set, attempts to split input files into groups, one
                        output file per group. Groups are determined by file
                        names. If two files share the same root name, such as
                        "video0.mkv" and "video0.srt", then they are part of
                        the same group.
  -u, --dry-run         If set, will analyze input files but won't demux or
                        generate any condensed files
  -o <name>, --output-name <name>
                        Output file name to save to, without the extension
                        (specify extension using -ae or -ve). By default, uses
                        the file name of the first input file with the input
                        extension removed and "condensed.{output extension}
                        added. Ignored if batch mode is enabled.
  -d /path/to/directory, --output-dir /path/to/directory
                        Output directory to save to. Default is the directory
                        the input files reside in.
  -ae <audio extension>, --audio-extension <audio extension>
                        Condensed audio extension to save as (without the
                        dot). Default is mp3, flac has been tested to work.
  -m, --gen-video       If set, generates condensed video along with condensed
                        audio. WARNING: VERY CPU INTENSIVE).
  --overwrite-on-demux  If set, will overwrite existing files when demuxing
                        temporary files.
  --keep-temporaries    If set, will not delete any demuxed temporary files.
  --no-overwrite-on-generation
                        If set, will not overwrite existing files when
                        generating condensed media.
  -p msecs, --padding msecs
                        Adds this many milliseconds of audio before and after
                        every subtitle. Overlaps with adjacent subtitles are
                        merged.
  -t msecs, --threshold msecs
                        If there's a subtitle that's threshold+padding msec
                        away, adds the intervening audio into the condensed
                        audio.
  -r secs, --partition secs
                        If set, attempts to partition the input audio
                        intoseperate blocks of this size seconds BEFORE
                        condensing. Partitions and splits respect subtitle
                        boundaries and will not split a single subtitle across
                        two output files. 0 partition length is ignored. For
                        example, if the partition size is 60 seconds and the
                        input media is 180 seconds long, then there will be
                        three output files. The first output file will contain
                        condensed media from the first 60 seconds of the
                        source material, the second output file will contain
                        the next 60 seconds of input media, and so on.
  -s secs, --split secs
                        If set, attempts to split the condensed audio
                        intoseperate blocks of this size AFTER condensing.
                        0split length is ignored. Partitions and splits
                        respect subtitle boundaries and will not split a
                        single subtitle across two output files. Done within a
                        partition. For example, say the split length is 60
                        seconds and the condensed audio length of a input
                        partition is 150 seconds. The output file will be
                        split into three files, the first two ~60 seconds long
                        and the last ~30 seconds long.
  -tl ISO_code, --target-language ISO_code
                        If set, attempts to use audio and subtitle files that
                        are in this language first. Should follow ISO language
                        codes.
  -v, --verbose         Verbose output if set.
  -vv, --debug          Verbose and debug output if set
  --preset preset#      If set, uses a given preset. User arguments will
                        override presets.
  -lp, --list-presets   Lists all available built-in presets.
```
## Examples
* Extract the first audio and subtitle track from ``video.mkv`` file and condense it
  * ``subs2cia -i video.mkv``
* Condense ``audio.mp3`` using ``subtitles.srt`` and save it to ``condensed.flac``
  * ``subs2cia -a "./audio.mp3" -s "./subtitles.srt" -o "./condensed.flac"
* Extract the second subtitle track and the first Japanese audio track from ``myvideo.mkv`` and save it to ``myvideo.mp3``
  * ``subs2cia -i video.mkv -o .mp3 -fs 1 -sl ja``
    



