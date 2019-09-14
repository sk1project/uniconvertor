# -*- coding: utf-8 -*-
#
#  Copyright (C) 2009-2019 by Maxim S. Barabash
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


PEC_HEADER_SIZE = 512

PES_DOCUMENT = "PES Document"
PES_HEADER = "PES Header"
PEC_HEADER = "PEC Header"
PEC_BODY = "PEC Body"
PES_UNKNOWN = "Unknown"

CID_TO_NAME = {
    PES_UNKNOWN: "Unknown",
}

from uc2 import uc2const

PES_TO_MM = 0.1
MM_TO_PES = 10.0

IN_TO_PES = uc2const.pt_to_mm * MM_TO_PES
PES_TO_IN = uc2const.mm_to_pt * PES_TO_MM

PES_SIGNATURE = '#PES'
PEC_SIGNATURE = '#PEC'

PES_to_SK2_TRAFO = [PES_TO_IN, 0.0, 0.0, PES_TO_IN, 0.0, 0.0]

CMD_STITCH = 'Stitch'
# CMD_SEQUIN_MODE = 0b01000011
CMD_JUMP = 'Jump'
CMD_CHANGE_COLOR = 'Change Color'
PES_THUMBNAIL = 'THUMBNAIL'
# CMD_STOP = 0b11110011
CMD_TRIM = 'TRIM'
CMD_END = 'END'

DATA_TERMINATOR = b'\xFF'
