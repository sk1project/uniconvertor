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

from uc2 import uc2const
from uc2.formats.generic import BinaryModelPresenter
from uc2.formats.pes import pes_model
from uc2.formats.pes.pes_config import PES_Config
from uc2.formats.pes.pes_filters import PES_Loader, PES_Saver
# from uc2.formats.pes.pes_to_sk2 import PES_to_SK2_Translator
# from uc2.formats.pes.pes_from_sk2 import SK2_to_PES_Translator


class PesPresenter(BinaryModelPresenter):
    cid = uc2const.PES
    palette = None

    def __init__(self, appdata, cnf=None):
        self.config = PES_Config()
        # config_file = os.path.join(appdata.app_config_dir, self.config.filename)
        # self.config.load(config_file)
        self.config.update(cnf or {})
        self.appdata = appdata
        self.loader = PES_Loader()
        self.saver = PES_Saver()
        self.new()

    def new(self):
        self.model = pes_model.PesDocument()
        self.model.childs = []

    # def translate_from_sk2(self, sk2_doc):
    #     translator = SK2_to_PES_Translator()
    #     translator.translate(sk2_doc, self)

    # def translate_to_sk2(self, sk2_doc):
    #     translator = PES_to_SK2_Translator()
    #     translator.translate(self, sk2_doc)
