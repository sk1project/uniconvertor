# -*- coding: utf-8 -*-
#
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


from uc2.formats.generic import BinaryModelObject
from uc2.formats.pes import pes_const
from uc2.formats.pes import pes_datatype


class BasePesModel(BinaryModelObject):
    cid = pes_const.PES_UNKNOWN

    def update(self):
        if self.chunk:
            self.deserialize()
        else:
            self.serialize()

    def deserialize(self):
        pass

    def serialize(self):
        pass

    def resolve(self):
        is_leaf = True
        if self.childs:
            is_leaf = False
        name = pes_const.CID_TO_NAME.get(self.cid) or self.cid
        return is_leaf, name, ''


class PesDocument(BasePesModel):
    cid = pes_const.PES_DOCUMENT

    def update_for_sword(self):
        self.cache_fields = [
            (0, 4, 'magic'),
            (4, 4, 'version')
        ]


class PesHeader(BasePesModel):
    cid = pes_const.PES_HEADER

    def update_for_sword(self):
        self.cache_fields = [
            (0, 4, 'pec start')
        ]


class PecHeader(BasePesModel):
    cid = pes_const.PEC_HEADER
    index_colors = None

    def update_for_sword(self):
        self.cache_fields = [
            (0, 20, 'label'),
            (34, 1, 'thumbnail image width in bytes'),
            (35, 1, 'thumbnail image height in pixels'),
            (48, 1, 'color number + 1'),
            (49, 1, 'first index in palette'),
        ]

    def deserialize(self):
        color_number = pes_datatype.packer_b.unpack(self.chunk[48:49])[0]
        self.index_colors = []
        for i in range(0, color_number+1):
            data = self.chunk[49+i:50+i]
            color_index = pes_datatype.packer_b.unpack(data)[0]
            self.index_colors.append(color_index)


class PecBody(BasePesModel):
    cid = pes_const.PEC_BODY

    def resolve(self):
        is_leaf = True
        if self.childs:
            is_leaf = False
        name = pes_const.CID_TO_NAME.get(self.cid) or self.cid
        info = '%d' % len(self.childs)
        return is_leaf, name, info

    def update_for_sword(self):
        self.cache_fields = [
            (0, 2, '`0x0000`(typical) Unknown'),
            (2, 3, 'Offset to thumbnail image subsection'),
            (5, 1, '`0x31`(typical) Unknown'),
            (6, 2, '`0xFFF0`(typical) Unknown'),
            (8, 2, 'Width'),
            (10, 2, 'Height'),
            (12, 2, '`0xE001`(typical) Unknown'),
            (14, 2, '`0xB001`(typical) Unknown'),
            (16, 2, '0x9000 | abs(bounds.left)'),
            (18, 2, '0x9000 | abs(bounds.bottom)'),
        ]


class PesUnknown(BasePesModel):
    cid = pes_const.PES_UNKNOWN


class PesThumbnail(BasePesModel):
    cid = pes_const.PES_THUMBNAIL

    def update_for_sword(self):
        self.cache_fields = []
        for i in range(0, len(self.chunk)/6):
            j = i * 6
            s = ' '.join('{:08b}'.format(ord(x))[::-1] for x in self.chunk[j:j+6])
            self.cache_fields.append((i*6, 6, s))


class PecCmd(BasePesModel):
    cid = pes_const.PES_UNKNOWN
    dx = 0
    dy = 0

    def parse(self, loader, chunk=None):
        stream = loader.fileptr
        val1, val2 = pes_datatype.packer_b2.unpack(chunk)
        if val1 == 0xFE and val2 == 0xB0:
            chunk += stream.read(1)
            self.chunk = chunk
            self.cid = pes_const.CMD_CHANGE_COLOR
        else:
            cid = pes_const.CMD_STITCH
            if val1 & 0x80:
                # 12 bit value
                if val1 & 0x20:
                    cid = pes_const.CMD_TRIM
                if val1 & 0x10:
                    cid = pes_const.CMD_JUMP

                dx = ((val1 & 0x0F) << 8) + val2
                if dx & 0x800:
                    dx -= 0x1000
                # read next byte for dy value
                c = stream.read(1)
                chunk += c
                val2 = pes_datatype.packer_b.unpack(c)[0]
            else:
                # 7 bit value
                dx = val1
                if dx >= 0x40:
                    dx -= 0x80

            if val2 & 0x80:
                # 12 bit value
                if val2 & 0x20:
                    cid = pes_const.CMD_TRIM
                if val2 & 0x10:
                    cid = pes_const.CMD_JUMP
                c = stream.read(1)
                chunk += c
                val3 = pes_datatype.packer_b.unpack(c)[0]
                dy = ((val2 & 0x0F) << 8) + val3
                if dy & 0x800 == 0x800:
                    dy -= 0x1000
            else:
                # 7 bit value
                dy = val2
                if dy >= 0x40:
                    dy -= 0x80

            self.cid = cid
            self.dx = dx
            self.dy = -dy
            self.chunk = chunk

    def resolve(self):
        is_leaf = True
        name = pes_const.CID_TO_NAME.get(self.cid) or self.cid
        info = '%d x %d' % (self.dx, self.dy)
        return is_leaf, name, info
