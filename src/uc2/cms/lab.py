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

import typing as tp


def _linear_to_rgb(c: float) -> float:
    """Converts linear sRGB to RGB

    :param c: (float) linear sRGB value
    :return: (float) RGB value
    """
    if c > 0.0031308:
        return pow(c, 1.0 / 2.4) * 1.055 - 0.055
    return abs(c * 12.92)


def _normalize(x):
    x = 0.0 if x <= 0.0 else x
    return 1.0 if x > 1.0 else x


def lab_to_rgb(color: tp.List[float]) -> tp.List[float]:
    """Converts CIE-L*ab value list to RGB value list.

    :param color: (list) 3-member Lab color value list
    :return: (list) 3-member RGB color value list
    """
    l_, a, b = color
    # L: 0..100
    # a:  -128..127
    # b:  -128..127

    l_ = l_ * 100.0
    a = a * 255.0 - 128.0
    b = b * 255.0 - 128.0

    # Lab -> normalized XYZ (X,Y,Z are all in 0...1)
    y = l_ * (1.0 / 116.0) + 16.0 / 116.0
    x = a * (1.0 / 500.0) + y
    z = b * (-1.0 / 200.0) + y

    if x > 6.0 / 29.0:
        x = x * x * x
    else:
        x = x * (108.0 / 841.0) - 432.0 / 24389.0
    if l_ > 8.0:
        y = y * y * y
    else:
        y = l_ * (27.0 / 24389.0)
    if z > 6.0 / 29.0:
        z = z * z * z
    else:
        z = z * (108.0 / 841.0) - 432.0 / 24389.0

    # normalized XYZ -> linear sRGB (in 0...1)
    r = x * (1219569.0 / 395920.0) + y * (-608687.0 / 395920.0) + z * (-107481.0 / 197960.0)
    g = x * (-80960619.0 / 87888100.0) + y * (82435961.0 / 43944050.0) + z * (3976797.0 / 87888100.0)
    b = x * (93813.0 / 1774030.0) + y * (-180961.0 / 887015.0) + z * (107481.0 / 93370.0)
    return [_normalize(_linear_to_rgb(x)) for x in (r, g, b)]


def xyz_to_lab(c: float) -> float:
    """Converts XYZ to Lab

    :param c: (float) XYZ value
    :return: (float) Lab value
    """
    if c > 216.0 / 24389.0:
        return pow(c, 1.0 / 3.0)
    return c * (841.0 / 108.0) + (4.0 / 29.0)


def _rgb_to_linear(c: float) -> float:
    """Converts RGB to linear sRGB

    :param c: (float) RGB value
    :return: (float) linear sRGB value
    """
    if c > (0.0031308 * 12.92):
        return pow(c * (1.0 / 1.055) + (0.055 / 1.055), 2.4)
    return c * (1.0 / 12.92)


def rgb_to_lab(color: tp.List[float]) -> tp.List[float]:
    """Converts RGB value list to CIE-L*ab value list.

    :param color: (list) 3-member RGB color value list
    :return: (list) 3-member Lab color value list
    """
    r, g, b = color

    # RGB -> linear sRGB
    r = _rgb_to_linear(r)
    g = _rgb_to_linear(g)
    b = _rgb_to_linear(b)

    # linear sRGB -> normalized XYZ (X,Y,Z are all in 0...1)
    x = xyz_to_lab(r * (10135552.0 / 23359437.0) + g * (8788810.0 / 23359437.0) + b * (4435075.0 / 23359437.0))
    y = xyz_to_lab(r * (871024.0 / 4096299.0) + g * (8788810.0 / 12288897.0) + b * (887015.0 / 12288897.0))
    z = xyz_to_lab(r * (158368.0 / 8920923.0) + g * (8788810.0 / 80288307.0) + b * (70074185.0 / 80288307.0))

    # normalized XYZ -> Lab
    l_ = (y * 116.0 - 16.0) / 100.0
    a = ((x - y) * 500.0 + 128.0) / 255.0
    b = ((y - z) * 200.0 + 128.0) / 255.0
    return [_normalize(x) for x in (l_, a, b)]
