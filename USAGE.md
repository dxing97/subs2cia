# Condense Usage 
More readable version Coming Soon.
```
$ subs2cia condense -h
usage: subs2cia condense [-h] [-v] [-vv] [-i <input files> [<input files> ...]]
                         [-si <index>] [-ai <index>] [-b] [-u] [-o <name>]
                         [-d /path/to/directory] [-ae <audio extension>]
                         [-q <bitrate in kbps>] [-M] [-m]
                         [--overwrite-on-demux] [--keep-temporaries]
                         [--no-overwrite-on-generation] [-ni]
                         [-R <regular expression>]
                         [-I [prefix]timestamp [prefix]timestamp] [-p msecs]
                         [-tl ISO_code] [-ls] [--preset preset#] [-lp] [-a]
                         [-ma] [-t msecs] [-r secs] [-s secs] [-c <ratio>]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output if set.
  -vv, --debug          Verbose and debug output if set
  -i <input files> [<input files> ...], --inputs <input files> [<input files> ...]
                        Paths to input files or a single path to a directory
                        of input files.
  -si <index>, --subtitle-index <index>
                        Force a certain subtitle stream to use. Takes
                        precedence over --target-language option.If any input
                        files are standalone subtitle files, they will be used
                        first. Use --list-streams for a list of available
                        streams and their indices.
  -ai <index>, --audio-index <index>
                        Force a certain subtitle audio to use. Takes
                        precedence over --target-language option.If any input
                        files are standalone audio files, they will be used
                        first. Use --list-streams for a list of available
                        streams and their indices.
  -b, --batch           If set, attempts to split input files into groups, one
                        output file per group. Groups are determined by file
                        names. If two files share the same root name, such as
                        "video0.mkv" and "video0.srt", then they are part of
                        the same group.
  -u, --dry-run         If set, will analyze input files but won't demux or
                        generate any output files
  -o <name>, --output-name <name>
                        Output file name to save to, without the extension
                        (specify extension using -ae or -ve). By default, uses
                        the file name of the first input file with the input
                        extension removed and "condensed.{output extension}
                        added. Ignored if batch mode is enabled.
  -d /path/to/directory, --output-dir /path/to/directory
                        Output directory to save to. Default is the directory
                        the input files reside in.
  -ae <audio extension>, --audio-extension <audio extension>
                        Output audio extension to save as (without the dot).
                        Default is mp3, flac has been tested to work.
  -q <bitrate in kbps>, --bitrate <bitrate in kbps>
                        Output audio bitrate in kbps, lower bitrates result in
                        smaller files and lower fidelity. Ignored if the
                        output type is not mp3. Default is 320 kbps. Bitrates
                        below 64 kbps are not recommended.
  -M, --mono            If set, mixes audio channels to a single channel,
                        primarily to save space.
  -m, --gen-video       If set, generates condensed video along with condensed
                        audio and subtitles. Subtitles are muxed in to video
                        file. WARNING: VERY CPU INTENSIVE).
  --overwrite-on-demux  If set, will overwrite existing files when demuxing
                        temporary files.
  --keep-temporaries    If set, will not delete any demuxed temporary files.
  --no-overwrite-on-generation
                        If set, will not overwrite existing files when
                        generating output media.
  -ni, --ignore-none    If set, will not use internal heuristics to remove
                        non-dialogue lines from the subtitle. Ignored if -R is
                        set.
  -R <regular expression>, --sref <regular expression>
                        For filtering non-dialogue subtitles. Lines that match
                        given regex are IGNORED during subtitle processing and
                        will not influence condensed audio or be included in
                        output cards. Ignored lines may still be included in
                        condensed subtitles if they overlap with non-ignored
                        subtitles. This option will override the internal
                        subs2cia non-dialogue filter.
  -I [prefix]timestamp [prefix]timestamp, --ignore-range [prefix]timestamp [prefix]timestamp
                        Time range to ignore when condensing, specified using
                        two timestamps. Useful for removing openings and
                        endings of shows. Time formatting example:
                        '2h30m2s100ms', '10m20s', etc. Subtitles that fall
                        into an ignored range before padding are trimmed so
                        that they do not overlap with the ignore range.
                        Timestamps can measured from the start of the audio
                        (no prefix), end of the audio (using the 'e' prefix),
                        or relative to another timestamp (using the '+'
                        prefix). If batch mode is enabled, the same ranges are
                        applied to ALL outputs.Multiple ranges can be
                        specified like so: -I 2m 3m30s -I 20m 21m.
  -p msecs, --padding msecs
                        Adds this many milliseconds of audio before and after
                        every subtitle. Overlaps with adjacent subtitles are
                        merged automatically.
  -tl ISO_code, --target-language ISO_code
                        If set, attempts to use audio and subtitle files that
                        are in this language first. Input should be an ISO
                        639-3 language code.
  -ls, --list-streams   Lists all audio, subtitle, and video streams found in
                        given input files and exits.
  --preset preset#      If set, uses a given preset. User arguments will
                        override presets.
  -lp, --list-presets   Lists all available built-in presets and exits.
  -a, --absolute-paths  Prints absolute paths from the root directory instead
                        of given paths.
  -ma, --interactive    If set, will enable interactive stream picking.
                        Overrides -ai, -si, -tl. Also overrides -c in
  -t msecs, --threshold msecs
                        If two subtitles start and end within (threshold +
                        2*padding) milliseconds of each other, they will be
                        merged. Useful for preserving silences between
                        subtitle lines.
  -r secs, --partition secs
                        If set, attempts to partition the input audio into
                        seperate blocks of this size seconds BEFORE
                        condensing. Partitions and splits respect subtitle
                        boundaries and will not split a single subtitle across
                        two output files. 0 partition length is ignored. For
                        example, if the partition size is 60 seconds and the
                        input media is 180 seconds long, then there will be
                        three output files. The first output file will contain
                        condensed media from the first 60 seconds of the
                        source material, the second output file will contain
                        the next 60 seconds of input media, and so on.
  -s secs, --split secs
                        If set, attempts to split the condensed audio into
                        seperate blocks of this size AFTER condensing. 0 split
                        length is ignored. Partitions and splits respect
                        subtitle boundaries and will not split a single
                        subtitle across two output files. Done within a
                        partition. For example, say the split length is 60
                        seconds and the condensed audio length of a input
                        partition is 150 seconds. The output file will be
                        split into three files, the first two ~60 seconds long
                        and the last ~30 seconds long.
  -c <ratio>, --minimum-compression-ratio <ratio>
                        Will only generate from subtitle files that are this
                        fraction long of the selected audio file. Default is
                        0.2, meaning the output condensed file must be at
                        least 20 percent as long as the chosen audio stream.
                        If the output doesn't reach this minimum, then a
                        different subtitle file will be chosen, if available.
                        Used for ignoring subtitles that contain onlysigns and
                        songs.
```

