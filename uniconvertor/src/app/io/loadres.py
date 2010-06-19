# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
# Read a Sketch resource file (dashes, arrows...)
#

from app.events.skexceptions import SketchError
from app.events.warn import warn_tb, USER

def read_resource_file(filename, magic, errmsg, functions):
	file = open(filename, 'r')
	try:
		line = file.readline()
		if line[:len(magic)] != magic:
			raise SketchError(errmsg % filename)

		from app.skread import parse_sk_line

		linenr = 1
		while 1:
			line = file.readline()
			if not line:
				break
			linenr = linenr + 1
			try:
				parse_sk_line(line, functions)
			except:
				warn_tb(USER, '%s:%d', filename, linenr)
	finally:
		file.close()
