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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

# Rectangle:
#
# The Rectangle is actually better described as a Parallelogram. When
# created interactively, instances of this class are rectangles with
# edges parallel to the axes of the coordinate system. The user can then
# rotate and shear it interactively so that it may become a
# (nonrectangular) Parallelogram.
#

from math import hypot

from app.conf.const import corners, AlternateMask
from app import _, SingularMatrix, PointsToRect, Trafo, Polar,\
		RoundedRectanglePath, RectanglePath, NullUndo
from app.events.warn import warn, INTERNAL

from base import Primitive, RectangularPrimitive, RectangularCreator, Editor
from bezier import PolyBezier
import handle
from properties import DefaultGraphicsProperties

class Rectangle(RectangularPrimitive):

	is_Rectangle = 1
	is_curve = 1
	is_clip = 1
	has_edit_mode = 1

	_lazy_attrs = RectangularPrimitive._lazy_attrs.copy()
	_lazy_attrs['rect_path'] = 'update_path'

	def __init__(self, trafo = None, radius1 = 0, radius2 = 0,
					properties = None, duplicate = None):
		if trafo is not None and trafo.m11==trafo.m21==trafo.m12==trafo.m22==0:
			trafo=Trafo(1,0,0,-1,trafo.v1,trafo.v2)
		RectangularPrimitive.__init__(self, trafo, properties = properties,
										duplicate = duplicate)	
		if duplicate is not None:
			self.radius1 = duplicate.radius1
			self.radius2 = duplicate.radius2
		else:
			self.radius1 = radius1
			self.radius2 = radius2

	def Radii(self):
		return self.radius1, self.radius2

	def SetTrafoAndRadii(self, trafo, radius1, radius2):	
		print 'TRAFO >>>>>>>>',trafo	
		undo = self.SetTrafoAndRadii, self.trafo, self.radius1, self.radius2
		self.trafo = trafo
		if radius1 <= 0 or radius2 <= 0:
			self.radius1 = 0
			self.radius2 = 0
			if __debug__:
				if radius1 > 0 or radius2 > 0:
					warn(INTERNAL,
							'Rectangle radius corrected: r1 = %g, r2 = %g',
							radius1, radius2)
		else:
			self.radius1 = radius1
			self.radius2 = radius2
		self._changed()
		return undo

	def DrawShape(self, device, rect = None, clip = 0):
		Primitive.DrawShape(self, device)
		if self.radius1 == self.radius2 == 0:
			device.Rectangle(self.trafo, clip)
		else:
			device.RoundedRectangle(self.trafo, self.radius1, self.radius2,
									clip)

	def update_path(self):
		if self.radius1 == self.radius2 == 0:
			self.rect_path = (RectanglePath(self.trafo),)
		else:
			self.rect_path = (RoundedRectanglePath(self.trafo, self.radius1,
													self.radius2),)

	def Paths(self):
		return self.rect_path

	def AsBezier(self):
		return PolyBezier(paths = self.rect_path,
							properties = self.properties.Duplicate())

	def Hit(self, p, rect, device, clip = 0):
		if self.radius1 == self.radius2 == 0:
			return device.ParallelogramHit(p, self.trafo, 1, 1,
											clip or self.Filled(),
											self.properties,
											ignore_outline_mode = clip)
		else:
			return device.MultiBezierHit(self.rect_path, p, self.properties,
											clip or self.Filled(),
											ignore_outline_mode = clip)
	def GetSnapPoints(self):
		return map(self.trafo, corners)
	
	def Snap(self, p):
		try:
			x, y = self.trafo.inverse()(p)
			minx = self.radius1
			maxx = 1 - self.radius1
			miny = self.radius2
			maxy = 1 - self.radius2
			if minx < x < maxx:
				if miny < y < maxy:
					ratio = hypot(self.trafo.m11, self.trafo.m21) \
							/ hypot(self.trafo.m12, self.trafo.m22)
					if x < 0.5:
						dx = x
					else:
						dx = 1 - x
					if y < 0.5:
						dy = y
					else:
						dy = 1 - y
					if dy / dx > ratio:
						x = round(x)
					else:
						y = round(y)
				elif y > maxy:
					y = 1
				else:
					y = 0
			elif miny < y < maxy:
				if x > maxx:
					x = 1
				else:
					x = 0
			elif minx > 0 and miny > 0:
				# the round corners
				if x < 0.5:
					cx = minx
				else:
					cx = maxx
				if y < 0.5:
					cy = miny
				else:
					cy = maxy
				trafo = Trafo(minx, 0, 0, miny, cx, cy)
				r, phi = trafo.inverse()(x, y).polar()
				x, y = trafo(Polar(1, phi))
			else:
				# normal corners
				x = round(min(max(x, 0), 1))
				y = round(min(max(y, 0), 1))

			p2 = self.trafo(x, y)
			return (abs(p - p2), p2)
		except SingularMatrix:
			return (1e200, p)

	def update_rects(self):
		rect = PointsToRect(map(self.trafo, corners))
		self.coord_rect = rect
		if self.properties.HasLine():
			self.bounding_rect = rect.grown(self.properties.GrowAmount())
		else:
			self.bounding_rect = rect

	def Info(self):
		trafo = self.trafo
		w = hypot(trafo.m11, trafo.m21)
		h = hypot(trafo.m12, trafo.m22)
		return _("Rectangle %(size)[size]"), {'size': (w, h)}

	def SaveToFile(self, file):
		Primitive.SaveToFile(self, file)
		file.Rectangle(self.trafo, self.radius1, self.radius2)

	def Blend(self, other, p, q):
		result = RectangularPrimitive.Blend(self, other, p, q)
		result.radius1 = p * self.radius1 + q * other.radius1
		result.radius2 = p * self.radius2 + q * other.radius2
		return result

	def Editor(self):
		return RectangleEditor(self)



