# -*- coding: utf-8 -*-
#
#  Copyright (C) 2012-2017 by Ihor E. Novikov
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

import uc2
from uc2 import app_cms, cmds
from uc2 import events, msgconst
from uc2.app_palettes import PaletteManager
from uc2.uc2conf import UCData, UCConfig
from uc2.utils import fsutils
from uc2.utils.mixutils import echo, config_logging

LOG = logging.getLogger(__name__)

LOG_MAP = {
    msgconst.JOB: LOG.info,
    msgconst.INFO: LOG.info,
    msgconst.OK: LOG.info,
    msgconst.WARNING: LOG.warn,
    msgconst.ERROR: LOG.error,
    msgconst.STOP: lambda *args: args,
}


class UCApplication(object):
    path = ''
    config = None
    appdata = None
    default_cms = None
    palettes = None
    do_verbose = False
    log_filepath = ''

    def __init__(self, path='', cfgdir='~', check=True):
        self.path = path
        cfgdir = fsutils.expanduser(fsutils.get_utf8_path(cfgdir))
        self.config = UCConfig()
        self.config.app = self
        self.appdata = UCData(self, cfgdir, check=check)
        self.config.load(self.appdata.app_config)
        setattr(uc2, 'config', self.config)
        setattr(uc2, 'appdata', self.appdata)

    def init_mngrs(self):
        if not self.default_cms:
            self.default_cms = app_cms.AppColorManager(self)
            self.palettes = PaletteManager(self)

    def verbose(self, *args):
        status = msgconst.MESSAGES[args[0]]
        LOG_MAP[args[0]](args[1])
        if self.do_verbose or args[0] in (msgconst.ERROR, msgconst.STOP):
            indent = ' ' * (msgconst.MAX_LEN - len(status))
            echo('%s%s| %s' % (status, indent, args[1]))
        if args[0] == msgconst.STOP:
            echo('For details see logs: %s\n' % self.log_filepath)

    def run(self, current_dir=None):
        if len(sys.argv) == 1:
            dt = self.appdata
            mark = '' if not dt.build else ' build %s' % dt.build
            msg = '%s %s%s%s\n' % (dt.app_name, dt.version, dt.revision, mark)
            cmds.show_short_help(msg)
            sys.exit(0)
        elif cmds.check_args(cmds.HELP_CMDS):
            cmds.show_help(self.appdata)
            sys.exit(0)
        elif cmds.check_args(cmds.PARTS_CMDS):
            cmds.show_parts(self.appdata)
            sys.exit(0)
        elif cmds.check_args(cmds.LOG_CMDS):
            log_filepath = os.path.join(self.appdata.app_config_dir, 'uc2.log')
            log_filepath = log_filepath.decode('utf-8')
            with open(log_filepath, 'rb') as fileptr:
                echo(fileptr.read())
            sys.exit(0)
        elif cmds.check_args(cmds.DIR_CMDS):
            echo(os.path.dirname(os.path.dirname(__file__)))
            sys.exit(0)
        elif cmds.check_args(cmds.CFG_SHOW_CMDS):
            cmds.show_config()
            sys.exit(0)
        elif cmds.check_args(cmds.CONFIG_CMDS):
            options = cmds.parse_cmd_args(current_dir)[1]
            cmds.normalize_options(options)
            cmds.change_config(options)
            self.config.save()
            sys.exit(0)
        elif len(sys.argv) == 2:
            cmds.show_short_help('Not enough arguments!')
            sys.exit(1)

        self.do_verbose = cmds.check_args(cmds.VERBOSE_CMDS)
        current_dir = os.getcwdu() if current_dir is None else current_dir
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
        elif not fsutils.exists(files[0]):
            cmds.show_short_help('Source file "%s" is not found!' % files[0])
            sys.exit(1)

        events.connect(events.MESSAGES, self.verbose)
        log_level = options.get('log', self.config.log_level)
        self.log_filepath = os.path.join(self.appdata.app_config_dir, 'uc2.log')
        config_logging(self.log_filepath, log_level)

        self.init_mngrs()

        # EXECUTION ----------------------------
        status = 0
        # noinspection PyBroadException
        try:
            command(self.appdata, files, options)
        except Exception:
            status = 1

        if self.do_verbose:
            echo()
        sys.exit(status)
