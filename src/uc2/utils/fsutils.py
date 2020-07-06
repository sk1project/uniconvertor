# -*- coding: utf-8 -*-
#
#  Copyright (C) 2003-2019 by Igor E. Novikov
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


import errno
import logging
import os
import sys

from uc2 import _, events, msgconst
from uc2.utils import system

LOG = logging.getLogger(__name__)

# Platform
IS_MSW = system.get_os_family() == system.WINDOWS
IS_MAC = system.get_os_family() == system.MACOS

HOME = os.path.expanduser('~')


def expanduser(path=''):
    if path.startswith('~'):
        path = path.replace('~', HOME)
    return path


def normalize_path(path):
    return os.path.abspath(expanduser(path))


def isfile(path):
    return os.path.isfile(path)


def isdir(path):
    return os.path.isdir(path)


def get_fileptr(path, writable=False, binary=True):
    if not path:
        msg = _('There is no file path')
        raise IOError(errno.ENODATA, msg, '')
    if writable:
        try:
            fileptr = open(path, 'wb' if binary else 'w')
        except Exception:
            msg = _('Cannot open %s file for writing') % path
            events.emit(events.MESSAGES, msgconst.ERROR, msg)
            LOG.exception(msg)
            raise
    else:
        try:
            fileptr = open(path, 'rb' if binary else 'r')
        except Exception:
            msg = _('Cannot open %s file for reading') % path
            events.emit(events.MESSAGES, msgconst.ERROR, msg)
            LOG.exception(msg)
            raise
    return fileptr


def makedirs(path):
    os.makedirs(path)


def lexists(path):
    return os.path.exists(path)


def exists(path):
    return os.path.exists(path)


def normalize_sys_argv():
    """Converts sys.argv to unicode and translate relative paths as
    absolute ones.
    """
    for item in range(1, len(sys.argv)):
        if not sys.argv[item] or sys.argv[item].startswith('-'):
            continue
        if sys.argv[item].startswith('~'):
            sys.argv[item] = os.path.expanduser(sys.argv[item])
        sys.argv[item] = os.path.abspath(sys.argv[item])
