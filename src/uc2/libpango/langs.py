#
#  Copyright (C) 2016-2020 by Ihor E. Novikov
#  Copyright (C) 2020 by Krzysztof Broński
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

MYANMAR = ('\u1000', '\u109f')
MYANMAR_EXT = ('\uaa60', '\uaa7f')
ARABIC = ('\u0600', '\u06ff')
ARABIC_SUPPLEMENT = ('\u0750', '\u077f')
ARABIC_FORMS_A = ('\ufb50', '\ufdff')
ARABIC_FORMS_B = ('\ufe70', '\ufeff')


def check_lang(text: str, ranges: tp.Tuple[tp.Tuple[str, str], ...]) -> bool:
    """Checks presence specific characters in text string.

    :param text: (str) text sample
    :param ranges: (tuple) characters range
    :return: (bool) check result
    """
    for item in text[:20]:
        for rng in ranges:
            if rng[0] <= item <= rng[1]:
                return True
    return False


def check_maynmar(text: str) -> bool:
    """Checks presence maynmar characters in text string.

    :param text: (str) text sample
    :return: (bool) check result
    """
    return check_lang(text, (MYANMAR, MYANMAR_EXT))


def check_arabic(text: str) -> bool:
    """Checks presence arabic characters in text string.

    :param text: (str) text sample
    :return: (bool) check result
    """
    return check_lang(text, (ARABIC, ARABIC_SUPPLEMENT, ARABIC_FORMS_A, ARABIC_FORMS_B))
