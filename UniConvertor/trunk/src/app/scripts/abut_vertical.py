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

# This is a reimplementation of the Arrange| Abut Vertical command. It
# is of course very similar to the abut_horizontal script, but this
# script is implemented as an advanced script that has to take care of
# undo information.

# The only new concept introduced here, compared to what is described in
# abut_horizontal.py, is how to handle undo information in an advanced
# script.
#
# In Sketch, every method that modifies an object returns an undo
# information object. The structure of this object is irrelevant here,
# the only important thing to know is that it stores all information
# necessary to undo the changes that the method performed.
#
# In most cases, an advanced script simply passes any undo information
# it receives from a method _immediately_ to the document method
# AddUndo(). Passing it to the document object _immediately_ is
# importan, because if an error occurs and an exception is thrown, the
# changes already performed have to be undone to make sure that the
# document is in a consistent state again.
#
# For more infomation about undo handling in Sketch, see the developer's
# manual and the Sketch sources, in particular the plugin objects in
# Plugins/Objects.
#
# I don't think that you'll ever have to do anything with undo info
# other than passing it immediately to the document, but under some
# circumstances it might be necessary to influence the order in which
# undo info is executed when the user selects the undo command or even
# discard the undo info you get from the methods you called and replace
# it with completely new undo info that still undoes the changes but at
# a higher level.
#


from app import Point

def abut_vertical(context):
	doc = context.document
	pos = []
	for obj in doc.SelectedObjects():
		rect = obj.coord_rect
		pos.append((rect.top, -rect.left, rect.top - rect.bottom, obj))
	if pos:
		pos.sort()
		pos.reverse()
		start, left, height, ob = pos[0]
		next = start - height
		for top, left, height, obj in pos[1:]:
			off = Point(0, next - top)
			doc.AddUndo(obj.Translate(off))
			next = next - height


# register script import app.Scripting
import app.Scripting
app.Scripting.AddFunction('abut_vertical', 'Abut Vertical',
								abut_vertical, menu = 'Arrange',
								script_type = app.Scripting.AdvancedScript)
