# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
# Miscellaneous functions for PostScript creation
#

from string import join
import operator

def make_ps_quote_table():
	table = [''] * 256
	quote = (ord('('), ord(')'), ord('\\'))
	for i in range(128):
		if i in quote:
			table[i] = '\\' + chr(i)
		else:
			table[i] = chr(i)
	for i in range(128, 256):
		table[i] = '\\' + oct(i)[1:]
	return table

quote_table = make_ps_quote_table()

def quote_ps_string(text):
	return join(map(operator.getitem, [quote_table]*len(text), map(ord, text)),
				'')

def make_textline(text):
	# return text unchanged if no character needs to be quoted, as a
	# PS-string (with enclosing parens) otherwise.
	quoted = quote_ps_string(text)
	if quoted == text:
		return text
	return "(%s)" % quoted
