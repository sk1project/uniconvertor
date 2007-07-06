# Sketch - A Python-based interactive drawing program
# Copyright (C) 1999 by Bernhard Herzog
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

# Read a path exported by GIMP's Layers & Channels dialog
#

# A new command "Read Gimp Path" for the Script menu that reads a path
# from a file created with "Export Path" in Gimp's Layers & Channels
# dialog and insert it into the document at a fixed position.
#
# The path is inserted at a fixed position so that if you import several
# paths from the same image these paths have the correct relative
# position.
#
# This you might want to change are the position at which the path is
# inserted, or scaling it, or placing it interactively.


from string import split, lstrip
import re

import app
from app import CreatePath, Point, PolyBezier, Trafo

BEZIER_ANCHOR = 1
BEZIER_CONTROL = 2
BEZIER_MOVE = 3

rx_point = re.compile('\
(?P<type>[123])\s+X:\s*(?P<x>[-+]?[0-9]+)\s+Y:\s*(?P<y>[-+]?[0-9]+)')


def read_path(filename):
	path = CreatePath()
	paths = [path]
	points = []
	file = open(filename)
	closed = 0

	for line in file.readlines():
		try:
			key, rest = split(line, ':', 1)
		except:
			continue
		if key == 'TYPE':
			rest = lstrip(rest)
			match = rx_point.match(rest)
			if match is not None:
				type = int(match.group('type'))
				p = Point(float(match.group('x')), float(match.group('y')))
				if type == BEZIER_MOVE:
					if closed and points:
						path.AppendBezier(points[0], points[1], path.Node(0))
						path.ClosePath()
						points = []
					path = CreatePath()
					paths.append(path)
					path.AppendLine(p)
				elif type == BEZIER_ANCHOR:
					if path.len == 0:
						path.AppendLine(p)
					else:
						if path.Node(-1) == points[0] and points[1] == p:
							path.AppendLine(p)
						else:
							path.AppendBezier(points[0], points[1], p)
						points = []
				elif type == BEZIER_CONTROL:
					points.append(p)
		elif key == 'CLOSED':
			closed = int(rest)
	if closed  and points:
		if path.Node(-1) == points[0] and points[1] == path.Node(0):
			path.AppendLine(path.Node(0))
		else:
			path.AppendBezier(points[0], points[1], path.Node(0))
		path.ClosePath()

	return tuple(paths)
	

def read_gimp_path(context, filename = ''):
	if not filename:
		filename = context.application.GetOpenFilename()
		if not filename:
			return
	paths = read_path(filename)
	object = PolyBezier(paths)
	object.Transform(Trafo(1, 0, 0, -1, 0, 800))
	#context.main_window.PlaceObject(object)
	context.document.Insert(object)


app.Scripting.AddFunction('read_gimp_path', 'Read Gimp Path',
								read_gimp_path,
								script_type = app.Scripting.AdvancedScript)
