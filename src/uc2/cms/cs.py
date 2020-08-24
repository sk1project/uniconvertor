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


def rgb_to_hexcolor(color_values: tp.List[float]) -> str:
    """Converts list of RGB float values to hexadecimal color string.
    For example: [1.0, 0.0, 1.0] => #ff00ff

    :param color_values: (list) 3-member RGB color value list
    :return: (str) hexadecimal color string
    """
    return '#%02x%02x%02x' % tuple(int(round(255 * x)) for x in color_values)


def rgba_to_hexcolor(color_values: tp.List[float]) -> str:
    """Converts list of RGBA float values to hex color string.
    For example: [1.0, 0.0, 1.0, 1.0] => #ff00ffff

    :param color_values: (list) 4-member RGBA color value list
    :return: (str) hexadecimal color string
    """
    return '#%02x%02x%02x%02x' % tuple(int(round(255 * x)) for x in color_values)


def cmyk_to_hexcolor(color_values: tp.List[float]) -> str:
    """Converts list of CMYK float values to hex color string.
    For example: [1.0, 0.0, 1.0, 1.0] => #ff00ffff

    :param color_values: (list) 4-member CMYK color value list
    :return: (str) hexadecimal color string
    """
    return rgba_to_hexcolor(color_values)


def hexcolor_to_rgb(hexcolor: str) -> tp.List[float]:
    """Converts hexadecimal color string as a list of float values.
    For example: #ff00ff => [1.0, 0.0, 1.0]

    :param hexcolor: (str) hexadecimal color string
    :return: (list) 3-member RGB color value list
    """
    if not hexcolor.startswith('#'):
        hexcolor = '#%s' % hexcolor
    if len(hexcolor) == 4:
        vals = (hexcolor[1] * 2, hexcolor[2] * 2, hexcolor[3] * 2)
    else:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_rgba(hexcolor: str) -> tp.List[float]:
    """Converts hexadecimal color string as a list of float values.
    For example: #ff00ffff => [1.0, 0.0, 1.0, 1.0]

    :param hexcolor: (str) hexadecimal color string
    :return: (list) 4-member RGBA color value list
    """
    vals = ('00', '00', '00', 'ff')
    if len(hexcolor) == 7:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:], 'ff')
    elif len(hexcolor) == 9:
        vals = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:7], hexcolor[7:])
    return [int(x, 0x10) / 255.0 for x in vals]


def hexcolor_to_cmyk(hexcolor: str) -> tp.List[float]:
    """Converts hexadecimal color string as a list of float values.
    For example: #ff00ffff => [1.0, 0.0, 1.0, 1.0]

    :param hexcolor: (str) hexadecimal color string
    :return: (list) 4-member CMYK color value list
    """
    return hexcolor_to_rgba(hexcolor)


def gdk_hexcolor_to_rgb(hexcolor: str) -> tp.List[float]:
    """ Converts hex color string as a list of float values.
    For example: #ffff0000ffff => [1.0, 0.0, 1.0]

    :param hexcolor: (str) hexadecimal color string
    :return: (list) 3-member RGB color value list
    """
    vals = (hexcolor[1:5], hexcolor[5:9], hexcolor[9:])
    return [int(x, 0x10) / 65535.0 for x in vals]


def rgb_to_gdk_hexcolor(color_values: tp.List[float]) -> str:
    """Converts list of float values into hex color string.
    For example: [1.0, 0.0, 1.0] => #ffff0000ffff

    :param color_values: (list) 3-member list of float values
    :return: (str) hexadecimal color string
    """
    return '#%04x%04x%04x' % tuple(int(round(x * 65535.0)) for x in color_values)


def cmyk_to_rgb(color_values: tp.List[float]) -> tp.List[float]:
    """Converts list of CMYK values to RGB.

    :param color_values: (list) 4-member CMYK color value list
    :return: (list) 3-member RGB color value list
    """
    return [round(1.0 - min(1.0, x + color_values[3]), 3) for x in color_values[:3]]


