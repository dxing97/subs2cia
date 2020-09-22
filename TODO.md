## The Todo List
### v0.3 point release goals
 - [X] Export subtitles with condensed timings for muxing into condensed video
     - [X] ~~Option to export raw condensed subtitle file~~ (done by default, no option added)
     - [X] Option to ignore certain ranges for OP/ED removal
 - [ ] clean up dry-run 
 - [ ] clean up debug, verbose logging (doesn't need to spit out that much input data)
 - [ ] Interactive [Y/n] mode for error handing and action confirmation
 - [ ] Simple CLI to GUI wrapper
    - .app and .exe releases would be nice
 - [X] PyPI package

### Bucket list 
 - [ ] Multiprocessor acceleration
 - [ ] (Bug) If file encoding is not utf-8, pysubs2 may error out/produce garbage output
 - [ ] (Windows) glob inputs 
 - [ ] Handle directories as inputs
 - [ ] make file extensions more flexible by making it more strict (for demuxing? and outputs)
    - [ ] handful of output formats to start with: flac, mp3 
    - [ ] for mp3, add user-settable bitrate/quality options 
        (right now if it outputs to mp3, defaults to 320k CBR)
    - [ ] add mono-channel output option
    - [ ] new cli interface for all this (replace -ae)
 - [ ] add more/better documentation, quick start guide
 - [ ] ~~Skip intermediate files be default, go directly from video to condensed audio/video~~
    - [ ] ~~try going to intermediate formats if direct method fails (and add a CLI switch for it as well)~~
 - [ ] output indivdual audio snippets instead of/in addition to one large condensed audio file (wait, where have I seen this before...)
 
### The neverending future
 - [ ] more testing
    - [ ] more Windows testing
 - [ ] automated test suite
 - [ ] bitmapped subtitles and OCR recognition