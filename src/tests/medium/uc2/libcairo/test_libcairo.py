import cairo
import re
from PIL import Image
from unittest import mock

from uc2 import (libcairo, uc2const, sk2const)

PATHS = [[[0.0, 0.0], [[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]], sk2const.CURVE_CLOSED]]
OPEN_PATHS = [[[0.0, 0.0], [[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]], sk2const.CURVE_OPENED]]


def test_get_version():
    versions = libcairo.get_version()
    assert len(versions) == 2
    cairo_ver, pycairo_ver = versions
    assert isinstance(cairo_ver, str)
    assert isinstance(pycairo_ver, str)
    pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    assert re.match(pattern, cairo_ver)
    assert re.match(pattern, pycairo_ver)


def test_create_cpath():
    cpath = libcairo.create_cpath(PATHS)
    assert isinstance(cpath, cairo.Path)
    assert len([item for item in cpath]) == 6


@mock.patch('uc2.libcairo.apply_cmatrix')
@mock.patch('uc2.libcairo.CTX')
def test_create_cpath_closed(ctx_mock, apply_cmatrix_mock):
    libcairo.create_cpath(PATHS)
    ctx_mock.new_path.assert_called_once()
    ctx_mock.new_sub_path.assert_called_once()
    ctx_mock.move_to.assert_called_once()
    assert ctx_mock.line_to.called
    assert not ctx_mock.curve_to.called
    ctx_mock.close_path.assert_called_once()
    ctx_mock.copy_path.assert_called_once()
    assert not apply_cmatrix_mock.called

    ctx_mock.reset_mock()
    apply_cmatrix_mock.reset_mock()

    libcairo.create_cpath(OPEN_PATHS)
    ctx_mock.new_path.assert_called_once()
    ctx_mock.new_sub_path.assert_called_once()
    ctx_mock.move_to.assert_called_once()
    assert ctx_mock.line_to.called
    assert not ctx_mock.curve_to.called
    assert not ctx_mock.close_path.called
    ctx_mock.copy_path.assert_called_once()
    assert not apply_cmatrix_mock.called

    ctx_mock.reset_mock()
    apply_cmatrix_mock.reset_mock()

    libcairo.create_cpath(PATHS, cairo.Matrix())
    apply_cmatrix_mock.assert_called_once()


def test_get_path_from_cpath():
    cpath = libcairo.create_cpath(PATHS)
    paths = libcairo.get_path_from_cpath(cpath)
    assert isinstance(paths, list)
    assert len(paths) == 2
    assert len(paths[0]) == 3


def test_get_flattened_path():
    cpath = libcairo.create_cpath(PATHS)
    cpath_flattened = libcairo.get_flattened_cpath(cpath)
    assert isinstance(cpath_flattened, cairo.Path)
    assert len([item for item in cpath_flattened]) == 6


@mock.patch('uc2.libcairo.CTX')
def test_get_flattened_cpath_mocked(ctx_mock):
    cpath = libcairo.create_cpath(PATHS)
    ctx_mock.reset_mock()
    libcairo.get_flattened_cpath(cpath)

    ctx_mock.set_matrix.assert_called_once()
    assert ctx_mock.set_tolerance.called
    ctx_mock.new_path.assert_called_once()
    ctx_mock.append_path.assert_called_with(cpath)
    ctx_mock.copy_path_flat.assert_called_once()


def test_apply_cmatrix():
    cpath = libcairo.create_cpath(PATHS)
    cmatrix = cairo.Matrix()
    cpath_transformed = libcairo.apply_cmatrix(cpath, cmatrix)
    assert isinstance(cpath_transformed, cairo.Path)
    assert len([item for item in cpath_transformed]) == 6


@mock.patch('uc2.libcairo.apply_trafo')
@mock.patch('uc2.libcairo.get_trafo_from_matrix')
def test_apply_cmatrix_mocked(get_trafo_from_matrix_mock, apply_trafo_mock):
    cpath = libcairo.create_cpath(PATHS)
    cmatrix = cairo.Matrix()
    get_trafo_from_matrix_mock.return_value = sk2const.NORMAL_TRAFO
    libcairo.apply_cmatrix(cpath, cmatrix)

    get_trafo_from_matrix_mock.assert_called_with(cmatrix)
    apply_trafo_mock.assert_called_with(cpath, sk2const.NORMAL_TRAFO)


def test_copy_cpath():
    cpath = libcairo.create_cpath(PATHS)
    cpath2 = libcairo.copy_cpath(cpath)
    assert isinstance(cpath2, cairo.Path)
    assert not cpath == cpath2


@mock.patch('uc2.libcairo.CTX')
def test_copy_cpath_mocked(ctx_mock):
    cpath = libcairo.create_cpath(PATHS)
    ctx_mock.reset_mock()
    libcairo.copy_cpath(cpath)

    ctx_mock.set_matrix.assert_called_with(libcairo.DIRECT_MATRIX)
    ctx_mock.new_path.assert_called_once()
    ctx_mock.append_path.assert_called_with(cpath)
    ctx_mock.copy_path.assert_called_once()


def test_apply_trafo():
    cpath = libcairo.create_cpath(PATHS)
    trafo = sk2const.NORMAL_TRAFO
    cpath2 = libcairo.apply_trafo(cpath, trafo)
    assert isinstance(cpath2, cairo.Path)
    assert cpath == cpath2
    cpath2 = libcairo.apply_trafo(cpath, trafo, True)
    assert isinstance(cpath2, cairo.Path)
    assert not cpath == cpath2