def rgb_to_cmyk(color_values: tp.List[float]) -> tp.List[float]:
    """Converts list of RGB values to CMYK.

    :param color_values: (list) 3-member RGB color value list
    :return: (list) 4-member CMYK color value list
    """
    if color_values == [0.0, 0.0, 0.0]:
        return [0.0, 0.0, 0.0, 1.0]
    r, g, b = color_values
    c = 1.0 - r
    m = 1.0 - g
    y = 1.0 - b

    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return [c, m, y, k]


def gray_to_cmyk(color_values: tp.List[float]) -> tp.List[float]:
    """Converts Gray value to CMYK.

    :param color_values: (list) 1-member Gray color value list
    :return: (list) 4-member CMYK color value list
    """
    k = 1.0 - color_values[0]
    return [0.0] * 3 + [k]


def gray_to_rgb(color_values: tp.List[float]) -> tp.List[float]:
    """Converts Gray value to RGB.

    :param color_values: (list) 1-member Gray color value list
    :return: (list) 3-member RGB color value list
    """
    return color_values * 3


def rgb_to_gray(color_values: tp.List[float]) -> tp.List[float]:
    """Converts RGB color values to Gray color value.

    :param color_values: (list) 3-member RGB color value list
    :return: (list) 1-member Gray color value list
    """
    return [sum(color_values) / 3.0]


TRANSFORMS: tp.Dict[str, tp.Callable[[tp.List[float]], tp.List[float]]] = {
    uc2const.COLOR_RGB + uc2const.COLOR_CMYK: rgb_to_cmyk,
    uc2const.COLOR_RGB + uc2const.COLOR_GRAY: rgb_to_gray,
    uc2const.COLOR_RGB + uc2const.COLOR_LAB: rgb_to_lab,

    uc2const.COLOR_CMYK + uc2const.COLOR_RGB: cmyk_to_rgb,
    uc2const.COLOR_CMYK + uc2const.COLOR_GRAY: lambda x: rgb_to_gray(cmyk_to_rgb(x)),
    uc2const.COLOR_CMYK + uc2const.COLOR_LAB: lambda x: rgb_to_lab(cmyk_to_rgb(x)),

    uc2const.COLOR_GRAY + uc2const.COLOR_RGB: gray_to_rgb,
    uc2const.COLOR_GRAY + uc2const.COLOR_CMYK: gray_to_cmyk,
    uc2const.COLOR_GRAY + uc2const.COLOR_LAB: lambda x: rgb_to_lab(gray_to_rgb(x)),

    uc2const.COLOR_LAB + uc2const.COLOR_RGB: lab_to_rgb,
    uc2const.COLOR_LAB + uc2const.COLOR_CMYK: lambda x: rgb_to_cmyk(lab_to_rgb(x)),
    uc2const.COLOR_LAB + uc2const.COLOR_GRAY: lambda x: rgb_to_gray(lab_to_rgb(x)),
}


def do_simple_transform(color_values: tp.List[float], cs_in: str, cs_out: str) -> tp.List[float]:
    """Emulates color management library transformation.
    Transforms color values from one color space to another.

    :param color_values: (list) incoming color values
    :param cs_in: (str) incoming color space
    :param cs_out: (str) outgoing color space
    :return: (list) outgoing color values
    """
    return TRANSFORMS.get(cs_in + cs_out, copy.copy)(color_values)


def colorb(color: tp.Optional[uc2const.ColorType] = None, use_cmyk: bool = False) -> tp.List[int]:
    """Emulates COLORB object from python-lcms.
    Actually function returns regular 4-member list.

    :param color: (uc2const.ColorType) incoming color values
    :param use_cmyk: (bool) flag to use CMYK values for SPOT colors
    :return: (list) 4-member COLORB list of integers
    """
    if not color:
        return [0, 0, 0, 0]

    values = color[1]
    if color[0] == uc2const.COLOR_SPOT:
        values = values[1] if use_cmyk else values[0]

    result = val_255(values)
    return result + [0] * (4 - len(result))


