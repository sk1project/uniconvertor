# Sketch - A Python-based interactive drawing program
# Copyright (C) 2002 by Bernhard Herzog
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

"""Demo Script for GNU/LinuxTag and EuroPython 2002.

Repeat foot-prints along a path.

Usage: Select two objects, one to be used as the left foot-print and
another one as the path to place the footprints on. Make sure that the
path is in front of the foot print.

The script will place copies of the foot print along the path as if
someone had walked along the path.
"""

import app.Scripting
from app.Graphics.text import coord_sys_at, PATHTEXT_ROTATE
from app import Group, Translation, Scale

def foot_prints_along_path(context):
	doc = context.document
	objects = doc.SelectedObjects()

	# The requirement for this script is, as described in the module
	# doc-string, that exactly two objects are selected and that the
	# top-most of these is the path.
	if len(objects) == 2 and objects[1].is_curve:

		# First, we take the foot print. We copy the foot print since we
		# have to modify it and we don't want the original to be
		# affected.
		foot_print = objects[0].Duplicate()

		# The rest of the script is easier to write if we have a foot
		# print located at the origin of the coordinate system that we
		# can use as a stencil, so we move the copy accordingly. The
		# Transform method modifies the object in place. That's why it
		# was important to copy it.
		r = foot_print.coord_rect
		foot_length = r.right - r.left
		foot_print.Transform(Translation(-r.right + foot_length/2,
											-r.bottom))

		# Now the path. The Paths() method of an object returns a tuple
		# of path-objects if the object can be represented as paths. All
		# objects whose is_curve attribute is true can be represented as
		# Paths. In this example script we only look at the first path.
		path = objects[1].Paths()[0]

		# arc_lengths returns a list of (LENGTH, POINT) pairs where
		# POINT is a point on the curve and LENGTH is the arc length
		# from the start of the curve to that point. The points are
		# placed so that the curve between successive points can be seen
		# as a straight line. We'll be using this list to determine the
		# positions and orientations of the individual foot prints.
		arc_lengths = path.arc_lengths()

		# In the loop below, we'll be positioning the foot prints one
		# after the other from the start of the curve to the end,
		# alternating between the left and right foot prints.

		# Total length of the path so that we know when we're done.
		total_length = arc_lengths[-1][0]

		# Distance along the path we've already covered.
		distance = 0

		# Count the number of foot prints so that we can mirror produce
		# left and right footprints.
		count = 0

		# List we put all the copies into.
		foot_prints = []

		# Now loop until we've walked along the whole path.
		while total_length - distance > foot_length:
			# Determine the transformation that turns the stencil into a
			# foot print at the right place with the right orientation.
			# We can borrow this functionality from the path-text code.
			# Placing letters along the path is practically the same as
			# placing foot prints.
			trafo = coord_sys_at(arc_lengths, distance, PATHTEXT_ROTATE)

			# Right feet are created by mirroring the left foot which
			# serves as stencil
			if count % 2:
				trafo = trafo(Scale(1, -1))

			# Create a transformed copy of the stencil.
			foot = foot_print.Duplicate()
			foot.Transform(trafo)
			foot_prints.append(foot)

			# Update the length and the counter
			distance = distance + foot_length
			count = count + 1

		# As the last step, insert the foot prints into the document as
		# a group. The Insert method takes care of undo handling.
		if foot_prints:
			doc.Insert(Group(foot_prints))


app.Scripting.AddFunction('foot_prints_along_path', 'Foot Prints',
								foot_prints_along_path,
								script_type = app.Scripting.AdvancedScript)
