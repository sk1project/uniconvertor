#
#  Copyright (C) 2016-2020 by Ihor E. Novikov
#  Copyright (C) 2020 by Krzysztof Broński
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

from copy import deepcopy
import typing as tp
import os

import cairo

from uc2 import uc2const
from . import _libpango
from .markup import apply_markup, apply_glyph_markup

PANGO_UNITS = 1024

SURFACE = cairo.ImageSurface(cairo.FORMAT_RGB24, 1, 1)
CTX = cairo.Context(SURFACE)
DIRECT_MATRIX = cairo.Matrix()

PANGO_MATRIX = cairo.Matrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0)
PANGO_LAYOUT = _libpango.create_layout(CTX)
NONPRINTING_CHARS = ' \n\t '


def get_version() -> str:
    """Returns Pango version like '1.2.3' string

    :return: (str) version string
    """
    return _libpango.get_version()


# --- Glyph caching

GLYPH_CACHE = {}


def get_glyph_cache(font_name: str, char: str) -> tp.Optional[uc2const.PathsType]:
    """Returns cached glyph paths

    :param font_name: (str) font name
    :param char: (str) character
    :return: (uc2const.PathsType) glyph paths
    """
    if font_name in GLYPH_CACHE and char in GLYPH_CACHE[font_name]:
        return deepcopy(GLYPH_CACHE[font_name][char])


def set_glyph_cache(font_name: str, char: str, glyph: uc2const.PathsType):
    """Sets cached glyph paths

    :param font_name: (str) font name
    :param char: (str) character
    :param glyph: (uc2const.PathsType) glyph paths
    """
    GLYPH_CACHE[font_name] = GLYPH_CACHE.get(font_name, {})
    GLYPH_CACHE[font_name][char] = deepcopy(glyph)


# --- Pango context functionality

def create_layout(ctx: cairo.Context = CTX) -> uc2const.PyCapsule:
    """Creates Pango layout

    :param ctx: (cairo.Context|None) Cairo context
    :return: (PyCapsule) Pango layout
    """
    return _libpango.create_layout(ctx)


def get_font_description(text_style: list, check_nt: bool = False) -> uc2const.PyCapsule:
    """Creates Pango font description

    :param text_style: (list) text style list
    :param check_nt: (bool) flag to check MSW platform
    :return: (PyCapsule) Pango font description
    """
    font_size = text_style[2] * 10.0 if check_nt and os.name == 'nt' else text_style[2]
    fnt_descr = f'{text_style[0]}, {text_style[1]} {str(font_size)}'
    return _libpango.create_font_description(fnt_descr)


def set_layout(text: str, width: int, text_style: list, markup: tp.Optional[list] = None,
               layout: uc2const.PyCapsule = PANGO_LAYOUT) -> None:
    """Sets layout markup

    :param text: (str) text string
    :param width: (int) text block width (-1 width is not defined)
    :param text_style: (list) text style list
    :param markup: (list|None) markup description list
    :param layout: (PyCapsule) Pango layout
    """
    width *= PANGO_UNITS if not width == -1 else 1
    _libpango.set_layout_width(layout, width)
    fnt_descr = get_font_description(text_style)
    _libpango.set_layout_font_description(layout, fnt_descr)
    _libpango.set_layout_alignment(layout, text_style[3])
    markuped_text = apply_markup(text, markup)
    _libpango.set_layout_markup(layout, markuped_text)


def set_glyph_layout(text: str, width: int, text_style: list, markup: tp.Optional[list] = None,
                     text_range: tp.Optional[list] = None, check_nt: bool = False,
                     layout: uc2const.PyCapsule = PANGO_LAYOUT) -> float:
    """Sets glyph layout markup

    :param text: (str) text string
    :param width: (int) text block width (-1 width is not defined)
    :param text_style: (list) text style list
    :param markup: (list|None) markup description list
    :param text_range: (list|None)
    :param check_nt: (bool) MSW platform check flag
    :param layout: (PyCapsule) Pango layout
    """
    text_range = text_range or []
    width *= PANGO_UNITS if not width == -1 else 1
    _libpango.set_layout_width(layout, width)
    fnt_descr = get_font_description(text_style, check_nt)
    _libpango.set_layout_font_description(layout, fnt_descr)
    _libpango.set_layout_alignment(layout, text_style[3])
    markuped_text, vpos = apply_glyph_markup(text, text_range, markup, check_nt)
    _libpango.set_layout_markup(layout, markuped_text)
    return vpos


def layout_path(ctx: cairo.Context = CTX, layout: uc2const.PyCapsule = PANGO_LAYOUT) -> None:
    """Layouts paths on cairo context

    :param ctx: (cairo.Context) The context on which to draw
    :param layout: (PyCapsule) Pango source layout
    """
    _libpango.layout_path(ctx, layout)


def get_line_positions(layout: uc2const.PyCapsule = PANGO_LAYOUT) -> tp.Tuple[float, ...]:
    """Returns line positions

    :param layout: (PyCapsule) Pango source layout
    :return: (tuple) line positions
    """
    return _libpango.get_layout_line_positions(layout)


def get_char_positions(size: int, layout: uc2const.PyCapsule = PANGO_LAYOUT
                       ) -> tp.Tuple[tp.Tuple[float, float, float, float, float], ...]:
    """Returns char positions

    :param size: number of characters in text layout
    :param layout: (PyCapsule) Pango source layout
    :return: (tuple) char positions
    """
    return _libpango.get_layout_char_positions(layout, size)


def get_cluster_positions(size: int, layout: uc2const.PyCapsule = PANGO_LAYOUT
                          ) -> tp.Tuple[tp.List[float], tp.List[float], tp.List[float], bool, bool]:
    """Returns cluster positions

    :param size: number of characters in text layout
    :param layout: (PyCapsule) Pango source layout
    :return: (tuple) cluster positions
    """
    return _libpango.get_layout_cluster_positions(layout, size)


def get_layout_size(layout: uc2const.PyCapsule = PANGO_LAYOUT) -> tp.Tuple[int, int]:
    """Returns text layout size

    :param layout: (PyCapsule) Pango source layout
    :return: (tuple) text layout size
    """
    return _libpango.get_layout_pixel_size(layout)


def get_layout_bbox(layout: uc2const.PyCapsule = PANGO_LAYOUT) -> tp.List[float]:
    """Returns text layout size

    :param layout: (PyCapsule) Pango source layout
    :return: (list) text layout bbox
    """
    w, h = get_layout_size(layout)
    return [0.0, 0.0, float(w), float(-h)]
