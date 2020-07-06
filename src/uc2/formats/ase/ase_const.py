# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015 by Igor E. Novikov
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

from uc2.uc2const import COLOR_CMYK, COLOR_GRAY, COLOR_LAB, COLOR_RGB

ASEF = b'ASEF'
ASE_VER = b'\x00\x01\x00\x00'
ASE_GROUP = b'\xc0\x01'
ASE_GROUP_END = b'\xc0\x02'
ASE_COLOR = b'\x00\x01'

ASE_NAMES = {
    ASE_GROUP: b'ASE Group',
    ASE_GROUP_END: b'ASE Group End',
    ASE_COLOR: b'ASE Color',
}

ASE_RGB = b'RGB '
ASE_CMYK = b'CMYK'
ASE_LAB = b'LAB '
ASE_GRAY = b'Gray'

CS_MATCH = {
    ASE_RGB: COLOR_RGB,
    ASE_CMYK: COLOR_CMYK,
    ASE_LAB: COLOR_LAB,
    ASE_GRAY: COLOR_GRAY,
    COLOR_RGB: ASE_RGB,
    COLOR_CMYK: ASE_CMYK,
    COLOR_LAB: ASE_LAB,
    COLOR_GRAY: ASE_GRAY,
}

ASE_GLOBAL = b'\x00\x00'
ASE_SPOT = b'\x00\x01'
ASE_PROCESS = b'\x00\x02'
