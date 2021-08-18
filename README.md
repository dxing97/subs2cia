subs2cia - Extract subtitled dialogue from audiovisual media for use in language acquisition 


## Features
 * Generates _condensed_ media from subtitled media that only contains spoken dialogue (`subs2cia condense`)
     * No unnatural stutters: simultaneous and overlapping subtitles lines are merged for seamless listening
     * Automatically generate condensed subtitles, audio, and video from input sources (video must be enabled with `-m`)
     * Automagically chooses subtitle and audio tracks from a certain language or manually specify what inputs to condense
     (`-tl`, `-si`, `-ai`, `-ls`)
     * Automatically filter out subtitles that don't contain dialogue using built in heuristics or user-defined regexes (`-ni`, `-R`)
     * Ignore subtitled music found in openings/endings manually (`-I`) or by chapter (`-Ic`)  
     * Reinserts natural spacing between sentences that start and end close together (`-t`)
     * Subtitles not perfectly aligned? Pad subtitles with additional audio (`-p`)
     * Process multiple files with batch mode (`-b`)
 * **EXPERIMENTAL**: Export subtitles with audio and screenshots into your flashcard SRS of choice (`subs2cia srs`)

## Dependencies
* Python 3.6 or later
* ffmpeg
    * `ffmpeg` and `ffprobe` must be on your PATH (i.e. can execute `ffmpeg` and `ffprobe` from the command line)
* pip packages:
    * ffmpeg-python
    * pycountry
    * pysubs2
    * setuptools
    * tqdm
    * pandas
    * gevent
    * colorlog

## Installation Instructions
subs2cia is currently a command-line script. Usage requires interaction with a terminal interface.
### Windows
Install Python 3.6 or later. During or after the installation process, make sure you add Python to your PATH and also install pip.

Instructions for installing and adding ffmpeg to your path can be found [here](http://blog.gregzaal.com/how-to-install-ffmpeg-on-windows/).

The subs2cia installation process is generally the same as for Linux, although some commands may have different aliases
(e.g. instead of `pip3`, you may need to run `py -m pip` instead). Running
```
py -m pip install subs2cia
```
in command prompt should work. 

Some useful links on installing `pip` and python packages:
* https://pip.pypa.io/en/stable/installing/
* https://docs.python.org/3/installing/index.html

You may need to restart Command Prompt for path changes to take effect when installing `pip`.

### macOS:
Install Python and ffmpeg through the method of your choice, e.g. [Homebrew](https://brew.sh/). In Terminal, run:
```
# run this after installing Homebrew
brew install python ffmpeg
```
Homebrew should have also installed `pip` for you, which you can use to install subs2cia from PyPI:
```
pip3 install subs2cia
```
You should now be able to run the script:
```
subs2cia condense -h
```

### Linux
On systems with the `apt` package manager (Ubuntu, Debian, etc):
```
sudo apt install python3 python3-pip ffmpeg
pip3 install subs2cia
subs2cia condense -h
```

### Install from source
Download or clone the repository and navigate to it:
```
$ git clone "https://github.com/dxing97/subs2cia"
$ cd subs2cia
```
Use pip to install:
```
$ pip3 install .
```
On WSL, you may need to add `~/.local/bin` to your PATH first.

### Run Without Installing
If you prefer, you can also download the repository and run ``subs2cia/main.py`` directly.


## Condense Quickstart and Examples
```
subs2cia condense -i "My Video.mkv"
```
* Condense `My Video.mkv` into `My Video.condensed.mp3` and `My Video.condensed.srt` (if embedded subtitles are SRT formatted)

```
subs2cia condense -i video.mkv -p 150 -t 1000 -tl english
```
* Condense `video.mkv` into `video.condensed.mp3` and `video.condensed.srt`
* Prefer english subtitle/audio tracks if they exist. 
* Pad each subtitle's start/end time by 150ms
* Merge subtitles that start within 1300ms (1000 + 2x150) of each other (i.e. also add silences shorter than 1300ms)

```
subs2cia condense -i video.mkv "video subtitles.ass" -ae flac --no-gen-subtitle
```

* Condense `video.mkv` using `video subtitles.ass` into `video.condensed.flac`. 
    * Note: subs2cia will default to try using external subtitle/audio files first.
* Don't generate condensed subtitles.

```subs2cia condense -i audio.mp3 subtitles.ass```
* Condense `audio.mp3` and `subtitles.srt` into `audio.condensed.mp3` and `audio.condensed.srt`

```subs2cia condense -b -i *.mkv *.srt -I 0m 1m30s -I e2m +1m30s -tl ja -t 1500 -p 100``` 
* Condense all `.mkv` and `.srt` files in a directory organized according to Plex standards. 
* Ignore the first 1m30s of subtitles and the 1m30s of subtitles 2 minutes from the end. 
* Prefer Japanese audio/subtitles. 
* Set subtitle padding to 100ms and threshold to merge subtitles to 1700ms:

For a more complete usage guide, run `subs2cia condense -h` or take a look at [USAGE](USAGE.md).

## SRS Export Quickstart and Examples
Most options are shared with `condense`. See `subs2cia srs -h` for a full list of options. 
### Example commands
```subs2cia srs -i video.mkv```
* extract the first audio and first subtitle track in `video.mkv`  and generate `video.tsv` and a lotta `.mp3` and `.jpg` files

```
subs2cia srs -b -i *.mkv *.ja.srt -d srs_export -p 100 -N 
```
* enable batch mode and use all `.mkv` and japanese `.srt` files in the current directory
* save output files to a directory called srs_export
* pad timings by 100ms
* normalize audio to be roughly the same volume
Note that each input file group will have its own `.tsv` output

### Usage notes

The same overall idea is the same: give subs2cia an audio and subtitle source. Instead of generating a set of 
condensed outputs, a .tsv (tab-seperated values) file is generated
along with audio clips and screenshots (if a video source is given). 

Each column of the .tsv file represents the following:
1. Subtitle text
2. Time range of subtitle in milliseconds: `start-end`
3. Audio:`[sound:media_start-end.mp3]`
4. Screenshot: `<img src='media_start-end.jpg'>`
   * Screenshot resolution is the video file's resolution
5. Video clip (currently disabled)
6. Comma-seperated list of input files used

Note that in batch mode, multiple .tsv files are generated, one for each input group. 

Since there could be hundreds output files, it's highly recommended to specify an output
directory with `-d` in order to avoid cluttering your filesystem. 

### Anki Import Instructions
1. In the main screen, click on `File->Import...`
2. Select the .tsv file you would like to import
3. In the Import dialog box:
   1. Choose the note type and deck you'd like to import to
   2. Make sure fields are separated by tabs
   3. Make sure `Allow HTML in fields` is checked
   4. Adjust the 6 fields (detailed above) to fit your note type
   5. Click `Import`
4. Verify audio and screenshots were automagically imported as well. If audio and/or screenshots are missing, they may 
    need to be manually moved into your collections folder. If the .tsv file isn't in the same directory as the generated
    audio clips and images, Anki won't copy them for you. 
    
## Limitations and Assumptions
* Won't work on bitmap subtitles (e.g. PGS subtitles), only text-based supports subtitle formats supported by ffmpeg and pysubs2 
  encoded in UTF-8 will work
* Subtitles must be properly aligned to audio. No attempt is made by subs2cia to align subtitles. 

# subzipper
Renames subtitle files to match a reference (video) file to conform with Plex-style naming standards, 
optionally adding language information to the suffix. Intended for use with shell wildcards.

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
Map all subtitles to all video files,
```
subzipper -s *.ass -r *.mkv -l ja
```
