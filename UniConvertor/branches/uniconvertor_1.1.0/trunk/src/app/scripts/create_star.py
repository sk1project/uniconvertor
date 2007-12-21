# Sketch - A Python-based interactive drawing program
# Copyright (C) 1999, 2000, 2002 by Bernhard Herzog
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

from math import pi

from Tkinter import IntVar, DoubleVar, Entry, Label, Button, Frame

import app.Scripting
from app import _, SolidPattern, StandardColors, PolyBezier, CreatePath, \
		Point, Polar

from app.UI.sketchdlg import SKModal

#
#   
#

def create_star_path(corners, step, radius):
	# create a star-like polygon.
	center = Point(300, 400)
	radius = 100
	angle = step * 2 * pi / corners

	# create an empty path and append the line segments
	path = CreatePath()
	for i in range(corners):
		p = Polar(radius, angle * i + pi / 2)
		path.AppendLine(p)
		
	# close the path.
	path.AppendLine(path.Node(0))
	path.ClosePath()

	return path

#
#   A modal dialog that asks for the parameters 
#
# SKModal is the baseclass Sketch uses for modal dialogs. It provides
# some standard functionality for all modal dialogs.
#
# The intended use of a sub-class of SKModal is to instantiate it and
# call its RunDialog method.
#
# RunDialog pops up the dialog and returns when the user either cancels
# the dialog or presses the OK button. Its return value is None if the
# dialog was canceled or whatever object was passed to the close_dlg
# method to close the dialog in response to the click on the OK-button.
# See the method ok below.
#

class CreateStarDlg(SKModal):

	title = _("Create Star")

	def __init__(self, master, **kw):
		# This constructor is here just for illustration purposes; it's
		# not really needed here, as it simply passes all parameters on
		# to the base class' constructor.
		#
		# The parameter master is the window this dialog belongs to. It
		# should normally be the top-level application window.
		apply(SKModal.__init__, (self, master), kw)

	def build_dlg(self):
		# The SKModal constructor automatically calls this method to
		# create the widgets in the dialog.
		#
		# self.top is the top-level window of the dialog. All widgets of
		# the dialog must contained in it.

		top = self.top

		# The rest is normal Tkinter code.

		self.var_corners = IntVar(top)
		self.var_corners.set(5)
		label = Label(top, text = _("Corners"), anchor = 'e')
		label.grid(column = 0, row = 0, sticky = 'ew')
		entry = Entry(top, textvariable = self.var_corners, width = 15)
		entry.grid(column = 1, row = 0, sticky = 'ew')
		
		self.var_steps = IntVar(top)
		self.var_steps.set(2)
		label = Label(top, text = _("Steps"), anchor = 'e')
		label.grid(column = 0, row = 1, sticky = 'ew')
		entry = Entry(top, textvariable = self.var_steps, width = 15)
		entry.grid(column = 1, row = 1, sticky = 'ew')

		self.var_radius = DoubleVar(top)
		self.var_radius.set(100)
		label = Label(top, text = _("Radius"), anchor = 'e')
		label.grid(column = 0, row = 2, sticky = 'ew')
		entry = Entry(top, textvariable = self.var_radius, width = 15)
		entry.grid(column = 1, row = 2, sticky = 'ew')
		

		but_frame = Frame(top)
		but_frame.grid(column = 0, row = 3, columnspan = 2)

		button = Button(but_frame, text = _("OK"), command = self.ok)
		button.pack(side = 'left', expand = 1)
		# The self.cancel method is provided by the base class and
		# cancels the dialog.
		button = Button(but_frame, text = _("Cancel"), command = self.cancel)
		button.pack(side = 'right', expand = 1)


	def ok(self, *args):
		# This method is bound to the OK-button. Its purpose is to
		# collect the values of the various edit fields and pass them as
		# one parameter to the close_dlg method.
		#
		# close_dlg() saves its parameter and closes the dialog.
		corners = self.var_corners.get()
		steps = self.var_steps.get()
		radius = self.var_radius.get()
		self.close_dlg((corners, steps, radius))



def create_star(context):
	# Instantiate the modal dialog...
	dlg = CreateStarDlg(context.application.root)
	# ... and run it.
	result = dlg.RunDialog()
	if result is not None:
		# if the result is not None, the user pressed OK. Now constuct
		# the star-path...
		corners, steps, radius = result
		path = create_star_path(corners, steps, radius)
	
		# ... and create the bezier object. The parameter to the
		# constructor must be a tuple of paths
		bezier = PolyBezier((path,))

		# Set the line color to blue, the line width to 4pt
		bezier.SetProperties(line_pattern = SolidPattern(StandardColors.blue),
								line_width = 4)

		# and insert it into the document
		context.main_window.PlaceObject(bezier)



	
app.Scripting.AddFunction('create_star', _("Create Star"),
								create_star,
								script_type = app.Scripting.AdvancedScript)

