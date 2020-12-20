import cairo

from uc2.libpango import fonts


def test_bbox_size():
    assert fonts.bbox_size((0.0, 0.0, 2.0, 3.0)) == (2.0, 3.0)
    assert fonts.bbox_size((0.0, 0.0, -2.0, -3.0)) == (2.0, 3.0)


def test_update_fonts():
    assert 'Sans' not in fonts.FAMILIES_LIST
    assert 'Sans' not in fonts.FAMILIES_DICT
    fonts.update_fonts()
    assert 'Sans' in fonts.FAMILIES_LIST
    assert 'Sans' in fonts.FAMILIES_DICT


def test_get_fonts():
    families_list, families_dict = fonts.get_fonts()
    assert isinstance(families_list, list)
    assert isinstance(families_dict, dict)
    assert 'Sans' in families_list
    assert 'Sans' in families_dict


def test_find_font_family():
    family, faces = fonts.find_font_family('Sans')
    assert family == 'Sans'
    assert set(faces) == {'Regular', 'Bold', 'Italic', 'Bold Italic'}
    family, faces = fonts.find_font_family('UnknownFont')
    assert family == 'Sans'
    assert set(faces) == {'Regular', 'Bold', 'Italic', 'Bold Italic'}


def test_find_font_and_face():
    family, face = fonts.find_font_and_face('Sans')
    assert family == 'Sans'
    assert face == 'Regular'
    family, face = fonts.find_font_and_face('UnknownFont')
    assert family == 'Sans'
    assert face == 'Regular'


def test_get_sample_size():
    size = fonts.get_sample_size('Probe', 'Sans', 12)
    assert isinstance(size, tuple)
    assert len(size) == 2
    assert isinstance(size[0], int) and isinstance(size[1], int)


def test_render_sample():
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
    ctx = cairo.Context(surface)
    fonts.render_sample(ctx, 'Probe', 'Sans', 12)
    assert True
