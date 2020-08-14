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

import io
import typing as tp

from . import _libcairo
import cairo
from PIL import Image

from uc2 import (uc2const, sk2const)

SURFACE = cairo.ImageSurface(cairo.FORMAT_RGB24, 1, 1)
CTX = cairo.Context(SURFACE)
DIRECT_MATRIX = cairo.Matrix()


def get_version() -> tp.Tuple[str, str]:
    """Allows retrieve cairo and pycairo version strings.

    :return: (tuple) two strings of cairo and pycairo versions
    """
    v0, v1, v2 = cairo.version_info
    return cairo.cairo_version_string(), '%d.%d.%d' % (v0, v1, v2)


def create_cpath(paths: uc2const.PathsType, cmatrix: tp.Union[cairo.Matrix, None] = None) -> cairo.Path:
    """Transforms Bezier paths into cairo path.

    :param paths: (uc2const.PathsType) Bezier paths
    :param cmatrix: (cairo.Matrix) cairo transformation matrix
    :return: (cairo.Path) cairo path
    """
    CTX.set_matrix(DIRECT_MATRIX)
    CTX.new_path()
    for path in paths:
        CTX.new_sub_path()
        start_point = path[0]
        points = path[1]
        end = path[2]
        CTX.move_to(*start_point)

        for point in points:
            if len(point) == 2:
                CTX.line_to(*point)
            else:
                p1, p2, p3 = point[:-1]
                CTX.curve_to(*(p1 + p2 + p3))
        if end == sk2const.CURVE_CLOSED:
            CTX.close_path()

    cairo_path = CTX.copy_path()
    if cmatrix is not None:
        cairo_path = apply_cmatrix(cairo_path, cmatrix)
    return cairo_path


def get_path_from_cpath(cairo_path: cairo.Path) -> uc2const.PathsType:
    """Converts cairo path into sk2 file format paths.

    :param cairo_path: (cairo.Path) incoming cairo path
    :return: (uc2const.PathsType) sk2 file format paths
    """
    return _libcairo.get_path_from_cpath(cairo_path)


def get_flattened_cpath(cairo_path: cairo.Path, tolerance: float = 0.1) -> cairo.Path:
    """Flats cairo path.

    :param cairo_path: (cairo.Path) incoming cairo path
    :param tolerance: (float) tolerance coefficient
    :return: (cairo.Path) outgoing cairo path
    """
    CTX.set_matrix(DIRECT_MATRIX)
    tlr = CTX.get_tolerance()
    CTX.set_tolerance(tolerance)
    CTX.new_path()
    CTX.append_path(cairo_path)
    result = CTX.copy_path_flat()
    CTX.set_tolerance(tlr)
    return result


def apply_cmatrix(cairo_path: cairo.Path, cmatrix: cairo.Matrix) -> cairo.Path:
    """Transforms cairo.Path by provided cairo.Matrix

    :param cairo_path: (cairo.Path) incoming cairo path
    :param cmatrix: (cairo.Matrix) cairo transformation matrix
    :return: (cairo.Path) outgoing cairo path
    """
    trafo = get_trafo_from_matrix(cmatrix)
    return apply_trafo(cairo_path, trafo)


def copy_cpath(cairo_path: cairo.Path) -> cairo.Path:
    """Creates cairo.Path copy

    :param cairo_path: (cairo.Path) incoming cairo path
    :return: (cairo.Path) outgoing cairo path
    """
    CTX.set_matrix(DIRECT_MATRIX)
    CTX.new_path()
    CTX.append_path(cairo_path)
    return CTX.copy_path()


def apply_trafo(cairo_path: cairo.Path, trafo: uc2const.TrafoType, copy: bool = False) -> cairo.Path:
    """Transforms cairo.Path by provided trafo list

    :param cairo_path: (cairo.Path) incoming cairo path
    :param trafo: (uc2const.TrafoType) transformation matrix
    :param copy: (bool) apply to copy flag
    :return: (cairo.Path) outgoing cairo path
    """
    if copy:
        cairo_path = copy_cpath(cairo_path)
    m11, m21, m12, m22, dx, dy = trafo
    _libcairo.apply_trafo(cairo_path, m11, m21, m12, m22, dx, dy)
    return cairo_path


def multiply_trafo(trafo1: uc2const.TrafoType, trafo2: uc2const.TrafoType) -> uc2const.TrafoType:
    """Multiplies provided transformation matrixes.

    :param trafo1: (uc2const.TrafoType) transformation matrix
    :param trafo2:  (uc2const.TrafoType) transformation matrix
    :return:  (uc2const.TrafoType) transformation matrix
    """
    matrix1 = get_matrix_from_trafo(trafo1)
    matrix2 = get_matrix_from_trafo(trafo2)
    matrix = matrix1.multiply(matrix2)
    return _libcairo.get_trafo(matrix)


def normalize_bbox(bbox: uc2const.BboxType) -> uc2const.BboxType:
    """Normalizes bounding box

    :param bbox: (uc2const.BboxType) incoming bbox
    :return: (uc2const.BboxType) normalized bbox
    """
    x0, y0, x1, y1 = bbox
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]


def get_cpath_bbox(cpath: cairo.Path) -> uc2const.BboxType:
    """Calcs normalized bounding box of cairo path

    :param cpath: (cairo.Path) incoming cairo path
    :return: (uc2const.BboxType) normalized bbox
    """
    CTX.set_matrix(DIRECT_MATRIX)
    CTX.new_path()
    CTX.append_path(cpath)
    return normalize_bbox(CTX.path_extents())


