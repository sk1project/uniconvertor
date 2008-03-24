# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000 by Bernhard Herzog
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


###Sketch Config
#type = PluginCompound
#class_name = 'RegularPolygon'
#menu_text = 'Regular Polygon'
#parameters = (\
# ('vertices', 'int', 6, (3, None), 'Vertices'), \
# ('radius', 'length', 72.0, (0.0, None), 'Radius'))
#standard_messages = 1
###End

(''"Regular Polygon")
(''"Vertices")
(''"Radius")

from math import pi

from app import Polar, TrafoPlugin, PolyBezier, CreatePath, ContAngle

class RegularPolygon(TrafoPlugin):

	class_name = 'RegularPolygon'
	is_curve = 1

	def __init__(self, vertices = 5, radius = 50.0, trafo = None, loading = 0,
					duplicate = None):
		TrafoPlugin.__init__(self, trafo = trafo, duplicate = duplicate)
		if duplicate is not None:
			self.vertices = duplicate.vertices
			self.radius = duplicate.radius
		else:
			self.vertices = vertices
			self.radius = radius
		if not loading:
			self.recompute()

	def recompute(self):
		path = CreatePath()
		vertices = float(self.vertices)
		radius = self.radius
		twopi = 2 * pi
		halfpi = pi / 2
		for i in range(vertices + 1):
			path.AppendLine(Polar(radius, twopi * i / vertices + halfpi),
							ContAngle)
		path.ClosePath()
		path.Transform(self.trafo)
		if self.objects:
			self.objects[0].SetPaths((path,))
		else:
			self.set_objects([PolyBezier((path,))])

	def Vertices(self):
		return self.vertices

	def Radius(self):
		return self.radius

	def SaveToFile(self, file):
		TrafoPlugin.SaveToFile(self, file, self.vertices, self.radius,
								self.trafo.coeff())

	def Info(self):
		return _("Regular Polygon: %(vertices)d vertices, "
					"radius %(radius)[length]"), self.__dict__

	def AsBezier(self):
		return self.objects[0].AsBezier()

	def Paths(self):
		return self.objects[0].Paths()

