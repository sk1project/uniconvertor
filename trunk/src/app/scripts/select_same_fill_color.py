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


# Select all objects in the current layer with the same fill color as
# the currently selected object. This is implemented as an advanced
# script. It doesn't have to deal with undo because it only changes the
# set of currently selected objects and not the objects themselves.
#
# Conceps and Methods:
#
# CurrentProperties():
#
#       This document method returns the properties of the currently
#       selected object. If more than one objects are selected or no
#       object is selected or the selected object doesn't have
#       properties, a special property object EmptyProperties is
#       returned.
#
#       Now, what does this mean? Objects like rectangles, text and
#       curves have graphics properties like fill or line patters, line
#       width or font whatever is applicable for that particular type.
#       Some obejcts have no graphics properties at all, e.g. groups,
#       while others can only have some properties, e.g. text objects
#       currently can't have a line color (this is really a limitation
#       in X11, PostScript wouldn't have problems with that).
#
#       All of the properties are stored in a properties object, and
#       that is what the CurrentProperties() method returns. Such a
#       properties object has three methods that indicate whether the
#       fill-, line- or text properties are valid: HasFill(), HasLine()
#       and HasFont(). Only if one of those methods returns true, can
#       you safely access the respective properties. The properties are
#       publicly readable attributes of the properties object. For the
#       EmptyProperties object that may be returned by
#       CurrentProperties(), all of these methods return false.
#

import time
	

def select_same_fill_color(context):
	doc = context.document
	select = []
	properties = doc.CurrentProperties()
	if properties.HasFill():
		color = properties.fill_pattern.Color()
		layer = doc.ActiveLayer()

		doc.SelectNone()
		for obj in layer.GetObjects():
			if obj.has_fill:
				prop = obj.Properties()
				if prop.HasFill() and prop.fill_pattern.is_Solid \
					and color == prop.fill_pattern.Color():
					select.append(obj)
	doc.SelectObject(select, Sketch.const.SelectAdd)


# register script
import Sketch.Scripting        
Sketch.Scripting.AddFunction('select_same_fill_color',
								'Select Same Fill Color',
								select_same_fill_color,
								script_type = Sketch.Scripting.AdvancedScript)
