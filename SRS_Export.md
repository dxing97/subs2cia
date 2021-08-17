## SRS Export

### Usage
Most options are shared with `condense`. See `subs2cia srs -h` for a full list of options. 

The same overall idea is the same: give subs2cia an audio and subtitle source. Instead of generating a set of 
condensed outputs, a .tsv (tab-seperated values) file is generated
along with audio clips and screenshots (if a video source is given). 

Each column of the .tsv file represents the following:
1. Subtitle text
2. Time range of subtitle in milliseconds: `start-end`
3. Audio:`[sound:media_start-end.mp3]`
4. Screenshot: `<img src='media_start-end.jpg'>`
   * Screenshot resolution is the video file's resolution
5. Video clip (currently disabled)
6. Comma-seperated list of input files used

Note that in batch mode, multiple .tsv files are generated, one for each input group. 

Since there could be hundreds output files, it's highly recommended to specify an output
directory with `-d` in order to avoid cluttering your filesystem. 

### Anki Instructions
1. In the main screen, click on `File->Import...`
2. Select the .tsv file you would like to import
3. In the Import dialog box:
   1. Choose the note type and deck you'd like to import to
   2. Make sure fields are separated by tabs
   3. Make sure `Allow HTML in fields` is checked
   4. Adjust the 6 fields (detailed above) to fit your note type
   5. Click `Import`
4. Verify audio and screenshots were automagically imported as well. If audio and/or screenshots are missing, they may 
    need to be manually moved into your collections folder. If the .tsv file isn't in the same directory as the generated
    audio clips and images, Anki won't copy them for you. 
#### Examples
`subs2cia srs -b -i *.mkv *.ja.srt -d outputdir`