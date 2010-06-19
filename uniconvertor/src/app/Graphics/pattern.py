# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2003 by Bernhard Herzog
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

import math
from math import atan2, hypot, pi, sin, cos

from app import Point, Rotation, Translation, Trafo, NullPoint, NullUndo

from blend import Blend, MismatchError, BlendTrafo
import color



class Pattern:

	is_procedural = 1
	is_Empty = 0
	is_Solid = 0
	is_Gradient = 0
	is_RadialGradient = 0
	is_AxialGradient = 0
	is_ConicalGradient = 0
	is_Hatching = 0
	is_Tiled = 0
	is_Image = 0

	name = ''

	def __init__(self, duplicate = None):
		pass

	def SetName(self, name):
		self.name = name

	def Name(self):
		return self.name

	def Execute(self, device, rect = None):
		pass

	def Transform(self, trafo, rects = None):
		# This method is usually called by a primitives Transform method.
		return NullUndo

	def Duplicate(self):
		return self.__class__(duplicate = self)

	Copy = Duplicate

class EmptyPattern_(Pattern):

	is_procedural = 0
	is_Empty = 1

	def Duplicate(self):
		return self

	Copy = Duplicate

	def Blend(self, *args):
		return self

	def SaveToFile(self, file):
		file.EmptyPattern()

	def __str__(self):
		return 'EmptyPattern'

EmptyPattern = EmptyPattern_()

class SolidPattern(Pattern):

	is_procedural = 0
	is_Solid = 1

	def __init__(self, color = None, duplicate = None):
		if duplicate is not None:
			self.color = duplicate.color
		elif color is not None:
			self.color = color
		else:
			raise ValueError,'SolidPattern be must created with color argument'

	def __cmp__(self, other):
		if self.__class__ == other.__class__:
			return cmp(self.color, other.color)
		else:
			return cmp(id(self), id(other))

	def __str__(self):
		return 'SolidPattern(%s)' % `self.color`

	def Execute(self, device, rect = None):
		device.SetFillColor(self.color)

	def Blend(self, other, frac1, frac2):
		if other.__class__ == self.__class__:
			return SolidPattern(Blend(self.color, other.color, frac1, frac2))
		else:
			raise MismatchError

	def Color(self):
		return self.color

	def SaveToFile(self, file):
		file.SolidPattern(self.color)

class GradientPattern(Pattern):

	is_Gradient = 1

	def __init__(self, gradient, duplicate = None):
		if duplicate is not None:
			Pattern.__init__(self, duplicate = duplicate)
			self.gradient = duplicate.gradient.Duplicate()
		elif gradient:
			self.gradient = gradient
		else:
			raise ValueError,\
					'GradientPattern must be created with gradient argument'

	def Gradient(self):
		return self.gradient

	def SetGradient(self, gradient):
		undo = (self.SetGradient, self.gradient)
		self.gradient = gradient
		return undo


class LinearGradient(GradientPattern):

	is_AxialGradient = 1

	def __init__(self, gradient = None, direction = Point(0, -1),
					border = 0, duplicate = None):
		GradientPattern.__init__(self, gradient,
									duplicate = duplicate)
		self.direction = direction
		self.border = border
		if duplicate is not None:
			if duplicate.__class__ == self.__class__:
				self.direction = duplicate.direction
				self.border = duplicate.border
			elif duplicate.__class__ == ConicalGradient:
				self.direction = duplicate.direction
			elif duplicate.__class__ == RadialGradient:
				self.border = duplicate.border

	def SetDirection(self, dir):
		undo = (self.SetDirection, self.direction)
		self.direction = dir
		return undo

	def Direction(self):
		return self.direction

	def Border(self):
		return self.border

	def SetBorder(self, border):
		undo = (self.SetBorder, self.border)
		self.border = border
		return undo

	def Transform(self, trafo, rects = None):
		dx, dy = self.direction
		dx, dy = trafo.DTransform(dy, -dx)
		dir = Point(dy, -dx).normalized()
		if dir * trafo.DTransform(self.direction) < 0:
			dir = -dir
		return self.SetDirection(dir)

	def Execute(self, device, rect):
		if device.has_axial_gradient:
			self.execute_axial_gradient(device, rect)
			return

		SetFillColor = device.SetFillColor
		FillRectangle = device.FillRectangle
		steps = device.gradient_steps

		colors = self.gradient.Sample(steps)
		SetFillColor(colors[0])
		apply(device.FillRectangle, tuple(rect))

		device.PushTrafo()
		vx, vy = self.direction
		angle = atan2(vy, vx) - pi / 2
		center = rect.center()
		rot = Rotation(angle, center)
		left, bottom, right, top = rot(rect)
		device.Concat(rot)
		device.Translate(center)
		height = top - bottom
		miny = -height / 2
		height = height * (1.0 - self.border)
		width = right - left
		dy = height / steps
		y = height / 2
		x = width / 2
		for i in range(steps):
			SetFillColor(colors[i])
			FillRectangle(-x, y, +x, miny)
			y = y - dy
		device.PopTrafo()

	def execute_axial_gradient(self, device, rect):
		vx, vy = self.direction
		angle = atan2(vy, vx) - pi / 2
		center = rect.center()
		rot = Rotation(angle, center)
		left, bottom, right, top = rot(rect)
		height = (top - bottom) * (1.0 - self.border)
		trafo = rot(Translation(center))
		device.AxialGradient(self.gradient, trafo(0, height / 2),
								trafo(0, -height / 2))

	def Blend(self, other, frac1, frac2):
		if other.__class__ == self.__class__:
			gradient = other.gradient
			dir = other.direction
			border = other.border
		elif other.__class__ == SolidPattern:
			gradient = other.Color()
			dir = self.direction
			border = self.border
		else:
			raise MismatchError
		return LinearGradient(Blend(self.gradient, gradient, frac1, frac2),
								frac1 * self.direction + frac2 * dir,
								frac1 * self.border + frac2 * border)

	def SaveToFile(self, file):
		file.LinearGradientPattern(self.gradient, self.direction, self.border)


