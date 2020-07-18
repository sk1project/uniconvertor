#
#  Copyright (C) 2017, 2020 by Ihor E. Novikov
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

import logging
import os
import sys
import typing as tp


def merge_cnf(cnf: tp.Union[tp.Dict, None] = None, kw: tp.Union[tp.Dict, None] = None) -> tp.Dict:
    """Merges dicts checking them

    :param cnf: (dict|None) target dict
    :param kw: (dict|None) source dict
    :return: merged dict
    """
    cnf = cnf or {}
    if kw:
        cnf.update(kw)
    return cnf


LOGGING_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARN,
    'WARNING': logging.WARN,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}


def config_logging(filepath: str, level: str = 'INFO') -> None:
    """Wrapper for 'basicConfig' to simplify logging configuration

    :param filepath: (str) path to log file
    :param level: (str) logging level
    """
    level = LOGGING_MAP.get(level.upper(), logging.INFO)
    logging.basicConfig(
        format=' %(levelname)-8s | %(asctime)s | %(name)s --> %(message)s',
        datefmt='%I:%M:%S %p',
        level=level,
        filename=filepath,
        filemode='w',
    )


MAGENTA = '\033[95m'
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


def echo(msg: str = '', newline: bool = True, flush: bool = True, code: str = '') -> None:
    """Prints escaped message into stdout

    :param msg: (str) message to print
    :param newline: (bool) flag for adding OS specific line separator
    :param flush: (bool) flag to flush stdout buffer
    :param code: (str) escape code (optional)
    """
    msg = '%s%s' % (msg, os.linesep) if newline else msg
    msg = '%s%s%s' % (code, msg, ENDC) if code else msg
    sys.stdout.write(msg)
    sys.stdout.flush() if flush else None


class Decomposable:
    """Parent class to provide field clearing functionality for cross referenced objects
    """
    def destroy(self) -> None:
        """Clears object fields allowing garbage collector to utilize it
        """
        for key in self.__dict__.keys():
            obj = self.__dict__[key]
            self.__dict__[key] = None
            if isinstance(obj, Decomposable):
                obj.destroy()


class DecomposableTreeObject:
    """Parent class to provide recursive field clearing functionality
       for cross referenced tree-like objects
    """
    childs: tp.List[Decomposable]

    def destroy(self) -> None:
        """Clears object fields recursively. By this way method destroys object tree and
           allows garbage collector to utilize tree components
        """
        for child in self.childs:
            child.destroy()
        for item in self.__dict__.keys():
            self.__dict__[item] = None
