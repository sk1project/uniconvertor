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

# (EDR) Embird color palette
# NOTE: The .edr format is an optional color file

import os
from uc2.formats.edr_pal.edr_presenter import EDR_Presenter
from uc2.formats.sk2.sk2_presenter import SK2_Presenter
from uc2.formats.skp.skp_presenter import SKP_Presenter
from uc2.utils.fsutils import get_fileptr
from uc2.utils.mixutils import merge_cnf


def edr_pal_loader(appdata, filename=None, fileptr=None, translate=True,
                   convert=False, cnf=None, **kw):
    doc = EDR_Presenter(appdata, cnf)
    doc.load(filename, fileptr)
    if convert:
        skp_doc = SKP_Presenter(appdata, cnf)
        doc.convert_to_skp(skp_doc)
        doc.close()
        return skp_doc
    if translate:
        skp_doc = SKP_Presenter(appdata, cnf)
        doc.convert_to_skp(skp_doc)
        sk2_doc = SK2_Presenter(appdata, cnf)
        skp_doc.translate_to_sk2(sk2_doc)
        doc.close()
        skp_doc.close()
        return sk2_doc
    return doc


def edr_pal_saver(doc, filename=None, fileptr=None, translate=True,
                  convert=False, cnf=None, **kw):
    cnf = merge_cnf(cnf, kw)
    appdata = doc.appdata
    if translate:
        skp_doc = SKP_Presenter(appdata, cnf)
        skp_doc.translate_from_sk2(doc)
        edr_doc = EDR_Presenter(appdata, cnf)
        edr_doc.convert_from_skp(skp_doc)
        edr_doc.save(filename, fileptr)
        edr_doc.close()
        skp_doc.close()
    elif convert:
        edr_doc = EDR_Presenter(appdata, cnf)
        edr_doc.convert_from_skp(doc)
        edr_doc.save(filename, fileptr)
        edr_doc.close()
    else:
        doc.save(filename, fileptr)


def check_edr_pal(path):
    file_size = os.path.getsize(path)
    fileptr = get_fileptr(path)
    magic = fileptr.read(4)
    fileptr.close()
    return file_size and not file_size % 4 and magic.endswith(b'\x00')
