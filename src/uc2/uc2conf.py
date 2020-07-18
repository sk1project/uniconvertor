# -*- coding: utf-8 -*-
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

import os
import typing as tp

from . import uc2const
from .utils import sconfig


class UCData:
    app: uc2const.AppHandle
    app_name: str = 'UniConvertor'
    app_proc: str = 'uniconvertor'
    app_org: str = 'sK1 Project'
    app_domain: str = 'sk1project.net'
    app_icon = None
    doc_icon = None
    version: str = uc2const.VERSION
    revision: str = uc2const.REVISION
    build: str = uc2const.BUILD
    app_config: str = ''
    app_config_dir: str = ''
    app_color_profile_dir: str = ''

    def __init__(self, app: uc2const.AppHandle, cfgdir: str = '~', check: bool = True) -> None:
        """Creates UC Data instance

        :param app: (UCApplication) UniConvertor application handle
        :param cfgdir: (str) parent directory for '.config' folder
        :param check: (bool)
        """
        self.app = app
        self.app_config_dir = os.path.expanduser(os.path.join(cfgdir, '.config', 'uc2-py3'))
        self.check_config_dirs() if check else None

    def check_config_dirs(self) -> None:
        """Checks config directories structure. If wrong, fixes them.
        """
        if not os.path.exists(self.app_config_dir):
            os.makedirs(self.app_config_dir)

        self.app_config = os.path.join(self.app_config_dir, 'preferences.cfg')

        # Check color profiles directory
        self.app_color_profile_dir = os.path.join(self.app_config_dir, 'profiles')
        if not os.path.exists(self.app_color_profile_dir):
            os.makedirs(self.app_color_profile_dir)

        from .cms import libcms

        for item in uc2const.COLORSPACES + [uc2const.COLOR_DISPLAY, ]:
            path = os.path.join(self.app_color_profile_dir, 'built-in_%s.icm' % item)
            if not os.path.exists(path):
                libcms.cms_save_default_profile(path, item)


class UCConfig(sconfig.SerializedConfig):
    """Represents UCApplication config
    """
    # ============== GENERIC SECTION ===================
    log_level: str = 'INFO'

    # ============== COLOR MANAGEMENT SECTION ===================

    cms_use: bool = True
    cms_display_profiles: tp.Dict = {}
    cms_rgb_profiles: tp.Dict = {}
    cms_cmyk_profiles: tp.Dict = {}
    cms_lab_profiles: tp.Dict = {}
    cms_gray_profiles: tp.Dict = {}

    cms_rgb_profile: str = ''
    cms_cmyk_profile: str = ''
    cms_lab_profile: str = ''
    cms_gray_profile: str = ''
    cms_display_profile: str = ''

    cms_use_display_profile: bool = False

    cms_rgb_intent: int = uc2const.INTENT_RELATIVE_COLORIMETRIC
    cms_cmyk_intent: int = uc2const.INTENT_PERCEPTUAL

    cms_flags: int = uc2const.cmsFLAGS_NOTPRECALC
    cms_proofing: bool = False
    cms_gamutcheck: bool = False
    cms_alarmcodes: tp.List[float, float, float] = [1.0, 0.0, 1.0]
    cms_proof_for_spot: bool = False
    cms_bpc_flag: bool = False
    cms_bpt_flag: bool = False

    @staticmethod
    def get_defaults() -> tp.Dict:
        """Returns default values of UCConfig class

        :return: dict of default field values
        """
        return UCConfig.__dict__.copy()
