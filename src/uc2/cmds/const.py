# -*- coding: utf-8 -*-
#
#  Copyright (C) 2021 by Ihor E. Novikov
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

from uc2 import uc2const


HELP_CMDS = ('--help', '-help', '--h', '-h')
DIR_CMDS = ('--package-dir', '-package-dir', '--pkg-dir', '-pkg-dir')
LOG_CMDS = ('--show-log', '-show-log', '--log', '-log')
VERBOSE_CMDS = ('--verbose', '-verbose', '-v', '--v')
VS_CMDS = ('--verbose-short', '-verbose-short', '-vs', '--vs')
CONFIG_CMDS = ('--configure', '-configure', '--config', '-config',
               '--preferences', '-preferences', '--prefs', '-prefs')
CFG_SHOW_CMDS = ('--show-config', '-show-config', '--show-prefs', '-show-prefs')
PARTS_CMDS = ('--parts', '-parts', '--components')

ALL_CMDS = HELP_CMDS + DIR_CMDS + LOG_CMDS + VERBOSE_CMDS + VS_CMDS + \
           CONFIG_CMDS + CFG_SHOW_CMDS + PARTS_CMDS

IMAGE_ACTIONS = ('--image-scale', '--image-antialiasing')

FIT_PAGE_TO_IMAGE = '--fit-page-to-image'
FIT_TO_PAGE = '--fit-to-page'
SK2_ACTIONS = (FIT_PAGE_TO_IMAGE, FIT_TO_PAGE)

SAVER_IDS = uc2const.PALETTE_SAVERS + uc2const.MODEL_SAVERS + uc2const.BITMAP_SAVERS
