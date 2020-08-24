# -*- coding: utf-8 -*-
#
#  libcms - provides binding to LittleCMS2 library.
#
#  Copyright (C) 2012-2020 by Ihor E. Novikov
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

import os
import typing as tp

from PIL import Image

from uc2 import uc2const
from . import _lcms2


class CmsError(Exception):
    """CMS specific exception class
    """


def get_version() -> str:
    """Returns LCMS version.

    :rtype str
    :return: version string
    """
    ver = str(_lcms2.getVersion())
    return '%s.%s' % (ver[0], ver[2])


def cms_set_alarm_codes(r: int, g: int, b: int) -> None:
    """Used to define gamut check marker.
    r,g,b are expected to be integers in range 0..255

    :param r: (int) red channel
    :param g: (int) green channel
    :param b: (int) blue channel
    """
    if all([isinstance(ch, int) and 0 <= ch < 256 for ch in (r, g, b)]):
        _lcms2.setAlarmCodes(r, g, b)
    else:
        raise CmsError('r,g,b are expected as integers in range 0..255')


def cms_open_profile_from_file(profile_path: str) -> uc2const.PyCapsule:
    """Returns a handle to lcms profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :param profile_path: (str) a valid filename path to the ICC profile
    :return: PyCapsule handle to lcms profile
    """
    if not os.path.isfile(profile_path):
        raise CmsError('Invalid profile path provided: %s' % profile_path)

    result = _lcms2.openProfile(profile_path)

    if result is None:
        msg = 'It seems provided profile is invalid'
        raise CmsError(msg + ': %s' % profile_path)

    return result


def cms_open_profile_from_bytes(profile_bytes: bytes) -> uc2const.PyCapsule:
    """Returns a handle to lcms profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically.

    :param profile_bytes: (bytes) ICC profile as a python bytes
    :return: PyCapsule handle to lcms profile
    """

    if not profile_bytes:
        raise CmsError("Empty profile string provided")

    result = _lcms2.openProfileFromString(profile_bytes)

    if result is None:
        raise CmsError('It seems provided profile string is invalid!')

    return result


def cms_create_srgb_profile() -> uc2const.PyCapsule:
    """Artificial functionality. The function emulates built-in sRGB
    profile reading profile resource attached to the package.
    Returns a handle to lcms built-in sRGB profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :return: PyCapsule handle to lcms built-in sRGB profile
    """
    from .profiles import srgb_profile_rc
    profile = srgb_profile_rc.get_resource(True)
    return cms_open_profile_from_file(profile.name)


def get_srgb_profile_resource() -> tp.IO:
    """Returns named temporary file object of built-in sRGB profile.

    :return: sRGB profile file object
    """
    from .profiles import srgb_profile_rc
    return srgb_profile_rc.get_resource(True)


def save_srgb_profile(path: str) -> None:
    """Saves content of built-in sRGB profile.

    :param path: (str) sRGB profile path as a string
    """
    from .profiles import srgb_profile_rc
    srgb_profile_rc.save_resource(path)


def cms_create_cmyk_profile() -> uc2const.PyCapsule:
    """Artificial functionality. The function emulates built-in CMYK
    profile reading profile resource attached to the package.
    Returns a handle to lcms built-in CMYK profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :return: PyCapsule handle to lcms built-in CMYK profile
    """
    from .profiles import cmyk_profile_rc
    profile = cmyk_profile_rc.get_resource(True)
    return cms_open_profile_from_file(profile.name)


def get_cmyk_profile_resource() -> tp.IO:
    """Returns named temporary file object of built-in CMYK profile.

    :return: built-in CMYK profile file object
    """
    from .profiles import cmyk_profile_rc
    return cmyk_profile_rc.get_resource(True)


def save_cmyk_profile(path: str) -> None:
    """Saves content of built-in CMYK profile.

    :param path: (str) CMYK profile path as a string
    """
    from .profiles import cmyk_profile_rc
    cmyk_profile_rc.save_resource(path)


def cms_create_display_profile() -> uc2const.PyCapsule:
    """Artificial functionality. The function emulates built-in display
    profile reading profile resource attached to the package.
    Returns a handle to lcms built-in display profile wrapped
    as a Python object.

    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :return: PyCapsule handle to lcms built-in display profile
    """
    from .profiles import display_profile_rc
    profile = display_profile_rc.get_resource(True)
    return cms_open_profile_from_file(profile.name)


def get_display_profile_resource() -> tp.IO:
    """Returns named temporary file object of built-in display profile.

    :return: built-in display profile file object
    """
    from .profiles import display_profile_rc
    return display_profile_rc.get_resource(True)


def save_display_profile(path: str) -> None:
    """Saves content of built-in display profile.

    :param path: (str) display profile path as a string
    """
    from .profiles import display_profile_rc
    display_profile_rc.save_resource(path)


