# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001 by Bernhard Herzog
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

from math import sin, cos, atan2, hypot, pi, fmod, floor

from app.conf.const import ArcArc, ArcChord, ArcPieSlice, ConstraintMask, \
		AlternateMask

from app import _, Point, Polar, Trafo, SingularMatrix, Rect, UnionRects, \
		CreateMultiUndo, NullUndo, RegisterCommands

#import graphics

#from app.UI.command import AddCmd

import handle
from base import Primitive, RectangularPrimitive, RectangularCreator, Creator,\
		Editor
from bezier import PolyBezier
from blend import Blend
from properties import DefaultGraphicsProperties

from app import _sketch



#
#	Ellipse
#

# helper function for snapping (might be useful elsewhere too):
def snap_to_line(start, end, p):
	if start != end:
		result = [(abs(start - p), start), (abs(end - p), end)]
		v = end - start
		length = abs(v)
		r = (v * (p - start)) / (length ** 2)
		if 0 <= r <= 1.0:
			p2 = start + r * v
			result.append((abs(p2 - p), p2))
		return min(result)
	else:
		return (abs(start - p), start)



class Ellipse(RectangularPrimitive):

	is_Ellipse = 1
	is_curve = 1
	is_clip = 1
	has_edit_mode = 1

	commands = RectangularPrimitive.commands[:]

	def __init__(self, trafo = None, start_angle = 0.0, end_angle = 0.0,
					arc_type = ArcPieSlice, properties = None, duplicate = None):
		if trafo is not None and trafo.m11==trafo.m21==trafo.m12==trafo.m22==0:
			trafo=Trafo(1,0,0,-1,trafo.v1,trafo.v2)
		if duplicate is not None:
			self.start_angle = duplicate.start_angle
			self.end_angle = duplicate.end_angle
			self.arc_type = duplicate.arc_type
		else:
			self.start_angle = start_angle
			self.end_angle = end_angle
			self.arc_type = arc_type
		RectangularPrimitive.__init__(self, trafo, properties = properties,
										duplicate = duplicate)
		self.normalize()

	def DrawShape(self, device, rect = None, clip = 0):
		Primitive.DrawShape(self, device)
		device.SimpleEllipse(self.trafo, self.start_angle, self.end_angle,
								self.arc_type, rect, clip)

	def SetAngles(self, start_angle, end_angle):
		undo = (self.SetAngles, self.start_angle, self.end_angle)
		self.start_angle = start_angle
		self.end_angle = end_angle
		self.normalize()
		self._changed()
		return undo

	def Angles(self):
		return self.start_angle, self.end_angle

	def SetArcType(self, arc_type):
		if arc_type == self.arc_type:
			return NullUndo
		undo = (self.SetArcType, self.arc_type)
		self.arc_type = arc_type
		self._changed()
		return undo

	def ArcType(self):
		return self.arc_type

	#AddCmd(commands, 'EllipseArc', _("Arc"), SetArcType, args = ArcArc)
	#AddCmd(commands, 'EllipseChord', _("Chord"), SetArcType, args = ArcChord)
	#AddCmd(commands, 'EllipsePieSlice', _("Pie Slice"), SetArcType, args = ArcPieSlice)

	def normalize(self):
		pi2 = 2 * pi
		self.start_angle = fmod(self.start_angle, pi2)
		if self.start_angle < 0:
			self.start_angle = self.start_angle + pi2
		self.end_angle = fmod(self.end_angle, pi2)
		if self.end_angle < 0:
			self.end_angle = self.end_angle + pi2

	def Paths(self):
		path = _sketch.approx_arc(self.start_angle, self.end_angle,
									self.arc_type)
		path.Transform(self.trafo)
		return (path,)

	def AsBezier(self):
		return PolyBezier(paths = self.Paths(),
							properties = self.properties.Duplicate())

	def Hit(self, p, rect, device, clip = 0):
		return device.SimpleEllipseHit(p, self.trafo, self.start_angle,
										self.end_angle, self.arc_type,
										self.properties, self.Filled() or clip,
										ignore_outline_mode = clip)

	def Blend(self, other, p, q):
		blended = RectangularPrimitive.Blend(self, other, p, q)
		if self.start_angle != self.end_angle \
			or other.start_angle != other.end_angle:
			blended.start_angle = p * self.start_angle + q * other.start_angle
			blended.end_angle = p * self.end_angle + q * other.end_angle
			if self.start_angle == self.end_angle:
				blended.arc_type = other.arc_type
			elif other.start_angle == other.end_angle:
				blended.arc_type = self.arc_type
			else:
				if self.arc_type == other.arc_type:
					blended.arc_type = self.arc_type
				# The rest of the arc type blends is quite arbitrary
				# XXX: are these rules acceptable? Maybe we should blend
				# the ellipses as bezier curves if the arc types differ
				elif self.arc_type == ArcArc or other.arc_type == ArcArc:
					blended.arc_type = ArcArc
				elif self.arc_type == ArcChord or other.arc_type == ArcChord:
					blended.arc_type = ArcChord
				else:
					blended.arc_type = ArcPieSlice
		return blended

	def GetSnapPoints(self):
		t = self.trafo
		start_angle = self.start_angle; end_angle = self.end_angle
		if self.start_angle == self.end_angle:
			a = Point(t.m11, t.m21)
			b = Point(t.m12, t.m22)
			c = t.offset()
			return [c, c + a, c - a, c + b, c - b]
		else:
			points = [t(Polar(start_angle)), t(Polar(end_angle)), t.offset()]
			if end_angle < start_angle:
				end_angle = end_angle + 2 * pi
			pi2 = pi / 2
			angle = pi2 * (floor(start_angle / pi2) + 1)
			while angle < end_angle:
				points.append(t(Polar(1, angle)))
				angle = angle + pi2
			return points

	def Snap(self, p):
		try:
			r, phi = self.trafo.inverse()(p).polar()
			start_angle = self.start_angle; end_angle = self.end_angle
			p2 = self.trafo(Polar(1, phi))
			if start_angle == end_angle:
				result = (abs(p - p2), p2)
			else:
				result = []
				if phi < 0:
					phi = phi + 2 * pi
				if start_angle < end_angle:
					between = start_angle <= phi <= end_angle
				else:
					between = start_angle <= phi or phi <= end_angle
				if between:
					result.append((abs(p - p2), p2))
				start = self.trafo(Polar(self.start_angle))
				end = self.trafo(Polar(self.end_angle))
				if self.arc_type == ArcArc:
					result.append((abs(start - p), start))
					result.append((abs(end - p), end))
				elif self.arc_type == ArcChord:
					result.append((snap_to_line(start, end, p)))
				elif self.arc_type == ArcPieSlice:
					center = self.trafo.offset()
					result.append(snap_to_line(start, center, p))
					result.append(snap_to_line(end, center, p))
				result = min(result)
			return result
		except SingularMatrix:
			# XXX this case could be handled better.
			return (1e200, p)


	def update_rects(self):
		trafo = self.trafo
		start = trafo.offset()
		# On some systems, atan2 can raise a ValueError if both
		# parameters are 0. In that case, the actual value the of angle
		# is not important since in the computation of p below, the
		# coordinate depending on the angle will always be 0 because
		# both trafo coefficients are 0. So set the angle to 0 in case
		# of an exception.
		try:
			phi1 = atan2(trafo.m12, trafo.m11)
		except ValueError:
			phi1 = 0
		try:
			phi2 = atan2(trafo.m22, trafo.m21)
		except ValueError:
			phi2 = 0
		p = Point(trafo.m11 * cos(phi1) + trafo.m12 * sin(phi1),
					trafo.m21 * cos(phi2) + trafo.m22 * sin(phi2))
		self.coord_rect = r = Rect(start + p, start - p)
		if self.properties.HasLine():
			width = self.properties.line_width
			r = r.grown(width / 2 + 1)
			# add the bounding boxes of arrows
			if self.arc_type == ArcArc:
				pi2 = pi / 2
				arrow1 = self.properties.line_arrow1
				if arrow1 is not None:
					pos = trafo(Polar(1, self.start_angle))
					dir = trafo.DTransform(Polar(1, self.start_angle - pi2))
					r = UnionRects(r, arrow1.BoundingRect(pos, dir, width))
				arrow2 = self.properties.line_arrow2
				if arrow2 is not None:
					pos = trafo(Polar(1, self.end_angle))
					dir = trafo.DTransform(Polar(1, self.end_angle + pi2))
					r = UnionRects(r, arrow2.BoundingRect(pos, dir, width))
		self.bounding_rect = r

	def Info(self):
		trafo = self.trafo
		w = hypot(trafo.m11, trafo.m21)
		h = hypot(trafo.m12, trafo.m22)
		dict = {'center': trafo.offset(), 'radius': w, 'axes': (w, h)}
		if w == h:
			text = _("Circle radius %(radius)[length], "
						"center %(center)[position]")
		else:
			text = _("Ellipse axes %(axes)[size], center %(center)[position]")
		return text, dict

	def SaveToFile(self, file):
		Primitive.SaveToFile(self, file)
		file.Ellipse(self.trafo, self.start_angle, self.end_angle,
						self.arc_type)

	def Editor(self):
		return EllipseEditor(self)

	context_commands = ('EllipseArc', 'EllipseChord', 'EllipsePieSlice')

