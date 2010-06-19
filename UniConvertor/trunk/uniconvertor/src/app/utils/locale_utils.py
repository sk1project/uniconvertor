# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

import os
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
	#FIXME: command line call should be replaced by regular Python string expressions
	from_bash = os.popen('echo "'+string+'" |iconv -f '+from_codec+' -t '+to_codec)
	result=from_bash.read()
	from_bash.close()
	return result
	
def strip_line(string=''):
	#may be .rstrip("\n") use?
	if string=='' :
		return string
	return string[0:len(string)-1]
	
def getshell_var(s):
	if os.confstr(s):
		return os.environ[s]
	return None
	