class RadialGradient(GradientPattern):

	is_RadialGradient = 1

	def __init__(self, gradient = None, center = Point(0.5, 0.5),
					border = 0, duplicate = None):
		GradientPattern.__init__(self, gradient,
									duplicate = duplicate)
		self.center = center
		self.border = border
		if duplicate is not None:
			if duplicate.__class__ == self.__class__:
				self.center = duplicate.center
				self.border = duplicate.border
			elif duplicate.__class__ == ConicalGradient:
				self.center = duplicate.center
			elif duplicate.__class__ == LinearGradient:
				self.border = duplicate.border

	def SetCenter(self, center):
		undo = (self.SetCenter, self.center)
		self.center = center
		return undo

	def Center(self):
		return self.center

	def Border(self):
		return self.border

	def SetBorder(self, border):
		undo = (self.SetBorder, self.border)
		self.border = border
		return undo

	def Transform(self, trafo, rects = None):
		if rects:
			r1, r2 = rects
			left, bottom, right, top = r1
			cx, cy = self.center
			cx = cx * right + (1 - cx) * left
			cy = cy * top   + (1 - cy) * bottom
			cx, cy = trafo(cx, cy)
			left, bottom, right, top = r2
			len = right - left
			if len:
				cx = (cx - left) / len
			else:
				cx = 0
			len = top - bottom
			if len:
				cy = (cy - bottom) / len
			else:
				cy = 0
			center = Point(cx, cy)
		else:
			center = self.center

		return self.SetCenter(center)

	def Execute(self, device, rect):
		if device.has_radial_gradient:
			self.execute_radial(device, rect)
			return
		steps = device.gradient_steps
		cx, cy = self.center
		cx = cx * rect.right + (1 - cx) * rect.left
		cy = cy * rect.top   + (1 - cy) * rect.bottom
		radius = max(hypot(rect.left - cx, rect.top - cy),
						hypot(rect.right - cx, rect.top - cy),
						hypot(rect.right - cx, rect.bottom - cy),
						hypot(rect.left - cx, rect.bottom - cy))
		color = self.gradient.ColorAt
		SetFillColor = device.SetFillColor
		FillCircle = device.FillCircle
		SetFillColor(color(0))
		apply(device.FillRectangle, tuple(rect))
		radius = radius * (1.0 - self.border)
		dr = radius / steps
		device.PushTrafo()
		device.Translate(cx, cy)
		center = NullPoint
		for i in range(steps):
			SetFillColor(color(float(i) / (steps - 1)))
			FillCircle(center, radius)
			radius = radius - dr
		device.PopTrafo()

	def execute_radial(self, device, rect):
		cx, cy = self.center
		cx = cx * rect.right + (1 - cx) * rect.left
		cy = cy * rect.top   + (1 - cy) * rect.bottom
		radius = max(hypot(rect.left - cx, rect.top - cy),
						hypot(rect.right - cx, rect.top - cy),
						hypot(rect.right - cx, rect.bottom - cy),
						hypot(rect.left - cx, rect.bottom - cy))
		radius = radius * (1.0 - self.border)
		device.RadialGradient(self.gradient, (cx, cy), radius, 0)

	def Blend(self, other, frac1, frac2):
		if other.__class__ == self.__class__:
			gradient = other.gradient
			center = other.center
			border = other.border
		elif other.__class__ == SolidPattern:
			gradient = other.Color()
			center = self.center
			border = self.border
		else:
			raise MismatchError
		return RadialGradient(Blend(self.gradient, gradient, frac1, frac2),
								frac1 * self.center + frac2 * center,
								frac1 * self.border + frac2 * border)

	def SaveToFile(self, file):
		file.RadialGradientPattern(self.gradient, self.center, self.border)



