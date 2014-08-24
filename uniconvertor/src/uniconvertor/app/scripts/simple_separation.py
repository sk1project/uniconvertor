# Sketch - A Python-based interactive drawing program
# Copyright (C) 2001, 2002 by Intevation GmbH
# Author: Bernhard Herzog <bernhard@users.sourceforge.net>
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

"""Save a document in several EPS files, one for each color used.

The resulting set of EPS files can be considered a simple form of color
separations.

Limitations:

	- Not all fill types are supported. At the moment, only solid fills and
	empty fills are implemented. If a drawing contains unsupported fills,
	an appropriate message is displayed.

	- Raster images and EPS objects are not supported.

"""

import os

from app import _, SolidPattern, StandardColors, CreateListUndo, Undo, \
		PostScriptDevice
from sk1libs.utils import system
from app.UI.sketchdlg import SKModal

from Tkinter import StringVar, Frame, Label, Button, Entry, E, W, X, TOP, \
		BOTTOM, LEFT, BOTH


black = StandardColors.black
white = StandardColors.white

# exception and messages used for unsupported features
class UnsupportedFeature(Exception):
	pass

unsupported_pattern = _("""\
The drawing contains unsupported fill or line patterns. Only solid
colors are supported.
""")

unsupported_type_raster = _("""\
The drawing contains raster images, which are not supported for separation
""")

unsupported_type_raster = _("""\
The drawing contains embedded EPS files which are not supported for
separation
""")

class ColorExtractor:

	"""Helper class to extract determine the colors used in a drawing.

	This is a class because the document object's WalkHierarchy method
	doesn't provide a way to pass an additional parameter through to the
	callback, so we use a bound method.
	"""

	def __init__(self):
		self.colors = {}

	def extract_colors(self, object):
		"""Extract the colors of the solid fill and line patterns of
		object. If the object has non-empty non-solid patterns raise
		UnsupportedFeature exception
		"""
		if object.has_properties:
			properties = object.Properties()
			pattern = properties.fill_pattern
			if pattern.is_Solid:
				self.colors[pattern.Color()] = 1
			elif not pattern.is_Empty:
				raise UnsupportedFeature(unsupported_pattern)
			pattern = properties.line_pattern
			if pattern.is_Solid:
				self.colors[pattern.Color()] = 1
			elif not pattern.is_Empty:
				raise UnsupportedFeature(unsupported_pattern)
		else:
			if object.is_Image:
				raise UnsupportedFeature(unsupported_type_raster)
			elif object.is_Eps:
				raise UnsupportedFeature(unsupported_type_eps)


class CreateSeparation:

	"""Helperclass to create a separation.

	This is a class so that we can use a method as the callback function
	for the document's WalkHierarchy method.
	"""

	def __init__(self, color):
		"""Initialze separator. color is the color to make black."""
		self.color = color
		self.undo = []

	def change_color(self, object):
		if object.has_properties:
			properties = object.Properties()
			pattern = properties.fill_pattern
			if pattern.is_Solid:
				if pattern.Color() == self.color:
					pattern = SolidPattern(black)
				else:
					pattern = SolidPattern(white)
				undo = properties.SetProperty(fill_pattern = pattern)
				self.undo.append(undo)

			pattern = properties.line_pattern
			if pattern.is_Solid:
				if pattern.Color() == self.color:
					pattern = SolidPattern(black)
				else:
					pattern = SolidPattern(white)
				undo = properties.SetProperty(line_pattern = pattern)
				self.undo.append(undo)

	def undo_changes(self):
		Undo(CreateListUndo(self.undo))

filename_dialog_text = _("""The drawing has %d unique colors.
Please choose a basename for the separation files.
There will be one file for each color with a name of
the form basename-XXXXXX.ps where XXXXXX is the
hexadecimal color value.
""")

