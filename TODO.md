## The Todo List

### Tier 1
 - [ ] demuxing-only options, including for subs2srs
 - [ ] make file extensions more flexible (for demuxing and outputs)
    - [ ] for mp3, add user-settable bitrate/quality options (right now if it outputs to mp3, defaults to 320k CBR)
 - [ ] clean up dry-run, verbose options 
    - [ ] clean up all the print statements
 - [X] cleanup code for v0.1 release
 - [ ] option to clean up intermediate files that get demuxed from any video files

### Tier 2
- [X] limited batching support for ``-i``
 - [ ] add more documentation, quick start guide
    - [ ] document presets
 - [X] add requirements.txt, more prep for packaging for v0.2 release
 - [ ] more testing

### Tier 3
 - [ ] full batching support (directory of similarly named sources to process)
 - [ ] make a C parser for PGS subtitle files and extract timings from there (the only python library on github doesn't have a license)
 - [ ] performance tuning