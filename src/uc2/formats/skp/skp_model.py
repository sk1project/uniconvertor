# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015 by Ihor E. Novikov
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


from uc2.formats.generic import TextModelObject


class SK1Palette(TextModelObject):
    """
    Represents sK1 palette object.
    This is a single and root DOM instance of SKP file format.
    All palette colors are members of colors field list.
    """

    name = ''
    source = ''
    comments = ''
    columns = 1
    colors = []
    builtin = False

    def __init__(self, name='', colors=None):
        self.colors = colors or []
        self.name = name or 'Untitled palette'
        self.source = self.comments = ''
        self.columns = 1

    def resolve(self, name=''):
        is_leaf = False
        info = '%d' % (len(self.colors))
        name = 'SK1Palette'
        return is_leaf, name, info
