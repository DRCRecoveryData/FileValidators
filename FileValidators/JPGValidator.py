# CIRA File Validators
# Copyright (C) 2014 InFo-Lab
#
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU
# Lesser General Public License as published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program; if not,
# write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# coding=utf-8
import struct
from Validator import Validator

class JPGValidator(Validator):
    """
    Class that validates an object to determine if it is a valid JPG file.
    """

    def __init__(self):
        super().__init__()
        self.converter = struct.Struct(">H")
        self._chunksize = 2048
        self.markers = {b'\xff\xc0', b'\xff\xc1', b'\xff\xc2', b'\xff\xc3', b'\xff\xc4', b'\xff\xc5',
                        b'\xff\xc6', b'\xff\xc7', b'\xff\xc8', b'\xff\xc9', b'\xff\xca', b'\xff\xcb',
                        b'\xff\xcc', b'\xff\xcd', b'\xff\xce', b'\xff\xcf', b'\xff\xd0', b'\xff\xd1',
                        b'\xff\xd2', b'\xff\xd3', b'\xff\xd4', b'\xff\xd5', b'\xff\xd6', b'\xff\xd7',
                        b'\xff\xd9', b'\xff\xda', b'\xff\xdb', b'\xff\xdc', b'\xff\xdd', b'\xff\xde',
                        b'\xff\xdf', b'\xff\xe0', b'\xff\xe1', b'\xff\xe2', b'\xff\xe3', b'\xff\xe4',
                        b'\xff\xe5', b'\xff\xe6', b'\xff\xe7', b'\xff\xe8', b'\xff\xe9', b'\xff\xea',
                        b'\xff\xeb', b'\xff\xec', b'\xff\xed', b'\xff\xee', b'\xff\xef', b'\xff\xf0',
                        b'\xff\xf1', b'\xff\xf2', b'\xff\xf3', b'\xff\xf4', b'\xff\xf5', b'\xff\xf6',
                        b'\xff\xf7', b'\xff\xf8', b'\xff\xf9', b'\xff\xfa', b'\xff\xfb', b'\xff\xfc',
                        b'\xff\xfd', b'\xff\xfe'}
        self.restart_markers = {b'\xff\x00', b'\xff\xd0', b'\xff\xd1', b'\xff\xd2', b'\xff\xd3',
                                b'\xff\xd4', b'\xff\xd5', b'\xff\xd6', b'\xff\xd7'}
        self.min_size = 135
        self.eoi_marker = False
        self.markers_found = []
        self.data = b""
        self.pos = 0

    def _ConvertBytes(self, value):
        return self.converter.unpack(value)[0]

    def _Read(self, length):
        ret = self.data[self.pos: self.pos + length]
        if len(ret) < length:
            self.eof = True
        self.pos += length
        return ret

    def GetDetails(self):
        return {
            "segments": self.markers_found,
            'extensions': ['.jpg'],
        }

    def Validate(self, fd):
        """
        Validates a file-like object to determine if it is a valid JPG file.

        :param fd: file-like object open for binary reading or raw bytes
        :return: True on a valid JPG file, False otherwise (bool)
        """
        if isinstance(fd, str):  # If fd is a file path, open and read it
            with open(fd, "rb") as f:
                self.data = f.read()
        elif isinstance(fd, bytes):
            self.data = fd
        else:
            raise TypeError("Argument must be a file path (str) or bytes.")

        self.pos = 0
        self.is_valid = True
        self.eof = False
        self.end = False
        self._SetValidBytes(0)
        self.markers_found = []

        if len(self.data) < 4:
            return False  # Not enough data for a valid JPEG

        first_read = self._Read(4)
        header_marker = first_read[:2]
        current_marker = first_read[2:]

        self.is_valid = header_marker == b'\xff\xd8' and current_marker in self.markers
        if self.is_valid:
            self.markers_found.append((b'ffd8', self.pos - 4, 2))
        self._CountValidBytes(4)

        is_eoi_marker = current_marker == b'\xff\xd9'
        while not self.eof and not is_eoi_marker and self.is_valid:
            if current_marker == b'\xff\xd9':
                is_eoi_marker = True
                break

            if current_marker == b'\xff\xdd':  # DRI marker has a fixed length of 4
                payload_length = 4
            else:
                payload_length_data = self._Read(2)
                self._CountValidBytes(2)
                payload_length = self._ConvertBytes(payload_length_data) - 2 if not self.eof else 0

            if self.is_valid and not self.eof:
                self.markers_found.append((current_marker.hex(), self.pos - 4, payload_length + 4))

            self._Read(payload_length)
            self._CountValidBytes(payload_length)

            current_marker = self._Read(2)
            self.is_valid = current_marker in self.markers
            self._CountValidBytes(2)
            is_eoi_marker = current_marker == b'\xff\xd9'

        if is_eoi_marker:
            self._SetValidBytes(self.bytes_last_valid - 2)
            self.end = True
            self.markers_found.append((b'ffd9', self.pos - 2, 2))

        if self.bytes_last_valid < self.min_size:
            self.is_valid = False

        return self.is_valid
