# -*- coding: utf-8 -*-
#
#  Copyright (C) 2019 by Igor E. Novikov
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

import gzip

from uc2 import uc2const
from uc2.formats.sk2.sk2_presenter import SK2_Presenter
from uc2.formats.svg.svg_presenter import SVG_Presenter
from uc2.utils.mixutils import merge_cnf
from uc2.utils.fsutils import get_fileptr, get_sys_path

SVGZ_HEADER = '\x1f\x8b\x08'


def svgz_loader(appdata, filename=None, fileptr=None,
               translate=True, cnf=None, **kw):
    cnf = merge_cnf(cnf, kw)
    svg_doc = SVG_Presenter(appdata, cnf)
    path = get_sys_path(filename)
    fileptr = gzip.open(path, 'rb')
    svg_doc.load(None, fileptr)
    if translate:
        sk2_doc = SK2_Presenter(appdata, cnf)
        if filename:
            sk2_doc.doc_file = filename
        svg_doc.translate_to_sk2(sk2_doc)
        svg_doc.close()
        return sk2_doc
    return svg_doc


def svgz_saver(sk2_doc, filename=None, fileptr=None,
              translate=True, cnf=None, **kw):
    cnf = merge_cnf(cnf, kw)
    if sk2_doc.cid == uc2const.SVG:
        translate = False
    path = get_sys_path(filename)
    fileptr = gzip.open(path, 'wb')
    if translate:
        svg_doc = SVG_Presenter(sk2_doc.appdata, cnf)
        svg_doc.translate_from_sk2(sk2_doc)
        svg_doc.save(None, fileptr)
        svg_doc.close()
    else:
        sk2_doc.save(None, fileptr)


def check_svgz(path):
    fileptr = get_fileptr(path)
    sign = fileptr.read(len(SVGZ_HEADER))
    fileptr.close()
    return sign == SVGZ_HEADER
