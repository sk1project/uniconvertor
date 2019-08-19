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
    dx = 0
    dy = 0

    def __init__(self, chunk=None, cid=None, dx=None, dy=None):
        self.chunk = chunk
        if cid is not None:
            self.cid = cid
        if dx is not None:
            self.dx = dx
        if dy is not None:
            self.dy = dy

    def update(self):
        if self.chunk:
            self.parse()
        else:
            self.chunk = self.get_content()

    def parse(self):
        pass

    def get_content(self):
        pass

    def resolve(self):
        is_leaf = True
        if self.childs:
            is_leaf = False
        name = pes_const.CID_TO_NAME.get(self.cid) or self.cid
        info = ''
        return is_leaf, name, info


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

    def update_for_sword(self):
        self.cache_fields = [
            (0, 20, 'label'),
            (34, 1, 'thumbnail image width in bytes'),
            (35, 1, 'thumbnail image height in pixels'),
            (48, 1, 'color number + 1'),
            (49, 1, 'first index in palette'),
        ]


class PecBody(BasePesModel):
    cid = pes_const.PEC_BODY

    def update_for_sword(self):
        self.cache_fields = []


class PesUnknown(BasePesModel):
    cid = pes_const.PES_UNKNOWN

    def update_for_sword(self):
        self.cache_fields = []