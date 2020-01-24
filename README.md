# subs2cia

A subtitle and audio track to condensed immersion audio converter.

Inspired by a script that takes subs2srs audio snippets and concatenates them together to achieve a similar effect. 
However, I didn't like the quality of the output files, so I decided to make a custom cross-platform tool.

## Todo

### Tier 1
 - [ ] demuxing-only options, including for subs2srs
 - [ ] include some presets for Japanese
 - [ ] cleanup code for v0.1 release
 - [ ] make file extensions more flexible (for demuxing and outputs)
 - [ ] reenable dry-run, verbose options

### Tier 2
 - [ ] update output file naming to be a little more flexible
 - [ ] add options/customization for dialogue filter (regex?)
 - [ ] add more documentation, quick start guide
 - [ ] add requirements.txt, more prep for packaging
 - [ ] batching support (directory of similarly named sources to process)
 - [ ] more testing

### Tier 3
 - [ ] make a C parser for PGS subtitle files and extract timings from there (the only python library on github doesn't have a license)
 - [ ] performance tuning
