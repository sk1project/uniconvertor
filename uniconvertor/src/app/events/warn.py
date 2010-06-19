# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 1999, 2001 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


import sys, string
from types import StringType, DictionaryType
import traceback

# import config
from app import _


INTERNAL = 'INTERNAL'
USER = 'USER'

#TEMPORAL CONSTANTS TO DO REFACTORING
WARN_METHOD = 'dialog'
PRINT_INTERNAL_WARNINGS =1
PRINT_DEBUG_MESSAGES = 1

def write_error(message):
	sys.stderr.write(message)
	if message and message[-1] != '\n':
		sys.stderr.write('\n')

def flexible_format(format, args, kw):
	try:
		if args:
			text = format % args
		elif kw:
			text = format % kw
		else:
			text = format
	except TypeError:
		if args:
			text = string.join([format] + map(str, args))
		elif kw:
			text = string.join([format] + map(str, kw.items()))
		else:
			text = format
	
	return text
	

def warn(_level, _message, *args, **kw):
	_message = flexible_format(_message, args, kw)

	if _level == INTERNAL:
		#TODO: reverse to preferences after refactoring
		if PRINT_INTERNAL_WARNINGS: 
# 		if config.preferences.print_internal_warnings:
			write_error(_message)
	else:
		write_error(_message)
	return _message

def warn_tb(_level, _message = '', *args, **kw):
	_message = flexible_format(_message, args, kw)

	if _level == INTERNAL:
		#TODO: reverse to preferences after refactoring
		if PRINT_INTERNAL_WARNINGS:
# 		if config.preferences.print_internal_warnings:
			write_error(_message)
			traceback.print_exc()
	else:
		write_error(_message)
		traceback.print_exc()
	return _message
		



def Dict(**kw):
	return kw

_levels = Dict(default = 1,
				__del__ = 0,
				Graphics = 1,
				properties = 0,
				DND = 1,
				context_menu = 0,
				Load = Dict(default = 1,
				PSK = 1,
				AI = 1,
				echo_messages = 1),
				PS = 1,
				bezier = 1,
				styles = 1,
				tkext = 0,
				handles = 0,
				timing = 0)

def pdebug(level, message, *args, **kw):
	#TODO: reverse to preferences after refactoring
# 	if not config.preferences.print_debug_messages:
	if not PRINT_DEBUG_MESSAGES:
		return
	if level:
		if type(level) == StringType:
			level = (level,)
		enabled = _levels
		for item in level:
			try:
				enabled = enabled[item]
			except:
				break
		if type(enabled) == DictionaryType:
			enabled = enabled['default']
		if not enabled:
			return
	message = flexible_format(message, args, kw)
	write_error(message)



