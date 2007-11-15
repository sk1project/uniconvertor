#
#  create_spiral.py - create spiral lines
#                     Tamito KAJIYAMA <26 March 2000>
#
# Copyright (C) 2000 by Tamito KAJIYAMA
# Copyright (C) 2000, 2002 by Bernhard Herzog
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

from math import pi, cos, sin
	
from app import _, PolyBezier, CreatePath, Polar, Point, \
		ContAngle, ContSmooth, ContSymmetrical
from app.UI.sketchdlg import SKModal

from Tkinter import *

import unit

class CreateStarDlg(SKModal):

	title = _("Create Spiral")

	def build_dlg(self):
		self.var_rotation = IntVar(self.top)
		self.var_rotation.set(4)
		label = Label(self.top, text=_("Rotations"))
		label.grid(column=0, row=0, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_rotation)
		entry.grid(column=1, row=0)

		self.var_radius = StringVar(self.top)
		self.var_radius.set("100pt")
		label = Label(self.top, text=_("Radius"))
		label.grid(column=0, row=1, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_radius)
		entry.grid(column=1, row=1)

		button = Button(self.top, text=_("OK"), command=self.ok)
		button.grid(column=0, row=2, sticky=W)
		button = Button(self.top, text=_("Cancel"), command=self.cancel)
		button.grid(column=1, row=2, sticky=E)

	def ok(self):
		self.close_dlg((self.var_rotation.get(),
						self.var_radius.get()))

def create_spiral(context):
	args = CreateStarDlg(context.application.root).RunDialog()
	if args is None:
		return
	path = apply(create_spiral_path, args)
	bezier = PolyBezier((path,))
	context.main_window.PlaceObject(bezier)

def create_spiral_path(rotation, radius):
	r = unit.convert(radius)
	rate = r / (rotation * 2 * pi)
	
	def tangent(phi, a = 0.55197 * rate):
		return a * Point(cos(phi) - phi * sin(phi),
							sin(phi) + phi * cos(phi))
	pi2 = pi / 2.0
	angle = 0
	tang = tangent(0)
	path = CreatePath()
	p = Point(0, 0)
	path.AppendLine(p)
	for i in range(rotation * 4):
		p1 = p + tang
		angle = pi2 * (i + 1)
		p = Polar(rate * angle, angle)
		tang = tangent(angle)
		p2 = p - tang
		path.AppendBezier(p1, p2, p, ContSymmetrical)
	return path

import app.Scripting
app.Scripting.AddFunction('create_spiral', _("Spiral"),
								create_spiral, menu = _("Create Objects"),
								script_type = app.Scripting.AdvancedScript)
