# -*- coding: utf-8 -*-
#
#  Copyright (C) 2019 by Ihor E. Novikov
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
import sys

from uc2 import events, msgconst
from .help import show_help, show_short_help
from .translate import convert, wildcard_convert, multiple_convert
from .translate import normalize_options
from .configure import show_config, change_config
from .parts import show_parts

HELP_CMDS = ('--help', '-help', '--h', '-h')
DIR_CMDS = ('--package-dir', '-package-dir', '--pkg-dir', '-pkg-dir')
LOG_CMDS = ('--show-log', '-show-log', '--log', '-log')
VERBOSE_CMDS = ('--verbose', '-verbose', '-v', '--v')
VS_CMDS = ('--verbose-short', '-verbose-short', '-vs', '--vs')
CONFIG_CMDS = ('--configure', '-configure', '--config', '-config',
               '--preferences', '-preferences', '--prefs', '-prefs')
CFG_SHOW_CMDS = ('--show-config', '-show-config', '--show-prefs', '-show-prefs')
PARTS_CMDS = ('--parts', '-parts', '--components')


def check_args(cmds):
    return any([cmd in sys.argv for cmd in cmds])


def parse_cmd_args(current_dir):
    files = []
    options_list = []
    options = {}

    for item in sys.argv[1:]:
        if item in VERBOSE_CMDS:
            options_list.append('--verbose')
        elif item in VS_CMDS:
            options_list.append('--verbose-short')
        elif item.startswith('--'):
            options_list.append(item)
        elif item.startswith('-'):
            msg = 'Unknown option "%s"' % item
            events.emit(events.MESSAGES, msgconst.WARNING, msg)
        else:
            if current_dir:
                if not os.path.dirname(item) or item.startswith('.'):
                    item = os.path.join(current_dir, item)
            if item.startswith('~'):
                item = os.path.expanduser(item)
            files.append(os.path.abspath(item))

    for item in options_list:
        result = item[2:].split('=', 1)
        if len(result) < 2:
            options[result[0]] = True
        else:
            key, value = result
            value = value.replace('"', '').replace("'", '')
            if value.isdigit():
                value = int(value)
            elif value.replace('.', '').isdigit():
                value = float(value)
            elif value.lower() in ('yes', 'no'):
                value = {'yes': True, 'no': False}[value.lower()]
            options[key] = value

    return files, options