class RectangleCreator(RectangularCreator):

	creation_text = _("Create Rectangle")

	state = 0
	
	def MouseMove(self, p, state):
		self.state = state
		RectangularCreator.MouseMove(self, p, state)
	
	def ButtonUp(self, p, button, state):
		if self.state & AlternateMask:
			p = self.apply_constraint(p, state)
			self.DragStop(p)
			off = 2 * self.off
			end = self.trafo.offset() - self.off
			self.trafo = Trafo(off.x, 0, 0, off.y, end.x, end.y)
		else:
			RectangularCreator.ButtonUp(self, p, button, state)

	def DrawDragged(self, device, partially):
		start = self.drag_start
		if self.state & AlternateMask:
			start = start - self.off
		device.DrawRectangle(start, self.drag_cur)

	def CurrentInfoText(self):
		start = self.drag_start
		if self.state & AlternateMask:
			start = start - self.off
		width, height = self.drag_cur - start
		return 'Rectangle: %(size)[size]', {'size': (abs(width), abs(height))}

	def CreatedObject(self):
		return Rectangle(self.trafo,
							properties = DefaultGraphicsProperties())


class RectangleEditor(Editor):

	EditedClass = Rectangle

	selection = None

	def ButtonDown(self, p, button, state):
		if self.selection is not None:
			start = self.selection.p
			Editor.DragStart(self, start)
			return p - start
		else:
			return None

	def ButtonUp(self, p, button, state):
		if self.selection is not None:
			trafo, radius1, radius2 = self.resize()
			self.selection = None
			return self.object.SetTrafoAndRadii(trafo, radius1, radius2)
		else:
			return NullUndo

	def resize(self):
		code = self.selection.x_code
		trafo = self.trafo; radius1 = self.radius1; radius2 = self.radius2
		if code < 0:
			# a special handle that has to be treated as a normal handle
			# depending on the direction of the drag
			width = hypot(trafo.m11, trafo.m21)
			height = hypot(trafo.m12, trafo.m22)
			t = Trafo(trafo.m11 / width, trafo.m21 / width,
						trafo.m12 / height, trafo.m22 / height, 0, 0)
			dx, dy = t.inverse()(self.off)
			#print code, dx, dy
			if code > -5:
				# one of the corners in a rectangle with sharp corners
				if abs(dx) > abs(dy):
					code = 4 - code
				else:
					code = (12, 10, 11, 9)[code]
			else:
				# the edge handle and the round corner handles coincide
				if code >= -7:
					# horizontal edges
					if abs(dx) > abs(dy):
						if dx < 0:
							code = -code
						else:
							code = -code + 1
					else:
						code = -4 - code
				else:
					# vertical edges
					if abs(dx) > abs(dy):
						code = code + 13
					else:
						if dy < 0:
							code = -code
						else:
							code = -code + 1
		#
		# code is now a normal handle
		#
		#print '->', code
		x, y = trafo.inverse()(self.drag_cur)
		width = hypot(trafo.m11, trafo.m21)
		height = hypot(trafo.m12, trafo.m22)
		if code <= 4:
			# drag one of the edges
			if code == 1:
				t = Trafo(1, 0, 0, 1 - y, 0, y)
				if y != 1:
					radius2 = radius2 / abs(1 - y)
				else:
					radius1 = radius2 = 0
			elif code == 2:
				t = Trafo(x, 0, 0, 1, 0, 0)
				if x != 0:
					radius1 = radius1 / abs(x)
				else:
					radius1 = radius2 = 0
			elif code == 3:
				t = Trafo(1, 0, 0, y, 0, 0)
				if y != 0:
					radius2 = radius2 / abs(y)
				else:
					radius1 = radius2 = 0
			elif code == 4:
				t = Trafo(1 - x, 0, 0, 1, x, 0)
				if x != 1:
					radius1 = radius1 / abs(1 - x)
				else:
					radius1 = radius2 = 0
			trafo = trafo(t)
			if radius1 != 0 or radius2 != 0:
				ratio = radius1 / radius2
				if radius1 > 0.5:
					radius1 = 0.5
					radius2 = radius1 / ratio
				if radius2 > 0.5:
					radius2 = 0.5
					radius1 = radius2 * ratio
		else:
			# modify the round corners
			if radius1 == radius2 == 0:
				ratio = height / width
			else:
				ratio = radius1 / radius2
			
			if ratio > 1:
				max1 = 0.5
				max2 = max1 / ratio
			else:
				max2 = 0.5
				max1 = max2 * ratio
			if code < 9:
				if code == 6 or code == 8:
					x = 1 - x
				radius1 = max(min(x, max1), 0)
				radius2 = radius1 / ratio
			else:
				if code == 10 or code == 12:
					y = 1 - y
				radius2 = max(min(y, max2), 0)
				radius1 = radius2 * ratio
		return trafo, radius1, radius2
	
	def DrawDragged(self, device, partially):
		if self.selection is not None:
			trafo, radius1, radius2 = self.resize()
			device.RoundedRectangle(trafo, radius1, radius2)

	def GetHandles(self):
		trafo = self.trafo; radius1 = self.radius1; radius2 = self.radius2
		handles = []

		if radius1 == radius2 == 0:
			for x, y, code in ((0, 0, -1), (1, 0, -2), (0, 1, -3), (1, 1, -4),
								(0.5,   0, 1), (1.0, 0.5, 2),
								(0.5, 1.0, 3), (  0, 0.5, 4)):
				h = handle.MakeNodeHandle(trafo(x, y))
				h.x_code = code
				handles.append(h)
		else:
			# horizontal edges
			if round(radius1, 3) >= 0.5:
				h = handle.MakeNodeHandle(trafo(0.5, 0))
				h.x_code = -5
				handles.append(h)
				h = handle.MakeNodeHandle(trafo(0.5, 1))
				h.x_code = -7
				handles.append(h)
			else:
				coords = ((radius1, 0, 5), (0.5, 0, 1), (1 - radius1, 0, 6),
							(radius1, 1, 7), (0.5, 1, 3), (1 - radius1, 1, 8))
				for x, y, code in coords:
					h = handle.MakeNodeHandle(trafo(x, y))
					h.x_code = code
					handles.append(h)

			# vertical edges
			if round(radius2, 3) >= 0.5:
				h = handle.MakeNodeHandle(trafo(0, 0.5))
				h.x_code = -9
				handles.append(h)
				h = handle.MakeNodeHandle(trafo(1, 0.5))
				h.x_code = -11
				handles.append(h)
			else:
				coords = ((0, radius2, 9), (0, 0.5, 4), (0, 1 - radius2, 10),
							(1, radius2, 11),(1, 0.5, 2), (1, 1 - radius2, 12))
				for x, y, code in coords:
					h = handle.MakeNodeHandle(trafo(x, y))
					h.x_code = code
					handles.append(h)
		#
		return handles

	def SelectHandle(self, handle, mode):
		self.selection = handle

	def SelectPoint(self, p, rect, device, mode):
		return 0


