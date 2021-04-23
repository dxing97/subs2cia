# Changelog

## [Unreleased]
### Added
 - Regex replace/filter: 
    - remove parts of subtitles with `-RR`
    - don't keep changes with `-RRnk`
    

## [0.3.3] - 2021-04-11
### Added
 - Option to disable outputting condensed subtitles (`no-gen-subtitle`)
 - Add explicit support for globbed inputs (esp. useful on Windows) [#11](https://github.com/dxing97/subs2cia/pull/11)
### Fixed 
 - Added fix for [#1](https://github.com/dxing97/subs2cia/issues/1) to ffmpeg_condense_video
 - Change required python version in setup.py to 3.6 (see [#15](https://github.com/dxing97/subs2cia/issues/15))
 - Fix for VTT subtitles and workaround for subtitle format detection edge case ([#12](https://github.com/dxing97/subs2cia/issues/12))



## [0.3.2] - 2020-11-19

### Fixed
- `-m` was raising an error due to an improper refactor

## [0.3.1] - 2020-11-11

### Added 
 - Can now ignore chapters `-Ic` in addition to time ranges (`-I`)
 - `-ls` now also lists chapter start/end times and titles for use with `-Ic`
 

## [0.3.0] - 2020-11-03
### Added
 - Export subtitles, audio, screenshots for use in a SRS application
 - Ignore ranges can now be specified relative to end of audio (using `e` prefix) and to start of ignore range 
 (using `+` prefix)
    - Examples: 
        - Ignore two minutes minute after 10 minute mark: `-I 10m +2m`
        - Ignore last minute: `-I e1m +1m` or `-I e1m e0m`
        - Ignore 1m30s after 2 minute mark: `-I 2m +1m30s`
 - Interactive mode for selecting audio/subtitle/video streams as alternative to current automatic picker system
 - Bitrate, mono-channel output controls
 
 ### Fixed
 - Fix infinite loop that occurred when ignore range exactly matched subtitle start/end
 - Fix issue where files were not correctly grouped
 - Picker now accounts for input file order when choosing streams
 
## [0.2.5] - 2020-09-22
### Added
 - Ignore ranges option for ignoring subtitles that lie in a certain time range for OP/ED removal

## [0.2.4] - 2020-09-17

### Added

 - Subtitles are now also condensed alongside audio and/or video
 - Condensed videos now come with condensed subtitles muxed in
 - Check to see if ffmpeg is in path, raises warning in the log if it's not found
 - PyPi package!

### Fixed

 - Fix pycountry exception occuring when looking up Stream language 

### Depreciated
 - subtools.py: `load_subtitles()` and `merge_times()` have been deprecated in favor of SubtitleManipulator and SubGroup

<!-- Added, Changed, Depreciated, Removed, Fixed, Security -->