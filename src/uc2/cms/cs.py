#
#  Copyright (C) 2011-2020 by Ihor E. Novikov
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

import copy

from uc2 import uc2const
from . import libcms
from .lab import (rgb_to_lab, lab_to_rgb)
from .utils import *


def get_registration_black():
    return [uc2const.COLOR_SPOT, [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], 1.0, uc2const.COLOR_REG]


def color_to_spot(color):
    if not color:
        return get_registration_black()
    if color[0] == uc2const.COLOR_SPOT:
        return copy.deepcopy(color)
    rgb = []
    cmyk = []
    name = ''
    if color[0] == uc2const.COLOR_RGB:
        rgb = copy.deepcopy(color[1])
    elif color[0] == uc2const.COLOR_CMYK:
        cmyk = copy.deepcopy(color[1])
    elif color[0] == uc2const.COLOR_GRAY:
        cmyk = gray_to_cmyk(color[1])
    if color[3]:
        name += color[3]
    return [uc2const.COLOR_SPOT, [rgb, cmyk], color[2], name]


def rgb_to_hexcolor(color):
    """Converts list of RGB float values to hex color string.
    For example: [1.0, 0.0, 1.0] => #ff00ff
    """
    return '#%02x%02x%02x' % tuple(int(round(255 * x)) for x in color)


def rgba_to_hexcolor(color):
    """Converts list of RGBA float values to hex color string.
    For example: [1.0, 0.0, 1.0, 1.0] => #ff00ffff
    """
    return '#%02x%02x%02x%02x' % tuple(int(round(255 * x)) for x in color)


def cmyk_to_hexcolor(color):
    return rgba_to_hexcolor(color)


