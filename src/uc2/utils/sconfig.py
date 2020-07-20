#
#  Copyright (C) 2017-2020 by Ihor E. Novikov
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

import json
import logging
import typing as tp

from uc2.utils import fsutils

LOG = logging.getLogger(__name__)
EXCLUDED_FIELDS = ('filename', 'app')


class SerializedConfig:
    """Represents parent class for application configs.
    """
    filename: str = ''

    def update(self, cnf: tp.Union[tp.Dict, None] = None) -> None:
        """Updates existent config fields from provided dict

        :param cnf: (dict) dict of values for update
        """
        cnf = cnf or {}
        for key in cnf.keys():
            if hasattr(self, key):
                setattr(self, key, cnf[key])

    def load_cfg(self, fp: tp.IO[str]) -> None:
        """Loads config values from INI-like config file

        :param fp: (tp.IO) file-like object
        """
        for line in fp.readlines():
            line = line.strip()
            if line.startswith('<?xml') or not line:
                raise IOError('Unsupported config file format %s', self.filename)
            if line.startswith('#'):
                continue
            # noinspection PyBroadException
            try:
                code = compile('self.' + line, '<string>', 'exec')
                exec(code)
            except Exception:
                LOG.exception('Error in line: %s in %', line, self.filename)

    def load_json(self, fp: tp.IO[str]) -> None:
        """Loads config values from JSON config file

        :param fp: (tp.IO) file-like object
        """
        self.update(json.load(fp))

    def load(self, filename: tp.Union[str, None] = None) -> None:
        """Loads config values from provided config file

        :param filename: (str) path to config file
        """
        self.filename = filename
        if fsutils.exists(filename):
            # noinspection PyBroadException
            try:
                with fsutils.get_fileptr(filename, binary=False) as fp:
                    reader = self.load_json if fp.read(1) == '{' else self.load_cfg
                    fp.seek(0)
                    # noinspection PyArgumentList
                    reader(fp)
            except Exception:
                LOG.exception('Error reading config %s', filename)

    def save(self, filename: tp.Union[str, None] = None) -> None:
        """Writes JSON config file by provided file path

        :param filename: (str) path to config file
        """

        filename = filename or self.filename
        if len(self.__dict__) and filename:
            defaults = SerializedConfig.__dict__
            items = sorted(list(self.__dict__.items()))
            json_dict = {}
            for key, value in items:
                if key in EXCLUDED_FIELDS:
                    continue
                if key in defaults and defaults[key] == value:
                    continue
                json_dict[key] = value
            if json_dict:
                # noinspection PyBroadException
                try:
                    with fsutils.get_fileptr(filename, writable=True, binary=False) as fp:
                        json.dump(json_dict, fp)
                except Exception:
                    LOG.exception('Error saving config %s', filename)
