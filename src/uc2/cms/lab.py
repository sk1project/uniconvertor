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


def linear_to_rgb(c):
    if c > 0.0031308:
        return pow(c, 1.0 / 2.4) * 1.055 - 0.055
    return c * 12.92


def lab_to_rgb(color):
    """Converts CIE-L*ab value to RGB.
    """
    L, a, b = color
    # L: 0..100
    # a:  -128..127
    # b:  -128..127
    L = L * 100.0
    a = a * 255.0 - 128.0
    b = b * 255.0 - 128.0

    # Lab -> normalized XYZ (X,Y,Z are all in 0...1)
    Y = L * (1.0 / 116.0) + 16.0 / 116.0
    X = a * (1.0 / 500.0) + Y
    Z = b * (-1.0 / 200.0) + Y

    if X > 6.0 / 29.0:
        X = X * X * X
    else:
        X = X * (108.0 / 841.0) - 432.0 / 24389.0
    if L > 8.0:
        Y = Y * Y * Y
    else:
        Y = L * (27.0 / 24389.0)
    if Z > 6.0 / 29.0:
        Z = Z * Z * Z
    else:
        Z = Z * (108.0 / 841.0) - 432.0 / 24389.0

    # normalized XYZ -> linear sRGB (in 0...1)
    R = X * (1219569.0 / 395920.0) + Y * (-608687.0 / 395920.0) + Z * (
            -107481.0 / 197960.0)
    G = X * (-80960619.0 / 87888100.0) + Y * (82435961.0 / 43944050.0) + Z * (
            3976797.0 / 87888100.0)
    B = X * (93813.0 / 1774030.0) + Y * (-180961.0 / 887015.0) + Z * (
            107481.0 / 93370.0)

    # linear sRGB -> gamma-compressed sRGB (in 0...1)
    r = round(linear_to_rgb(R), 3)
    g = round(linear_to_rgb(G), 3)
    b = round(linear_to_rgb(B), 3)
    return [r, g, b]


def xyz_to_lab(c):
    if c > 216.0 / 24389.0:
        return pow(c, 1.0 / 3.0)
    return c * (841.0 / 108.0) + (4.0 / 29.0)


def rgb_to_linear(c):
    if c > (0.0031308 * 12.92):
        return pow(c * (1.0 / 1.055) + (0.055 / 1.055), 2.4)
    return c * (1.0 / 12.92)


def rgb_to_lab(color):
    R, G, B = color

    # RGB -> linear sRGB
    R = rgb_to_linear(R)
    G = rgb_to_linear(G)
    B = rgb_to_linear(B)

    # linear sRGB -> normalized XYZ (X,Y,Z are all in 0...1)
    X = xyz_to_lab(
        R * (10135552.0 / 23359437.0) + G * (8788810.0 / 23359437.0) + B * (
                4435075.0 / 23359437.0))
    Y = xyz_to_lab(
        R * (871024.0 / 4096299.0) + G * (8788810.0 / 12288897.0) + B * (
                887015.0 / 12288897.0))
    Z = xyz_to_lab(
        R * (158368.0 / 8920923.0) + G * (8788810.0 / 80288307.0) + B * (
                70074185.0 / 80288307.0))

    # normalized XYZ -> Lab
    L = round((Y * 116.0 - 16.0) / 100.0, 3)
    a = round(((X - Y) * 500.0 + 128.0) / 255.0, 3)
    b = round(((Y - Z) * 200.0 + 128.0) / 255.0, 3)
    return [L, a, b]