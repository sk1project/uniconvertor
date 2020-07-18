# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015-2020 by Igor E. Novikov
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
#  along with this program.  If not, see <https://www.gnu.org/licenses/>..

import typing as tp

from uc2 import uc2const


class PaletteManager:
    """Represents basic palette manager object
    """
    app: uc2const.AppHandle
    palettes: tp.Dict = {}

    def __init__(self, app: uc2const.AppHandle) -> None:
        """Creates PaletteManager object for provided application instance.

        :param app: (UCApplication) UniConvertor application handle
        """
        self.app = app
        self.scan_palettes()

    def scan_palettes(self) -> None:
        """Not implemented interface for subclass palette scanning
        """
