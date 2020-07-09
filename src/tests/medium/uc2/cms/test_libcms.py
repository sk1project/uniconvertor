import os

import PIL

from uc2 import uc2const
from uc2.cms import libcms

_pkgdir = os.path.abspath(os.path.dirname(__file__))


def get_filepath(filename):
    return os.path.join(_pkgdir, 'cms_data', filename)


IN_PROFILE = libcms.cms_open_profile_from_file(get_filepath('sRGB.icm'))
OUT_PROFILE = libcms.cms_open_profile_from_file(get_filepath('GenericCMYK.icm'))
TRANSFORM = libcms.cms_create_transform(
    IN_PROFILE, uc2const.TYPE_RGBA_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
    uc2const.INTENT_PERCEPTUAL, uc2const.cmsFLAGS_NOTPRECALC)
TRANSFORM2 = libcms.cms_create_transform(
    IN_PROFILE, uc2const.TYPE_RGBA_8, OUT_PROFILE,
    uc2const.TYPE_CMYK_8, uc2const.INTENT_PERCEPTUAL, 0)


def test_open_invalid_profile():
    try:
        profile = get_filepath('empty.icm')
        libcms.cms_open_profile_from_file(profile)
    except libcms.CmsError:
        return
    assert False


def test_open_absent_profile():
    try:
        profile = get_filepath('xxx.icm')
        libcms.cms_open_profile_from_file(profile)
    except libcms.CmsError:
        return
    assert False


# ---Transform related tests


def test_create_transform():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGBA_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8) is not None
    assert libcms.cms_create_transform(
        OUT_PROFILE, uc2const.TYPE_CMYK_8,
        IN_PROFILE, uc2const.TYPE_RGBA_8) is not None
    assert libcms.cms_create_transform(
        OUT_PROFILE, uc2const.TYPE_CMYK_8,
        IN_PROFILE, uc2const.TYPE_RGB_8) is not None


def test_create_transform_with_custom_intent():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_RELATIVE_COLORIMETRIC) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_SATURATION) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_ABSOLUTE_COLORIMETRIC) is not None


def test_create_transform_with_custom_flags():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC | uc2const.cmsFLAGS_GAMUTCHECK) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_PRESERVEBLACK |
        uc2const.cmsFLAGS_BLACKPOINTCOMPENSATION) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_HIGHRESPRECALC) is not None
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, uc2const.TYPE_CMYK_8,
        uc2const.INTENT_PERCEPTUAL,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_LOWRESPRECALC) is not None


def test_create_transform_with_invalid_intent():
    assert libcms.cms_create_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.TYPE_CMYK_8, 3) is not None
    try:
        libcms.cms_create_transform(
            IN_PROFILE, uc2const.TYPE_RGB_8,
            OUT_PROFILE, uc2const.TYPE_CMYK_8, 4)
    except libcms.CmsError:
        return
    assert False


# ---Proof transform related tests

def test_create_proofing_transform():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGBA_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGBA_8,
        OUT_PROFILE) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGBA_8, IN_PROFILE, uc2const.TYPE_RGBA_8,
        OUT_PROFILE) is not None


def test_create_proofing_transform_with_custom_intent():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_RELATIVE_COLORIMETRIC) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_SATURATION) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_ABSOLUTE_COLORIMETRIC) is not None


def test_create_proofing_transform_with_custom_proofing_intent():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_PERCEPTUAL) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_RELATIVE_COLORIMETRIC) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_SATURATION) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_ABSOLUTE_COLORIMETRIC) is not None


def test_create_proofing_transform_with_custom_flags():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_RELATIVE_COLORIMETRIC,
        uc2const.cmsFLAGS_NOTPRECALC | uc2const.cmsFLAGS_GAMUTCHECK) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_RELATIVE_COLORIMETRIC,
        uc2const.cmsFLAGS_PRESERVEBLACK |
        uc2const.cmsFLAGS_BLACKPOINTCOMPENSATION) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_RELATIVE_COLORIMETRIC,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_HIGHRESPRECALC) is not None
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8, IN_PROFILE, uc2const.TYPE_RGB_8,
        OUT_PROFILE, uc2const.INTENT_PERCEPTUAL,
        uc2const.INTENT_RELATIVE_COLORIMETRIC,
        uc2const.cmsFLAGS_NOTPRECALC |
        uc2const.cmsFLAGS_LOWRESPRECALC) is not None


