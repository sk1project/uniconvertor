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

import base64
import time
import uuid


def generate_id() -> str:
    """Generates numeric id based on UNIX time like '159490432636592'

    :return: (str) numeric id
    """
    time.sleep(0.001)
    return str(int(time.time() * 100000))


def generate_base64_id() -> str:
    """Generates base64 encoded id based on UNIX time like 'MTU5NDkwNDM0NDgyMTYw'

    :return: (str) base64 encoded id
    """
    time.sleep(0.001)
    return base64.b64encode(generate_id().encode()).decode()


def generate_guid() -> str:
    """Generates classic GUID like '514a70a4-c764-11ea-8364-28f10e13a705'

    :return: (str) GUID string
    """
    time.sleep(0.001)
    return str(uuid.uuid1())
