# -*- coding: utf-8 -*-

# Copyright (C) 2011 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

from uc_conf import UCConfig, dummy_translate
import uc2

config = UCConfig()
setattr(uc2, "_", dummy_translate)