# SRS Export Usage

Many options are shared between SRS and Condense.
```
$ subs2cia srs -h
usage: subs2cia srs [-h] [-v] [-vv] [-i <input files> [<input files> ...]]
                    [-si <index>] [-ai <index>] [-b] [-u] [-o <name>]
                    [-d /path/to/directory] [-ae <audio extension>]
                    [-q <bitrate in kbps>] [-M] [-m] [--overwrite-on-demux]
                    [--keep-temporaries] [--no-overwrite-on-generation] [-ni]
                    [-R <regular expression>]
                    [-I [prefix]timestamp [prefix]timestamp] [-p msecs]
                    [-tl ISO_code] [-ls] [--preset preset#] [-lp] [-a] [-ma]
                    [-N]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose output if set.
  -vv, --debug          Verbose and debug output if set
  -i <input files> [<input files> ...], --inputs <input files> [<input files> ...]
                        Paths to input files or a single path to a directory
                        of input files.
  -si <index>, --subtitle-index <index>
                        Force a certain subtitle stream to use. Takes
                        precedence over --target-language option.If any input
                        files are standalone subtitle files, they will be used
                        first. Use --list-streams for a list of available
                        streams and their indices.
  -ai <index>, --audio-index <index>
                        Force a certain subtitle audio to use. Takes
                        precedence over --target-language option.If any input
                        files are standalone audio files, they will be used
                        first. Use --list-streams for a list of available
                        streams and their indices.
  -b, --batch           If set, attempts to split input files into groups, one
                        output file per group. Groups are determined by file
                        names. If two files share the same root name, such as
                        "video0.mkv" and "video0.srt", then they are part of
                        the same group.
  -u, --dry-run         If set, will analyze input files but won't demux or
                        generate any output files
  -o <name>, --output-name <name>
                        Output file name to save to, without the extension
                        (specify extension using -ae or -ve). By default, uses
                        the file name of the first input file with the input
                        extension removed and "condensed.{output extension}
                        added. Ignored if batch mode is enabled.
  -d /path/to/directory, --output-dir /path/to/directory
                        Output directory to save to. Default is the directory
                        the input files reside in.
  -ae <audio extension>, --audio-extension <audio extension>
                        Output audio extension to save as (without the dot).
                        Default is mp3, flac has been tested to work.
  -q <bitrate in kbps>, --bitrate <bitrate in kbps>
                        Output audio bitrate in kbps, lower bitrates result in
                        smaller files and lower fidelity. Ignored if the
                        output type is not mp3. Default is 320 kbps. Bitrates
                        below 64 kbps are not recommended.
  -M, --mono            If set, mixes audio channels to a single channel,
                        primarily to save space.
  -m, --gen-video       If set, generates condensed video along with condensed
                        audio and subtitles. Subtitles are muxed in to video
                        file. WARNING: VERY CPU INTENSIVE).
  --overwrite-on-demux  If set, will overwrite existing files when demuxing
                        temporary files.
  --keep-temporaries    If set, will not delete any demuxed temporary files.
  --no-overwrite-on-generation
                        If set, will not overwrite existing files when
                        generating output media.
  -ni, --ignore-none    If set, will not use internal heuristics to remove
                        non-dialogue lines from the subtitle. Ignored if -R is
                        set.
  -R <regular expression>, --sref <regular expression>
                        For filtering non-dialogue subtitles. Lines that match
                        given regex are IGNORED during subtitle processing and
                        will not influence condensed audio or be included in
                        output cards. Ignored lines may still be included in
                        condensed subtitles if they overlap with non-ignored
                        subtitles. This option will override the internal
                        subs2cia non-dialogue filter.
  -I [prefix]timestamp [prefix]timestamp, --ignore-range [prefix]timestamp [prefix]timestamp
                        Time range to ignore when condensing, specified using
                        two timestamps. Useful for removing openings and
                        endings of shows. Time formatting example:
                        '2h30m2s100ms', '10m20s', etc. Subtitles that fall
                        into an ignored range before padding are trimmed so
                        that they do not overlap with the ignore range.
                        Timestamps can measured from the start of the audio
                        (no prefix), end of the audio (using the 'e' prefix),
                        or relative to another timestamp (using the '+'
                        prefix). If batch mode is enabled, the same ranges are
                        applied to ALL outputs.Multiple ranges can be
                        specified like so: -I 2m 3m30s -I 20m 21m.
  -p msecs, --padding msecs
                        Adds this many milliseconds of audio before and after
                        every subtitle. Overlaps with adjacent subtitles are
                        merged automatically.
  -tl ISO_code, --target-language ISO_code
                        If set, attempts to use audio and subtitle files that
                        are in this language first. Input should be an ISO
                        639-3 language code.
  -ls, --list-streams   Lists all audio, subtitle, and video streams found in
                        given input files and exits.
  --preset preset#      If set, uses a given preset. User arguments will
                        override presets.
  -lp, --list-presets   Lists all available built-in presets and exits.
  -a, --absolute-paths  Prints absolute paths from the root directory instead
                        of given paths.
  -ma, --interactive    If set, will enable interactive stream picking.
                        Overrides -ai, -si, -tl. Also overrides -c in
  -N, --normalize       If set, normalizes volume of audio clips to the same
                        loudness. YMMV.
```