RegisterCommands(Ellipse)


class EllipseCreator(RectangularCreator):

	creation_text = _("Create Ellipse")

	def compute_trafo(self, state):
		start = self.drag_start
		end = self.drag_cur
		if state & AlternateMask:
			# start is the center of the ellipse
			if state & ConstraintMask:
				# end is a point of the periphery of a *circle* centered
				# at start
				radius = abs(start - end)
				self.trafo = Trafo(radius, 0, 0, radius, start.x, start.y)
			else:
				# end is a corner of the bounding box
				d = end - start
				self.trafo = Trafo(d.x, 0, 0, d.y, start.x, start.y)
		else:
			# the ellipse is inscribed into the rectangle with start and
			# end as opposite corners. 
			end = self.apply_constraint(self.drag_cur, state)
			d = (end - start) / 2
			self.trafo = Trafo(d.x, 0, 0, d.y, start.x + d.x, start.y + d.y)
			
	def MouseMove(self, p, state):
		# Bypass RectangularCreator
		Creator.MouseMove(self, p, state)
		self.compute_trafo(state)

	def ButtonUp(self, p, button, state):
		Creator.DragStop(self, p)
		self.compute_trafo(state)

	def DrawDragged(self, device, partially):
		device.DrawEllipse(self.trafo(-1, -1), self.trafo(1, 1))

	def CurrentInfoText(self):
		t = self.trafo
		data = {}
		if abs(round(t.m11, 2)) == abs(round(t.m22, 2)):
			text = _("Circle %(radius)[length], center %(center)[position]")
			data['radius'] = t.m11
		else:
			text = _("Ellipse %(size)[size], center %(center)[position]")
			data['size'] = (abs(t.m11), abs(t.m22))
		data['center'] = t.offset()
		return text, data

	def CreatedObject(self):
		return Ellipse(self.trafo,
						properties = DefaultGraphicsProperties())


