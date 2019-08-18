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

import struct
from colorsys import hsv_to_rgb
from uc2 import uc2const, cms

from uc2.formats.jcw.jcw_const import JCW_PMS, JCW_CMYK_PANTONE, \
    JCW_RGB_PANTONE, JCW_HSV_PANTONE, JCW_CMYK, JCW_SPOT_CMYK, JCW_RGB, \
    JCW_SPOT_RGB, JCW_HSV, JCW_SPOT_HSV


def val_to_dec(vals):
    ret = []
    for item in vals:
        ret.append(item / 10000.0)
    return ret


def dec_to_val(vals):
    ret = []
    for item in vals:
        ret.append(int(item * 10000))
    return ret


def parse_cmyk(data):
    cmyk = val_to_dec(struct.unpack('<4H', data))
    return [uc2const.COLOR_CMYK, cmyk, 1.0, '']


def parse_rgb(data):
    rgb = val_to_dec(struct.unpack('<3H', data[:6]))
    return [uc2const.COLOR_RGB, rgb, 1.0, '']


def parse_hsv(data):
    hsv = val_to_dec(struct.unpack('<3H', data[:6]))
    rgb = list(hsv_to_rgb(*hsv))
    return [uc2const.COLOR_RGB, rgb, 1.0, '']


SPOT_CS = (JCW_CMYK_PANTONE, JCW_SPOT_CMYK, JCW_RGB_PANTONE, JCW_SPOT_RGB,
           JCW_HSV_PANTONE, JCW_SPOT_HSV)
CS_MAP = dict(
    [(cs, parse_cmyk)
     for cs in (JCW_PMS, JCW_CMYK_PANTONE, JCW_CMYK, JCW_SPOT_CMYK)] +
    [(cs, parse_rgb) for cs in (JCW_RGB_PANTONE, JCW_RGB, JCW_SPOT_RGB)] +
    [(cs, parse_hsv) for cs in (JCW_HSV_PANTONE, JCW_HSV, JCW_SPOT_HSV)])


def parse_jcw_color(cs, data):
    color = CS_MAP[cs](data) if cs in CS_MAP else []
    return cms.color_to_spot(color) if cs in SPOT_CS else color


def get_jcw_color(color):
    if color[0] == uc2const.COLOR_CMYK:
        return struct.pack('<4H', *dec_to_val(color[1]))
    if color[0] == uc2const.COLOR_GRAY:
        vals = cms.gray_to_cmyk(color[1])
        return struct.pack('<4H', *dec_to_val(vals))
    else:
        return struct.pack('<3H', *dec_to_val(color[1])) + '\x00\x00'
