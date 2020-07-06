# -*- coding: utf-8 -*-
#
#  Copyright (C) 2015 by Igor E. Novikov
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

from uc2.formats.scribus_pal.scribus_pal_model import SP_TAG
from uc2.formats.scribus_pal.scribus_pal_presenter import \
    ScribusPalettePresenter
from uc2.formats.skp.skp_presenter import SKP_Presenter
from uc2.utils.fsutils import get_fileptr
from uc2.utils.mixutils import merge_cnf


def scribus_pal_loader(appdata, filename=None, fileptr=None, translate=True,
                       convert=False, cnf=None, **kw):
    cnf = merge_cnf(cnf, kw)
    doc = ScribusPalettePresenter(appdata, cnf)
    doc.load(filename, fileptr)
    if convert:
        skp_doc = SKP_Presenter(appdata, cnf)
        doc.convert_to_skp(skp_doc)
        doc.close()
        return skp_doc
    return doc


def scribus_pal_saver(doc, filename=None, fileptr=None, translate=True,
                      convert=False, cnf=None, **kw):
    cnf = merge_cnf(cnf, kw)
    appdata = doc.appdata
    if convert:
        scrb_doc = ScribusPalettePresenter(appdata, cnf)
        scrb_doc.convert_from_skp(doc)
        scrb_doc.save(filename, fileptr)
        scrb_doc.close()
    else:
        doc.save(filename, fileptr)


def check_scribus_pal(path):
    fileptr = get_fileptr(path, binary=False)
    ret = False
    i = 0
    while i < 20:
        line = fileptr.readline()
        if not line.find(SP_TAG) == -1:
            ret = True
            break
        i += 1
    fileptr.close()
    return ret