class SimpleSeparationDialog(SKModal):

	title = "Simple Separation"

	def __init__(self, master, num_colors, basename):
		self.num_colors = num_colors
		self.basename = basename
		SKModal.__init__(self, master)

	def build_dlg(self):
		self.var_name = StringVar(self.top)
		self.var_name.set(self.basename)

		frame = Frame(self.top)
		frame.pack(side = TOP, fill = BOTH, expand = 1)

		text = filename_dialog_text % self.num_colors
		label = Label(frame, text = text, justify = "left")
		label.grid(column = 0, row = 0, sticky = E, columnspan = 2)

		label = Label(frame, text = _("Basename:"))
		label.grid(column = 0, row = 1, sticky = E)
		entry = Entry(frame, width = 15, textvariable = self.var_name)
		entry.grid(column = 1, row = 1)

		frame = Frame(self.top)
		frame.pack(side = BOTTOM, fill = X, expand = 1)
		button = Button(frame, text = _("OK"), command = self.ok)
		button.pack(side = LEFT, expand = 1)
		button = Button(frame, text = _("Cancel"), command = self.cancel)
		button.pack(side = LEFT, expand = 1)

	def ok(self):
		self.close_dlg(self.var_name.get())



def hexcolor(color):
	"""Return the color in hexadecimal form"""
	return "%02x%02x%02x" \
			% (255 * color.red, 255 * color.green, 255 * color.blue)

def draw_alignment_marks(psdevice, bbox, length, distance):
	"""Draw alignment marks onto the postscript device"""
	llx, lly, urx, ury = bbox
	# the marks should be black
	psdevice.SetLineColor(StandardColors.black)
	psdevice.SetLineAttributes(1)
	# lower left corner
	psdevice.DrawLine((llx - distance, lly), (llx - distance - length, lly))
	psdevice.DrawLine((llx, lly - distance), (llx, lly - distance - length))
	# lower right corner
	psdevice.DrawLine((urx + distance, lly), (urx + distance + length, lly))
	psdevice.DrawLine((urx, lly - distance), (urx, lly - distance - length))
	# upper right corner
	psdevice.DrawLine((urx + distance, ury), (urx + distance + length, ury))
	psdevice.DrawLine((urx, ury + distance), (urx, ury + distance + length))
	# upper left corner
	psdevice.DrawLine((llx - distance, ury), (llx - distance - length, ury))
	psdevice.DrawLine((llx, ury + distance), (llx, ury + distance + length))


def simple_separation(context):
	doc = context.document

	# first determine the number of unique colors in the document
	color_extractor = ColorExtractor()
	try:
		doc.WalkHierarchy(color_extractor.extract_colors, all = 1)
	except UnsupportedFeature, value:
		context.application.MessageBox(_("Simple Separation"),
										value)
		return

	colors = color_extractor.colors.keys()

	doc_bbox = doc.BoundingRect()
	
	filename = doc.meta.fullpathname
	if filename is None:
		filename = "unnamed"
	basename = os.path.splitext(filename)[0]

	# ask the user for a filename
	dlg = SimpleSeparationDialog(context.application.root, len(colors),
									basename)
	basename = dlg.RunDialog()

	if basename is None:
		# the dialog was cancelled
		return

	# the EPS bbox is larger than the doc's bbox because of the
	# alignment marks
	align_distance = 6
	align_length = 12
	grow = align_length + align_distance
	llx, lly, urx, ury = doc_bbox
	ps_bbox = (llx - grow, lly - grow, urx + grow, ury + grow)
	for color in colors:
		separator = CreateSeparation(color)
		try:
			# do this in a try-finall to make sure the document colors
			# get restored even if something goes wrong
			doc.WalkHierarchy(separator.change_color)
			filename = basename + '-' + hexcolor(color)  + '.ps'
			ps_dev = PostScriptDevice(filename, as_eps = 1,
										bounding_box = ps_bbox,
										For = system.get_real_username(),
										CreationDate = system.current_date(),
										Title = os.path.basename(filename),
										document = doc)
			doc.Draw(ps_dev)
			draw_alignment_marks(ps_dev, doc_bbox,
									align_length, align_distance)
			ps_dev.Close()
		finally:
			separator.undo_changes()


import app.Scripting        
app.Scripting.AddFunction('simple_separation',
								_("Simple Separation"),
								simple_separation,
								script_type = app.Scripting.AdvancedScript)
