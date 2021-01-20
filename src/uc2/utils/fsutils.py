# -*- coding: utf-8 -*-
#
#  Copyright (C) 2003-2021 by Ihor E. Novikov
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
import shutil
import sys

from uc2 import _, events, msgconst
from uc2.utils import system

LOG = logging.getLogger(__name__)

# Platform
IS_MSW = system.get_os_family() == system.WINDOWS
IS_MAC = system.get_os_family() == system.MACOSX

HOME = os.path.expanduser('~')\
    .decode(sys.getfilesystemencoding()).encode('utf-8')


def expanduser(path=''):
    if path.startswith('~'):
        path = HOME + path[1:]
    return path


def normalize_path(path):
    return os.path.abspath(expanduser(path))


def get_sys_path(path):
    if not isinstance(path, unicode):
        path = path.decode('utf-8')
    return path.encode(sys.getfilesystemencoding())


def get_utf8_path(path):
    if not isinstance(path, unicode):
        path = path.decode(sys.getfilesystemencoding())
    return path.encode('utf-8')


def isfile(path):
    return os.path.isfile(get_sys_path(path))


def isdir(path):
    return os.path.isdir(get_sys_path(path))


def uopen(path, mode='rb'):
    if not isinstance(path, unicode):
        path = path.decode('utf8')
    return open(path, mode)


def get_fileptr(path, writable=False):
    if not path:
        msg = _('There is no file path')
        raise IOError(errno.ENODATA, msg, '')
    try:
        return uopen(path, 'wb' if writable else 'rb')
    except Exception:
        msg = _('Cannot open %s file for writing') % path \
            if writable else _('Cannot open %s file for reading') % path
        events.emit(events.MESSAGES, msgconst.ERROR, msg)
        LOG.exception(msg)
        raise


def makedirs(path):
    os.makedirs(get_sys_path(path))


def lexists(path):
    return os.path.lexists(get_sys_path(path))


def exists(path):
    return os.path.exists(get_sys_path(path))


def remove(path):
    os.remove(get_sys_path(path))


def rename(oldpath, newpath):
    os.rename(get_sys_path(oldpath), get_sys_path(newpath))


def listdir(path):
    return os.listdir(get_sys_path(path))


def copy(src, dest):
    shutil.copy(get_sys_path(src), get_sys_path(dest))


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