@mock.patch('uc2.libcairo.copy_cpath')
@mock.patch('uc2.libcairo._libcairo')
def test_apply_trafo_mocked(_libcairo_mock, copy_cpath_mock):
    cpath = libcairo.create_cpath(PATHS)
    trafo = sk2const.NORMAL_TRAFO
    libcairo.apply_trafo(cpath, trafo)
    _libcairo_mock.apply_trafo.assert_called_with(cpath, *trafo)
    assert not copy_cpath_mock.called

    _libcairo_mock.reset_mock()
    copy_cpath_mock.reset_mock()

    libcairo.apply_trafo(cpath, trafo, True)
    _libcairo_mock.apply_trafo.assert_called_once()
    copy_cpath_mock.assert_called_with(cpath)


def test_multiply_trafo():
    trafo1 = [2.0] + sk2const.NORMAL_TRAFO[1:]
    trafo2 = [] + sk2const.NORMAL_TRAFO
    trafo = libcairo.multiply_trafo(trafo1, trafo2)
    assert len(trafo) == 6
    assert trafo == [2.0, 0.0, 0.0, 1.0, 0.0, 0.0]


def test_normalize_bbox():
    bbox1 = [4.0, 0.0, 1.0, -5.0]
    bbox = libcairo.normalize_bbox(bbox1)
    assert len(bbox) == 4
    assert bbox == [1.0, -5.0, 4.0, 0.0]


def test_get_cpath_bbox():
    cpath = libcairo.create_cpath(PATHS)
    bbox = libcairo.get_cpath_bbox(cpath)
    assert len(bbox) == 4
    assert bbox == [0.0, 0.0, 1.0, 1.0]


def test__get_trafo():
    trafo = libcairo._get_trafo(cairo.Matrix())
    assert trafo == sk2const.NORMAL_TRAFO


def test_get_trafo_from_matrix():
    trafo = libcairo.get_trafo_from_matrix(cairo.Matrix())
    assert trafo == sk2const.NORMAL_TRAFO


def test_reverse_trafo():
    trafo = libcairo.reverse_trafo([2.0, 0.0, 0.0, 2.0, 1.0, 2.0])
    assert trafo == [0.5, 0.0, 0.0, 0.5, -1.0, -2.0]


def test_get_matrix_from_trafo():
    matrix = libcairo.get_matrix_from_trafo(sk2const.NORMAL_TRAFO)
    assert isinstance(matrix, cairo.Matrix)
    assert libcairo.get_trafo_from_matrix(matrix) == sk2const.NORMAL_TRAFO


def test_reverse_matrix():
    matrix = libcairo.reverse_matrix(cairo.Matrix(2.0, 0.0, 0.0, 2.0, 1.0, 2.0))
    assert libcairo.get_trafo_from_matrix(matrix) == [0.5, 0.0, 0.0, 0.5, -1.0, -2.0]


def test_invert_trafo():
    trafo = libcairo.invert_trafo([2.0, 0.0, 0.0, 2.0, 1.0, 2.0])
    assert trafo == [0.5, 0.0, 0.0, 0.5, -0.5, -1.0]


def test_apply_trafo_to_point():
    point = [1.0, 1.0]
    trafo = [2.0, 0.0, 0.0, 2.0, 5.0, 2.0]
    res = libcairo.apply_trafo_to_point(point, trafo)
    assert len(res) == 2
    assert res == [7.0, 4.0]


def test_apply_trafo_to_bbox():
    bbox = [0.0, 0.0, 1.0, 1.0]
    trafo = [2.0, 0.0, 0.0, 2.0, 5.0, 2.0]
    res = libcairo.apply_trafo_to_bbox(bbox, trafo)
    assert len(res) == 4
    assert res == [5.0, 2.0, 7.0, 4.0]


def test_convert_bbox_to_cpath():
    bbox = [0.0, 0.0, 1.0, 1.0]
    cpath = libcairo.convert_bbox_to_cpath(bbox)
    assert isinstance(cpath, cairo.Path)
    assert len([item for item in cpath]) == 6


def test_get_surface_pixel():
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 1, 1)
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    assert libcairo.get_surface_pixel(surface) == [0, 0, 0]
    ctx.set_source_rgb(255, 255, 0)
    ctx.paint()
    assert libcairo.get_surface_pixel(surface) == [0, 255, 255]


def test_check_surface_whiteness():
    surface = cairo.ImageSurface(cairo.FORMAT_RGB24, 1, 1)
    ctx = cairo.Context(surface)
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()
    assert not libcairo.check_surface_whiteness(surface)
    ctx.set_source_rgb(255, 255, 255)
    ctx.paint()
    assert libcairo.check_surface_whiteness(surface)


def test_image_to_surface_n():
    img = Image.new(uc2const.IMAGE_RGB, (10, 10))
    sf = libcairo.image_to_surface_n(img)
    assert isinstance(sf, cairo.ImageSurface)
    assert sf.get_format() == cairo.Format.RGB24
    assert sf.get_width() == 10
    assert sf.get_height() == 10


def test_image_to_surface():
    img = Image.new(uc2const.IMAGE_RGB, (10, 10))
    sf = libcairo.image_to_surface(img)
    assert isinstance(sf, cairo.ImageSurface)
    assert sf.get_format() == cairo.Format.RGB24
    assert sf.get_width() == 10
    assert sf.get_height() == 10
