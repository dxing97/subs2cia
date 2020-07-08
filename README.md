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

in the subs2cia root folder. A PyPi package is in the works. If you prefer, you can also run ``main.py`` directly.

## Usage
```
$ sub2cia -h
subs2cia: subtitle-based condensed audio generator

optional arguments:
  -h, --help            show this help message and exit
  -a path/to/audio, --audio path/to/audio
                        Path to audio file. Supported types: any type ffmpeg
                        supports.
  -s path/to/subtitles, --subtitles path/to/subtitles
                        Path to subtitle file. Supported types: .ass, .srt.
                        Unsupported types: .sup, PGS
  -i path/to/video [path/to/video ...], --video path/to/video [path/to/video ...]
                        Path to video file containing audio and subtitles that
                        can be demuxed. Tracks from video sources are ignored
                        if -a or -s is present. If multiple video files are
                        specified, it will apply all options to each video
                        file.Supported containers: any type ffmpeg supports.
  -o path/to/outputfile.flac, --output path/to/outputfile.flac
                        Path to output condensed audio to (audio codec assumed
                        from extension). Default is to use the audio or video
                        file name and extension (usually flac). You can also
                        specify just the output file type by using an
                        extension, e.g. for .mp3, use -o ".mp3"
  -d, --dry-run         If nonzero, reads inputs, processes them, but does not
                        demux or write output(s) to disk
  -v, --verbose         Print verbose output if set.
  -vv, --debug          Print debug output if set.
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
* Extract the first audio and subtitle track from ``video.mkv`` file and condense it
  * ``subs2cia -i video.mkv``
* Condense ``audio.mp3`` using ``subtitles.srt`` and save it to ``condensed.flac``
  * ``subs2cia -a "./audio.mp3" -s "./subtitles.srt" -o "./condensed.flac"
* Extract the second subtitle track and the first Japanese audio track from ``myvideo.mkv`` and save it to ``myvideo.mp3``
  * ``subs2cia -i video.mkv -o .mp3 -fs 1 -sl ja``
    



