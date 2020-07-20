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

import typing as tp
from copy import deepcopy

from PIL import Image

from uc2 import uc2const
from . import cs
from . import libcms


class AbstractColorManager:
    """The class provides abstract color manager.
    On CM object instantiation default built-in profiles
    are used to create internal stuff.
    """

    handles: tp.Dict[str, uc2const.PyCapsule]
    transforms: tp.Dict[str, uc2const.PyCapsule]
    proof_transforms: tp.Dict[str, uc2const.PyCapsule]

    use_cms: bool = True
    use_display_profile: bool = False
    proofing: bool = False
    gamutcheck: bool = False
    alarm_codes = (0.0, 1.0, 1.0)
    proof_for_spot: bool = False

    rgb_intent: int = uc2const.INTENT_RELATIVE_COLORIMETRIC
    cmyk_intent: int = uc2const.INTENT_PERCEPTUAL
    flags: int = uc2const.cmsFLAGS_NOTPRECALC

    def __init__(self) -> None:
        self.update()

    def update(self) -> None:
        """Sets color profile handles using built-in profiles
        """
        self.clear_transforms()
        self.handles = {item: libcms.cms_create_default_profile(item) for item in uc2const.COLORSPACES}

    def clear_transforms(self) -> None:
        self.transforms, self.proof_transforms = {}, {}

    def get_transform(self, cs_in: str, cs_out: str) -> uc2const.PyCapsule:
        """Returns requested color transform using self.transforms dict.
        If requested transform is not initialized yet, creates it.

        :param cs_in: (str) incoming color space
        :param cs_out: (str) outgoing color space
        :return: (uc2const.PyCapsule) transformation handle
        """
        tr_type = cs_in + cs_out
        intent = self.cmyk_intent if cs_out == uc2const.COLOR_CMYK else self.rgb_intent
        if tr_type not in self.transforms:
            handle_in = self.handles[cs_in]
            handle_out = self.handles[cs_out]
            cs_out = uc2const.COLOR_RGB if cs_out == uc2const.COLOR_DISPLAY else cs_out
            self.transforms[tr_type] = libcms.cms_create_transform(
                handle_in, cs_in,
                handle_out, cs_out,
                intent, self.flags)
        return self.transforms[tr_type]

    def get_proof_transform(self, cs_in: str) -> uc2const.PyCapsule:
        """Returns requested proof transform using self.proof_transforms dict.
        If requested transform is not initialized yet, creates it.

        :param cs_in: (str) incoming color space
        :return: (uc2const.PyCapsule) proof transformation handle
        """
        tr_type = cs_in
        if tr_type not in self.proof_transforms:
            handle_in = self.handles[cs_in]
            if self.use_display_profile and uc2const.COLOR_DISPLAY in self.handles:
                handle_out = self.handles[uc2const.COLOR_DISPLAY]
            else:
                handle_out = self.handles[uc2const.COLOR_RGB]
            handle_proof = self.handles[uc2const.COLOR_CMYK]
            self.proof_transforms[tr_type] = libcms.cms_create_proofing_transform(
                handle_in, cs_in,
                handle_out, uc2const.COLOR_RGB,
                handle_proof,
                self.cmyk_intent,
                self.rgb_intent,
                self.flags)
        return self.proof_transforms[tr_type]

    def do_transform(self, color: uc2const.ColorType, cs_in: str, cs_out: str) -> uc2const.ColorType:
        """Converts color between colorspaces.
        Returns list of color values.

        :param color: (uc2const.ColorType) original color
        :param cs_in: (str) incoming color space
        :param cs_out: (str) outgoing color space
        :return: (uc2const.ColorType) transformed color
        """
        if not self.use_cms:
            return cs.do_simple_transform(color[1], cs_in, cs_out)
        in_color = cs.colorb(color)
        out_color = cs.colorb()
        transform = self.get_transform(cs_in, cs_out)
        libcms.cms_do_transform(transform, in_color, out_color)
        return cs.decode_colorb(out_color, cs_out)

    def do_bitmap_transform(self, img: Image, mode: str, cs_out: tp.Union[str, None] = None) -> Image:
        """Does image proof transform. Returns new image instance.

        :param img: (Image) Pillow Image instance
        :param mode: (str) Pillow Image mode
        :param cs_out: (str) outgoing image color space
        :return: (Image) Transformed Pillow Image instance
        """
        if not self.use_cms and not img.mode == uc2const.IMAGE_LAB:
            return img.convert(mode)
        cs_in = uc2const.IMAGE_TO_COLOR[img.mode]
        if not cs_out:
            cs_out = uc2const.IMAGE_TO_COLOR[mode]
        transform = self.get_transform(cs_in, cs_out)
        return libcms.cms_do_bitmap_transform(transform, img, img.mode, mode)

    def do_proof_transform(self, color: uc2const.ColorType, cs_in) -> uc2const.ColorType:
        """Does color proof transform. Returns list of color values.

        :param color: (uc2const.ColorType) original color
        :param cs_in: (str) incoming color space
        :return: (uc2const.ColorType) transformed color
        """
        in_color = cs.colorb(color)
        out_color = cs.colorb()
        transform = self.get_proof_transform(cs_in)
        libcms.cms_do_transform(transform, in_color, out_color)
        return cs.decode_colorb(out_color, uc2const.COLOR_RGB)

    def do_proof_bitmap_transform(self, img: Image) -> Image:
        """Does image proof transform. Returns new image instance.

        :param img: (Image) Pillow Image instance
        :return: (Image) Transformed Pillow Image instance
        """
        cs_in = uc2const.IMAGE_TO_COLOR[img.mode]
        mode = uc2const.IMAGE_RGB
        transform = self.get_proof_transform(cs_in)
        return libcms.cms_do_bitmap_transform(transform, img, img.mode, mode)

    # Color management API
    def get_rgb_color(self, color: uc2const.ColorType) -> uc2const.ColorType:
        """Convert color into RGB color. Stores alpha channel and color name.

        :param color: (uc2const.ColorType) original color
        :return: (uc2const.ColorType) RGB color
        """
        if color[0] == uc2const.COLOR_RGB:
            return deepcopy(color)
        if color[0] == uc2const.COLOR_SPOT:
            if color[1][0]:
                return [uc2const.COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                clr = [uc2const.COLOR_CMYK, [] + color[1][1], color[2], color[3]]
            return self.get_rgb_color(clr)
        res = self.do_transform(color, color[0], uc2const.COLOR_RGB)
        return [uc2const.COLOR_RGB, res, color[2], color[3]]

    def get_rgb_color255(self, color: uc2const.ColorType) -> tp.List[float]:
        """Convert color into RGB color. Returns RGB color value list only.

        :param color: (uc2const.ColorType) original color
        :return: (list) RGB color values
        """
        return cs.val_255(self.get_rgb_color(color)[1])

    def get_rgba_color255(self, color: uc2const.ColorType) -> tp.List[float]:
        """Convert color into RGB color. Returns RGBA color value list only.

        :param color: (uc2const.ColorType) original color
        :return: (list) RGBA color values
        """
        clr = self.get_rgb_color(color)
        clr[1].append(clr[2])
        return cs.val_255(clr[1])

    def get_cmyk_color(self, color: uc2const.ColorType) -> uc2const.ColorType:
        """Convert color into CMYK color. Stores alpha channel and color name.

        :param color: (uc2const.ColorType) original color
        :return: (uc2const.ColorType) transformed CMYK color
        """
        if color[0] == uc2const.COLOR_CMYK:
            return deepcopy(color)
        if color[0] == uc2const.COLOR_SPOT:
            if color[1][1]:
                return [uc2const.COLOR_CMYK, [] + color[1][1], color[2], color[3]]
            else:
                clr = [uc2const.COLOR_RGB, [] + color[1][0], color[2], color[3]]
                return self.get_cmyk_color(clr)
        res = self.do_transform(color, color[0], uc2const.COLOR_CMYK)
        return [uc2const.COLOR_CMYK, res, color[2], color[3]]

    def get_cmyk_color255(self, color: uc2const.ColorType) -> tp.List[float]:
        """Convert color into CMYK color. Returns CMYK color value list only.

        :param color: (uc2const.ColorType) original color
        :return: (list) CMYK color values
        """
        return cs.val_255(self.get_cmyk_color(color)[1])

    def get_lab_color(self, color: uc2const.ColorType) -> uc2const.ColorType:
        """Convert color into L*a*b* color. Stores alpha channel and color name.

        :param color: (uc2const.ColorType) original color
        :return: (uc2const.ColorType) L*a*b* color
        """
        if color[0] == uc2const.COLOR_LAB:
            return deepcopy(color)
        if color[0] == uc2const.COLOR_SPOT:
            if color[1][0]:
                color = [uc2const.COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                color = [uc2const.COLOR_CMYK, [] + color[1][1], color[2], color[3]]
        res = self.do_transform(color, color[0], uc2const.COLOR_LAB)
        return [uc2const.COLOR_LAB, res, color[2], color[3]]

    def get_grayscale_color(self, color: uc2const.ColorType) -> uc2const.ColorType:
        """Convert color into Grayscale color. Stores alpha channel and color name.

        :param color: (uc2const.ColorType) original color
        :return: (uc2const.ColorType) Grayscale color
        """
        if color[0] == uc2const.COLOR_GRAY:
            return deepcopy(color)
        if color[0] == uc2const.COLOR_SPOT:
            if color[1][0]:
                color = [uc2const.COLOR_RGB, [] + color[1][0], color[2], color[3]]
            else:
                color = [uc2const.COLOR_CMYK, [] + color[1][1], color[2], color[3]]
        res = self.do_transform(color, color[0], uc2const.COLOR_GRAY)
        return [uc2const.COLOR_GRAY, res, color[2], color[3]]

    def get_color(self, color: uc2const.ColorType, colorspace: str = uc2const.COLOR_RGB) -> uc2const.ColorType:
        """Convert color into requested color space. Stores alpha channel and color name.

        :param color: (uc2const.ColorType) original color
        :param colorspace: (str) outgoing color space
        :return: (uc2const.ColorType) transformed color
        """
        methods_map: tp.Dict[str, tp.Callable] = {
            uc2const.COLOR_RGB: self.get_rgb_color,
            uc2const.COLOR_LAB: self.get_lab_color,
            uc2const.COLOR_CMYK: self.get_cmyk_color,
            uc2const.COLOR_GRAY: self.get_grayscale_color}
        return methods_map[colorspace](color=color)

    @staticmethod
    def mix_colors(color0: uc2const.ColorType,
                   color1: uc2const.ColorType, coef: float = .5) -> tp.Union[uc2const.ColorType, None]:
        """Mixes two color with identical color spaces.

        :param color0: (uc2const.ColorType) first color
        :param color1: (uc2const.ColorType) second color
        :param coef: (float) mixing coefficient
        :return: (uc2const.ColorType) mixed color
        """
        supported = [uc2const.COLOR_RGB, uc2const.COLOR_CMYK, uc2const.COLOR_GRAY]
        if all([color0[0] in supported, color1[0] in supported, color0[0] == color1[0]]):
            color_values = cs.mix_lists(color0[1], color1[1], coef)
            alpha = cs.mix_vals(color0[2], color1[2], coef)
            return [color0[0], color_values, alpha, '']

    def get_display_color(self, color: uc2const.ColorType) -> tp.List[float]:
        """Calcs display color representation. Returns list of RGB values.

        :param color: (uc2const.ColorType) original color
        :return: (list) display color float values (0.0-1.0)
        """
        if not self.use_cms:
            return self.get_rgb_color(color)[1]

        if color == uc2const.COLOR_SPOT:
            if self.proof_for_spot:
                color = self.get_cmyk_color(color)
            else:
                color = self.get_rgb_color(color)

        cs_in = color[0]
        cs_out = uc2const.COLOR_RGB
        if self.use_display_profile and uc2const.COLOR_DISPLAY in self.handles:
            cs_out = uc2const.COLOR_DISPLAY
        if self.proofing:
            if cs_in == uc2const.COLOR_CMYK:
                ret = self.do_transform(color, cs_in, cs_out)
            elif cs_in == uc2const.COLOR_SPOT:
                if self.proof_for_spot:
                    color = self.get_cmyk_color(color)
                else:
                    color = self.get_rgb_color(color)
                if color[0] == cs_out:
                    ret = color[1]
                else:
                    ret = self.do_transform(color, color[0], cs_out)
            else:
                ret = self.do_proof_transform(color, cs_in)
        else:
            if cs_in == cs_out:
                ret = color[1]
            elif cs_in == uc2const.COLOR_SPOT:
                color = self.get_rgb_color(color)
                if color[0] == cs_out:
                    ret = color[1]
                else:
                    ret = self.do_transform(color, color[0], cs_out)
            else:
                ret = self.do_transform(color, cs_in, cs_out)
        return ret

    def get_display_color255(self, color: uc2const.ColorType) -> tp.List[float]:
        """Calcs display color representation. Returns list of RGB float values.

        :param color: (uc2const.ColorType) original color
        :return: (list) display color integer values (0-255)
        """
        return cs.val_255(self.get_display_color(color))

    def convert_image(self, img: Image, outmode: str, cs_out: tp.Union[str, None] = None) -> Image:
        """Converts image between color spaces and image modes. Returns new image instance.

        :param img: (Image) Pillow Image instance
        :param outmode: (str) outgoing Pillow Image mode
        :param cs_out: (str) outgoing image color space or None
        :return: (Image) Transformed Pillow Image instance
        """
        if img.mode == uc2const.IMAGE_MONO:
            img = img.convert(uc2const.IMAGE_GRAY)
        if img.mode == outmode:
            return img.copy()
        if outmode == uc2const.IMAGE_MONO:
            ret = self.do_bitmap_transform(img, uc2const.IMAGE_GRAY, cs_out)
            return ret.convert(uc2const.IMAGE_MONO)
        return self.do_bitmap_transform(img, outmode, cs_out)

    def adjust_image(self, img: Image, profile_bytes: bytes) -> Image:
        """Adjust image with embedded profile to similar color space defined by current profile.
        Returns new image instance.


        :param img: (Image) Pillow Image instance
        :param profile_bytes: (bytes) embedded profile as a python bytes sequence
        :return: (Image) Transformed Pillow Image instance
        """
        custom_profile = libcms.cms_open_profile_from_bytes(profile_bytes)
        cs_in = cs_out = uc2const.IMAGE_TO_COLOR[img.mode]
        out_profile = self.handles[cs_in]
        intent = self.cmyk_intent if cs_out == uc2const.COLOR_CMYK else self.rgb_intent
        transform = libcms.cms_create_transform(
            custom_profile, cs_in, out_profile, cs_out, intent, self.flags)
        return libcms.cms_do_bitmap_transform(transform, img, cs_in, cs_out)

    def get_display_image(self, img: Image) -> Image:
        """Creates display image representation. Returns new image instance.

        :param img: (Image) Pillow Image instance
        :return: (Image) Transformed Pillow Image instance
        """
        outmode = uc2const.IMAGE_RGB
        cs_out = None

        if not self.use_cms:
            return self.convert_image(img, outmode)

        if self.use_display_profile and uc2const.COLOR_DISPLAY in self.handles:
            cs_out = uc2const.COLOR_DISPLAY

        if self.proofing:
            if img.mode == uc2const.IMAGE_CMYK:
                return self.convert_image(img, outmode, cs_out)
            else:
                return self.do_proof_bitmap_transform(img)
        else:
            return self.convert_image(img, outmode, cs_out)

    @staticmethod
    def get_color_name(color: uc2const.ColorType) -> str:
        """Extracts color name from provided color

        :param color: (uc2const.ColorType) original color
        :return: (str) color_name
        """
        return color[3] if len(color) > 3 else ''