class ConicalGradient(GradientPattern):

	is_ConicalGradient = 1

	def __init__(self, gradient = None,
					center = Point(0.5, 0.5), direction = Point(1, 0),
					duplicate = None):
		GradientPattern.__init__(self, gradient, duplicate = duplicate)
		self.center = center
		self.direction = direction
		if duplicate is not None:
			if duplicate.__class__ == self.__class__:
				self.center = duplicate.center
				self.direction = duplicate.direction
			elif duplicate.__class__ == LinearGradient:
				self.direction = duplicate.direction
			elif duplicate.__class__ == RadialGradient:
				self.center = duplicate.center

	def __set_center_and_dir(self, center, dir):
		undo = (self.__set_center_and_dir, self.center, self.direction)
		self.center = center
		self.direction = dir
		return undo

	def Transform(self, trafo, rects = None):
		dir = trafo.DTransform(self.direction).normalized()
		if rects:
			r1, r2 = rects
			left, bottom, right, top = r1
			cx, cy = self.center
			cx = cx * right + (1 - cx) * left
			cy = cy * top   + (1 - cy) * bottom
			cx, cy = trafo(cx, cy)
			left, bottom, right, top = r2
			len = right - left
			if len:
				cx = (cx - left) / len
			else:
				cx = 0
			len = top - bottom
			if len:
				cy = (cy - bottom) / len
			else:
				cy = 0
			center = Point(cx, cy)
		else:
			center = self.center

		return self.__set_center_and_dir(center, dir)

	def SetCenter(self, center):
		undo = (self.SetCenter, self.center)
		self.center = center
		return undo

	def Center(self):
		return self.center

	def SetDirection(self, dir):
		undo = (self.SetDirection, self.direction)
		self.direction = dir
		return undo

	def Direction(self):
		return self.direction

	def Execute(self, device, rect):
		if device.has_conical_gradient:
			self.execute_conical(device, rect)
			return
		steps = device.gradient_steps
		cx, cy = self.center
		left, bottom, right, top = rect
		cx = cx * right + (1 - cx) * left
		cy = cy * top	+ (1 - cy) * bottom
		vx, vy = self.direction
		angle = atan2(vy, vx)
		rot = Rotation(angle, cx, cy)
		radius = max(hypot(left - cx, top - cy),
						hypot(right - cx, top - cy),
						hypot(right - cx, bottom - cy),
						hypot(left-cx,bottom-cy)) + 10
		device.PushTrafo()
		device.Concat(rot)
		device.Translate(cx, cy)
		device.Scale(radius)
		colors = self.gradient.Sample(steps)
		SetFillColor = device.SetFillColor
		FillPolygon = device.FillPolygon
		da = pi / steps
		points = [(1, 0)]
		for i in range(steps):
			a = da * (i + 1)
			x = cos(a);	y = sin(a)
			points.insert(0, (x, y))
			points.append((x, -y))
		colors.reverse()
		SetFillColor(colors[0])
		FillPolygon(points)
		points.insert(0, (0, 0))
		for i in range(steps):
			SetFillColor(colors[i])
			del points[1]
			del points[-1]
			FillPolygon(points)
		device.PopTrafo()

	def execute_conical(self, device, rect):
		cx, cy = self.center
		left, bottom, right, top = rect
		cx = cx * right + (1 - cx) * left
		cy = cy * top	+ (1 - cy) * bottom
		angle = self.direction.polar()[1]
		device.ConicalGradient(self.gradient, (cx, cy), angle)

	def Blend(self, other, frac1, frac2):
		if other.__class__ == self.__class__:
			gradient = other.gradient
			dir = other.direction
			center = other.center
		elif other.__class__ == SolidPattern:
			gradient = other.Color()
			dir = self.direction
			center = self.center
		else:
			raise MismatchError
		return ConicalGradient(Blend(self.gradient, gradient, frac1, frac2),
								frac1 * self.center +  frac2 * center,
								frac1 * self.direction + frac2 * dir)

	def SaveToFile(self, file):
		file.ConicalGradientPattern(self.gradient, self.center, self.direction)

		
