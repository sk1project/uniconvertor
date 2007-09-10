# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1998 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

# Sketch specific exceptions

class SketchError(Exception):
	pass

class SketchInternalError(SketchError):
	pass

class SketchLoadError(SketchError):
	pass


class SketchIOError(SketchError):

	def __init__(self, errno, strerror, filename = ''):
		self.errno = errno
		self.strerror = strerror
		self.filename = filename
