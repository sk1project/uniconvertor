#  Copyright (C) 2009-2019 by Maxim S. Barabash
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

import struct

from uc2.formats.generic import BinaryModelObject


class EDR_Palette(BinaryModelObject):
    """
    Represent EDR Palette object.
    """
    def __init__(self):
        self.childs = []
        self.cache_fields = []

    def parse(self, loader):
        while True:
            chunk = loader.readbytes(4)
            if chunk:
                color = EDR_Color()
                color.chunk = chunk
                self.add(color)
            else:
                break

    def resolve(self, name=''):
        is_leaf = False
        info = '%d' % (len(self.childs))
        name = 'EDR palette'
        return is_leaf, name, info

    def update(self):
        pass


class EDR_Color(BinaryModelObject):
    """
    Represent EDR Color object.
    """
    hexcolor = ''

    def update_for_sword(self):
        self.cache_fields = [
            (0, 3, 'rgb'),
            (3, 1, 'zero')
        ]

    def update(self):
        if self.chunk:
            self.deserialize()
        else:
            self.serialize()

    def deserialize(self):
        data = struct.unpack('BBBB', self.chunk)
        self.hexcolor = '#%02x%02x%02x' % data[:3]

    def serialize(self):
        hexcolor = self.hexcolor
        items = (hexcolor[1:3], hexcolor[3:5], hexcolor[5:], '0')
        data = [int(x, 0x10) for x in items]
        self.chunk = struct.pack('BBBB', *data)

    def resolve(self, name=''):
        return True, self.hexcolor, ''
