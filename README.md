# subs2cia

A subtitled media to condensed immersion audio converter.

Inspired by a script demoed [here](https://www.youtube.com/watch?v=QOLTeO-uCYU) that takes audio snippets played during 
subtitles and concatenates them together to make one large audio file that should contain just spoken audio. 
However, the quality of the snippets you use directly influences the quality of the final condensed audio, and subtitle 
timing information isn't taken into account when generating the final condensed audio, potentially resulting in 
stutters, repeated audio, and dialogue with little to no space between each sentence.

This script aims to fix these issues, as well as allow users the flexibility to choose how the audio is generated. 

## Usage
```
$ main.py -h
usage: main.py [-h] [-a path/to/audio] [-s path/to/subtitles]
               [-i path/to/video] [-o path/to/outputfile.flac] [-d] [-v]
               [-t msecs] [-p msecs] [-P secs] [-S secs]
               [--use-absolute-numbering] [-al ISO_code] [-sl ISO_code]
               [-fs stream#] [-fa stream#] [-N] [--preset preset#] [-lp]

subs2cia: subtitle-based condensed audio generator

optional arguments:
  -h, --help            show this help message and exit
  -a path/to/audio, --audio path/to/audio
                        Path to audio file. Supported types: any type ffmpeg
                        supports.
  -s path/to/subtitles, --subtitles path/to/subtitles
                        Path to subtitle file. Supported types: .ass, .srt.
                        Unsupported types: .sup, PGS
  -i path/to/video, --video path/to/video
                        Path to video file containing audio and subtitles that
                        can be demuxed. Tracks from video sources are ignored
                        if -a or -s is present. . Supported containers: any
                        type ffmpeg supports.
  -o path/to/outputfile.flac, --output path/to/outputfile.flac
                        Path to output condensed audio to (audio codec assumed
                        from extension). Default is to use the audio or video
                        file name and extension (usually flac). You can also
                        specify just the output file type by using an
                        extension, e.g. for .mp3, use -o ".mp3"
  -d, --dry-run         If nonzero, reads inputs, processes them, but does not
                        demux or write output(s) to disk
  -v, --verbose         Verbose output if set.
  -t msecs, --threshold msecs
                        maximum distance between subtitles before splitting
                        the audio snippet
  -p msecs, --padding msecs
                        default padding added to both ends of a subtitle
                        interval
  -P secs, --partition secs
                        If set, attempts to partition the input audio into
                        seperate blocks of this size before condensing. 0
                        partition length is ignored.
  -S secs, --split secs
                        If set, attempts to split the condensed audio into
                        seperate parts that do not exceed this size. 0 split
                        size is ignored.
  --use-absolute-numbering
                        If set, names partitions/splits as "pt1, pt2, ...",
                        instead of "p1s1, p1s2, p2s1, ..."
  -al ISO_code, --audio-language ISO_code
                        If set, and given a video file, attempts to use audio
                        from the video that is in this language. Expects ISO
                        language code.
  -sl ISO_code, --subtitle-language ISO_code
                        If set, and given a video file, attempts to use
                        subtitles from the video that is in this language.
                        Expects ISO language code.
  -fs stream#, --force-subtitle-stream stream#
                        If set, and given a video file, attempts to use the
                        stream# subtitle stream from the video file for
                        subtitles. Default is to use the first subtitle track.
                        Ignored if -s is present. 1-indexed.
  -fa stream#, --force-audio-stream stream#
                        If set, and given a video file, attempts to use the
                        stream# audio stream from the video file for audio.
                        Default is to use the first audio track. Ignored if -a
                        is present. 1-indexed
  -N, --no-retry        If set, makes no attempt to retry different
                        audio/subtitle tracks if anything is wrong with an
                        audio/subtitle file.
  --preset preset#      If set, uses a given preset. Will override user
                        arguments.
  -lp, --list-presets   If set, uses a given preset. Will override user
                        arguments.
```
## Examples
``subs2cia -i video.mkv``


## Todo

### Tier 1
 - [ ] demuxing-only options, including for subs2srs
 - [ ] make file extensions more flexible (for demuxing and outputs)
    - [ ] for mp3, add user-settable bitrate/quality options (right now if it outputs to mp3, defaults to 320k CBR)
 - [ ] clean up dry-run, verbose options 
 - [ ] cleanup code for v0.1 release
 - [ ] option to clean up intermediate files that get demuxed from any video files

### Tier 2
- [ ] limited batching support for ``-i``
 - [ ] add more documentation, quick start guide
    - [ ] document presets
 - [ ] add requirements.txt, more prep for packaging for v0.2 release
 - [ ] more testing

### Tier 3
 - [ ] full batching support (directory of similarly named sources to process)
 - [ ] make a C parser for PGS subtitle files and extract timings from there (the only python library on github doesn't have a license)
 - [ ] performance tuning
