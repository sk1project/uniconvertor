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

from app import CreatePath, Rotation, Translation, Scale

from app._sketch import ContAngle, ContSmooth, ContSymmetrical, Bezier, Line


def arrow_vectors(path, arrow1, arrow2):
	# Return the directions for the arrow heads of path as a pair of
	# point objects. If the path is closed or consists of only one Node,
	# return (None, None).
	dir1 = dir2 = None
	if not path.closed and path.len > 1:
		if arrow1:
			type, controls, p3, cont = path.Segment(1)
			p = path.Node(0)
			if type == Bezier:
				p1, p2 = controls
				dir = p - p1
				if not abs(dir):
					dir = p - p2
			else:
				dir = p - p3
			dir1 = dir
		if arrow2:
			type, controls, p, cont = path.Segment(-1)
			p3 = path.Node(-2)
			if type == Bezier:
				p1, p2 = controls
				dir = p - p2
				if not abs(dir):
					dir = p - p1
			else:
				dir = p - p3
			dir2 = dir
	return dir1, dir2

def arrow_trafos(path, properties):
	dir1, dir2 = arrow_vectors(path, properties.line_arrow1,
								properties.line_arrow2)
	width = properties.line_width
	if width < 1.0:
		width = 1.0
	scale = Scale(width)
	t1 = t2 = None
	if dir1 is not None:
		t1 = Translation(path.Node(0))(Rotation(dir1.polar()[1]))(scale)
	if dir2 is not None:
		t2 = Translation(path.Node(-1))(Rotation(dir2.polar()[1]))(scale)
	return t1, t2
