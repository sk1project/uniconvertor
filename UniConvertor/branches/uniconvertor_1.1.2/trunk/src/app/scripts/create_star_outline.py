#
#  create_star.py - create star-like objects
#                   Tamito KAJIYAMA <26 March 2000>
# Copyright (C) 2000 by Tamito KAJIYAMA
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

from app import _, PolyBezier, CreatePath, Polar
from app.UI.sketchdlg import SKModal

from Tkinter import *

import math, unit

class CreateStarDlg(SKModal):

	title = _("Create Star")

	def build_dlg(self):
		self.var_corners = IntVar(self.top)
		self.var_corners.set(10)
		label = Label(self.top, text=_("Corners"))
		label.grid(column=0, row=0, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_corners)
		entry.grid(column=1, row=0)

		self.var_outer_radius = StringVar(self.top)
		self.var_outer_radius.set("100pt")
		label = Label(self.top, text=_("Outer Radius"))
		label.grid(column=0, row=1, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_outer_radius)
		entry.grid(column=1, row=1)

		self.var_inner_radius = StringVar(self.top)
		self.var_inner_radius.set("75pt")
		label = Label(self.top, text=_("Inner Radius"))
		label.grid(column=0, row=2, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_inner_radius)
		entry.grid(column=1, row=2)

		button = Button(self.top, text=_("OK"), command=self.ok)
		button.grid(column=0, row=3, sticky=W)
		button = Button(self.top, text=_("Cancel"), command=self.cancel)
		button.grid(column=1, row=3, sticky=E)

	def ok(self):
		self.close_dlg((self.var_corners.get(),
						self.var_outer_radius.get(),
						self.var_inner_radius.get()))

def create_star_outline(context):
	args = CreateStarDlg(context.application.root).RunDialog()
	if args is None:
		return
	path = apply(create_star_path, args)
	bezier = PolyBezier((path,))
	context.main_window.PlaceObject(bezier)

def create_star_path(corners, outer_radius, inner_radius):
	outer_radius = unit.convert(outer_radius)
	inner_radius = unit.convert(inner_radius)
	path = CreatePath()
	angle = math.pi * 2 / corners
	for i in range(corners):
		path.AppendLine(Polar(outer_radius, angle * i))
		path.AppendLine(Polar(inner_radius, angle * i + angle / 2))
	path.AppendLine(path.Node(0))
	path.ClosePath()
	return path

import app.Scripting
app.Scripting.AddFunction('create_star_outline', _("Star Outline"),
								create_star_outline, menu = _("Create Objects"),
								script_type = app.Scripting.AdvancedScript)
