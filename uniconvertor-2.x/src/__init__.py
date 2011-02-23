#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2011 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

import os

from cfgparser import XmlConfigParser

class UCData():
		
	app_name = 'UniConvertor'
	app_icon = None
	
	app_config_dir = os.path.expanduser(os.path.join('~', '.config', 'uc2'))
	if not os.path.lexists(app_config_dir):
		os.makedirs(app_config_dir)
	app_config = os.path.expanduser(os.path.join('~', '.config', 'uc2', 'preferences.cfg'))
	
	
class UCConfig(XmlConfigParser):
	
	#============== GENERIC SECTION ===================
	uc_version = ''
	system_encoding = 'utf-8'	# default encoding for sK1 (GUI uses utf-8 only)
	
	#============== DOCUMENT SECTION ==================
