# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
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

#
# Some convenience functions for specifying the coordinates and the
# shape of handles.
#
#
# A handle is described by a tuple of the form: (TYPE, P, CURSOR)
#
# Note: This is no longer true (Sketch 0.5.3), the handles are now
# represented by instances of the Handle class below, but the
# interpretation of the values hasn't changed.
#
# TYPE is an integer specifying the type of tuple. Constants for this
# are defined in const.py and have names of the form Handle*.
#
# P is usually a Point object (in document coordinates) specifying the
# position of the handle. An alternative form is a tuple of the form (P,
# (X, Y)) where P is the position like before, and X and Y are offsets
# inicating that the handle should not be shown exactly at P. X and Y
# can be 0, +1 or -1 which currently means that the offset is 0 or +/- 8
# pixels.
# The second form is used for instance for the handles at the corners
# and sides of the current selection where the user can click and resize
# the object.
#
# CURSOR specifies the shape of the mouse pointer when it is over the
# handle. In the current Tk version this is usually a string with the
# name of the cursor. None means the default cursor of the window.
#
# There are two handle types which have a slightly different
# representation:
#
# HandleLine:	(HandleLine, P1, P2)
#	This handle is not really a handle but a (dashed) line from P1
#	to P2. P1 and P2 are Point objects in document coordinates. This
#	type is used by the PolyBezier object in edit mode.
#
# Handle_Pixmap:	(Handle_Pixmap, P, PIXMAP, CURSOR)
#	PIXMAP is drawn as a handle at P. PIXMAP is a Pixmap object and
#	not a Tk-like pixmap specification (a string of a certain
#	format). The pixmap must have depth 1. P and CURSOR are used as
#	in the normal case.
#
# The functions in this module should be used to create the handle
# specifications since the representation may change. More specifically,
# a class hierarchy might be used for the various types of handles.
#

from app import Point
from app.conf import const

class Handle:

	def __init__(self, type, p, cursor = const.CurHandle, offset = None,
					p2 = None, list = None, pixmap = None, code = None):
		self.type = type
		self.p = p
		self.cursor = cursor
		self.p2 = p2
		self.offset = offset
		self.list = list
		self.pixmap = pixmap
		self.index = 0
		self.code = code

	def __str__(self):
		return "Handle(%d, %s)" % (self.type, self.p)
	
	def __repr__(self):
		return "Handle(%d, %s, index = %s)" % (self.type, self.p, self.index)

def MakeHandle(type, p, cursor = const.CurHandle):
	return Handle(type, p, cursor)

def MakeNodeHandle(p, selected = 0, code = 0):
	if selected:
		return Handle(const.HandleSelectedNode, p, code = code)
	return Handle(const.HandleNode, p, code = code)

def MakeObjectHandleList(list):
	return Handle(const.Handle_SmallOpenRectList, None, list = list)

def MakeControlHandle(p, code = 0):
	return Handle(const.HandleControlPoint, p, code = code)

def MakeCurveHandle(p):
	return Handle(const.HandleCurvePoint, p, cursor = None)

def MakeLineHandle(p1, p2):
	return Handle(const.HandleLine, p1, p2 = p2)

def MakeOffsetHandle(p, offset, cursor = const.CurHandle):
	return Handle(const.Handle, p, cursor, offset = offset)

def MakePixmapHandle(p, offset, pixmap, cursor = const.CurHandle):
	return Handle(const.Handle_Pixmap, p, cursor, offset = offset,
					pixmap = pixmap)

def MakeCaretHandle(p, up):
	return Handle(const.Handle_Caret, p, p2 = up)

def MakePathTextHandle(p, up):
	return Handle(const.Handle_PathText, p, p2 = up)
