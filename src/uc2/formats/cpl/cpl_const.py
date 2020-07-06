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


CPLX4_SPOT = b'\xcd\xdd'
CPL12_SPOT = b'\xcd\xbc'
CPL12 = b'\xdd\xdc'
CPL10 = b'\xcd\xdc'
CPL8 = b'\xdc\xdc'
CPL7 = b'\xcc\xdc'
CPL7_UTF = b'\xcc\xbc'

CPL_IDs = [CPLX4_SPOT, CPL12, CPL12_SPOT, CPL10, CPL8, CPL7, CPL7_UTF]

CPL12_PALTYPE = b'\x05\x00'
CPL12_NHEADERS = b'\x03\x00\x00\x00'
