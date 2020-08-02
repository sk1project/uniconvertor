from unittest import mock
from unittest.mock import Mock

from uc2 import uc2const
from uc2.cms import cmngr


@mock.patch('uc2.cms.cmngr.DefaultColorManager.update')
def test_cmngr_init(update_mock):
    cmngr.DefaultColorManager()
    assert update_mock.called


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.clear_transforms')
def test_cmngr_update(clear_mock, libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert clear_mock.called
    assert libcms_mock.cms_create_default_profile.call_count == len(uc2const.COLORSPACES)
    assert not hasattr(mngr, 'transforms')
    assert not hasattr(mngr, 'proof_transforms')
    assert hasattr(mngr, 'handles')
    assert isinstance(mngr.handles, dict)
    assert len(mngr.handles) == len(uc2const.COLORSPACES)


@mock.patch('uc2.cms.cmngr.libcms')
def test_cmngr_clear_transforms(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    assert mngr.proof_transforms == {}


@mock.patch('uc2.cms.cmngr.libcms')
def test_cmngr_get_transform(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    transform = mngr.get_transform(uc2const.COLOR_RGB, uc2const.COLOR_CMYK)
    libcms_mock.cms_create_transform.assert_called_with(
        mngr.handles[uc2const.COLOR_RGB],
        uc2const.COLOR_RGB,
        mngr.handles[uc2const.COLOR_CMYK],
        uc2const.COLOR_CMYK,
        mngr.cmyk_intent,
        mngr.flags)
    assert mngr.transforms
    assert mngr.transforms[uc2const.COLOR_RGB+uc2const.COLOR_CMYK] == transform


@mock.patch('uc2.cms.cmngr.libcms')
def test_cmngr_get_proof_transform(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.proof_transforms == {}
    transform = mngr.get_proof_transform(uc2const.COLOR_RGB)
    libcms_mock.cms_create_proofing_transform.assert_called_with(
        mngr.handles[uc2const.COLOR_RGB], uc2const.COLOR_RGB,
        mngr.handles[uc2const.COLOR_RGB], uc2const.COLOR_RGB,
        mngr.handles[uc2const.COLOR_CMYK],
        mngr.cmyk_intent,
        mngr.rgb_intent,
        mngr.flags)
    assert mngr.proof_transforms
    assert mngr.proof_transforms[uc2const.COLOR_RGB] == transform


@mock.patch('uc2.cms.cmngr.libcms')
def test_do_transform(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    ret = mngr.do_transform(color, uc2const.COLOR_RGB, uc2const.COLOR_CMYK)
    libcms_mock.cms_do_transform.assert_called_with(
        mngr.get_transform(uc2const.COLOR_RGB, uc2const.COLOR_CMYK),
        [255, 128, 0, 0],
        [0, 0, 0, 0])
    assert ret == [0.0, 0.0, 0.0, 0.0]
    assert mngr.transforms


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.cs')
def test_do_transform_not_use_cms(cs_mock, libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    mngr.use_cms = False
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    mngr.do_transform(color, uc2const.COLOR_RGB, uc2const.COLOR_CMYK)
    cs_mock.do_simple_transform.assert_called_with(
        [1.0, 0.5, 0.0], uc2const.COLOR_RGB, uc2const.COLOR_CMYK)
    assert mngr.transforms == {}


@mock.patch('uc2.cms.cmngr.libcms')
def test_do_bitmap_transform(libcms_mock):
    image_mock = Mock()
    image_mock.mode = uc2const.IMAGE_RGB
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    mngr.do_bitmap_transform(image_mock, uc2const.IMAGE_CMYK)
    libcms_mock.cms_do_bitmap_transform.assert_called_with(
        mngr.get_transform(uc2const.COLOR_RGB, uc2const.COLOR_CMYK),
        image_mock, uc2const.IMAGE_RGB, uc2const.IMAGE_CMYK)
    assert mngr.transforms


@mock.patch('uc2.cms.cmngr.libcms')
def test_do_bitmap_transform_not_use_cms(libcms_mock):
    image_mock = Mock()
    image_mock.mode = uc2const.IMAGE_RGB
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.transforms == {}
    mngr.use_cms = False
    mngr.do_bitmap_transform(image_mock, uc2const.IMAGE_CMYK)
    image_mock.convert.assert_called_with(uc2const.IMAGE_CMYK)
    assert mngr.transforms == {}


@mock.patch('uc2.cms.cmngr.libcms')
def test_cmngr_do_proof_transform(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.proof_transforms == {}
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    mngr.do_proof_transform(color, uc2const.COLOR_RGB)
    libcms_mock.cms_do_transform.assert_called_with(
        mngr.get_proof_transform(uc2const.COLOR_RGB),
        [255, 128, 0, 0],
        [0, 0, 0, 0])
    assert mngr.proof_transforms


@mock.patch('uc2.cms.cmngr.libcms')
def do_proof_bitmap_transform(libcms_mock):
    image_mock = Mock()
    image_mock.mode = uc2const.IMAGE_RGB
    mngr = cmngr.DefaultColorManager()
    assert libcms_mock.cms_create_default_profile.called
    assert mngr.proof_transforms == {}
    mngr.do_proof_bitmap_transform(image_mock)
    libcms_mock.cms_do_bitmap_transform.assert_called_with(
        mngr.get_proof_transform(uc2const.COLOR_RGB),
        image_mock, uc2const.IMAGE_RGB, uc2const.IMAGE_RGB)
    assert mngr.proof_transforms


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_rgb_color(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    assert id(color) != id(mngr.get_rgb_color(color))
    assert id(color[1]) != id(mngr.get_rgb_color(color)[1])
    color_spot = [uc2const.COLOR_SPOT, [[1.0, 0.5, 0.0], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    assert [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color'] == mngr.get_rgb_color(color_spot)
    color_cmyk = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'test cmyk color']
    mngr.get_rgb_color(color_cmyk)
    do_transform_mock.assert_called_with(color_cmyk, uc2const.COLOR_CMYK, uc2const.COLOR_RGB)


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_rgb_color255(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    assert mngr.get_rgb_color255(color) == [255, 128, 0]
    assert not do_transform_mock.called


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_rgba_color255(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    assert mngr.get_rgba_color255(color) == [255, 128, 0, 255]
    assert not do_transform_mock.called


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_cmyk_color(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'test cmyk color']
    assert id(color) != id(mngr.get_cmyk_color(color))
    assert id(color[1]) != id(mngr.get_cmyk_color(color)[1])
    color_spot = [uc2const.COLOR_SPOT, [[1.0, 0.5, 0.0], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    assert [uc2const.COLOR_CMYK, [0.5, 0.5, 0.1, 0.0], 1.0, 'test spot color'] == mngr.get_cmyk_color(color_spot)
    color_rgb = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test color']
    mngr.get_cmyk_color(color_rgb)
    do_transform_mock.assert_called_with(color_rgb, uc2const.COLOR_RGB, uc2const.COLOR_CMYK)


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_rgb_color255(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'test cmyk color']
    assert mngr.get_cmyk_color255(color) == [255, 128, 0, 0]
    assert not do_transform_mock.called


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_lab_color(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_LAB, [1.0, 0.5, 0.0], 1.0, 'test lab color']
    assert id(color) != id(mngr.get_lab_color(color))
    assert id(color[1]) != id(mngr.get_lab_color(color)[1])

    color_spot = [uc2const.COLOR_SPOT, [[1.0, 0.5, 0.0], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    color_rgb = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color']
    mngr.get_lab_color(color_spot)
    do_transform_mock.assert_called_with(color_rgb, uc2const.COLOR_RGB, uc2const.COLOR_LAB)

    do_transform_mock.reset_mock()
    color_spot = [uc2const.COLOR_SPOT, [[], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    color_cmyk = [uc2const.COLOR_CMYK, [0.5, 0.5, 0.1, 0.0], 1.0, 'test spot color']
    mngr.get_lab_color(color_spot)
    do_transform_mock.assert_called_with(color_cmyk, uc2const.COLOR_CMYK, uc2const.COLOR_LAB)


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
def test_get_lab_color(do_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_GRAY, [0.5], 1.0, 'test gray color']
    assert id(color) != id(mngr.get_grayscale_color(color))
    assert id(color[1]) != id(mngr.get_grayscale_color(color)[1])

    color_spot = [uc2const.COLOR_SPOT, [[1.0, 0.5, 0.0], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    color_rgb = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color']
    mngr.get_grayscale_color(color_spot)
    do_transform_mock.assert_called_with(color_rgb, uc2const.COLOR_RGB, uc2const.COLOR_GRAY)

    do_transform_mock.reset_mock()
    color_spot = [uc2const.COLOR_SPOT, [[], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    color_cmyk = [uc2const.COLOR_CMYK, [0.5, 0.5, 0.1, 0.0], 1.0, 'test spot color']
    mngr.get_grayscale_color(color_spot)
    do_transform_mock.assert_called_with(color_cmyk, uc2const.COLOR_CMYK, uc2const.COLOR_GRAY)


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_rgb_color')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_lab_color')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_cmyk_color')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_grayscale_color')
def test_get_color(get_grayscale_color_mock, get_cmyk_color_mock, get_lab_color_mock,
                   get_rgb_color_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    color = [uc2const.COLOR_GRAY, [0.5], 1.0, 'test gray color']
    mngr.get_color(color, uc2const.COLOR_RGB)
    get_rgb_color_mock.assert_called_with(color=color)

    mngr.get_color(color, uc2const.COLOR_LAB)
    get_lab_color_mock.assert_called_with(color=color)

    mngr.get_color(color, uc2const.COLOR_CMYK)
    get_cmyk_color_mock.assert_called_with(color=color)

    mngr.get_color(color, uc2const.COLOR_GRAY)
    get_grayscale_color_mock.assert_called_with(color=color)


def test_mix_colors():
    c1 = [uc2const.COLOR_GRAY, [0.5], 1.0, 'color1']
    c2 = [uc2const.COLOR_GRAY, [1.0], 1.0, 'color2']
    assert cmngr.DefaultColorManager.mix_colors(c1, c2) == [uc2const.COLOR_GRAY, [0.75], 1.0, '']
    assert cmngr.DefaultColorManager.mix_colors(c1, c2, 0.25) == [uc2const.COLOR_GRAY, [0.625], 1.0, '']

    c1 = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'color1']
    c2 = [uc2const.COLOR_RGB, [0.0, 0.5, 1.0], 1.0, 'color2']
    assert cmngr.DefaultColorManager.mix_colors(c1, c2) == [uc2const.COLOR_RGB, [0.5] * 3, 1.0, '']

    c1 = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'color1']
    c2 = [uc2const.COLOR_CMYK, [0.0, 0.0, 0.5, 1.0], 1.0, 'color2']
    assert cmngr.DefaultColorManager.mix_colors(c1, c2) == [uc2const.COLOR_CMYK, [0.5, 0.25, 0.25, 0.5], 1.0, '']


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_rgb_color')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_cmyk_color')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_transform')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_proof_transform')
def test_get_display_color(do_proof_transform_mock, do_transform_mock,
                           get_cmyk_color_mock, get_rgb_color_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()

    mngr.use_cms = False
    c1 = [uc2const.COLOR_GRAY, [0.5], 1.0, 'color1']
    mngr.get_display_color(c1)
    get_rgb_color_mock.assert_called_with(c1)
    get_rgb_color_mock.reset_mock()

    mngr.use_cms = True
    mngr.proofing = False
    c2 = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'color1']
    assert mngr.get_display_color(c2) == c2[1]

    c3 = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'color1']
    mngr.get_display_color(c3)
    do_transform_mock.assert_called_with(c3, uc2const.COLOR_CMYK, uc2const.COLOR_RGB)
    do_transform_mock.reset_mock()

    c4 = [uc2const.COLOR_LAB, [1.0, 0.5, 0.0], 1.0, 'test lab color']
    mngr.get_display_color(c4)
    do_transform_mock.assert_called_with(c4, uc2const.COLOR_LAB, uc2const.COLOR_RGB)
    do_transform_mock.reset_mock()

    c5 = [uc2const.COLOR_SPOT, [[1.0, 0.5, 0.0], [0.5, 0.5, 0.1, 0.0]], 1.0, 'test spot color']
    get_rgb_color_mock.return_value = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color']
    assert mngr.get_display_color(c5) == c5[1][0]
    get_rgb_color_mock.assert_called_with(c5)
    get_rgb_color_mock.reset_mock()

    mngr.proofing = True
    mngr.get_display_color(c3)
    do_transform_mock.assert_called_with(c3, uc2const.COLOR_CMYK, uc2const.COLOR_RGB)
    do_transform_mock.reset_mock()

    mngr.get_display_color(c2)
    do_proof_transform_mock.assert_called_with(c2, uc2const.COLOR_RGB)
    do_proof_transform_mock.reset_mock()

    mngr.get_display_color(c4)
    do_proof_transform_mock.assert_called_with(c4, uc2const.COLOR_LAB)
    do_proof_transform_mock.reset_mock()

    mngr.proof_for_spot = False
    get_rgb_color_mock.return_value = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color']
    assert mngr.get_display_color(c5) == c5[1][0]
    get_rgb_color_mock.assert_called_with(c5)

    mngr.proof_for_spot = True
    get_cmyk_color_mock.return_value = c3
    mngr.get_display_color(c5)
    get_cmyk_color_mock.assert_called_with(c5)
    do_transform_mock.assert_called_with(c3, uc2const.COLOR_CMYK, uc2const.COLOR_RGB)


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.get_display_color')
def test_get_display_color255(get_display_color_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    c1 = [uc2const.COLOR_CMYK, [1.0, 0.5, 0.0, 0.0], 1.0, 'color1']
    get_display_color_mock.return_value = [1.0, 0.5, 0.0]
    assert mngr.get_display_color255(c1) == [255, 128, 0]


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_bitmap_transform')
def test_convert_image(do_bitmap_transform_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    img = Mock()
    img_gray = Mock()

    img_gray.mode = uc2const.IMAGE_GRAY
    mngr.convert_image(img_gray, uc2const.IMAGE_GRAY)
    img_gray.copy.assert_called()
    do_bitmap_transform_mock.assert_not_called()
    img_gray.reset_mock()

    img.mode = uc2const.IMAGE_MONO
    img_gray.mode = uc2const.IMAGE_GRAY
    img.convert.return_value = img_gray
    mngr.convert_image(img, uc2const.IMAGE_GRAY)
    img.convert.assert_called_with(uc2const.IMAGE_GRAY)
    img_gray.copy.assert_not_called()
    img.reset_mock()
    img_gray.reset_mock()

    img.mode = uc2const.IMAGE_RGB
    img_gray.mode = uc2const.IMAGE_GRAY
    do_bitmap_transform_mock.return_value = img_gray
    mngr.convert_image(img, uc2const.IMAGE_MONO)
    do_bitmap_transform_mock.assert_called_with(img, uc2const.IMAGE_GRAY, None)
    img_gray.convert.assert_called_with(uc2const.IMAGE_MONO)
    img.reset_mock()
    img_gray.reset_mock()

    img.mode = uc2const.IMAGE_RGB
    mngr.convert_image(img, uc2const.IMAGE_CMYK)
    do_bitmap_transform_mock.assert_called_with(img, uc2const.IMAGE_CMYK, None)
    img.copy.assert_not_called()
    img.convert.assert_not_called()


@mock.patch('uc2.cms.cmngr.libcms')
def test_adjust_image(libcms_mock):
    mngr = cmngr.DefaultColorManager()
    img = Mock()
    img.mode = uc2const.IMAGE_RGB
    profile = b'00000000000000000000000'

    mngr.adjust_image(img, profile)
    libcms_mock.cms_open_profile_from_bytes.assert_called_with(profile)
    libcms_mock.cms_create_transform.assert_called()
    libcms_mock.cms_do_bitmap_transform.assert_called()


@mock.patch('uc2.cms.cmngr.libcms')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.convert_image')
@mock.patch('uc2.cms.cmngr.DefaultColorManager.do_proof_bitmap_transform')
def test_get_display_image(do_proof_bitmap_transform_mock, convert_image_mock, _libcms_mock):
    mngr = cmngr.DefaultColorManager()
    img = Mock()
    img.mode = uc2const.IMAGE_RGB

    mngr.use_cms = False
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB)
    do_proof_bitmap_transform_mock.assert_not_called()
    convert_image_mock.reset_mock()

    mngr.use_cms = True
    mngr.proofing = False
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB, None)
    do_proof_bitmap_transform_mock.assert_not_called()
    convert_image_mock.reset_mock()

    mngr.proofing = True
    mngr.get_display_image(img)
    convert_image_mock.assert_not_called()
    do_proof_bitmap_transform_mock.assert_called_with(img)
    do_proof_bitmap_transform_mock.reset_mock()

    img.mode = uc2const.IMAGE_CMYK
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB, None)
    do_proof_bitmap_transform_mock.assert_not_called()
    convert_image_mock.reset_mock()

    mngr.use_display_profile = True
    mngr.handles[uc2const.COLOR_DISPLAY] = True
    mngr.proofing = True
    img.mode = uc2const.IMAGE_RGB
    mngr.get_display_image(img)
    convert_image_mock.assert_not_called()
    do_proof_bitmap_transform_mock.assert_called_with(img)
    do_proof_bitmap_transform_mock.reset_mock()

    img.mode = uc2const.IMAGE_CMYK
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB, uc2const.COLOR_DISPLAY)
    do_proof_bitmap_transform_mock.assert_not_called()
    convert_image_mock.reset_mock()

    mngr.proofing = False
    img.mode = uc2const.IMAGE_RGB
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB, uc2const.COLOR_DISPLAY)
    do_proof_bitmap_transform_mock.assert_not_called()
    convert_image_mock.reset_mock()

    img.mode = uc2const.IMAGE_CMYK
    mngr.get_display_image(img)
    convert_image_mock.assert_called_with(img, uc2const.IMAGE_RGB, uc2const.COLOR_DISPLAY)
    do_proof_bitmap_transform_mock.assert_not_called()


@mock.patch('uc2.cms.cmngr.libcms')
def test_get_color_name(_libcms_mock):
    c1 = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test spot color']
    c2 = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0, 'test']
    c3 = [uc2const.COLOR_RGB, [1.0, 0.5, 0.0], 1.0]
    assert cmngr.DefaultColorManager.get_color_name(c1) == 'test spot color'
    assert cmngr.DefaultColorManager.get_color_name(c2) == 'test'
    assert cmngr.DefaultColorManager.get_color_name(c3) == ''
