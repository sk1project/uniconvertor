#
#  average_points.py - average coordinates of selected points
#                       Tamito KAJIYAMA <24 March 2000>
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

from app import CreatePath, Point, _
from app.UI.sketchdlg import SKModal

from Tkinter import *

AVERAGE_BOTH = 0
AVERAGE_X = 1
AVERAGE_Y = 2

class AverageDialog(SKModal):

	title = "Average Points"

	def build_dlg(self):
		self.var_which = IntVar(self.top)
		self.var_which.set(AVERAGE_X)
		label = Label(self.top, text="Average", anchor=W)
		label.pack(fill=X)
		button = Radiobutton(self.top, text="X Coordinates",
								variable=self.var_which, value=AVERAGE_X,
								anchor=W)
		button.pack(fill=X)
		button = Radiobutton(self.top, text="Y Coordinates",
								variable=self.var_which, value=AVERAGE_Y,
								anchor=W)
		button.pack(fill=X)
		button = Radiobutton(self.top, text="Both Coordinates",
								variable=self.var_which, value=AVERAGE_BOTH,
								anchor=W)
		button.pack(fill=X)
		button = Button(self.top, text="OK", command=self.ok)
		button.pack(side=LEFT)
		button = Button(self.top, text="Cancel", command=self.cancel)
		button.pack(side=RIGHT)

	def ok(self, *args):
		self.close_dlg(self.var_which.get())

def average_points(context):
	# find a bezier polygon selected
	selection = []
	for object in context.document.SelectedObjects():
		if not object.is_Bezier:
			continue
		selection.append(object)
	if len(selection) != 1:
		context.application.MessageBox(title="Average Points",
										message="Select one polygon.")
		return None
	# count selected points
	object = selection[0]
	object_paths = object.Paths()
	npoints = 0
	for path in object_paths:
		for i in range(path.len):
			if path.SegmentSelected(i):
				npoints = npoints + 1
	if npoints == 0:
		context.application.MessageBox(title="Average Points", 
										message="Select two or more points.")
		return None
	# inquiry parameters
	which = AverageDialog(context.application.root).RunDialog()
	if which is None:
		return None
	# compute average coordinates of the selected points
	ax = 0
	ay = 0
	modified_paths = []
	for path in object_paths:
		modified_paths.append([])
		for i in range(path.len):
			type, controls, point, cont = path.Segment(i)
			modified_paths[-1].append([type, list(controls), point, cont])
			if path.SegmentSelected(i):
				ax = ax + point.x
				ay = ay + point.y
	ax = float(ax) / npoints
	ay = float(ay) / npoints
	# translate the selected points
	for i in range(len(object_paths)):
		path = object_paths[i]
		new_path = modified_paths[i]
		for j in range(path.len):
			if path.SegmentSelected(j):
				point = new_path[j][2]
				if which == AVERAGE_X:
					new_point = Point(ax, point.y)
				elif which == AVERAGE_Y:
					new_point = Point(point.x, ay)
				else:
					new_point = Point(ax, ay)
				new_path[j][2] = new_point
				offset = point - new_point
				if len(new_path[j][1]) == 2:
					new_path[j  ][1][1] = new_path[j  ][1][1] - offset
				if j < path.len - 1 and len(new_path[j+1][1]) == 2:
					new_path[j+1][1][0] = new_path[j+1][1][0] - offset
	# create new paths
	new_paths = []
	for i in range(len(object_paths)):
		path = object_paths[i]
		new_path = CreatePath()
		for type, controls, point, cont in modified_paths[i]:
			new_path.AppendSegment(type, tuple(controls), point, cont)
		if path.closed:
			new_path.AppendLine(new_path.Node(0))
			new_path.ClosePath()
		new_paths.append(new_path)
	# set the new paths
	undo = object.SetPaths(new_paths)
	# return Undo info
	return undo

def run(context):
	document = context.document
	undo = average_points(context)
	if undo is not None:
		document.AddUndo(undo)

import app.Scripting
app.Scripting.AddFunction('average_points', 'Average Points', run,
								script_type = app.Scripting.AdvancedScript)
