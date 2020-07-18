#
#  Copyright (C) 2003-2020 by Ihor E. Novikov
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
import typing as tp

from uc2 import _, events, msgconst
from . import system

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


def makedirs(path):
    os.makedirs(path)


def lexists(path):
    return os.path.exists(path)


def exists(path):
    return os.path.exists(path)


def get_fileptr(path: str, writable: bool = False, binary: bool = True) -> tp.IO:
    """Returns file object for provided file path

    :param path: (str) file path
    :param writable: (bool) file object for writing flag
    :param binary: (bool) binary file object flag
    :return: (tp.IO) file object
    """
    if not path:
        msg = _('There is no file path')
        raise IOError(errno.ENODATA, msg, '')
    try:
        key = 'w' if writable else 'r'
        key += 'b' if binary else ''
        return open(path, key)
    except IOError:
        msg = _('Cannot open %s file for writing') if writable \
            else _('Cannot open %s file for reading')
        msg = msg % path
        events.emit(events.MESSAGES, msgconst.ERROR, msg)
        LOG.exception(msg)
        raise


def normalize_sys_argv() -> None:
    """Converts sys.argv to unicode and translate relative paths as
    absolute ones.
    """
    for item in range(1, len(sys.argv)):
        if sys.argv[item] and not sys.argv[item].startswith('-'):
            if sys.argv[item].startswith('~'):
                sys.argv[item] = os.path.expanduser(sys.argv[item])
            sys.argv[item] = os.path.abspath(sys.argv[item])
