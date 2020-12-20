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

import cairo
import html
import string
import typing as tp

from uc2 import uc2const
from . import _libpango
from .core import PANGO_LAYOUT

FAMILIES_LIST = []
FAMILIES_DICT = {}


def bbox_size(bbox: uc2const.ScreenBboxType) -> uc2const.SizeType:
    """Returns bounding box size

    :param bbox: (uc2const.ScreenBboxType) bounding box
    :return: (uc2const.SizeType) bounding box size
    """
    x0, y0, x1, y1 = bbox
    w = abs(x1 - x0)
    h = abs(y1 - y0)
    return w, h


def update_fonts(do_update: bool = True) -> None:
    """Updates font families list and font face dict

    :param do_update: (bool) update flag
    """
    if do_update:
        FAMILIES_LIST[:] = []
        FAMILIES_DICT.clear()
        font_map = _libpango.get_fontmap()
        for item in font_map:
            font_name = item[0]
            font_faces = item[1]
            if font_faces:
                FAMILIES_LIST.append(font_name)
                FAMILIES_DICT[font_name] = list(font_faces)
        FAMILIES_LIST.sort()


def get_fonts() -> tp.Tuple[tp.List[str], tp.Dict[str, tp.List[str]]]:
    """Returns actual font families list and font face dict.
    Updates them if needed.

    :return: (tuple) actual font families list and font face dict
    """
    update_fonts(do_update=not FAMILIES_LIST)
    return FAMILIES_LIST, FAMILIES_DICT


def find_font_family(family: str = None) -> tp.Tuple[str, tp.List[str]]:
    """Returns font family name and list of font faces for
    provided font family. If family is not found, uses
    fallback 'Sans' family.

    :param family: (str) font family name
    :return: (tuple) font family name and list of font faces
    """
    update_fonts(do_update=not FAMILIES_LIST)
    if not family or family not in FAMILIES_LIST:
        # TODO: here should be substitution staff
        if string.capwords(family) in FAMILIES_LIST:
            family = string.capwords(family)
        elif string.capwords(family.lower()) in FAMILIES_LIST:
            family = string.capwords(family.lower())
        else:
            family = 'Sans'
    return family, FAMILIES_DICT[family]


def find_font_and_face(family: str = None) -> tp.Tuple[str, str]:
    """Returns font family name and normal font face for
    provided font family. If family is not found, uses
    fallback 'Sans' family. tries to find 'Regular' or 'Normal' face.
    If not returns first face name.

    :param family: (str) font family name
    :return: (tuple) font family name and normal font face
    """
    family, faces = find_font_family(family)
    a, b = 'Regular', 'Normal'
    font_face = a if a in faces else b if b in faces else faces[0]
    return family, font_face


# ---Font sampling

def _set_sample_layout(layout: uc2const.PyCapsule, text: str, family: str, fontsize: tp.Union[float, int]) -> None:
    """Helper function. Sets text on Pango layout.

    :param layout: (PyCapsule) Pango layout
    :param text: (str) text string
    :param family: (str) font family name
    :param fontsize: (float|int) font size
    """
    _libpango.set_layout_width(layout, -1)
    fnt_descr = family + ', ' + str(fontsize)
    fnt_descr = _libpango.create_font_description(fnt_descr)
    _libpango.set_layout_font_description(layout, fnt_descr)
    markup = html.escape(text)
    _libpango.set_layout_markup(layout, markup)


def get_sample_size(text: str, family: str, fontsize: tp.Union[float, int]) -> tp.Tuple[int, int]:
    """Calcs sample text size in pixels (w,h)

    :param text: (str) sample text
    :param family: (str) font family name
    :param fontsize: (float|int) font
    :return: (tuple) sample size in pixels
    """
    _set_sample_layout(PANGO_LAYOUT, text, family, fontsize)
    return _libpango.get_layout_pixel_size(PANGO_LAYOUT)


def render_sample(ctx: cairo.Context, text: str, family: str, fontsize: tp.Union[float, int]) -> None:
    """Renders sample text on provided Cairo context

    :param ctx: (cairo.Context) cairo context
    :param text: (str) sample text
    :param family: (str) font family name
    :param fontsize: (float|int) font size
    """
    ctx.new_path()
    ctx.move_to(0, 0)
    layout = _libpango.create_layout(ctx)
    _set_sample_layout(layout, text, family, fontsize)
    _libpango.layout_path(ctx, layout)

# ---Font sampling end
