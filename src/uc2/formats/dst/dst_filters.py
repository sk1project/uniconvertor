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


from uc2.formats.generic_filters import AbstractLoader, AbstractSaver
from uc2.formats.dst import dst_model
from uc2.formats.dst import dst_const


class DST_Loader(AbstractLoader):
    name = 'DST_Loader'

    def do_load(self):
        stream = self.fileptr
        self.model.childs = []
        parent_stack = self.model.childs

        # read header
        signature_size = len(dst_const.DST_SIGNATURE)
        chunk = stream.read(signature_size)
        if chunk == dst_const.DST_SIGNATURE:
            chunk += stream.read(dst_const.DST_HEADER_SIZE - signature_size)
            header = dst_model.DstHeader(chunk)
            parent_stack.append(header)

        # read stitch commands
        while True:
            chunk = stream.read(3)
            if chunk:
                stitch = dst_model.DstCmd(chunk)
                parent_stack.append(stitch)
            else:
                break


class DST_Saver(AbstractSaver):
    name = 'DST_Saver'

    def do_save(self):
        for rec in self.model.childs:
            self.fileptr.write(rec.chunk)
