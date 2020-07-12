# -*- coding: utf-8 -*-
#
#  Copyright (C) 2018-2020 by Ihor E. Novikov
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

from . import uc2const
from .uc2const import COLOR_DISPLAY

from .cms import (ColorManager, CS, libcms, val_255)

Application = tp.TypeVar('Application')


class AppColorManager(ColorManager):
    """Represents full-featured Color Manager for UniConvertor application
    """
    app: Application

    def __init__(self, app: Application) -> None:
        """Creates AppColorManager object for provided application instance

        :param app: (UCApplication) UniConvertor application handle
        """
        self.app = app
        ColorManager.__init__(self)

    def update_profiles(self) -> None:
        """Profile update method
        """
        config = self.app.config
        profiles = [config.cms_rgb_profile,
                    config.cms_cmyk_profile,
                    config.cms_lab_profile,
                    config.cms_gray_profile,
                    config.cms_display_profile]
        profile_dicts = [config.cms_rgb_profiles,
                         config.cms_cmyk_profiles,
                         config.cms_lab_profiles,
                         config.cms_gray_profiles,
                         config.cms_display_profiles]
        index = 0
        profile_dir = self.app.appdata.app_color_profile_dir
        for item in CS + [COLOR_DISPLAY, ]:
            path = None
            profile = profiles[index]
            if profile and profile in profile_dicts[index]:
                profile_filename = profile_dicts[index][profile]
                path = os.path.join(profile_dir, profile_filename)
            if path:
                self.handles[item] = libcms.cms_open_profile_from_file(path)
            else:
                profile_dir = self.app.appdata.app_color_profile_dir
                filename = 'built-in_%s.icm' % item
                path = os.path.join(profile_dir, filename)
                self.handles[item] = libcms.cms_open_profile_from_file(path)
            index += 1

    def _update_opts(self) -> None:
        """Color management options update method
        """
        config = self.app.config
        self.use_cms = config.cms_use
        self.use_display_profile = config.cms_use_display_profile
        self.rgb_intent = config.cms_rgb_intent
        self.cmyk_intent = config.cms_cmyk_intent
        self.flags = config.cms_flags
        self.proofing = config.cms_proofing
        self.alarm_codes = config.cms_alarmcodes
        self.gamutcheck = config.cms_gamutcheck
        if self.gamutcheck:
            libcms.cms_set_alarm_codes(*val_255(self.alarm_codes))
        self.proof_for_spot = config.cms_proof_for_spot
        if self.proofing:
            self.flags |= uc2const.cmsFLAGS_SOFTPROOFING
        if self.gamutcheck:
            self.flags |= uc2const.cmsFLAGS_GAMUTCHECK
        if config.cms_bpc_flag:
            self.flags |= uc2const.cmsFLAGS_BLACKPOINTCOMPENSATION
        if config.cms_bpt_flag:
            self.flags |= uc2const.cmsFLAGS_PRESERVEBLACK

    def update(self, *_args: tp.Any) -> None:
        """Event callable update method. Updates application color management after changes in preferences
        """
        self.handles = {}
        self.clear_transforms()
        self.update_profiles()
        self._update_opts()
