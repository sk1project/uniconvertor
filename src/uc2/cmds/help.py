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

import datetime

from uc2 import uc2const
from uc2.utils.mixutils import echo

HELP_TEMPLATE = '''
%s

Color palette translator
copyright (C) 2018-%s sK1 Project Team (https://sk1project.net/color-picker/)
For detailed help visit https://sk1project.net/color-picker/help/

Usage: color-picker-cmd [OPTIONS] INPUT_FILE OUTPUT_FILE
Example: color-picker-cmd drawing.cdr drawing.svg

 Available options:
 -h, --help      Display this help and exit
 -v, --verbose   Show internal logs
 --log=          Logging level: DEBUG, INFO, WARN, ERROR (by default, INFO)
 --format=       Type of output file format (values provided below)
 --package-dir   Show installation directory (for import as Python package)
 --show-log      Show detailed log of previous run
 
---Bulk operations:---------------------------------
 
Usage: color-picker-cmd [OPTIONS] FILE_PATTERN OUTPUT_DIRECTORY
Example: color-picker-cmd --recursive --format=GPL ~/palettes/*.ase ~/palettes_gpl/

 Available options:
 -vs, --verbose-short    Show minimized internal logs
 --dry-run               Execute command without translation
 --recursive             Recursive scanning
 
---Configuring:-------------------------------------

Usage: color-picker-cmd --configure [OPTIONS]
Example: color-picker-cmd --configure --cms_use=yes

 Available options:
 color-picker-cmd --show-config

---INPUT FILE FORMATS-------------------------------

   %s

---OUTPUT FILE FORMATS------------------------------

   %s

----------------------------------------------------
'''


def _get_infos(loaders):
    result = []
    for loader in loaders:
        if loader in (uc2const.COREL_PAL, uc2const.SCRIBUS_PAL):
            desc = uc2const.FORMAT_DESCRIPTION[loader]
            desc = desc.replace(' - ', ') - ')
            result.append('%s (%s' % (uc2const.FORMAT_NAMES[loader], desc))
        else:
            result.append(uc2const.FORMAT_DESCRIPTION[loader])
    return '\n   '.join(result)


def show_help(appdata):
    mark = '' if not appdata.build \
        else ' build %s' % appdata.build
    app_name = '%s %s%s%s' % (appdata.app_name, appdata.version,
                              appdata.revision, mark)
    echo(HELP_TEMPLATE % (app_name, str(datetime.date.today().year),
                          _get_infos(uc2const.PALETTE_LOADERS),
                          _get_infos(uc2const.PALETTE_SAVERS),))


def show_short_help(msg):
    echo()
    echo(msg)
    echo('USAGE: color-picker-cmd [OPTIONS] [INPUT FILE] [OUTPUT FILE]')
    echo('Use --help for more details.')
    echo('For detailed help visit '
         'https://sk1project.net/color-picker/help/' + '\n')
