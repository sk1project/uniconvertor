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


# This is a reimplementation of the Arrange| Abut Horizontal command as
# a safe script.
#
# This script uses these methods and concepts:
#
# SelectedObjects():
#
#       The document method SelectedObjects returns a list of all
#       currently selected objects. If no objects are selected the list
#       is empty.
#
# coord_rect:
#
#       The coord_rect attribute of a graphics object is an axis-aligned
#       rectangle that contains the entire object. This is not exactly
#       the same as a bounding rectangle, as explained in more detail in
#       the developer's guide (Doc/devguide.html).
#
#       The coord_rect is a rect object and has four read only
#       attributes, left, bottom, right, and top, that contain the
#       coordinates of the rectangle.
#
# Point(x, y):
#
#       Point is a function that returns a point object with the
#       coordinates x and y. point objects are immutable objects that
#       overload the usual arithmetic operators such as +, -, * among
#       others. * is the inner product or multiplication with a scalar
#       depending on the operand types. Thy are interpreted as points or
#       vectors depending on the context in which they are used.
#
#       Point objects are described in more detail in the developer's
#       guide.
#
# Translate(offset):
#
#       The translate method of a graphics object translates (i.e.
#       moves) the object by offset, which has to be a point object.
#
#       This method modifies the object involved and an advanced script
#       would have to deal with undo when using this method.
#

# First, we need the Sketch specific function Point. Point creates
# point-objects, that represent a 2D-point or vector.
from app import Point


# define the abut_horizontal function. As stated above, it has to accept
# a single argument, customarily called 'context'.
def abut_horizontal(context):
	# We have to refer to the document frequently, so save some typing
	# by binding it to the local variable doc.
	doc = context.document

	pos = []
	for obj in doc.SelectedObjects():
		rect = obj.coord_rect
		pos.append((rect.left, rect.top, rect.right - rect.left, obj))
	if pos:
		# pos is empty (= false) if no object is selected
		pos.sort()
		start, top, width, ob = pos[0]
		next = start + width
		for left, top, width, obj in pos[1:]:
			obj.Translate(Point(next - left, 0))
			next = next + width


# register script
import app.Scripting
app.Scripting.AddFunction('abut_horizontal', 'Abut Horizontal',
								abut_horizontal, menu = 'Arrange')