class HatchingPattern(Pattern):

	is_Hatching = 1

	def __init__(self, foreground = None, background = None,
					direction = Point(1, 0),
					spacing = 5.0, width = 0.5, duplicate = None):
		if duplicate is not None:
			self.foreground = duplicate.foreground
			self.background = duplicate.background
			self.spacing = duplicate.spacing
			self.width = duplicate.width
			self.direction = duplicate.direction
		elif foreground:
			self.foreground = foreground
			if not background:
				background = color.StandardColors.white
			self.background = background
			self.spacing = spacing
			self.width = width
			self.direction = direction
		else:
			raise ValueError,\
					'HatchingPattern must be created with color argument'

	def SetDirection(self, dir):
		undo = (self.SetDirection, self.direction)
		self.direction = dir
		return undo

	def Direction(self):
		return self.direction

	def SetSpacing(self, spacing):
		undo = (self.SetSpacing, self.spacing)
		self.spacing = spacing
		return undo

	def Spacing(self):
		return self.spacing

	def Width(self):
		return self.width

	def Transform(self, trafo, rects = None):
		# XXX: should spacing be transformed as well? Should the pattern be
		# transformed at all?
		dir = trafo.DTransform(self.direction).normalized()
		return self.SetDirection(dir)

	def SetForeground(self, foreground):
		undo = (self.SetForeground, self.foreground)
		self.foreground = foreground
		return undo

	def Foreground(self):
		return self.foreground

	def SetBackground(self, color):
		undo = (self.SetBackground, self.background)
		self.background = color
		return undo

	def Background(self):
		return self.background

	def Execute(self, device, rect):
		left, bottom, right, top = rect
		dy = self.spacing
		if dy > 0:
			device.SetFillColor(self.background)
			device.FillRectangle(left, top, right, bottom)
			device.PushTrafo()
			vx, vy = self.direction
			angle = atan2(vy, vx)
			center = rect.center()
			rot = Rotation(angle, center)
			left, bottom, right, top = rot(rect)
			device.Concat(rot)
			device.Translate(center)
			height = top - bottom
			width = right - left
			steps = int(height / dy + 1)
			y = height / 2
			x = width / 2
			device.SetLineColor(self.foreground)
			device.SetLineAttributes(self.width)
			drawline = device.DrawLineXY
			for i in range(steps):
				drawline(-x, y, +x, y)
				y = y - dy
			device.PopTrafo()
		else:
			device.SetFillColor(self.foreground)
			device.FillRectangle(left, bottom, right, top)

	def Blend(self, other, frac1, frac2):
		if other.__class__ == self.__class__:
			fg = other.foreground
			bg = other.background
			dir = other.direction
			spacing = other.spacing
			width = other.width
		elif other.__class__ == SolidPattern:
			fg = bg = other.Color()
			dir = self.direction
			spacing = self.spacing
			width = self.width
		else:
			raise MismatchError
		return HatchingPattern(Blend(self.foreground, fg, frac1, frac2),
								Blend(self.background, bg, frac1, frac2),
								frac1 * self.direction + frac2 * dir,
								frac1 * self.spacing + frac2 * spacing,
								frac1 * self.width + frac2 * width)

	def SaveToFile(self, file):
		file.HatchingPattern(self.foreground, self.background,
								self.direction, self.spacing, self.width)


class ImageTilePattern(Pattern):

	is_Tiled = 1
	is_Image = 1
	data = None

	def __init__(self, data = None, trafo = None, duplicate = None):
		if duplicate is not None:
			data = duplicate.data
			self.trafo = duplicate.trafo
		else:
			if trafo is None:
				#width, height = data.size
				trafo = Trafo(1, 0, 0, -1, 0, 0)
			self.trafo = trafo
		self.data = data

	def set_transformation(self, trafo):
		undo = (self.set_transformation, self.trafo)
		self.trafo = trafo
		return undo

	def Transform(self, trafo, rects = None):
		if rects:
			r1, r2 = rects
			trafo = trafo(Translation(r1.left, r1.top))
			trafo = Translation(-r2.left, -r2.top)(trafo)
		return self.set_transformation(trafo(self.trafo))

	def Execute(self, device, rect):
		device.TileImage(self.data,
							Translation(rect.left, rect.top)(self.trafo))

	def Blend(self, other, frac1, frac2):
		if self.__class__ == other.__class__:
			if self.data is other.data:
				return self.__class__(self.data,
										BlendTrafo(self.trafo, other.trafo,
													frac1, frac2))
		raise MismatchError

	def SaveToFile(self, file):
		file.ImageTilePattern(self.data, self.trafo)
