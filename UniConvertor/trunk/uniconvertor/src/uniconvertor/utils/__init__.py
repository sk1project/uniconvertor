# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2002, 2003 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#	Some useful functions used in various places...
#

import os, string, re, stat


#An empty class...
class Empty:
	def __init__(self, **kw):
		for key, value in kw.items():
			setattr(self, key, value)

#
#	List Manipulation
#

from types import ListType
def flatten(list):
	result = []
	for item in list:
		if type(item) == ListType:
			result = result + flatten(item)
		else:
			result.append(item)
	return result
		
		
#
#       String Manipulation
#

rx_format = re.compile(r'%\((?P<item>[a-zA-Z_0-9]+)\)'
						r'\[(?P<converter>[a-zA-Z_]+)\]')

def format(template, converters, dict):
	result = []
	pos = 0
	while pos < len(template):
		match = rx_format.search(template, pos)
		if match:
			result.append(template[pos:match.start()] % dict)
			converter = converters[match.group('converter')]
			item = dict[match.group('item')]
			result.append(converter(item))
			pos = match.end()
		else:
			result.append(template[pos:] % dict)
			pos = len(template)

	return string.join(result, '')

# convert a bitmap to a string containing an xbm file. The linedlg uses
# this for instance to convert bitmap objects to Tk bitmap images.
def xbm_string(bitmap):
	import string
	width, height = bitmap.GetGeometry()[3:5]
	lines = ['#define sketch_width %d' % width,
				'#define sketch_height %d' % height,
				'static unsigned char sketch_bits[] = {']
	lines = lines + bitmap.GetXbmStrings() + ['}', '']
	return string.join(lines, '\n')


# sh_quote taken almost verbatim from the python standard library with
# the only difference that it doesn't prepend a space
def sh_quote(x):
	"""Return a unix shell quoted version of the string x.

	The result is of a form that can be inserted into an argument to
	os.system so that it looks like a single word to the shell.
	"""
	# Two strategies: enclose in single quotes if it contains none;
	# otherwise, enclose in double quotes and prefix quotable characters
	# with backslash.
	if '\'' not in x:
		return '\'' + x + '\''
	s = '"'
	for c in x:
		if c in '\\$"`':
			s = s + '\\'
		s = s + c
	s = s + '"'
	return s