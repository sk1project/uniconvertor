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
from uc2 import uc2const, cms
from uc2.formats.edr_pal.edr_filters import EDR_Loader, EDR_Saver
from uc2.formats.edr_pal.edr_model import EDR_Palette, EDR_Color
from uc2.formats.generic import BinaryModelPresenter


class EDR_Presenter(BinaryModelPresenter):
    cid = uc2const.EDR

    config = None
    doc_file = ''
    model = None

    def __init__(self, appdata, cnf=None):
        self.config = cnf or {}
        self.appdata = appdata
        self.cms = appdata.app.default_cms
        self.loader = EDR_Loader()
        self.saver = EDR_Saver()
        self.new()

    def new(self):
        self.model = EDR_Palette()
        self.model.childs = []

    def convert_from_skp(self, skp_doc):
        for item in skp_doc.model.colors:
            rgb = self.cms.get_rgb_color(item)[1]
            color = EDR_Color()
            color.hexcolor = cms.rgb_to_hexcolor(rgb)
            self.model.add(color)
        self.model.do_update(self)

    def convert_to_skp(self, skp_doc):
        skp_model = skp_doc.model
        skp_model.name = 'EDR palette'
        skp_model.source = 'EDR palette'
        if self.doc_file:
            filename = os.path.basename(self.doc_file)
            skp_model.name = '%s' % filename.split('.')[0]
            skp_model.comments += 'Converted from %s' % filename

        for index, child in enumerate(self.model.childs, 1):
            color_val = cms.hexcolor_to_rgb(child.hexcolor)
            color_name = "{:03d} - {}".format(index, child.hexcolor)
            clr = [uc2const.COLOR_RGB, color_val, 1.0, color_name]
            skp_model.colors.append(clr)
