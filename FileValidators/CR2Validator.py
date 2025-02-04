class CR2Validator(Validator):
    """
    Validates if a file is a proper Canon CR2 raw file.
    """

    def __init__(self):
        super(CR2Validator, self).__init__()
        self.data = ""
        self.pos = 0
        self.details = {}

    def _Read(self, length):
        ret = self.data[self.pos: self.pos + length]
        if len(ret) < length:
            self.eof = True
        self.pos += length
        return ret

    def GetDetails(self):
        return self.details

    def _CleanDetails(self):
        self.details = {
            "extensions": [".cr2"],
        }

    def Validate(self, fd):
        if isinstance(fd, str):
            self.data = fd
        else:
            self.data = fd.read()

        self.pos = 0
        self.is_valid = True
        self.eof = False
        self._CleanDetails()

        # Read first 10 bytes
        header = self._Read(10)
        if len(header) < 10:
            return False  # Not enough data

        # Check TIFF magic number and CR2 identifier
        if header[:4] != b"II\x2A\x00" or header[8:10] != b"CR":
            return False

        return True