def decode_colorb(colorb_list: tp.List[int], cs: str) -> tp.List[float]:
    """Decodes COLORB list into generic color values.

    :param colorb_list: (list) incoming COLORB list
    :param cs: (str) incoming color space
    :return: (list) color values list
    """
    if cs == uc2const.COLOR_CMYK:
        values = colorb_list
    elif cs == uc2const.COLOR_GRAY:
        values = colorb_list[:1]
    else:
        values = colorb_list[:3]

    return val_255_to_dec(values)


def get_registration_black() -> uc2const.ColorType:
    """Returns newly created Registration color object

    :return: (uc2const.ColorType) registration color
    """
    return [uc2const.COLOR_SPOT, [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], 1.0, uc2const.COLOR_REG]


def color_to_spot(color: tp.Union[uc2const.ColorType, None, tp.List] = None) -> uc2const.ColorType:
    """Returns SPOT color created using provided color

    :param color: (uc2const.ColorType) original color
    :return: (uc2const.ColorType) new SPOT color
    """
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


def verbose_color(color: tp.Union[uc2const.ColorType, tp.List, None]) -> str:
    """Returns pretty color description

    :param color: (uc2const.ColorType) incoming color
    :return: (str) color description
    """
    if not color:
        return 'No color'
    cs = color[0]
    color_values = color[1]
    alpha = (color[2],) if color[2] < 1.0 else None
    if cs == uc2const.COLOR_CMYK:
        ret = 'C-%d%% M-%d%% Y-%d%% K-%d%%' % tuple(val_100(color_values))
        ret += ' A-%d%%' % val_100(alpha)[0] if alpha else ''
    elif cs == uc2const.COLOR_RGB:
        ret = 'R-%d G-%d B-%d' % tuple(val_255(color_values))
        ret += ' A-%d' % val_255(alpha)[0] if alpha else ''
    elif cs == uc2const.COLOR_GRAY:
        ret = 'Gray-%d' % val_255(color_values)[0]
        ret += ' Alpha-%d' % val_255(alpha)[0] if alpha else ''
    elif cs == uc2const.COLOR_LAB:
        l_, a, b = color_values
        l_ = l_ * 100.0
        a = a * 255.0 - 128.0
        b = b * 255.0 - 128.0
        ret = 'L %d a %d b %d' % (l_, a, b)
        ret += ' Alpha-%d' % val_255(alpha)[0] if alpha else ''
    elif cs == uc2const.COLOR_SPOT:
        ret = color[3]
    else:
        return '???'

    return ret


def get_profile_name(filepath: str) -> tp.Optional[str]:
    """Returns profile name. If file is not suitable profile
    or doesn't exist returns None.

    :param filepath: (str) path to profile
    :return: (str|None) profile name or None
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        return libcms.cms_get_profile_name(profile)
    except Exception:
        pass


def get_profile_info(filepath: str) -> tp.Optional[str]:
    """Returns profile info. If file is not suitable profile
    or doesn't exist returns None.

    :param filepath: (str) path to profile
    :return: (str|None) profile info or None
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        return libcms.cms_get_profile_info(profile)
    except Exception:
        pass


def get_profile_descr(filepath: str) -> tp.Tuple[str, str, str]:
    """Returns profile description tuple (name, copyright, info).
    If file is not suitable profile or doesn't exist returns None.

    :param filepath: (str) path to profile
    :return: (tuple) profile name, copyright and info
    """
    # noinspection PyBroadException
    try:
        profile = libcms.cms_open_profile_from_file(filepath)
        return (libcms.cms_get_profile_name(profile),
                libcms.cms_get_profile_copyright(profile),
                libcms.cms_get_profile_info(profile))
    except Exception:
        return '', '', ''
