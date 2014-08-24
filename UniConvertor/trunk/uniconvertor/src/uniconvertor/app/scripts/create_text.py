# Sketch - A Python-based interactive drawing program
# Copyright (C) 1999, 2000 by Bernhard Herzog
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

import app.Scripting
from app import SimpleText, Translation, SolidPattern, StandardColors, \
		GetFont


def create_text(context):
	# Create the text 'xyzzy' at 100,100. The first parameter to the
	# constructor is an affine transformation.
	text = SimpleText(Translation(100, 100), "xyzzy")
	
	# Set the font to 36pt Times-Bold and fill with solid green.
	# The text object is modified by this method, but the text object is
	# not yet part of the document, so we don't have to deal with undo
	# here.
	text.SetProperties(fill_pattern = SolidPattern(StandardColors.green),
						font = GetFont('Times-Bold'),
						font_size = 36)
	# Finally, insert the text object at the top of the current layer
	# and select it. Like all public document methods that modify the
	# document, the Insert method takes care of undo information itself.
	context.document.Insert(text)

app.Scripting.AddFunction('create_text', 'Create Text', create_text,
								script_type = app.Scripting.AdvancedScript)

