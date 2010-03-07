# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999 by Bernhard Herzog
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


from app import _, Point, PointType, InfinityRect
from base import GraphicsObject, Draggable

class GuideLine(GraphicsObject, Draggable):

	is_GuideLine = 1

	def __init__(self, point, horizontal = 0):
		self.point = point
		self.horizontal = horizontal

	def DrawShape(self, device):
		device.DrawGuideLine(self.point, self.horizontal,1)

	def DrawDragged(self, device, partially):
		device.DrawGuideLine(self.drag_cur, self.horizontal,0)

	def Hit(self, p, rect, device):
		if self.horizontal:
			return rect.contains_point(Point(p.x, self.point.y))
		else:
			return rect.contains_point(Point(self.point.x, p.y))

	def ButtonDown(self, p, button, state):
		self.DragStart(p)
		if self.horizontal:
			result = Point(0, p.y - self.point.y)
		else:
			result = Point(p.x - self.point.x, 0)
		return result

	def ButtonUp(self, p, button, state):
		self.DragStop(p)

	def SetPoint(self, point):
		undo = (self.SetPoint, self.point)
		if type(point) != PointType:
			if type(point) == type(()):
				point = apply(Point, point)
			else:
				if self.horizontal:
					point = Point(self.point.x, point)
				else:
					point = Point(point, self.point.y)
		self.point = point
		return undo

	def update_rects(self):
		self.bounding_rect = self.coord_rect = InfinityRect

	def get_clear_rect(self):
		return (self.point, self.horizontal)

	def Snap(self, p):
		if self.horizontal:
			return (abs(p.y - self.point.y), (None, self.point.y))
		else:
			return (abs(p.x - self.point.x), (self.point.x, None))

	def SaveToFile(self, file):
		file.GuideLine(self.point, self.horizontal)

	def Coordinates(self):
		if self.horizontal:
			return (self.point.y, 1)
		else:
			return (self.point.x, 0)


	def CurrentInfoText(self):
		if self.horizontal:
			text = _("Horizontal Guide Line at %(coord)[length]")
			dict = {'coord': self.drag_cur.y}
		else:
			text = _("Vertical Guide Line at %(coord)[length]")
			dict = {'coord': self.drag_cur.x}
		return text, dict
