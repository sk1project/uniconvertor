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
from uc2.formats.edr_pal import EDR_Palette
from uc2.formats.pes import pes_model
from uc2.formats.pes import pes_const
from uc2.formats.pes import pes_datatype
import struct


class PES_Loader(AbstractLoader):
    name = 'PES_Loader'

    def do_load(self):
        stream = self.fileptr
        self.presenter.palette = EDR_Palette(self.filepath)
        self.model.childs = []
        parent_stack = self.model.childs

        # read header #PES0001 or #PEC0001
        magic_chunk = stream.read(8)
        self.model.chunk = magic_chunk

        if magic_chunk.startswith('#PES'):
            # read pes block
            pecstart_chunk = stream.read(4)
            pecstart_offset = struct.unpack('<I', pecstart_chunk)[0]
            pes_header_size = pecstart_offset - 8 - 4

            pes_data_chunk = stream.read(pes_header_size)
            pes_chunk_chunk = pecstart_chunk + pes_data_chunk
            pes_header = pes_model.PesHeader(pes_chunk_chunk)
            parent_stack.append(pes_header)

        # read pec block
        pec_chunk = stream.read(pes_const.PEC_HEADER_SIZE)
        pec_header = pes_model.PecHeader(pec_chunk)
        parent_stack.append(pec_header)

        thumbnail_chunk1 = stream.read(2)
        thumbnail_chunk2 = stream.read(3)
        thumbnail_chunk2_ = pes_datatype.unpack_uint24le(thumbnail_chunk2)

        pec_body_size = thumbnail_chunk2_ - 2 - 3

        pec_body_chunk = stream.read(pec_body_size)
        chunk = thumbnail_chunk1 + thumbnail_chunk2 + pec_body_chunk
        pec_body = pes_model.PecBody(chunk)
        parent_stack.append(pec_body)

        # XXX: this is so as not to lose data at the end of the file
        while True:
            chunk_size = self.file_size - stream.tell()
            if chunk_size <= 0:
                break
            chunk_size = min(chunk_size, 0x5000)

            unknown_chunk = stream.read(chunk_size)
            unknown = pes_model.PesUnknown(unknown_chunk)
            parent_stack.append(unknown)


class PES_Saver(AbstractSaver):
    name = 'PES_Saver'

    def do_save(self):
        for rec in self.model.childs:
            self.fileptr.write(rec.chunk)

        if self.config.create_edr_palette:
            dst_doc = self.presenter
            edr_palette = EDR_Palette()
            edr_palette.colors.clear()
            [edr_palette.add_color(c) for c in dst_doc.palette]
            palette_name = edr_palette.palette_file_name(dst_doc.doc_file)
            edr_palette.save_palette(palette_name)
