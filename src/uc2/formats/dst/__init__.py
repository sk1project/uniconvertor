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

import os

from uc2.utils.fsutils import get_fileptr
from uc2.utils.mixutils import merge_cnf
from uc2.formats.dst.dst_const import DST_SIGNATURE
from uc2.formats.dst.dst_colors import get_available_color_scheme


def dst_loader(appdata, filename=None, fileptr=None, translate=True, cnf=None,
               **kw):
    from uc2.formats.dst.dst_presenter import DstPresenter
    from uc2.formats.sk2.sk2_presenter import SK2_Presenter
    cnf = merge_cnf(cnf, kw)
    doc = DstPresenter(appdata, cnf)
    doc.colors = get_available_color_scheme(doc, filename)
    doc.load(filename, fileptr)
    if translate:
        sk2_doc = SK2_Presenter(appdata, cnf)
        sk2_doc.doc_file = filename
        doc.translate_to_sk2(sk2_doc)
        doc.close()
        doc = sk2_doc
    return doc


def dst_saver(doc, filename=None, fileptr=None, translate=True, cnf=None, **kw):
    from uc2.formats.dst.dst_presenter import DstPresenter
    cnf = merge_cnf(cnf, kw)
    if translate:
        dst_doc = DstPresenter(doc.appdata, cnf)
        dst_doc.doc_file = filename
        dst_doc.translate_from_sk2(doc)
        dst_doc.save(filename, fileptr)
        dst_doc.close()
    else:
        doc.save(filename)

    if dst_doc.config.create_edr_palette:
        from uc2.formats.skp import SKP_Presenter
        from uc2.formats.edr_pal import edr_pal_saver
        skp_doc = SKP_Presenter(doc.appdata)
        skp_doc.model.colors = dst_doc.colors or []
        edr_pal_saver(
            skp_doc, filename=filename.rsplit('.', 1)[0] + '.edr',
            translate=False, convert=True
        )


def check_dst(path):
    size = len(DST_SIGNATURE)
    fileptr = get_fileptr(path)
    signature = fileptr.read(size)
    fileptr.close()
    return DST_SIGNATURE == signature
