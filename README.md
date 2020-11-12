subs2cia - Extract subtitled dialogue from audiovisual media for use in language acquisition 


## Features
 * Generates _condensed_ media from subtitled media that only contains spoken dialogue (`subs2cia condense`)
     * No unnatural stutters: simultaneous subtitles lines are merged for seamless listening
     * Automatically generate condensed subtitle, audio, and video (video must be enabled with `-m`)
     * Automagically choose input sources from a certain language or manually specify what inputs to condense
     (`-tl`, `-si`, `-ai`, `-ls`)
     * Automatically filter out subtitles that don't contain dialogue using built in heuristics or user-defined regexes (`-ni`, `-R`)
     * Ignore subtitled music found in openings/endings manually (`-I`) or by chapter (`-Ic`)  
     * Reinserts natural spacing between sentences that start and end close together (`-t`)
     * Pads subtitles with additional audio (`-p`)
     * Process multiple files with batch mode (`-b`)
 * Export subtitles with screenshots into your SRS of choice (`subs2cia srs`)

## Installation
#### Dependencies
* Python 3.6 or later
* FFmpeg binaries (ffmpeg and ffprobe) must be on your PATH (i.e. can execute `ffmpeg` from the command line)

### (Recommended) pip install:
```
pip3 install subs2cia
subs2cia condense -h
```

### Pip install from source (macOS, Linux)
Git clone or otherwise download the repository and navigate to it:
```
$ git clone "https://github.com/dxing97/subs2cia"
$ cd subs2cia
```

Use pip to install:
```
$ pip3 install .
```
On WSL, you may need to add `~/.local/bin` to your PATH first.

### Run as script
If you prefer, you can also run ``subs2cia/main.py`` directly.

### Windows
Instructions for installing and adding ffmpeg to your path can be found [here](http://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/).
The subs2cia installation process is generally the same as for Linux, although some commands may have different names 
(e.g. instead of `pip3`, you may need to run `py -m pip` instead).
Some useful links on installing `pip` and python packages:
* https://pip.pypa.io/en/stable/installing/
* https://docs.python.org/3/installing/index.html

You may need to restart command prompt for path changes to take effect when installing `pip`. 

## Condense Quickstart Usage
Condense `video.mkv` into `video.condensed.mp3` and `video.condensed.srt` (if embedded subtitles are SRT):
* ```subs2cia condense -i video.mkv```

Condense `video.mkv`, preferring english subtitle/audio tracks if they exist. 
Additionally, pad each subtitle's start/end time by 150ms, and merge subtitles that start within
1300ms (1000 + 2x150) of each other (i.e. also add silences shorter than 1300ms):
 * ```subs2cia condense -i video.mkv -p 150 -t 1000 -tl english```

Condense `video.mkv` using `video_subtitles.ass` into `video.condensed.flac` and `video.condensed.ass`
* ```subs2cia condense -i video.mkv video_subtitles.ass -ae flac```

Condense `audio.mp3` and `subtitles.srt` into `audio.condensed.mp3` and `audio.condensed.srt`
* ```subs2cia condense -i audio.mp3 subtitles.ass```

[Linux/macOS] Condense all `.mkv` and `.srt` files in a directory organized according to Plex standards. 
Ignore the first 1m30s of subtitles and the 1m30s of subtitles 2 minutes from the end. 
Prefer japanese audio/subtitles. Set subtitle padding to 100ms and 
threshold to merge subtitles to 1500ms:
* ```subs2cia condense -b -i *.mkv *.srt -I 0m 1m30s -I e2m +1m30s -tl ja -t 1500 -p 100``` 

For a full usage guide, run `subs2cia condense -h` or take a look at [USAGE](USAGE.md).

## SRS Export Quickstart
```subs2cia srs -i video.mkv```

## Limitations and Assumptions
* Won't work on bitmap subtitles (e.g. PGS), only supports subtitle formats supported by ffmpeg and pysubs2
* Subtitles must be properly aligned to audio. 

# subzipper
Renames subtitle files to match a reference (video) file to conform with Plex-style naming standards, 
optionally adding language information. Intended for use with shell wildcards.

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