def test_create_proofing_transform_with_invalid_intent():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, 3) is not None
    try:
        libcms.cms_create_proofing_transform(
            IN_PROFILE, uc2const.TYPE_RGB_8,
            IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, 4)
    except libcms.CmsError:
        return
    assert False


def test_create_proofing_transform_with_invalid_proofing_intent():
    assert libcms.cms_create_proofing_transform(
        IN_PROFILE, uc2const.TYPE_RGB_8,
        IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, 1, 2) is not None
    try:
        libcms.cms_create_proofing_transform(
            IN_PROFILE, uc2const.TYPE_RGB_8,
            IN_PROFILE, uc2const.TYPE_RGB_8, OUT_PROFILE, 1, 4)
    except libcms.CmsError:
        return
    assert False


# ---Alarmcodes related tests

def test_set_alarm_codes_with_null_values():
    try:
        libcms.cms_set_alarm_codes(0, 1, 1)
        libcms.cms_set_alarm_codes(1, 0, 1)
        libcms.cms_set_alarm_codes(1, 1, 0)
    except libcms.CmsError:
        assert False


def test_set_alarm_codes_with_lagest_values():
    try:
        libcms.cms_set_alarm_codes(0, 255, 255)
        libcms.cms_set_alarm_codes(255, 0, 255)
        libcms.cms_set_alarm_codes(255, 255, 0)
    except libcms.CmsError:
        assert False


