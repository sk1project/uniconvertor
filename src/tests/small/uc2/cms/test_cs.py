from unittest import mock

from uc2 import uc2const
from uc2.cms import cs

REG_COLOR = [uc2const.COLOR_SPOT, [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0, 1.0]], 1.0, uc2const.COLOR_REG]


def test_rgb_to_hexcolor():
    assert cs.rgb_to_hexcolor([1.0, 0.0, 1.0]) == '#ff00ff'
    assert cs.rgb_to_hexcolor([0.1, 0.3, 0.7]) == '#1a4cb2'
    assert cs.rgb_to_hexcolor([0.9, 0.5, 0.2]) == '#e68033'


def test_rgba_to_hexcolor():
    assert cs.rgba_to_hexcolor([1.0, 0.0, 1.0, 1.0]) == '#ff00ffff'
    assert cs.rgba_to_hexcolor([0.1, 0.3, 0.7, 0.5]) == '#1a4cb280'
    assert cs.rgba_to_hexcolor([0.9, 0.5, 0.2, 0.3]) == '#e680334c'


def test_cmyk_to_hexcolor():
    assert cs.cmyk_to_hexcolor([1.0, 0.0, 1.0, 1.0]) == '#ff00ffff'
    assert cs.cmyk_to_hexcolor([0.1, 0.3, 0.7, 0.5]) == '#1a4cb280'
    assert cs.cmyk_to_hexcolor([0.9, 0.5, 0.2, 0.3]) == '#e680334c'


def test_hexcolor_to_rgb():
    assert cs.hexcolor_to_rgb('#ff00ff') == [1.0, 0.0, 1.0]
    assert cs.hexcolor_to_rgb('#1a4cb2') == [0.10196078431372549, 0.2980392156862745, 0.6980392156862745]
    assert cs.hexcolor_to_rgb('#e68033') == [0.9019607843137255, 0.5019607843137255, 0.2]


def test_hexcolor_to_rgba():
    assert cs.hexcolor_to_rgba('#ff00ffff') == [1.0, 0.0, 1.0, 1.0]
    assert cs.hexcolor_to_rgba('#1a4cb280') == [0.10196078431372549, 0.2980392156862745,
                                                0.6980392156862745, 0.5019607843137255]
    assert cs.hexcolor_to_rgba('#e680334c') == [0.9019607843137255, 0.5019607843137255, 0.2, 0.2980392156862745]


def test_hexcolor_to_cmyk():
    assert cs.hexcolor_to_cmyk('#ff00ffff') == [1.0, 0.0, 1.0, 1.0]
    assert cs.hexcolor_to_cmyk('#1a4cb280') == [0.10196078431372549, 0.2980392156862745,
                                                0.6980392156862745, 0.5019607843137255]
    assert cs.hexcolor_to_cmyk('#e680334c') == [0.9019607843137255, 0.5019607843137255, 0.2, 0.2980392156862745]


def test_gdk_hexcolor_to_rgb():
    assert cs.gdk_hexcolor_to_rgb('#ffff0000ffff') == [1.0, 0.0, 1.0]
    assert cs.gdk_hexcolor_to_rgb('#1a2b4c8db213') == [0.10222018768596933, 0.29903105210955977, 0.6956130312046997]
    assert cs.gdk_hexcolor_to_rgb('#e680334cb4c8') == [0.9004043640802625, 0.20038147554741742, 0.7061875333791104]


def test_rgb_to_gdk_hexcolor():
    assert cs.rgb_to_gdk_hexcolor([1.0, 0.0, 1.0]) == '#ffff0000ffff'
    assert cs.rgb_to_gdk_hexcolor([0.10222018768596933, 0.29903105210955977,
                                   0.6956130312046997]) == '#1a2b4c8db213'
    assert cs.rgb_to_gdk_hexcolor([0.9004043640802625, 0.20038147554741742,
                                   0.7061875333791104]) == '#e680334cb4c8'


def test_cmyk_to_rgb():
    assert cs.cmyk_to_rgb([0.0, 0.0, 0.0, 1.0]) == [0.0, 0.0, 0.0]
    assert cs.cmyk_to_rgb([1.0, 0.0, 0.0, 0.0]) == [0.0, 1.0, 1.0]
    assert cs.cmyk_to_rgb([0.0, 1.0, 0.0, 0.0]) == [1.0, 0.0, 1.0]
    assert cs.cmyk_to_rgb([0.0, 0.0, 1.0, 0.0]) == [1.0, 1.0, 0.0]
    assert cs.cmyk_to_rgb([0.5, 0.2, 0.3, 0.1]) == [0.4, 0.7, 0.6]


def test_rgb_to_cmyk():
    assert cs.rgb_to_cmyk([0.0, 0.0, 0.0]) == [0.0, 0.0, 0.0, 1.0]
    assert cs.rgb_to_cmyk([0.0, 1.0, 1.0]) == [1.0, 0.0, 0.0, 0.0]
    assert cs.rgb_to_cmyk([1.0, 0.0, 1.0]) == [0.0, 1.0, 0.0, 0.0]
    assert cs.rgb_to_cmyk([1.0, 1.0, 0.0]) == [0.0, 0.0, 1.0, 0.0]
    assert cs.rgb_to_cmyk([0.4, 0.7, 0.6]) == [0.4285714285714285, 0.0, 0.14285714285714282, 0.30000000000000004]


