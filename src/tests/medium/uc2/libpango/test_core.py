import re

from uc2.libpango import core

TEXT_STYLE = ['Sans', 'Regular', 12.0, 0]


def test_get_version():
    version = core.get_version()
    assert isinstance(version, str)
    pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\b'
    assert re.match(pattern, version)


def test_create_layout():
    assert core.create_layout()


def test_get_font_description():
    assert core.get_font_description(TEXT_STYLE)
    text_style = ['Вердана', 'Regular', 12.0]
    assert core.get_font_description(text_style)
    text_style = ['٢٠٢٠ م جرافيكا', 'Regular', 12.0]
    assert core.get_font_description(text_style)
    text_style = ['嘗試', 'Regular', 12.0]
    assert core.get_font_description(text_style)


def test_set_layout():
    assert core.set_layout('Sans', -1, TEXT_STYLE) is None
    assert core.set_layout('٢٠٢٠ م جرافيكا', -1, TEXT_STYLE) is None
    assert core.set_layout('嘗試', -1, TEXT_STYLE) is None


def test_set_glyph_layout():
    assert isinstance(core.set_glyph_layout('Sans', -1, TEXT_STYLE), float)
    assert isinstance(core.set_glyph_layout('٢٠٢٠ م جرافيكا', -1, TEXT_STYLE), float)
    assert isinstance(core.set_glyph_layout('嘗試', -1, TEXT_STYLE), float)


def test_layout_path():
    core.set_glyph_layout('Sans', -1, TEXT_STYLE)
    assert core.layout_path() is None


def test_get_line_positions():
    text = 'First line\n' \
           'Second line\n' \
           'Third line'
    core.set_layout(text, -1, TEXT_STYLE)
    lines = core.get_line_positions()
    assert isinstance(lines, tuple)
    assert len(lines) == 3


def test_get_char_positions():
    text = 'First tt line\n' \
           'Second ff line\n' \
           'Third line'
    core.set_layout(text, -1, TEXT_STYLE)
    pos = core.get_char_positions(39)
    assert isinstance(pos, tuple)
    assert len(pos) == 39


def test_get_cluster_positions():
    text = 'First tt line\n' \
           'Second ff line\n' \
           'Third line'
    core.set_layout(text, -1, TEXT_STYLE)
    clusters = core.get_cluster_positions(39)
    assert isinstance(clusters, tuple)
    assert len(clusters) == 5


def test_get_layout_size():
    text = 'First tt line\n' \
           'Second ff line\n' \
           'Third line'
    core.set_layout(text, -1, TEXT_STYLE)
    size = core.get_layout_size()
    assert isinstance(size, tuple)
    assert len(size) == 2


def test_get_layout_bbox():
    text = 'First tt line\n' \
           'Second ff line\n' \
           'Third line'
    core.set_layout(text, -1, TEXT_STYLE)
    bbox = core.get_layout_bbox()
    assert isinstance(bbox, list)
    assert len(bbox) == 4
