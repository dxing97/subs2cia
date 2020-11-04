# Changelog

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
 
 ### Fixed
 - Fix infinite loop that ococured when ignore range exactly matched subtitle start/end
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