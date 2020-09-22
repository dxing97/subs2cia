# Changelog

## [Unreleased]

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