class EllipseEditor(Editor):

	EditedClass = Ellipse

	selection = 0

	def ButtonDown(self, p, button, state):
		if self.selection == 1:
			start = self.trafo(cos(self.start_angle), sin(self.start_angle))
		else:
			start = self.trafo(cos(self.end_angle), sin(self.end_angle))
		Editor.DragStart(self, start)
		return p - start

	def apply_constraint(self, p, state):
		if state & ConstraintMask:
			try:
				inverse = self.trafo.inverse()
				p2 = inverse(p)
				r, phi = p2.polar()
				pi12 = pi / 12
				angle = pi12 * floor(phi / pi12 + 0.5)
				pi2 = 2 * pi
				d1 = fmod(abs(phi - angle), pi2)
				if self.selection == 1:
					selected_angle = self.end_angle
				else:
					selected_angle = self.start_angle
				d2 = fmod(abs(phi - selected_angle), pi2)
				if d2 < d1:
					phi = selected_angle
				else:
					phi = angle
				p = self.trafo(Polar(r, phi))
			except SingularMatrix:
				pass
		return p

	def MouseMove(self, p, state):
		p = self.apply_constraint(p, state)
		Editor.MouseMove(self, p, state)

	def ButtonUp(self, p, button, state):
		p = self.apply_constraint(p, state)
		Editor.DragStop(self, p)
		start_angle, end_angle, arc_type = self.angles()
		return CreateMultiUndo(self.object.SetAngles(start_angle, end_angle),
								self.object.SetArcType(arc_type))

	def angles(self):
		start_angle = self.start_angle; end_angle = self.end_angle
		if self.arc_type == ArcChord:
			arc_type = ArcChord
		else:
			arc_type = ArcPieSlice

		try:
			inverse = self.trafo.inverse()
			p = inverse(self.drag_cur)
			if self.selection == 1:
				start_angle = atan2(p.y, p.x)
			elif self.selection == 2:
				end_angle = atan2(p.y, p.x)
			if abs(p) > 1:
				arc_type = ArcArc
		except SingularMatrix:
			pass
		if fmod(abs(start_angle - end_angle), 2 * pi) < 0.0001:
			if self.selection == 1:
				start_angle = end_angle
			else:
				end_angle = start_angle
		return (start_angle, end_angle, arc_type)

	def DrawDragged(self, device, partially):
		start_angle, end_angle, arc_type = self.angles()
		device.SimpleEllipse(self.trafo, start_angle, end_angle, arc_type)

	def GetHandles(self):
		trafo = self.trafo
		start_angle = self.start_angle; end_angle = self.end_angle
		p1 = trafo(cos(self.start_angle), sin(self.start_angle))
		if start_angle == end_angle:
			return [handle.MakeNodeHandle(p1)]
		p2 = trafo(cos(self.end_angle), sin(self.end_angle))
		return [handle.MakeNodeHandle(p1), handle.MakeNodeHandle(p2)]

	def SelectHandle(self, handle, mode):
		self.selection = handle.index + 1

	def SelectPoint(self, p, rect, device, mode):
		return 0
