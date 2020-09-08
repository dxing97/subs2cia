# subs2cia

A subtitled media to condensed immersion media converter.

Inspired by a script demoed [here](https://www.youtube.com/watch?v=QOLTeO-uCYU) that takes audio snippets played during 
subtitles and concatenates them together to make one large audio file that should contain just spoken audio. 
However, the quality of the snippets you use directly influences the quality of the final condensed audio, and subtitle 
timing information isn't taken into account when generating the final condensed audio, potentially resulting in 
stutters, repeated audio, and dialogue with unnatural spacing between each sentence.

This script aims to fix these issues, as well as allow users the flexibility to choose how the audio is generated. 

Currently only tested on *nix operating systems. 

## Features
 * Removes overlaps between subtitle timings
 * Generate condensed video
 * Automagically prefer desired language audio and subtitles from multiple inputs
 * Filter out subtitles that don't contain text (WIP) 
 * Re-adds natural spacing between sentences that start and end close together (disabled by default)
 * Pads subtitles with audio (disabled by default)
 * Process multiple files at once in batch mode (disabled by default)
  

## Installation
Currently actively tested on Ubuntu 20.04 LTS and macOS Catalina. Windows support is limited, but has been tested to work.

### Dependencies
Make sure you have Python 3.6 or later installed, along with pip.
Built and tested on Python 3. Python package dependencies are listed in [requirements.txt](requirements.txt).

You'll also need to install ffmpeg and make sure it's on your PATH (i.e. can execute `ffmpeg` on the command line).

### Linux, macOS CLI 
Git clone or otherwise download the repository and navigate to it:
```
$ git clone "https://github.com/dxing97/subs2cia"
$ cd subs2cia
```

Tell pip to install the dependencies and then subs2cia itself:
```
$ pip3 install -r requirements.txt
$ pip3 install .
```
On WSL, you may need to add `~/.local/bin` to your PATH first.

You should then be able to run subs2cia:
```
$ subs2cia -h
```
A PyPi package is coming Eventually.
If you prefer, you can also run ``subs2cia/main.py`` directly.

### Windows CLI
Instructions for installing and adding ffmpeg to your path can be found [here](http://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/).
The subs2cia installation process is the same as for Linux, just run the commands in command prompt.

## Usage
```
$ subs2cia -h
usage: main.py [-h] [-i <input files> [<input files> ...]] [-b] [-u]
               [-o <name>] [-d /path/to/directory] [-ae <audio extension>]
               [-m] [--overwrite-on-demux] [--keep-temporaries]
               [--no-overwrite-on-generation] [-ni] [-p msecs] [-t msecs]
               [-r secs] [-s secs] [-c <ratio>] [-tl ISO_code] [-a] [-v] [-vv]
               [--preset preset#] [-lp]

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
  -ni, --ignore-none    If set, will not try to remove non-dialogue lines from
                        the subtitle.
  -p msecs, --padding msecs
                        Adds this many milliseconds of audio before and after
                        every subtitle. Overlaps with adjacent subtitles are
                        merged.
  -t msecs, --threshold msecs
                        If there's a subtitle that's threshold+padding msec
                        away, adds the intervening audio into the condensed
                        audio.
  -r secs, --partition secs
                        If set, attempts to partition the input audio into
                        seperate blocks of this size seconds BEFORE
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
                        If set, attempts to split the condensed audio into
                        seperate blocks of this size AFTER condensing. 0 split
                        length is ignored. Partitions and splits respect
                        subtitle boundaries and will not split a single
                        subtitle across two output files. Done within a
                        partition. For example, say the split length is 60
                        seconds and the condensed audio length of a input
                        partition is 150 seconds. The output file will be
                        split into three files, the first two ~60 seconds long
                        and the last ~30 seconds long.
  -c <ratio>, --minimum-out-length <ratio>
                        Will only generate from subtitle files that are this
                        fraction long of the selected audio file. Default is
                        0.3, meaning the output condensed file must be at
                        least 30{'option_strings': ['-c', '--minimum-out-
                        length'], 'dest': 'minimum_compression_ratio',
                        'nargs': None, 'const': None, 'default': 0.3, 'type':
                        'float', 'choices': None, 'required': False, 'help':
                        "Will only generate from subtitle files that are this
                        fraction long of the selected audio file. Default is
                        0.3, meaning the output condensed file must be at
                        least 30% as long as the chosen audio stream. If the
                        output doesn't reach this minimum, then a different
                        subtitle file will be chosen, if available. Used to
                        ignore subtitles that contain onlysigns and songs.",
                        'metavar': '<ratio>', 'container':
                        <argparse._ArgumentGroup object at 0x7fc7451f9a90>,
                        'prog': 'main.py'}s long as the chosen audio stream.
                        If the output doesn't reach this minimum, then a
                        different subtitle file will be chosen, if available.
                        Used to ignore subtitles that contain onlysigns and
                        songs.
  -tl ISO_code, --target-language ISO_code
                        If set, attempts to use audio and subtitle files that
                        are in this language first. Should follow ISO language
                        codes.
  -a, --absolute-paths  Prints absolute paths from the root directory instead
                        of given paths.
  -v, --verbose         Verbose output if set.
  -vv, --debug          Verbose and debug output if set
  --preset preset#      If set, uses a given preset. User arguments will
                        override presets.
  -lp, --list-presets   Lists all available built-in presets.
```
## Examples
* Extract the first audio and subtitle track from ``video.mkv`` file and generate the condensed file ``video.condensed.mp3``
  * ``subs2cia -i video.mkv``
* Condense ``audio.mp3`` using ``subtitles.srt`` and save it to ``audio.condensed.flac``
  * ``subs2cia -i "./audio.mp3" "./subtitles.srt" -ae flac``
* Condense `file1.mkv`, `file2.mkv`, `file3.mkv` in batch mode. Automatically pick English subtitle/audio tracks if 
present. Don't delete extracted subtitle and audio files. Pad subtitles with 300 ms on each side and group subtitles within 
1500 ms of each other together to keep short silences. 
  * ``subs2cia -i file1.mkv file2.mkv file3.mkv --batch --tl en --keep-temporaries -p 300 -t 1500``
  * If batch mode is not specified, then subs2cia assumes that all three input files are meant to map to *one* output file.
  * On Linux and macOS systems, can use shell wildcard to grab all files that end in .mkv:
    * ``subs2cia -i *.mkv --batch --tl en --keep-temporaries -p 300 -t 1500``

## Known Issues
* [Windows] On input files that result in hundreds of audio snippets to condense, the arguments passed to ffmpeg can exceed Windows cmd.exe argument limits. 

# subzipper
Renames subtitle files to match a reference (video) file to conform with Plex-style naming standards, 
optionally adding language information. 

## Usage
```
$ subzipper -h
usage: subzipper.py [-h] -s <input files> [<input files> ...] -r <input files>
                    [<input files> ...] [-l ISO_LANG_CODE] [-ns] [-d] [-v]

SubZipper: Map video files to subtitle files

optional arguments:
  -h, --help            show this help message and exit
  -s <input files> [<input files> ...], --subtitle <input files> [<input files> ...]
                        List of subtitle files. Number of subtitle files
                        should equal number of reference files.
  -r <input files> [<input files> ...], --reference <input files> [<input files> ...]
                        List of reference files, typically video files. Number
                        of subtitle files should equal number of reference
                        files.
  -l ISO_LANG_CODE, --language ISO_LANG_CODE
                        Language code to append to end of subtitle file.
                        Optional. If set, will be checked for validity.
  -ns, --no-sort        If set, will not sort input files alphabetically.
  -d, --dry-run         If set, will print out mappings but will not write any
                        changes to disk.
  -v, --verbose         Verbose output if set.
```

## Examples
Rename ``episode01.ass`` to ``MyShow_S01E01.ja.ass`` and ``episode02.ass`` to ``MyShow_S01E02.ja.ass``, 
```
subzipper -s "episode01.ass" "episode02.ass" -r "MyShow_S01E01.mkv" "MyShow_S01E02.mkv" -l ja
```


