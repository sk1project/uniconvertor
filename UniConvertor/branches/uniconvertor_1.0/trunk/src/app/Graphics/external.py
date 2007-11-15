# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#
# Handle external data
#
#
# This module defines two classes to represent external graphics like
# bitmapped images or encapsulated PostScript files.


from app import Rect, Trafo, IdentityMatrix, NullUndo, SKCache

from base import GraphicsObject, RectangularObject
from properties import EmptyProperties


instance_cache = SKCache()

class ExternalData:

	# default instance variables
	stored_in_cache = 0
	filename = ''

	def __init__(self, filename = '', do_cache = 1):
		if filename and do_cache:
			self.stored_in_cache = 1
			instance_cache[filename] = self
		if filename:
			self.filename = filename

	def __del__(self):
		if self.stored_in_cache and instance_cache.has_key(self.filename):
			del instance_cache[self.filename]

	def Filename(self):
		return self.filename


	# to be supplied by derived classes
	#
	#    Size() return the size as a tuple (width, height)


def get_cached(filename):
	if instance_cache.has_key(filename):
		return instance_cache[filename]
	return None


class ExternalGraphics(RectangularObject, GraphicsObject):

	has_edit_mode = 0
	# by default this has no properties:
	has_fill = has_line = has_font = 0

	data = None

	def __init__(self, data = None, trafo = None, duplicate = None):
		RectangularObject.__init__(self, trafo, duplicate = duplicate)
		GraphicsObject.__init__(self, duplicate = duplicate)
		if duplicate is not None:
			data = duplicate.data
		self.data = data

	def Data(self):
		return self.data

	def SetData(self, data):
		undo = self.SetData, self.data
		self.data = data
		# XXX issue_changed() here ?
		return undo

	def Hit(self, p, rect, device, clip = 0):
		width, height = self.data.Size()
		return device.ParallelogramHit(p, self.trafo, width, height, 1,
										ignore_outline_mode = clip)

	def SetLowerLeftCorner(self, corner):
		# Used by the place mode in SketchCanvas. Currently no undo
		# needed since this is called *before* self is a part of a
		# document.
		self.trafo = apply(Trafo, self.trafo.coeff()[:4] + tuple(corner))
		self.del_lazy_attrs()

	def RemoveTransformation(self):
		if self.trafo.matrix() != IdentityMatrix:
			center = self.coord_rect.center()
			width, height = self.data.Size()
			trafo = Trafo(1, 0, 0, 1,
							center.x - width / 2, center.y - height / 2)
			return self.set_transformation(trafo)
		return NullUndo

	def update_rects(self):
		width, height = self.data.Size()
		rect = self.trafo(Rect(0, 0, width, height))
		self.coord_rect = rect
		self.bounding_rect = rect.grown(2)

	def Info(self):
		# Should be overwritten by derived classes
		return 'ExternalGraphics'

	def SetProperties(self, **kw):
		return NullUndo

	def AddStyle(self, style):
		return NullUndo

	def Properties(self):
		return EmptyProperties

	def GetSnapPoints(self):
		width, height = self.data.Size()
		corners = ((0, 0), (width, 0), (width, height), (0, height))
		return map(self.trafo, corners)

	def Snap(self, p):
		width, height = self.data.Size()
		try:
			x, y = self.trafo.inverse()(p)
			if 0 <= x <= width:
				if 0 <= y <= height:
					x = round(x / width) * width
					y = round(y / height) * height
				else:
					y = min(max(y, 0), height)
			else:
				x = min(max(x, 0), width)
				if 0 > y or y > height:
					y = min(max(y, 0), height)

			p2 = self.trafo(x, y)
			return (abs(p - p2), p2)
		except SingularMatrix:
			return (1e200, p)
