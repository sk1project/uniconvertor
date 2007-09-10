# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


# some factors to convert between different length units and the base
# unit of sketch, PostScript points

in_to_pt = 72.0
cm_to_pt = in_to_pt / 2.54
mm_to_pt = cm_to_pt / 10
m_to_pt	 = 100 * cm_to_pt

pt_to_in = 1.0 / 72.0
pt_to_cm = 2.54 * pt_to_in
pt_to_mm = pt_to_cm * 10
pt_to_m	 = pt_to_cm / 100


unit_dict = {'pt': 1.0, 'in': in_to_pt, 'cm': cm_to_pt, 'mm': mm_to_pt}
unit_names = ['pt', 'in', 'cm', 'mm']
