from subs2cia_v2.sources import AVSFile

# single ffmpeg stream
class Stream:
    index = None

    def __init__(self, file: AVSFile, index=None):
        self.file = file
        self.index = index
        # index of None indicates that demuxing with ffmpeg is not nessecary to extract data