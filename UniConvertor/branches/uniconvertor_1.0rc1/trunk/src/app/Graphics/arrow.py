# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2001 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


#
#	Arrows
#

import os
from types import TupleType, ListType
from math import atan2, sin, cos

from app.events.warn import warn_tb, USER, pdebug
from app import config
from app import _, Trafo, CreatePath

from app.io.loadres import read_resource_file

class Arrow:

	def __init__(self, path, closed = 0):
		self.path = CreatePath()
		if type(path) in (ListType, TupleType):
			for segment in path:
				if len(segment) == 2:
					apply(self.path.AppendLine, segment)
				else:
					apply(self.path.AppendBezier, segment)
		else:
			self.path = path
		if closed:
			self.path.load_close()

	def BoundingRect(self, pos, dir, width):
		angle = atan2(dir.y, dir.x)
		if width < 1.0:
			width = 1.0
		s = width * sin(angle)
		c = width * cos(angle)
		trafo = Trafo(c, s, -s, c, pos.x, pos.y)
		return self.path.accurate_rect(trafo)

	def Draw(self, device, rect = None):
		if self.path.closed:
			device.FillBezierPath(self.path, rect)
		else:
			device.DrawBezierPath(self.path, rect)

	def Paths(self):
		return (self.path,)

	def IsFilled(self):
		return self.path.closed

	def SaveRepr(self):
		path = map(lambda t: t[:-1], self.path.get_save())
		return (path, self.path.closed)

	def __hash__(self):
		return hash(id(self.path))

	def __cmp__(self, other):
		if __debug__:
			pdebug(None, 'Arrow.__cmp__, %s', other)
		if isinstance(other, self.__class__):
			return cmp(self.path, other.path)
		return cmp(id(self), id(other))


def read_arrows(filename):
	arrows = []
	def arrow(path, closed, list = arrows):
		list.append(Arrow(path, closed))
	dict = {'arrow': arrow}

	read_resource_file(filename, '##Sketch Arrow 0', _("%s is not an arrow definition file"), dict)

	return arrows


std_arrows = None
def StandardArrows():
	global std_arrows
	if std_arrows is None:
		filename = os.path.join(config.std_res_dir, config.preferences.arrows)
		try:
			std_arrows = read_arrows(filename)
		except:
			warn_tb(USER, _("Error trying to read arrows from %s\n"
							"Using builtin defaults"), filename)
			std_arrows = []
	return std_arrows
