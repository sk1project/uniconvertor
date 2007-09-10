# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

import os
from popen2 import popen2
from app import config

UTF_CODEC='utf-8'

def locale_to_utf(string=''): 
	if string=='' :
		return string
	locale=get_locale()
	if locale==UTF_CODEC:
		return string
	return strip_line(cmd_iconv(locale, UTF_CODEC, string))

def utf_to_locale(string=''): 
	if string=='' :
		return string	
	locale=get_locale()
	if locale==UTF_CODEC:
		return string
	return strip_line(cmd_iconv(UTF_CODEC, locale, string))
		
def get_locale():	
	return config.preferences.system_encoding
	
def cmd_iconv(from_codec='', to_codec='', string=''):
	if from_codec=='' or to_codec=='' or string=='' :
		return string
	from_bash = os.popen('echo "'+string+'" |iconv -f '+from_codec+' -t '+to_codec)
# 	to_bash.write(string)
	result=from_bash.read()
# 	to_bash.close()
	from_bash.close()
	return result
	
def strip_line(string=''):
	if string=='' :
		return string
	return string[0:len(string)-1]
	
def getshell_var(s):
	if os.confstr(s):
		return os.environ[s]
	return None
	