def test_set_alarm_codes_with_incorrect_values():
    counter = 0
    try:
        libcms.cms_set_alarm_codes(256, 255, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(0, 256, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(0, 255, 256)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(-1, 255, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(255, -1, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(255, 255, -1)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(255, 255, .1)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(255, .1, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes(.1, 255, 255)
    except libcms.CmsError:
        counter += 1

    try:
        libcms.cms_set_alarm_codes("#fff", "#fff", "#fff")
    except libcms.CmsError:
        counter += 1

    assert counter == 10


# ---Color transformation related tests

def test_do_transform_with_null_input():
    rgb = [0, 0, 0, 0]
    cmyk = [0, 0, 0, 0]
    libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    assert cmyk[0] != 0
    assert cmyk[1] != 0
    assert cmyk[2] != 0
    assert cmyk[3] != 0


def test_do_transform_with_maximum_allowed_input():
    rgb = [0, 0, 0, 0]
    cmyk = [0, 0, 0, 0]
    rgb[0] = 255
    rgb[1] = 255
    rgb[2] = 255
    libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    assert 0 == cmyk[0]
    assert 0 == cmyk[1]
    assert 0 == cmyk[2]
    assert 0 == cmyk[3]


def test_do_transform_with_intermediate_input():
    rgb = [0, 0, 0, 0]
    cmyk = [0, 0, 0, 0]
    rgb[0] = 100
    rgb[1] = 190
    rgb[2] = 150
    libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    assert 0 != cmyk[0]
    assert 0 != cmyk[1]
    assert 0 != cmyk[2]
    assert 0 != cmyk[3]


def test_do_transform_with_incorrect_color_values():
    rgb = [0, 0, 0, 0]
    cmyk = [0, 0, 0, 0]
    rgb[0] = 455
    rgb[1] = 255
    rgb[2] = 255
    try:
        libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    except libcms.CmsError:
        assert False


def test_do_transform_with_incorrect_input_buffer():
    cmyk = [0, 0, 0, 0]
    rgb = 255
    try:
        libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    except libcms.CmsError:
        return
    assert False


def test_do_transform_with_incorrect_output_buffer():
    rgb = [0, 0, 0, 0]
    rgb[0] = 255
    rgb[1] = 255
    rgb[2] = 255
    cmyk = 255
    try:
        libcms.cms_do_transform(TRANSFORM, rgb, cmyk)
    except libcms.CmsError:
        return
    assert False


# ---Bitmap related tests

def test_do_bitmap_transform():
    in_image = PIL.Image.open(get_filepath('black100x100.png'))
    pixel = in_image.getpixel((1, 1))
    assert 3 == len(pixel)
    out_image = libcms.cms_do_bitmap_transform(
        TRANSFORM2, in_image, uc2const.TYPE_RGB_8, uc2const.TYPE_CMYK_8)
    pixel = out_image.getpixel((1, 1))
    assert 4 == len(pixel)

    in_image = PIL.Image.open(get_filepath('white100x100.png'))
    pixel = in_image.getpixel((1, 1))
    assert 3 == len(pixel)
    out_image = libcms.cms_do_bitmap_transform(
        TRANSFORM2, in_image, uc2const.TYPE_RGB_8, uc2const.TYPE_CMYK_8)
    pixel = out_image.getpixel((1, 1))
    assert 4 == len(pixel)

    in_image = PIL.Image.open(get_filepath('color100x100.png'))
    pixel = in_image.getpixel((1, 1))
    assert 3 == len(pixel)
    out_image = libcms.cms_do_bitmap_transform(
        TRANSFORM2, in_image, uc2const.TYPE_RGB_8, uc2const.TYPE_CMYK_8)
    pixel = out_image.getpixel((1, 1))
    assert 4 == len(pixel)


def test_do_bitmap_transform_with_unsupported_image():
    in_image = PIL.Image.open(get_filepath('black100x100.png'))
    in_image.load()
    in_image = in_image.convert("YCbCr")
    try:
        libcms.cms_do_bitmap_transform(
            TRANSFORM2, in_image, uc2const.TYPE_RGB_8, uc2const.TYPE_CMYK_8)
    except libcms.CmsError:
        return
    assert False


def test_do_bitmap_transform_with_unsupported_in_mode():
    in_image = PIL.Image.open(get_filepath('black100x100.png'))
    try:
        libcms.cms_do_bitmap_transform(
            TRANSFORM2, in_image, "YCbCr", uc2const.TYPE_CMYK_8)
    except libcms.CmsError:
        return
    assert False


def test_do_bitmap_transform_with_unsupported_out_mode():
    in_image = PIL.Image.open(get_filepath('black100x100.png'))
    try:
        libcms.cms_do_bitmap_transform(
            TRANSFORM2, in_image, uc2const.TYPE_RGB_8, "YCbCr")
    except libcms.CmsError:
        return
    assert False


# ---Profile info related tests

def test_get_profile_name():
    name = libcms.cms_get_profile_name(OUT_PROFILE)
    assert name == 'Fogra27L CMYK Coated Press'


def test_get_profile_info():
    name = libcms.cms_get_profile_info(OUT_PROFILE)
    assert name[:15] == 'Offset printing'


def test_get_profile_copyright():
    name = libcms.cms_get_profile_copyright(OUT_PROFILE)
    if os.name == 'nt':
        assert name == ''
    else:
        assert name == 'Public Domain'


# ---Embedded profile related tests
def test_get_embedded_profile():
    img = PIL.Image.open(get_filepath('CustomRGB.jpg'))
    profile = img.info.get('icc_profile')
    try:
        custom_profile = libcms.cms_open_profile_from_bytes(profile)
        transform = libcms.cms_create_transform(custom_profile,
                                                uc2const.TYPE_RGB_8,
                                                IN_PROFILE,
                                                uc2const.TYPE_RGB_8,
                                                uc2const.INTENT_PERCEPTUAL,
                                                uc2const.cmsFLAGS_NOTPRECALC)
        libcms.cms_do_bitmap_transform(
            transform, img, uc2const.TYPE_RGB_8, uc2const.TYPE_RGB_8)
    except libcms.CmsError:
        assert False