def cms_create_lab_profile() -> uc2const.PyCapsule:
    """Artificial functionality. The function emulates built-in Lab
    profile reading profile resource attached to the package.
    Returns a handle to lcms built-in Lab profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :return: PyCapsule handle to lcms built-in display profile
    """
    from .profiles import lab_profile_rc
    profile = lab_profile_rc.get_resource(True)
    return cms_open_profile_from_file(profile.name)


def get_lab_profile_resource() -> tp.IO:
    """Returns named temporary file object of built-in Lab profile.

    :return: built-in Lab profile file object
    """
    from .profiles import lab_profile_rc
    return lab_profile_rc.get_resource(True)


def save_lab_profile(path: str) -> None:
    """Saves content of built-in Lab profile.

    :param path: (str) Lab profile path as a string
    """
    from .profiles import lab_profile_rc
    lab_profile_rc.save_resource(path)


def cms_create_gray_profile() -> uc2const.PyCapsule:
    """Artificial functionality. The function emulates built-in Gray
    profile reading profile resource attached to the package.
    Returns a handle to lcms built-in Gray profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :return: PyCapsule handle to lcms built-in Gray profile
    """
    from .profiles import gray_profile_rc
    profile = gray_profile_rc.get_resource(True)
    return cms_open_profile_from_file(profile.name)


def get_gray_profile_resource() -> tp.IO:
    """Returns named temporary file object of built-in Gray profile.

    :return: built-in Gray profile file object
    """
    from .profiles import gray_profile_rc
    return gray_profile_rc.get_resource(True)


def save_gray_profile(path: str) -> None:
    """Saves content of built-in Gray profile.

    :param path: Gray profile path as a string
    """
    from .profiles import gray_profile_rc
    gray_profile_rc.save_resource(path)


COLOR_FUNC_MAP = {
    uc2const.COLOR_RGB: (cms_create_srgb_profile, get_srgb_profile_resource, save_srgb_profile),
    uc2const.COLOR_CMYK: (cms_create_cmyk_profile, get_cmyk_profile_resource, save_cmyk_profile),
    uc2const.COLOR_LAB: (cms_create_lab_profile, get_lab_profile_resource, save_lab_profile),
    uc2const.COLOR_GRAY: (cms_create_gray_profile, get_gray_profile_resource, save_gray_profile),
    uc2const.COLOR_DISPLAY: (cms_create_display_profile, get_display_profile_resource, save_display_profile),
}


def cms_create_default_profile(colorspace: str) -> tp.Optional[uc2const.PyCapsule]:
    """Artificial functionality. The function emulates built-in
    profile reading according profile resource attached to the package.
    Returns a handle to lcms built-in profile wrapped as a Python object.
    The handle doesn't require to be closed after usage because
    on object delete operation Python calls native cms_close_profile()
    function automatically

    :param colorspace: (str) colorspace constant
    :return: PyCapsule handle to lcms profile or None
    """
    profile = COLOR_FUNC_MAP.get(colorspace, None)
    return None if profile is None else profile[0]()


def cms_get_default_profile_resource(colorspace: str) -> tp.Optional[tp.IO]:
    """Artificial functionality.
    Returns temporary named file object.

    :param colorspace: (str) colorspace constant
    :return: built-in profile file object or None
    """
    profile = COLOR_FUNC_MAP.get(colorspace, None)
    return None if profile is None else profile[1]()


def cms_save_default_profile(path: str, colorspace: str):
    """Artificial functionality.
    Saves content of built-in specified profile.

    :param path: (str) profile path as a string
    :param colorspace: (str) colorspace constant
    """
    profile = COLOR_FUNC_MAP.get(colorspace, None)
    if profile is not None:
        profile[2](path)
    else:
        raise CmsError('Unexpected colorspace requested %s' % str(colorspace))


INTENTS: tp.List[int] = [uc2const.INTENT_PERCEPTUAL,
                         uc2const.INTENT_RELATIVE_COLORIMETRIC,
                         uc2const.INTENT_SATURATION,
                         uc2const.INTENT_ABSOLUTE_COLORIMETRIC]


def cms_create_transform(in_profile: uc2const.PyCapsule, in_mode: str,
                         out_profile: uc2const.PyCapsule, out_mode: str,
                         intent: int = uc2const.INTENT_PERCEPTUAL,
                         flags: int = uc2const.cmsFLAGS_NOTPRECALC) -> uc2const.PyCapsule:
    """Returns a handle to lcms transformation wrapped as a Python object.

    :param in_profile: (uc2const.PyCapsule) valid lcms profile handle
    :param in_mode: (str) valid lcms or PIL mode
    :param out_profile: (uc2const.PyCapsule) valid lcms profile handle
    :param out_mode: (str) valid lcms or PIL mode
    :param intent: (int) integer constant (0-3) of transform rendering intent
    :param flags: (int) lcms flags

    :return: PyCapsule handle to lcms transformation
    """

    if intent not in INTENTS:
        raise CmsError('renderingIntent must be an integer between 0 and 3')

    result = _lcms2.buildTransform(in_profile, in_mode, out_profile, out_mode, intent, flags)

    if result is None:
        msg = 'Cannot create requested transform'
        raise CmsError("%s: %s %s" % (msg, in_mode, out_mode))

    return result


