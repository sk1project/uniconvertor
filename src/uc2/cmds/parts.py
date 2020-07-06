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

import sys

from uc2.utils.mixutils import echo

ALIGNMENT = 25


def _show_part(name, value):
    value = value.replace('\n', '')
    msg = ' ' * 4 + name + '.' * (ALIGNMENT - len(name)) + '[ %s ]' % value
    echo(msg)


def show_parts(appdata):
    echo()
    mark = '' if not appdata.build \
        else ' build %s' % appdata.build
    app_name = '%s %s%s%s' % (appdata.app_name, appdata.version,
                              appdata.revision, mark)
    echo('%s components:\n' % app_name)
    part = ''
    try:
        part = 'Python'
        _show_part(part, sys.version)

        part = 'LCMS'
        from uc2 import cms
        _show_part(part, cms.libcms.get_version())

    except Exception as e:
        _show_part(part, 'FAIL')
        echo('Reason: %s' % str(e))
    echo()
