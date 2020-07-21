#
#  Copyright (C) 2012, 2020 by Ihor E. Novikov
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

import typing as tp

JOB: int = 0
OK: int = 1
INFO: int = 2
WARNING: int = 3
ERROR: int = 4
STOP: int = 5

MESSAGES: tp.Dict[int, str] = {
    JOB: 'JOB',
    OK: 'OK',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    STOP: 'STOP',
}

MAX_LEN = max(*[len(val) for val in MESSAGES.values()])