def cms_create_proofing_transform(in_profile: uc2const.PyCapsule, in_mode: str,
                                  out_profile: uc2const.PyCapsule, out_mode: str,
                                  proof_profile: uc2const.PyCapsule,
                                  intent: int = uc2const.INTENT_PERCEPTUAL,
                                  pintent: int = uc2const.INTENT_RELATIVE_COLORIMETRIC,
                                  flags: int = uc2const.cmsFLAGS_SOFTPROOFING) -> uc2const.PyCapsule:
    """Returns a handle to lcms transformation wrapped as a Python object.

    :param in_profile: (uc2const.PyCapsule) valid lcms profile handle
    :param in_mode: (str) valid lcms or PIL mode
    :param out_profile: (uc2const.PyCapsule) valid lcms profile handle
    :param out_mode: (str) valid lcms or PIL mode
    :param proof_profile: (uc2const.PyCapsule) valid lcms profile handle
    :param intent: (int) integer constant (0-3) of transform rendering intent
    :param pintent:  (int) integer constant (0-3) of transform proofing intent
    :param flags: (int) lcms flags

    :return: PyCapsule handle to lcms transformation
    """

    if intent not in INTENTS:
        raise CmsError('Rendering intent must be an integer between 0 and 3')

    if pintent not in INTENTS:
        raise CmsError('Proofing intent must be an integer between 0 and 3')

    result = _lcms2.buildProofingTransform(in_profile, in_mode,
                                           out_profile, out_mode,
                                           proof_profile, intent,
                                           pintent, flags)

    if result is None:
        msg = 'Cannot create requested proofing transform'
        raise CmsError("%s: %s %s" % (msg, in_mode, out_mode))

    return result


def cms_do_transform(transform: uc2const.PyCapsule, inbuff: tp.List[int], outbuff: tp.List[int]) -> None:
    """Transform color values from inputBuffer to outputBuffer using provided
    lcms transform handle.

    :param transform: (uc2const.PyCapsule) valid lcms transformation handle
    :param inbuff: (list) 4-member list. The members should be between 0 and 255
    :param outbuff: (list) 4-member list. The members should be between 0 and 255
    """
    if isinstance(inbuff, list) and isinstance(outbuff, list):
        outbuff[:] = _lcms2.transformPixel(transform, *inbuff)
    else:
        msg = 'inbuff and outbuff must be Python 4-member list objects'
        raise CmsError(msg)


def cms_do_bitmap_transform(transform: uc2const.PyCapsule, image: Image.Image,
                            in_mode: str, out_mode: str) -> Image.Image:
    """Provides PIL images support for color management.
    Currently supports L, RGB, CMYK and LAB modes only.

    :param transform: (uc2const.PyCapsule) valid lcms transformation handle
    :param image: (Image.Image) valid PIL image object
    :param in_mode: (str) valid lcms or PIL mode
    :param out_mode: (str) valid lcms or PIL mode

    :return: new PIL image object in out_mode colorspace
    """

    if image.mode not in uc2const.IMAGE_COLORSPACES:
        raise CmsError('Unsupported image type: %s' % image.mode)

    if in_mode not in uc2const.IMAGE_COLORSPACES:
        raise CmsError('Unsupported in_mode type: %s' % in_mode)

    if out_mode not in uc2const.IMAGE_COLORSPACES:
        raise CmsError('unsupported out_mode type: %s' % out_mode)

    w, h = image.size
    image.load()
    new_image = Image.new(out_mode, (w, h))

    _lcms2.transformBitmap(transform, image.im, new_image.im, w, h)

    return new_image


def cms_get_profile_name(profile: uc2const.PyCapsule) -> str:
    """Returns profile name

    :param profile: (uc2const.PyCapsule) valid lcms profile handle
    :return: profile name string
    """
    return _lcms2.getProfileName(profile).decode('cp1252').strip()


def cms_get_profile_info(profile: uc2const.PyCapsule) -> str:
    """Returns profile description info

    :param profile: (uc2const.PyCapsule) valid lcms profile handle
    :return: profile description info string
    """
    return _lcms2.getProfileInfo(profile).decode('cp1252').strip()


def cms_get_profile_copyright(profile: uc2const.PyCapsule) -> str:
    """Returns profile copyright info

    :param profile: (uc2const.PyCapsule) valid lcms profile handle
    :return: profile copyright info string
    """
    return _lcms2.getProfileInfoCopyright(profile).decode('cp1252').strip()