def test_gray_to_cmyk():
    assert cs.gray_to_cmyk([0.0]) == [0.0, 0.0, 0.0, 1.0]
    assert cs.gray_to_cmyk([0.5]) == [0.0, 0.0, 0.0, 0.5]
    assert cs.gray_to_cmyk([1.0]) == [0.0, 0.0, 0.0, 0.0]


def test_gray_to_rgb():
    assert cs.gray_to_rgb([0.0]) == [0.0, 0.0, 0.0]
    assert cs.gray_to_rgb([0.5]) == [0.5, 0.5, 0.5]
    assert cs.gray_to_rgb([1.0]) == [1.0, 1.0, 1.0]


def test_rgb_to_gray():
    assert cs.rgb_to_gray([1.0, 0.5, 0.0]) == [0.5]
    assert cs.rgb_to_gray([0.1, 0.5, 0.9]) == [0.5]
    assert cs.rgb_to_gray([1.0, 0.1, 0.4]) == [0.5]


def test_do_simple_transform():
    assert cs.do_simple_transform([0.5], uc2const.COLOR_GRAY, uc2const.COLOR_RGB) == [0.5, 0.5, 0.5]
    assert cs.do_simple_transform([1.0], uc2const.COLOR_GRAY, uc2const.COLOR_RGB) == [1.0, 1.0, 1.0]
    assert cs.do_simple_transform([0.5], uc2const.COLOR_GRAY, uc2const.COLOR_CMYK) == [0.0, 0.0, 0.0, 0.5]
    assert cs.do_simple_transform([1.0], uc2const.COLOR_GRAY, uc2const.COLOR_CMYK) == [0.0, 0.0, 0.0, 0.0]
    assert cs.do_simple_transform([0.5], uc2const.COLOR_GRAY, uc2const.COLOR_LAB) == \
        [0.5338896474111431, 0.5019607843137255, 0.5019607843137255]
    assert cs.do_simple_transform([1.0], uc2const.COLOR_GRAY, uc2const.COLOR_LAB) == \
        [1.0, 0.5019607843137255, 0.5019607843137255]

    assert cs.do_simple_transform([1.0, 1.0, 0.0], uc2const.COLOR_RGB, uc2const.COLOR_CMYK) == [0.0, 0.0, 1.0, 0.0]
    assert cs.do_simple_transform([0.4, 0.7, 0.6], uc2const.COLOR_RGB, uc2const.COLOR_CMYK) == \
        [0.4285714285714285, 0.0, 0.14285714285714282, 0.30000000000000004]
    assert cs.do_simple_transform([1.0, 0.5, 0.0], uc2const.COLOR_RGB, uc2const.COLOR_GRAY) == [0.5]
    assert cs.do_simple_transform([0.1, 0.5, 0.9], uc2const.COLOR_RGB, uc2const.COLOR_GRAY) == [0.5]
    assert cs.do_simple_transform([1.0, 0.5, 0.0], uc2const.COLOR_RGB, uc2const.COLOR_LAB) == \
        [0.6695433251627613, 0.6708595624593359, 0.7919927566820204]
    assert cs.do_simple_transform([0.1, 0.5, 0.9], uc2const.COLOR_RGB, uc2const.COLOR_LAB) == \
        [0.5317262525736435, 0.54165043979609, 0.26968537672374326]

    assert cs.do_simple_transform([0.0, 0.0, 0.0, 1.0], uc2const.COLOR_CMYK, uc2const.COLOR_RGB) == [0.0, 0.0, 0.0]
    assert cs.do_simple_transform([0.5, 0.2, 0.3, 0.1], uc2const.COLOR_CMYK, uc2const.COLOR_RGB) == [0.4, 0.7, 0.6]
    assert cs.do_simple_transform([0.0, 0.0, 0.0, 0.5], uc2const.COLOR_CMYK, uc2const.COLOR_GRAY) == [0.5]
    assert cs.do_simple_transform([0.5, 0.2, 0.3, 0.1], uc2const.COLOR_CMYK, uc2const.COLOR_GRAY) == \
        [0.5666666666666668]
    assert cs.do_simple_transform([0.0, 0.0, 0.0, 1.0], uc2const.COLOR_CMYK, uc2const.COLOR_LAB) == \
        [0.0, 0.5019607843137255, 0.5019607843137255]
    assert cs.do_simple_transform([0.5, 0.2, 0.3, 0.1], uc2const.COLOR_CMYK, uc2const.COLOR_LAB) == \
        [0.6739982588979951, 0.3851243209230969, 0.5241778995255767]

    assert cs.do_simple_transform([1.0, 0.5, 0.0], uc2const.COLOR_LAB, uc2const.COLOR_RGB) == [1.0, 1.0, 1.0]
    assert cs.do_simple_transform([0.5, 0.5, 0.5], uc2const.COLOR_LAB, uc2const.COLOR_RGB) == \
        [0.4612081648569169, 0.4675080745400589, 0.46956266421421994]


