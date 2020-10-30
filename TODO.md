## The Todo List
### v0.3 point release goals
 - [X] Export subtitles with condensed timings for muxing into condensed video
     - [X] ~~Option to export raw condensed subtitle file~~ (done by default, no option added)
     - [X] Option to ignore certain ranges for OP/ED removal
 - [X] PyPI package
 - [ ] output indivdual audio snippets instead of/in addition to one large condensed audio file (where have I seen this before...)
     - [ ] Clip audio (with options) 
     - [ ] Snapshot support (with options)
     - [ ] TSV-formatted output index containing subtitle text, output file names
 - [X] make file extensions more flexible by making it more strict (for demuxing? and outputs)
    - [ ] ~~handful of output formats to start with: flac, mp3~~
    - [X] for mp3, add user-settable bitrate/quality options 
        (right now if it outputs to mp3, defaults to 320k CBR)
    - [X] add mono-channel output option
    - [ ] ~~new cli interface for all this (replace -ae)~~
 - [ ] make ignore-range more powerful (subs2cia#6)
    - [ ] specify negative ranges (relative to end of audio)
    - [ ] specify intervals relative to an absolute timestamp
    
### Bucket list 
 - [ ] Multiprocessor acceleration where sensible
 - [ ] clean up dry-run 
 - [ ] clean up ~~debug, verbose~~ logging (doesn't need to spit out that much input data)
 - [ ] Interactive [Y/n] mode for error handing and action confirmation
 - [ ] Simple CLI to GUI wrapper
    - .app and .exe releases would be nice
 - [ ] (Bug) If file encoding is not utf-8, pysubs2 may error out/produce garbage output
 - [ ] (Windows) glob inputs 
 - [ ] Handle directories as inputs
 - [ ] add more/better documentation, quick start guide
 - [ ] ~~Skip intermediate files be default, go directly from video to condensed audio/video~~
    - [ ] ~~try going to intermediate formats if direct method fails (and add a CLI switch for it as well)~~

 
### The neverending future
 - [ ] more testing
    - [ ] more Windows testing
 - [ ] automated test suite
 - [ ] bitmapped subtitles and OCR recognition