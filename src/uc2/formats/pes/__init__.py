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


def pes_loader(appdata, filename=None, fileptr=None, translate=True, cnf=None,
               **kw):
    from uc2.formats.pes.pes_presenter import PesPresenter
    from uc2.formats.sk2.sk2_presenter import SK2_Presenter
    cnf = merge_cnf(cnf, kw)
    doc = PesPresenter(appdata, cnf)
    doc.load(filename, fileptr)
    if translate:
        sk2_doc = SK2_Presenter(appdata, cnf)
        sk2_doc.doc_file = filename
        doc.translate_to_sk2(sk2_doc)
        doc.close()
        doc = sk2_doc
    return doc


def pes_saver(doc, filename=None, fileptr=None, translate=True, cnf=None, **kw):
    from uc2.formats.pes.pes_presenter import PesPresenter
    cnf = merge_cnf(cnf, kw)
    if translate:
        pes_doc = PesPresenter(doc.appdata, cnf)
        pes_doc.translate_from_sk2(doc)
        pes_doc.save(filename, fileptr)
        pes_doc.close()
    else:
        doc.save(filename)


def check_pes(path):
    file_size = os.path.getsize(path)
    fileptr = get_fileptr(path)

    if file_size > 4:
        string = fileptr.read(4)
    else:
        string = fileptr.read()

    fileptr.close()
    return string.startswith('#PES') or string.startswith('#PEC')