def test_colorb():
    assert cs.colorb() == [0, 0, 0, 0]
    assert cs.colorb([uc2const.COLOR_CMYK, [1.0, 1.0, 1.0, 1.0], 1.0, '']) == [255, 255, 255, 255]
    assert cs.colorb([uc2const.COLOR_RGB, [1.0, 0.0, 1.0], 1.0, '']) == [255, 0, 255, 0]
    assert cs.colorb(REG_COLOR) == [0, 0, 0, 0]
    assert cs.colorb(REG_COLOR, use_cmyk=True) == [255, 255, 255, 255]


def test_decode_colorb():
    assert cs.decode_colorb([0, 255, 255, 0], cs=uc2const.COLOR_CMYK) == [0.0, 1.0, 1.0, 0.0]
    assert cs.decode_colorb([0, 255, 255, 0], cs=uc2const.COLOR_RGB) == [0.0, 1.0, 1.0]
    assert cs.decode_colorb([0, 255, 255, 0], cs=uc2const.COLOR_GRAY) == [0.0]


def test_get_registration_black():
    assert cs.get_registration_black() == REG_COLOR


def test_color_to_spot():
    assert cs.color_to_spot() == REG_COLOR
    assert cs.color_to_spot([]) == REG_COLOR
    assert cs.color_to_spot([uc2const.COLOR_RGB, [1.0, 1.0, 1.0], 1.0, '']) == \
        [uc2const.COLOR_SPOT, [[1.0, 1.0, 1.0], []], 1.0, '']
    assert cs.color_to_spot([uc2const.COLOR_CMYK, [1.0, 1.0, 1.0, 1.0], 1.0, '']) == \
        [uc2const.COLOR_SPOT, [[], [1.0, 1.0, 1.0, 1.0]], 1.0, '']
    assert cs.color_to_spot([uc2const.COLOR_GRAY, [1.0], 1.0, '']) == \
        [uc2const.COLOR_SPOT, [[], [0.0, 0.0, 0.0, 0.0]], 1.0, '']


def test_verbose_color():
    assert cs.verbose_color(None) == 'No color'
    assert cs.verbose_color([]) == 'No color'
    assert cs.verbose_color([uc2const.COLOR_CMYK, [1.0, 1.0, 1.0, 1.0], 0.5, '']) == 'C-100% M-100% Y-100% K-100% A-50%'
    assert cs.verbose_color([uc2const.COLOR_CMYK, [1.0, 1.0, 1.0, 1.0], 1.0, '']) == 'C-100% M-100% Y-100% K-100%'
    assert cs.verbose_color([uc2const.COLOR_RGB, [1.0, 1.0, 1.0], 0.5, '']) == 'R-255 G-255 B-255 A-128'
    assert cs.verbose_color([uc2const.COLOR_RGB, [1.0, 1.0, 1.0], 1.0, '']) == 'R-255 G-255 B-255'
    assert cs.verbose_color([uc2const.COLOR_GRAY, [1.0], 0.5, '']) == 'Gray-255 Alpha-128'
    assert cs.verbose_color([uc2const.COLOR_GRAY, [1.0], 1.0, '']) == 'Gray-255'
    assert cs.verbose_color([uc2const.COLOR_LAB, [1.0, 1.0, 1.0], 0.5, '']) == 'L 100 a 127 b 127 Alpha-128'
    assert cs.verbose_color([uc2const.COLOR_LAB, [1.0, 1.0, 1.0], 1.0, '']) == 'L 100 a 127 b 127'
    assert cs.verbose_color(REG_COLOR) == uc2const.COLOR_REG
    assert cs.verbose_color(['x', [1.0, 1.0, 1.0], 1.0, '']) == '???'


@mock.patch('uc2.cms.cs.libcms')
def test_get_profile_name(libcms_mock):
    libcms_mock.cms_get_profile_name.return_value = 'profile name'
    assert cs.get_profile_name('/profile.icc') == 'profile name'
    libcms_mock.cms_open_profile_from_file.assert_called_with('/profile.icc')


@mock.patch('uc2.cms.cs.libcms')
def test_get_profile_info(libcms_mock):
    libcms_mock.cms_get_profile_info.return_value = 'profile info'
    assert cs.get_profile_info('/profile.icc') == 'profile info'
    libcms_mock.cms_open_profile_from_file.assert_called_with('/profile.icc')


@mock.patch('uc2.cms.cs.libcms')
def test_get_profile_descr(libcms_mock):
    libcms_mock.cms_get_profile_name.return_value = 'profile name'
    libcms_mock.cms_get_profile_copyright.return_value = 'profile copyright'
    libcms_mock.cms_get_profile_info.return_value = 'profile info'
    assert cs.get_profile_descr('/profile.icc') == ('profile name', 'profile copyright', 'profile info')
    libcms_mock.cms_open_profile_from_file.assert_called_with('/profile.icc')
