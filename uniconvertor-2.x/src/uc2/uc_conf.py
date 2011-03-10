# -*- coding: utf-8 -*-
#
#	Copyright (C) 2011 by Igor E. Novikov
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from uc2.utils.fs import expanduser_unicode

from cfgparser import XmlConfigParser

def dummy_translate(str):
	return str


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

PAGE_FORMATS = {  
			'A0': (2383.9370078740158, 3370.3937007874015),
			'A1': (1683.7795275590549, 2383.9370078740158),
			'A2': (1190.5511811023621, 1683.7795275590549),
			'A3': (841.88976377952747, 1190.5511811023621),
			'A4': (595.27559055118104, 841.88976377952747),
			'A5': (419.52755905511805, 595.27559055118104),
			'A6': (297.63779527559052, 419.52755905511805),
			'B1 (ISO)': (2004.0944881889761, 2834.6456692913384),
			'B4 (ISO)': (708.66141732283461, 1000.6299212598424),
			'B5 (ISO)': (498.89763779527556, 708.66141732283461),
			'C3': (918.42519685039372, 1298.267716535433),
			'C4': (649.1338582677165, 918.42519685039372),
			'C5': (459.21259842519686, 649.1338582677165),
			'C6': (323.14960629921262, 459.21259842519686),
			'Envelope C4': (649.1338582677165, 918.42519685039372),
			'Envelope C5': (459.21259842519686, 649.1338582677165),
			'Envelope C6': (323.14960629921262, 459.21259842519686),
			'Envelope E65/DL': (311.81102362204723, 623.62204724409446),
			'Executive': (522.0, 756.0),
			'Legal': (612.0, 1008.0),
			'Letter': (612.0, 792.0),
			'Half Letter': (396.0, 612.0),
			'Visit card #1': (141.73228346456693, 255.11811023622045),
			'Visit card #2': (155.90551181102362, 240.94488188976379),
			} 

PORTRAIT = 0
LANDSCAPE = 1 

class UCData:
		
	app_name = 'UniConvertor'
	app_icon = None
	
	app_config_dir = expanduser_unicode(os.path.join('~', '.config', 'uc2'))
	if not os.path.lexists(app_config_dir):
		os.makedirs(app_config_dir)
	app_config = expanduser_unicode(os.path.join('~', '.config', 'uc2', 'preferences.cfg'))
	
	
class UCConfig(XmlConfigParser):
	
	#============== GENERIC SECTION ===================
	uc_version = ''
	system_encoding = 'utf-8'	# default encoding for sK1 (GUI uses utf-8 only)
	
	#============== DOCUMENT SECTION ==================
	
	# 0 - page center
	# 1 - lower-left page corner
	# 2 - upper-left page corner 
	doc_origin = 1
	
	page_format = 'A4'
	page_orientation = PORTRAIT
	
	layer_color = '#3252A2'
	guide_color = '#0051FF'
	grid_color = '#D3DEE8'
	master_layer_color = '#000000'
	
	grid_geometry = [0, 0, 2.83465, 2.83465]
