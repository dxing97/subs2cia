# subs2cia

Extract subtitled dialogue from videos for use in language learning.


## Features

- Generates _condensed_ media from subtitled media that only contains spoken dialogue (`subs2cia condense`)
    - No unnatural stutters: simultaneous and overlapping subtitles lines are merged for seamless listening
    - Automatically generate condensed subtitles, audio, and video from input sources (video must be enabled with `-m`)
    - Automatically chooses subtitle and audio tracks from a certain language or manually specify what inputs to condense (`-tl`, `-si`, `-ai`, `-ls`)
    - Automatically filter out subtitles that don't contain dialogue using built in heuristics or user-defined regexes (`-ni`, `-R`)
    - Ignore subtitled music found in openings/endings manually (`-I`) or by chapter (`-Ic`)  
    - Reinserts natural spacing between sentences that start and end close together (`-t`)
    - Subtitles not perfectly aligned? Pad subtitles with additional audio (`-p`)
    - Process multiple files with batch mode (`-b`)
- **EXPERIMENTAL**: Export subtitles with audio and screenshots into your flashcard SRS of choice (`subs2cia srs`)


## Installation

Make sure you have installed [ffmpeg](https://ffmpeg.org/). Mac users may install it using [Homebrew](https://brew.sh/).

Then, you may install or run `subs2cia` from source as though it were any other Python package.

Running from source:

```
# Clone this repository and run from the root of this directory
python3 -m subs2cia
```

Installing from source:

```
# Clone this repository and run from the root of this directory
python3 -m pip install -e .
```

See these links for help with using pip or installing Python packages:

- https://pip.pypa.io/en/stable/installing/


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

The Anki manual has two pages that may be relevant for manually working with media files:

- Info about how to find your media folder - [File Locations (docs.ankiweb.net)](https://docs.ankiweb.net/files.html#file-locations)
- Info about media files - [Media (docs.ankiweb.net)](https://docs.ankiweb.net/media.html)

## Limitations and Assumptions

- Won't work on bitmap subtitles (e.g. PGS subtitles), only text-based supports subtitle formats supported by ffmpeg and pysubs2 encoded in UTF-8 will work
- Subtitles must be properly aligned to audio. No attempt is made by subs2cia to align subtitles. 


# subzipper

Renames subtitle files to match a reference (video) file to conform with Plex-style naming standards, optionally adding language information to the suffix. Intended for use with shell wildcards.

## Usage

Use `subzipper -h` to view a list of arguments and features.

## Examples

Rename ``episode01.ass`` to ``MyShow_S01E01.ja.ass`` and ``episode02.ass`` to ``MyShow_S01E02.ja.ass``, 

```
subzipper -s "episode01.ass" "episode02.ass" -r "MyShow_S01E01.mkv" "MyShow_S01E02.mkv" -l ja
```

Map all subtitles to all video files,

```
subzipper -s *.ass -r *.mkv -l ja
```


# Future Work

- [ ] (Bug) If file encoding is not utf-8, pysubs2 may error out/produce garbage output
- [ ] Automated test suite
- [ ] Multiprocessor acceleration where sensible
- [ ] clean up dry-run
- [ ] Handle directories as inputs
- [ ] Add more/better documentation
- [ ] Option to point to custom FFmpeg binary not on PATH
- [ ] Bitmapped subtitles and OCR recognition

