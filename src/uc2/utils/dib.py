#
#  Copyright (C) 2020 by Ihor E. Novikov
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License
#  as published by the Free Software Foundation, either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math
import struct


def dib_to_bmp(dib: bytes) -> bytes:
    """Reconstructs BMP bitmap file header for DIB

    :param dib: (bytes) device-independent bitmap string
    :return: (bytes) BMP string
    """
    offset = dib_header_size = struct.unpack('<I', dib[:4])[0]
    if dib_header_size == 12:
        bitsperpixel = struct.unpack('<h', dib[10:12])[0]
        if not bitsperpixel > 8:
            offset += math.pow(2, bitsperpixel) * 3
    else:
        bitsperpixel = struct.unpack('<h', dib[14:16])[0]
        colorsnum = struct.unpack('<I', dib[32:36])[0]
        if bitsperpixel > 8:
            offset += colorsnum * 3
        else:
            offset += math.pow(2, bitsperpixel) * 3
    offset = math.ceil(offset / 4.0) * 4

    pixel_offset = struct.pack('<I', 14 + offset)
    file_size = struct.pack('<I', 14 + len(dib))
    return b'BM' + file_size + b'\x00\x00\x00\x00' + pixel_offset + dib


def bmp_to_dib(bmp: bytes) -> bytes:
    """Extracts DIB from BMP

    :param bmp: BMP string
    :return: DIB string
    """
    return bmp[14:]
