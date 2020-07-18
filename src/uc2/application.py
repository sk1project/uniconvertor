# -*- coding: utf-8 -*-
#
#  Copyright (C) 2012-2020 by Ihor E. Novikov
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

import uc2
from . import (app_cms, cmds, events, msgconst)
from .app_palettes import PaletteManager
from .uc2conf import (UCData, UCConfig)
from .utils.mixutils import (echo, config_logging)

LOG = logging.getLogger(__name__)

LOG_MAP: tp.Dict[int, tp.Callable] = {
    msgconst.JOB: LOG.info,
    msgconst.INFO: LOG.info,
    msgconst.OK: LOG.info,
    msgconst.WARNING: LOG.warning,
    msgconst.ERROR: LOG.error,
    msgconst.STOP: lambda *args: args,
}


class UCApplication:
    """ Represents UniConvertor application.
    The object exists during translation process only.
    """
    path: str
    config: UCConfig
    appdata: UCData
    default_cms: app_cms.AppColorManager
    palettes: PaletteManager
    log_filepath: str
    do_verbose: bool = False

    def __init__(self, path: str = '', cfgdir: str = '~', check: bool = True) -> None:
        """Creates UniConvertor application instance.

        :param path: (str) current application path
        :param cfgdir: (str) path to '.config'
        :param check: (bool) config directory check flag
        """
        self.path = path
        cfgdir = os.path.expanduser(cfgdir)
        self.config = UCConfig()
        self.config.app = self
        self.appdata = UCData(self, cfgdir, check=check)
        self.config.load(self.appdata.app_config)
        self.log_filepath = os.path.join(self.appdata.app_config_dir, 'uc2.log')
        setattr(uc2, 'config', self.config)
        setattr(uc2, 'appdata', self.appdata)

    def verbose(self, *args: tp.Union[int, str]) -> None:
        """Logging callable to write event message records

        :param args: (list) event message args
        """
        status = msgconst.MESSAGES[args[0]]
        LOG_MAP[args[0]](args[1])
        if self.do_verbose or args[0] in (msgconst.ERROR, msgconst.STOP):
            indent = ' ' * (msgconst.MAX_LEN - len(status))
            echo('%s%s| %s' % (status, indent, args[1]))
        if args[0] == msgconst.STOP:
            echo('For details see logs: %s\n' % self.log_filepath)

    def check_sys_args(self, current_dir: tp.Union[str, None]) -> tp.Union[tp.NoReturn, None]:
        """Checks system arguments before translation executed

        :param current_dir: (str|None) directory path where UniConvertor command executed
        """
        if len(sys.argv) == 1:
            dt = self.appdata
            mark = '' if not dt.build else ' build %s' % dt.build
            msg = '%s %s%s%s\n' % (dt.app_name, dt.version, dt.revision, mark)
            cmds.show_short_help(msg)
        elif cmds.check_args(cmds.HELP_CMDS):
            cmds.show_help(self.appdata)
        elif cmds.check_args(cmds.PARTS_CMDS):
            cmds.show_parts(self.appdata)
        elif cmds.check_args(cmds.LOG_CMDS):
            log_filepath = os.path.join(self.appdata.app_config_dir, 'uc2.log')
            with open(log_filepath, 'r') as fp:
                echo(fp.read())
        elif cmds.check_args(cmds.DIR_CMDS):
            echo(os.path.dirname(os.path.dirname(__file__)))
        elif cmds.check_args(cmds.CFG_SHOW_CMDS):
            cmds.show_config()
        elif cmds.check_args(cmds.CONFIG_CMDS):
            options = cmds.parse_cmd_args(current_dir)[1]
            cmds.normalize_options(options)
            cmds.change_config(options)
            self.config.save()
        elif len(sys.argv) == 2:
            cmds.show_short_help('Not enough arguments!')
            sys.exit(1)
        else:
            return
        sys.exit(0)

    @staticmethod
    def get_translation_args(current_dir: tp.Union[str, None]) \
            -> tp.Union[tp.NoReturn, tp.Tuple[tp.Callable, tp.List[str], tp.Dict]]:
        """Prepares UniConvertor execution command, options, targets and destinations

        :param current_dir: (str|None) directory path where UniConvertor command executed
        """
        current_dir = current_dir or os.getcwd()
        files, options = cmds.parse_cmd_args(current_dir)

        if not files:
            cmds.show_short_help('File names are not provided!')
            sys.exit(1)
        elif len(files) == 1:
            msg = 'Destination directory or file name is not provided!'
            cmds.show_short_help(msg)
            sys.exit(1)

        command = cmds.convert
        if any(['*' in files[0], '?' in files[0]]):
            command = cmds.wildcard_convert
            if os.path.exists(files[1]):
                if not os.path.isdir(files[1]):
                    msg = 'Destination directory "%s" is not a directory!'
                    cmds.show_short_help(msg % files[1])
                    sys.exit(1)
            else:
                os.makedirs(files[1])
        elif len(files) > 2:
            command = cmds.multiple_convert
            if os.path.exists(files[-1]):
                if not os.path.isdir(files[-1]):
                    msg = 'Destination directory "%s" is not a directory!'
                    cmds.show_short_help(msg % files[-1])
                    sys.exit(1)
            else:
                os.makedirs(files[-1])
        elif not os.path.exists(files[0]):
            cmds.show_short_help('Source file "%s" is not found!' % files[0])
            sys.exit(1)

        return command, files, options

    def __call__(self, current_dir: tp.Union[str, None] = None) -> tp.NoReturn:
        """UniConvertor translation callable.

        :param current_dir: (str|None) directory path where UniConvertor command executed
        """
        self.check_sys_args(current_dir=current_dir)

        self.do_verbose = cmds.check_args(cmds.VERBOSE_CMDS)
        command, files, options = self.get_translation_args(current_dir=current_dir)

        events.connect(events.MESSAGES, self.verbose)
        config_logging(filepath=self.log_filepath,
                       level=options.get('log') or self.config.log_level)

        self.default_cms = app_cms.AppColorManager(self)
        self.palettes = PaletteManager(self)

        # ------------ EXECUTION ----------------
        status = 0
        # noinspection PyBroadException
        try:
            command(self.appdata, files, options)
        except Exception:
            status = 1

        echo() if self.do_verbose else None
        sys.exit(status)