def _get_trafo(cmatrix: cairo.Matrix) -> uc2const.TrafoType:
    """Converts cairo matrix to trafo list

    :param cmatrix: (cairo.Matrix) cairo transformation matrix
    :return: (uc2const.TrafoType) transformation matrix
    """
    return [i for i in cmatrix]


def get_trafo_from_matrix(cmatrix: cairo.Matrix) -> uc2const.TrafoType:
    """Converts cairo matrix to trafo list using native extension

    :param cmatrix: (cairo.Matrix) cairo transformation matrix
    :return: (uc2const.TrafoType) transformation matrix
    """
    return _libcairo.get_trafo(cmatrix)


def reverse_trafo(trafo: uc2const.TrafoType) -> uc2const.TrafoType:
    """Reverses transformation matrix

    :param trafo: (uc2const.TrafoType) transformation matrix
    :return: (uc2const.TrafoType) reversed transformation matrix
    """
    return [1.0/i if i else i for i in trafo[:4]] + [-i for i in trafo[4:]]


def get_matrix_from_trafo(trafo: uc2const.TrafoType) -> cairo.Matrix:
    """Converts trafo list to cairo matrix

    :param trafo: (uc2const.TrafoType) transformation matrix
    :return: (cairo.Matrix) cairo transformation matrix
    """
    return cairo.Matrix(*trafo)


def reverse_matrix(cmatrix: cairo.Matrix) -> cairo.Matrix:
    """Reverses cairo transformation matrix

    :param cmatrix: (cairo.Matrix) cairo transformation matrix
    :return: (cairo.Matrix) reversed cairo transformation matrix
    """
    return get_matrix_from_trafo(reverse_trafo(get_trafo_from_matrix(cmatrix)))


def invert_trafo(trafo: uc2const.TrafoType) -> uc2const.TrafoType:
    """Inverts transformation matrix using native extension

    :param trafo: (uc2const.TrafoType) transformation matrix
    :return: (uc2const.TrafoType) reversed transformation matrix
    """
    cmatrix = get_matrix_from_trafo(trafo)
    cmatrix.invert()
    return get_trafo_from_matrix(cmatrix)


def apply_trafo_to_point(point: uc2const.PointType, trafo: uc2const.TrafoType) -> uc2const.PointType:
    """Transform point by transformation matrix

    :param point: (uc2const.PointType) incoming point
    :param trafo: (uc2const.TrafoType) transformation matrix
    :return: (uc2const.PointType) transformed point
    """
    x0, y0 = point
    m11, m21, m12, m22, dx, dy = trafo
    x1 = m11 * x0 + m12 * y0 + dx
    y1 = m21 * x0 + m22 * y0 + dy
    return [x1, y1]


def apply_trafo_to_bbox(bbox: uc2const.BboxType, trafo: uc2const.TrafoType) -> uc2const.BboxType:
    """Transforms bounding box by transformation matrix

    :param bbox: (uc2const.BboxType) incoming bounding box
    :param trafo: (uc2const.TrafoType) transformation matrix
    :return: (uc2const.BboxType) transformed bounding box
    """
    x0, y0, x1, y1 = bbox
    start = apply_trafo_to_point([x0, y0], trafo)
    end = apply_trafo_to_point([x1, y1], trafo)
    return start + end


def convert_bbox_to_cpath(bbox: uc2const.BboxType) -> cairo.Path:
    """Converts bbox into cairo path

    :param bbox: (uc2const.BboxType) incoming bounding box
    :return: (cairo.Path) outgoing cairo path
    """
    x0, y0, x1, y1 = bbox
    CTX.set_matrix(DIRECT_MATRIX)
    CTX.new_path()
    CTX.move_to(x0, y0)
    CTX.line_to(x1, y0)
    CTX.line_to(x1, y1)
    CTX.line_to(x0, y1)
    CTX.line_to(x0, y0)
    CTX.close_path()
    return CTX.copy_path()


def get_surface_pixel(surface: cairo.ImageSurface) -> uc2const.PixelType:
    """Returns first pixel value of provided image surface

    :param surface: (cairo.ImageSurface) testing image surface
    :return: (uc2const.PixelType) BGR pixel color value [b,g,r]
    """
    return _libcairo.get_pixel(surface)


def check_surface_whiteness(surface: cairo.ImageSurface) -> bool:
    """Checks first pixel value is white in provided image surface

    :param surface: (cairo.ImageSurface) testing image surface
    :return: (bool) whiteness check result
    """
    return _libcairo.get_pixel(surface) == [255, 255, 255]


def image_to_surface_n(image: Image) -> cairo.ImageSurface:
    """Creates cairo ImageSurface from Pillow image

    :param image: (PIL.Image) incoming Pillow image
    :return: (cairo.ImageSurface) created image surface
    """
    png_stream = io.BytesIO()
    image.save(png_stream, format='PNG')
    png_stream.seek(0)
    return cairo.ImageSurface.create_from_png(png_stream)


def image_to_surface(image: Image) -> cairo.ImageSurface:
    """Creates cairo ImageSurface from Pillow image

    :param image: (PIL.Image) incoming Pillow image
    :return: (cairo.ImageSurface) created image surface
    """
    if image.mode not in (uc2const.IMAGE_RGB, uc2const.IMAGE_RGBA):
        image = image.convert(uc2const.IMAGE_RGBA if image.mode.endswith('A')
                              else uc2const.IMAGE_RGB)
    surface = None
    w, h = image.size
    image.load()
    if image.mode == uc2const.IMAGE_RGBA:
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        _libcairo.draw_rgba_image(surface, image.im, w, h)
    elif image.mode == uc2const.IMAGE_RGB:
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
        _libcairo.draw_rgb_image(surface, image.im, w, h)
    return surface
