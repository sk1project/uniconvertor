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

import typing as tp


def val_100(values: tp.Union[tp.List[float], tp.Tuple[float, ...]]) -> tp.List[int]:
    """Converts list/tuple of float values (0.0-1.0) into list of integers (0-100)

    :param values: (list|tuple) list/tuple of float values (0.0-1.0)
    :return: list of integers (0-100)
    """
    return [int(round(100 * value)) for value in values]


def val_255(values: tp.Union[tp.List[float], tp.Tuple[float, ...]]) -> tp.List[int]:
    """Converts list/tuple of float values (0.0-1.0) into list of integers (0-255)

    :param values: (list|tuple) list/tuple of float values (0.0-1.0)
    :return: list of integers (0-255)
    """
    return [int(round(255 * value)) for value in values]


def val_255_to_dec(values: tp.Union[tp.List[int], tp.Tuple[int, ...]]) -> tp.List[float]:
    """Converts list/tuple of integers (0-255) into list of float values (0.0-1.0)

    :param values: (list|tuple) list/tuple of integers (0-255)
    :return: list of float values (0.0-1.0)
    """
    return [value / 255.0 for value in values]


def val_100_to_dec(values):
    """Converts list/tuple of integers (0-100) into list of float values (0.0-1.0)

    :param values: (list|tuple) list/tuple of integers (0-100)
    :return: list of float values (0.0-1.0)
    """
    return [value / 100.0 for value in values]


def mix_vals(value1: tp.Union[int, float], value2: tp.Union[int, float], coef: float = 0.5) -> float:
    """Mixes values according to ratio coefficient

    :param value1: (int|float) first value
    :param value2: (int|float) second value
    :param coef: (float) ratio coefficient (0.0-1.0)
    :return: (float) mixed value
    """
    return value1 - (value1 - value2) * coef


def mix_lists(values1: tp.Union[tp.List[tp.Union[int, float]], tp.Tuple[tp.Union[int, float], ...]],
              values2: tp.Union[tp.List[tp.Union[int, float]], tp.Tuple[tp.Union[int, float], ...]],
              coef: float = 0.5) -> tp.List[float]:
    """Mixes values of two lists/tuples into list according to ratio coefficient.
    The sequences should be equal in length

    :param values1: (list|tuple) list/tuple of values
    :param values2: (list|tuple) list/tuple of values
    :param coef: (float) ratio coefficient (0.0-1.0)
    :return: (list) mixed value
    """
    if len(values1) == len(values2):
        return [mix_vals(value1, value2, coef) for value1, value2 in zip(values1, values2)]
