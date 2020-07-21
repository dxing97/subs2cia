## Notes

start(program args)
```
examine input files
Are they all valid files? Are any files not a media file?
Does the metadata all look gucci? 
Individually, is there something wrong with a file? (not considering output file yet)
Note: at this point, nothing besides metadata is read from input files

determine output files

if batching is disabled
    throw all input files into a single "condensing operation" and treat it as a batch of size 1

How many output files are there? 
Cluster output files based on how Plex enforces external assets

for each output file target
    generate condensed media
```

picker(input files)
```
one stream for each media type (audio, subtitle, video) can be chosen 
    a "stream" being one of the following:
     - a individual standalone audio or subtitle file (.mp3. .srt, .flac, etc)
     - a media stream in a multimedia file (e.g. audio stream in .mkv or .mp4)
    Only subtitle, audio, and video streams are considered. Others are ignored.
    
streams are chosen in order of this preference:
     - individual file (.mp3, .srt, etc)
     - media stream in multimedia file in desired language
     - media stream in multimedia file in other languages
    stream pickers are generators, so each iteration of this while loop yields different streams
```
condense(input files, output file parameters)
```
given: 
 - output file name (either user specified in non-batch mode or determined from input file clustering)
 - a set of input files, each individually vetted for metadata validity


chosen_audio = chosen subtitle = chosen video = empty set
while(set of chosen streams is insufficient):
    # pick a stream candidate for each chosen stream set that is an empty set
    if chosen audio is empty
        audio_picker()
    repeat for subtitle, video
    
    read chosen stream data 
        if the stream is a standalone file, just read it in directly from disk
        if the stream is embedded in a container, 
            demux it if nessecary (subtitles)
            otherwise just read the metadata if metadata is acceptable
    analyze chosen stream data of each type
        read subtitles and make sure they contain dialogue, is not empty, etc
        make sure audio... exists?
        make sure video... exists? 
        if any of the chosen stream types are not good
            set chosen_{type} to empty set

at this point, if one of the input stream types is missing (i.e. one of the chosen types is the empty set), 
delete any demuxed files (if told to do so) then terminate execution


do ffmpeg condensing stuff here

```