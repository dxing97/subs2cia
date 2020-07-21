## The Todo List

### Tier 1
 - [X] simple demuxing tools
 - [ ] subtitle retiming option
 - [ ] make file extensions more flexible (for demuxing and outputs)
    - [ ] for mp3, add user-settable bitrate/quality options 
    (right now if it outputs to mp3, defaults to 320k CBR)
 - [X] clean up dry-run 
 - [ ] verbose options 
    - [ ] clean up all the print statements
 - [X] add debug mode (moar verbose)
 - [X] cleanup code for v0.1 release
 - [X] option to clean up intermediate files that get demuxed from any video files

### Tier 2
 - [X] limited batching support for ``-i``
 - [X] override presets at runtime
 - [ ] add more documentation, quick start guide
    - [ ] document presets
 - [X] add requirements.txt
 - [ ] more prep for packaging for v0.2 release
 - [ ] more testing
 - [ ] Skip intermediate files, go directly from video to condensed audio/video
 - [ ] Condensed video

### Tier 3
 - [ ] flexible batching support (directory of similarly named sources to process)
 - [ ] make a C parser for PGS subtitle files and extract timings from there 
 (the only python library on github doesn't have a license)
 - [ ] performance tuning