def hexcolor_to_rgb(hexcolor):
    """Converts hex color string as a list of float values.
    For example: #ff00ff => [1.0, 0.0, 1.0]
    """
    if not hexcolor.startswith('#'):
        hexcolor = '#%s' % hexcolor
    if len(hexcolor) == 4:
        vals = (hexcolor[1] * 2, hexcolor[2] * 2, hexcolor[3] * 2)
    else:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_rgba(hexcolor):
    """Converts hex color string as a list of float values.
    For example: #ff00ffff => [1.0, 0.0, 1.0, 1.0]
    """
    vals = ('00', '00', '00', 'ff')
    if len(hexcolor) == 7:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:], 'ff')
    elif len(hexcolor) == 9:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:7], hexcolor[7:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_cmyk(hexcolor):
    return hexcolor_to_rgba(hexcolor)


def gdk_hexcolor_to_rgb(hexcolor):
    """ Converts hex color string as a list of float values.
    For example: #ffff0000ffff => [1.0, 0.0, 1.0]
    """
    vals = (hexcolor[1:5], hexcolor[5:6], hexcolor[9:])
    return [int(x, 0x10) / 65535.0 for x in vals]


def rgb_to_gdk_hexcolor(color):
    """Converts hex color string as a list of float values.
    For example: #ffff0000ffff => [1.0, 0.0, 1.0]
    """
    return '#%04x%04x%04x' % tuple(x * 65535.0 for x in color)


def cmyk_to_rgb(color):
    """Converts list of CMYK values to RGB.
    """
    c, m, y, k = color
    return [round(1.0 - min(1.0, x + k), 3) for x in (c, m, y)]


def rgb_to_cmyk(color):
    """Converts list of RGB values to CMYK.
    """
    r, g, b = color
    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b
    k = min(c, m, y)
    return [c - k, m - k, y - k, k]


def gray_to_cmyk(color):
    """Converts Gray value to CMYK.
    """
    k = 1.0 - color[0]
    c = m = y = 0.0
    return [c, m, y, k]


def gray_to_rgb(color):
    """Converts Gray value to RGB.
    """
    r = g = b = color[0]
    return [r, g, b]


def rgb_to_gray(color):
    """Converts RGB value to Gray.
    """
    r, g, b = color
    val = (r + g + b) / 3.0
    return [val, ]


def do_simple_transform(color, cs_in, cs_out):
    """
    Emulates color management library transformation
    """
    if cs_in == cs_out:
        return copy.copy(color)

    if cs_in == uc2const.COLOR_RGB:
        if cs_out == uc2const.COLOR_CMYK:
            return rgb_to_cmyk(color)
        elif cs_out == uc2const.COLOR_GRAY:
            return rgb_to_gray(color)
        elif cs_out == uc2const.COLOR_LAB:
            return rgb_to_lab(color)
    elif cs_in == uc2const.COLOR_CMYK:
        if cs_out == uc2const.COLOR_RGB:
            return cmyk_to_rgb(color)
        elif cs_out == uc2const.COLOR_GRAY:
            return rgb_to_gray(cmyk_to_rgb(color))
        elif cs_out == uc2const.COLOR_LAB:
            return rgb_to_lab(cmyk_to_rgb(color))
    elif cs_in == uc2const.COLOR_GRAY:
        if cs_out == uc2const.COLOR_RGB:
            return gray_to_rgb(color)
        elif cs_out == uc2const.COLOR_CMYK:
            return gray_to_cmyk(color)
        elif cs_out == uc2const.COLOR_LAB:
            return rgb_to_lab(gray_to_rgb(color))
    elif cs_in == uc2const.COLOR_LAB:
        if cs_out == uc2const.COLOR_RGB:
            return lab_to_rgb(color)
        elif cs_out == uc2const.COLOR_CMYK:
            return rgb_to_cmyk(lab_to_rgb(color))
        elif cs_out == uc2const.COLOR_GRAY:
            return rgb_to_gray(lab_to_rgb(color))


def colorb(color=None, cmyk=False):
    """
    Emulates COLORB object from python-lcms.
    Actually function returns regular 4-member list.
    """
    if color is None:
        return [0, 0, 0, 0]
    if color[0] == uc2const.COLOR_SPOT:
        if cmyk:
            values = color[1][1]
        else:
            values = color[1][0]
    else:
        values = color[1]

    result = []
    if color[0] == uc2const.COLOR_LAB:
        result.append(int(round(values[0] * 100)))
        result.append(int(round(values[1] * 255)))
        result.append(int(round(values[2] * 255)))
    else:
        for value in values:
            result.append(int(round(value * 255)))

    if len(result) == 1:
        result += [0, 0, 0]
    elif len(result) == 3:
        result += [0]
    return result


def decode_colorb(colorb_list, color_type):
    """
    Decodes colorb list into generic color values.
    """
    result = []
    if color_type == uc2const.COLOR_CMYK:
        values = colorb_list
    elif color_type == uc2const.COLOR_GRAY:
        values = [colorb_list[0], ]
    else:
        values = colorb_list[:3]

    if color_type == uc2const.COLOR_LAB:
        result.append(values[0] / 100.0)
        result.append(values[1] / 255.0)
        result.append(values[2] / 255.0)
    else:
        for value in values:
            result.append(value / 255.0)
    return result


def verbose_color(color):
    if not color:
        return 'No color'
    cs = color[0]
    val = [] + color[1]
    alpha = color[2]
    if cs == uc2const.COLOR_CMYK:
        c, m, y, k = val_100(val)
        ret = 'C-%d%% M-%d%% Y-%d%% K-%d%%' % (c, m, y, k)
        if alpha < 1.0:
            ret += ' A-%d%%' % val_100([alpha, ])[0]
    elif cs == uc2const.COLOR_RGB:
        r, g, b = val_255(val)
        ret = 'R-%d G-%d B-%d' % (r, g, b)
        if alpha < 1.0:
            ret += ' A-%d' % val_255([alpha, ])[0]
    elif cs == uc2const.COLOR_GRAY:
        g = val_255(val)[0]
        ret = 'Gray-%d' % g
        if alpha < 1.0:
            ret += ' Alpha-%d' % val_255([alpha, ])[0]
    elif cs == uc2const.COLOR_LAB:
        l_, a, b = val
        l_ = l_ * 100.0
        a = a * 255.0 - 128.0
        b = b * 255.0 - 128.0
        ret = 'L %d a %d b %d' % (l_, a, b)
        if alpha < 1.0:
            ret += ' Alpha-%d' % val_255([alpha, ])[0]
    elif cs == uc2const.COLOR_SPOT:
        ret = color[3]
    else:
        return '???'

    return ret


def get_profile_name(filepath):
    """Returns profile name.
    If file is not suitable profile or doesn't exist
    returns None.
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = libcms.cms_get_profile_name(profile)
    except Exception:
        ret = None
    return ret


def get_profile_info(filepath):
    """Returns profile info.
    If file is not suitable profile or doesn't exist
    returns None.
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = libcms.cms_get_profile_info(profile)
    except Exception:
        ret = None
    return ret


def get_profile_descr(filepath):
    """Returns profile description tuple (name, copyright, info).
    If file is not suitable profile or doesn't exist
    returns None.
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        ret = (libcms.cms_get_profile_name(profile),)
        ret += (libcms.cms_get_profile_copyright(profile),)
        ret += (libcms.cms_get_profile_info(profile),)
    except Exception:
        ret = ('', '', '')
    return ret
