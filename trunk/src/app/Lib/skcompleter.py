# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2003 by Bernhard Herzog 
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

# This is a more general completer than the one of python 1.5 on which this
# one is based...

import readline
import __builtin__
import __main__

class Completer:

	def __init__(self, global_dict = None, local_dict = None):
		if global_dict is None:
			global_dict = __main__.__dict__
		self.global_dict = global_dict
		if local_dict is None:
			local_dict = global_dict
		self.local_dict = local_dict

	def complete(self, text, state):
		if state == 0:
			if "." in text:
				self.matches = self.attr_matches(text)
			else:
				self.matches = self.global_matches(text)
		return self.matches[state]

	def global_matches(self, text):
		import keyword
		matches = []
		n = len(text)
		for list in [keyword.kwlist,
				self.local_dict.keys(),
				self.global_dict.keys(),
				__builtin__.__dict__.keys()]:
			for word in list:
				if word[:n] == text:
					matches.append(word)
		return matches

	def attr_matches(self, text):
		import re
		m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
		if not m:
			return
		expr, attr = m.group(1, 3)
		words = dir(eval(expr, self.global_dict, self.local_dict))
		matches = []
		n = len(attr)
		for word in words:
			if word[:n] == attr:
				matches.append("%s.%s" % (expr, word))
		return matches

def install(global_dict = None, local_dict = None):
	readline.set_completer(Completer(global_dict, local_dict).complete)
