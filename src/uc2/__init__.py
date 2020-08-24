#
#  Copyright (C) 2011-2020 by Ihor E. Novikov
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

import os
import typing as tp

from .utils import translator

config = None
appdata = None

# Global message translator
_ = translator.MsgTranslator()

AppHandle = tp.TypeVar('AppHandle')


def uc2_init() -> AppHandle:
    """UniConvertor initializing routine.
    """
    from .application import UCApplication
    _pkgdir = __path__[0]
    app = UCApplication(_pkgdir)
    return app


def uc2_run(cwd: tp.Optional[str] = None) -> tp.NoReturn:
    """UniConvertor launch routine.

    :param cwd: (str|None) application working directory
    """
    uc2_init()(cwd or os.getcwd())
