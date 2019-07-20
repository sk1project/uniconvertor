# -*- coding: utf-8 -*-
#
#  Copyright (C) 2019 by Igor E. Novikov
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
import shutil

import uc2
from uc2 import uc2const, cms
from uc2.utils import fsutils
from uc2.utils.mixutils import echo

LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

DEFAULT_RGB = 'Built-in RGB profile'
DEFAULT_CMYK = 'Built-in CMYK profile'
DEFAULT_LAB = 'Built-in Lab profile'
DEFAULT_GRAY = 'Built-in Grayscale profile'

INTENTS = {
    uc2const.INTENT_PERCEPTUAL: 'PERCEPTUAL',
    uc2const.INTENT_RELATIVE_COLORIMETRIC: 'RELATIVE_COLORIMETRIC',
    uc2const.INTENT_SATURATION: 'SATURATION',
    uc2const.INTENT_ABSOLUTE_COLORIMETRIC: 'ABSOLUTE_COLORIMETRIC',
    'PERCEPTUAL': uc2const.INTENT_PERCEPTUAL,
    'RELATIVE_COLORIMETRIC': uc2const.INTENT_RELATIVE_COLORIMETRIC,
    'SATURATION': uc2const.INTENT_SATURATION,
    'ABSOLUTE_COLORIMETRIC': uc2const.INTENT_ABSOLUTE_COLORIMETRIC,
}

BOOL_ATTRS = ('cms_use', 'black_point_compensation',
              'black_preserving_transform')
INTENT_ATTRS = ('cms_rgb_intent', 'cms_cmyk_intent')
PROFILES = ('cms_rgb_profile', 'cms_cmyk_profile',
            'cms_lab_profile', 'cms_gray_profile')
PROFILE_DICTS = ('cms_rgb_profiles', 'cms_cmyk_profiles',
                 'cms_lab_profiles', 'cms_gray_profiles')


def to_bool(val):
    return 'yes' if val else 'no'


def show_config():
    config = uc2.config
    echo()
    echo('UniConvertor 2.0 preferences:\n')
    echo('  --log_level=%s' % config.log_level)
    echo()
    echo('  --cms_use=%s' % to_bool(config.cms_use))
    echo('  --cms_rgb_profile="%s"' % (config.cms_rgb_profile or DEFAULT_RGB))
    echo('  --cms_cmyk_profile="%s"' % (config.cms_cmyk_profile or DEFAULT_CMYK))
    echo('  --cms_lab_profile="%s"' % (config.cms_lab_profile or DEFAULT_LAB))
    echo('  --cms_gray_profile="%s"' % (config.cms_gray_profile or DEFAULT_GRAY))
    echo()
    echo('  --cms_rgb_intent="%s"' % INTENTS[config.cms_rgb_intent])
    echo('  --cms_cmyk_intent="%s"' % INTENTS[config.cms_cmyk_intent])
    echo()
    echo('  --black_point_compensation=%s' % to_bool(config.cms_bpc_flag))
    echo('  --black_preserving_transform=%s' % to_bool(config.cms_bpt_flag))
    echo()


def change_config(options):
    config = uc2.config
    for key, value in options.items():
        if key in BOOL_ATTRS:
            config.__dict__[key] = bool(value)
        elif key == 'log_level':
            if value in LEVELS:
                config.log_level = value
        elif key in INTENT_ATTRS:
            if isinstance(value, int) and value in INTENTS:
                config.__dict__[key] = value
            elif value in INTENTS:
                config.__dict__[key] = INTENTS[value]
        elif key in PROFILES and isinstance(value, str):
            if not value:
                config.__dict__[key] = ''
                continue
            cs = uc2const.COLORSPACES[PROFILES.index(key)]
            path = fsutils.normalize_path(value)
            if not fsutils.exists(path):
                echo('ERROR: file "%s" is not found!' % path)
                continue
            profile_name = cms.get_profile_name(path)
            if not profile_name:
                echo('ERROR: file "%s" is not valid color profile!' % path)
                continue
            profile_dir = config.app.appdata.app_color_profile_dir
            dest_path = os.path.join(profile_dir, '%s.icc' % cs)
            if fsutils.exists(dest_path):
                os.remove(dest_path)
            shutil.copy(path, dest_path)
            profile_dict = PROFILE_DICTS[PROFILES.index(key)]
            config.__dict__[profile_dict] = {profile_name: dest_path}
            config.__dict__[key] = profile_name
