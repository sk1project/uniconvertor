# A Drawfile input filter for Sketch (http://sketch.sourceforge.net)
# Copyright (C) 2001, 2002 by David Boddie
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Versions history:
# 
# 0.10 (Fri 24th August 2001)
# 
# First release version.
# 
# 0.11 (Fri 24th August 2001)
# 
# Added tagged object rendering.
#
# 0.12 (Wed 29th August 2001)
#
# Tidied up text area rendering.
#
# 0.13 (Sun 17th February 2002)
#
# Changed the transformation matrix encoding for sprites so that the
# off-diagonal elements should now be scaled appropriately according to
# the horizontal and vertical dots per inch of the sprite.

###Sketch Config
#type = Import
#class_name = 'DrawfileLoader'
#rx_magic = 'Draw'
#tk_file_type = ('Drawfile', '.aff')
format_name = 'Drawfile'
#standard_messages = 1
#unload = 1
###End

(''"Drawfile")

version = '0.12 (Wed 29th August 2001)'

import os, string

try:
	import cStringIO
	StringIO = cStringIO
except ImportError:
	import StringIO

from math import floor

from app import Document, Layer, CreatePath, ContSmooth, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient,\
		CreateRGBColor, CreateCMYKColor, MultiGradient, Trafo, Point, Polar, \
		StandardColors, GetFont, PathText, SimpleText, const, UnionRects, \
		Arrow, Translation, Trafo, GridLayer, Scale

from app.io.load import GenericLoader, EmptyCompositeError

from app.Graphics import pagelayout

from app import SolidPattern, EmptyPattern

from PIL import Image

from uniconvertor.filters.formats import drawfile

scale = float(drawfile.units_per_point)

papersizes = [
		#    'A0', 'A1', 'A2',
		'A3', 'A4', 'A5', 'A6', 'A7',
		'letter', 'legal', 'executive',
		]

orientations = ['portrait', 'landscape']

def RISCOSFont(fontname):

	font = string.split(fontname, '.')

	if font[0] == 'Trinity':
		new_font = 'Times'
	elif font[0] == 'Homerton':
		new_font = 'Helvetica'
	elif font[0] == 'Corpus':
		new_font = 'Courier'
	else:
		return GetFont(fontname)

	if len(font) == 1:
		return GetFont(new_font)

	if font[1] == 'Medium':
		if new_font == 'Times':
			new_font = new_font + '-Roman'
	elif font[1] == 'Bold':
		new_font = new_font + '-Bold'

	if len(font) == 2:
		return GetFont(new_font)

	new_font = new_font + '-' + font[2]

	return GetFont(new_font)


class DrawfileLoader(GenericLoader):
	"""
	DrawfileLoader

	Read a Draw file and store the elements in a Sketch document
	"""

	format_name = format_name

	def __init__(self, file, filename, match):

		GenericLoader.__init__(self, file, filename, match)

		# GenericLoader puts file, filename and match into object attributes
		# with the same names

	def Load(self):

		# Font table
		self.font_table = {}

		# Page layout
		self.page_layout = None

		# Instantiate a drawfile object
		self.drawfile = drawfile.drawfile(self.file)

		# Create the document
		self.document()

		# Insert a layer
		self.layer('Layer 1')

		# Read the drawfile objects
#        try:
		self.read_objects(self.drawfile.objects)
#        except drawfile.drawfile_error:
#            self.add_message(_('Failed to read Drawfile '+self.filename))
#            self.debugout.write('Failed to read Drawfile '+self.filename+'\n')

		self.end_all()

		# Page layout
		if self.page_layout == None:

			# No page layout, so create a page which is large
			# enough to contain the objects
#            width = (self.drawfile.x2 - self.drawfile.x1)/scale
#            height = (self.drawfile.y2 - self.drawfile.y1)/scale
			width = self.drawfile.x2 / scale
			height = self.drawfile.y2 / scale

			if width > 0.0 and height > 0.0:
				self.object.load_SetLayout(
					pagelayout.PageLayout(width = width, height = height) )
		else:
			self.object.load_SetLayout(self.page_layout)

		self.object.load_Completed()

		# Return the document
		return self.object

	def read_objects(self, objects):

		n_objects = 0

		# Traverse the list of drawfile object
		for object in objects:

			if isinstance(object, drawfile.group):

				# Start a group object in the document
				self.begin_group()

				# Descend into the group
				n_objects_lower = self.read_objects(object.objects)

				# If the group was empty then don't try to end it
				if n_objects_lower == 0:
#                    self.__pop()
					(self.composite_class,
						self.composite_args,
						self.composite_items,
						self.composite_stack) = self.composite_stack
				else:
					# End group object
					self.end_group()
					n_objects = n_objects + 1

			elif isinstance(object, drawfile.tagged):

				# Tagged object
				n_objects_lower = self.read_objects([object.object])

				if n_objects_lower != 0:
					n_objects = n_objects + 1

			elif isinstance(object, drawfile.path):

				# Path object
				n_objects = n_objects + 1

				# Set the path style
				self.style.line_width = object.width / scale

				if object.style['join'] == 'mitred':
					self.style.line_join = const.JoinMiter

				if object.style['start cap'] == 'butt':
					self.style.line_cap = const.CapButt

				elif object.style['start cap'] == 'round':

					if object.width > 0:
						width  = 0.5
						length = 0.5
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width),
							(0.5*length, width, length, 0.5*width, length, 0.0),
							(length, -0.5*width,
								0.5*length, -width,
								0.0, -width), (0.0, width)]

					self.style.line_arrow1 = Arrow(path, 1)

				elif object.style['start cap'] == 'square':

					if object.width > 0:
						width  = 0.5
						length = 0.5
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width), (length, width),
							(length, -width), (0.0, -width),
							(0.0, width)]

					self.style.line_arrow1 = Arrow(path, 1)

				elif object.style['start cap'] == 'triangular':

					if object.width > 0:
						width  = object.style['triangle cap width'] / 16.0
						length = object.style['triangle cap length'] / 16.0
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width), (length, 0.0),
							(0.0, -width), (0.0, width)]

					self.style.line_arrow1 = Arrow(path, 1)
					if (object.width / scale) < 1.0:
						self.style.line_arrow1.path.Transform(Scale(object.width / scale, object.width / scale) )

				if object.style['end cap'] == 'butt':
					self.style.line_cap = const.CapButt

				elif object.style['end cap'] == 'round':

					if object.width > 0:
						width  = 0.5
						length = 0.5
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width),
							(0.5*length, width, length, 0.5*width, length, 0.0),
							(length, -0.5*width,
								0.5*length, -width,
								0.0, -width), (0.0, width)]
					
					self.style.line_arrow2 = Arrow(path, 1)

				elif object.style['end cap'] == 'square':

					if object.width > 0:
						width  = 0.5
						length = 0.5
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width), (length, width),
							(length, -width), (0.0, -width),
							(0.0, width)]

					self.style.line_arrow2 = Arrow(path, 1)

				elif object.style['end cap'] == 'triangular':

					if object.width > 0:
						width  = object.style['triangle cap width'] / 16.0
						length = object.style['triangle cap length'] / 16.0
					else:
						width = 0.0
						length = 0.0

					# Draw arrow
					path = [(0.0, width),
							(length, 0.0),
							(0.0, -width),
							(0.0, width)]
					
					self.style.line_arrow2 = Arrow(path, 1)
					if (object.width / scale) < 1.0:
						self.style.line_arrow2.path.Transform(Scale(object.width / scale, object.width / scale) )

				# Outline colour
				if object.outline == [255, 255, 255, 255]:
					self.style.line_pattern = EmptyPattern
				else:
					self.style.line_pattern = SolidPattern(
						CreateRGBColor( float(object.outline[1]) / 255.0,
										float(object.outline[2]) / 255.0,
										float(object.outline[3]) / 255.0 ) )

				# Fill colour
				if object.fill == [255, 255, 255, 255]:
					self.style.fill_pattern = EmptyPattern
				else:
					self.style.fill_pattern = SolidPattern(
						CreateRGBColor( float(object.fill[1]) / 255.0,
										float(object.fill[2]) / 255.0,
										float(object.fill[3]) / 255.0 )
									)

				# Dash pattern
				if object.style['dash pattern'] == 'present':
					line_dashes = []
					for n in object.pattern:

						line_dashes.append(int(n/scale))

					self.style.line_dashes = tuple(line_dashes)

				# Create a list of path objects in the document
				paths = []
				path = None

				# Examine the path elements
				for element in object.path:

					if element[0] == 'move':

						x, y = self.relative(element[1][0], element[1][1])

						# Add any previous path to the list
						if path != None:
#                            path.load_close()
							paths.append(path)

						path = CreatePath()
						path.AppendLine(x, y)

					elif element[0] == 'draw':

						x, y = self.relative(element[1][0], element[1][1])
						path.AppendLine(x, y)

					elif element[0] == 'bezier':

						x1, y1 = self.relative(element[1][0], element[1][1])
						x2, y2 = self.relative(element[2][0], element[2][1])
						x, y = self.relative(element[3][0], element[3][1])
						path.AppendBezier(x1, y1, x2, y2, x, y)

					elif element[0] == 'close':

						path.ClosePath()

					elif element[0] == 'end':

						# Should be the last object in the path
#                        path.load_close()
						paths.append(path)
						break

				# Create a bezier object
				if paths != []:
					self.bezier(tuple(paths))

			elif isinstance(object, drawfile.font_table):

				# Font table
				n_objects = n_objects + 1

				# Set object level instance
				self.font_table = object.font_table

			elif isinstance(object, drawfile.text):

				# Text object
				n_objects = n_objects + 1

				# Determine the font
				if self.font_table.has_key(object.style):
					self.style.font = RISCOSFont(self.font_table[object.style])
				else:
					self.style.font = GetFont('Times Roman')

				# The size
				self.style.font_size = object.size[0]/scale

				# Outline colour
				if object.background == [255, 255, 255, 255]:
					self.style.line_pattern = EmptyPattern
				else:
					self.style.line_pattern = SolidPattern(
						CreateRGBColor( float(object.background[1]) / 255.0,
										float(object.background[2]) / 255.0,
										float(object.background[3]) / 255.0 )
									)

				# Fill colour
				if object.foreground == [255, 255, 255, 255]:
					self.style.fill_pattern = EmptyPattern
				else:
					self.style.fill_pattern = SolidPattern(
						CreateRGBColor( float(object.foreground[1]) / 255.0,
										float(object.foreground[2]) / 255.0,
										float(object.foreground[3]) / 255.0 )
									)

				# Transformation
				if hasattr(object, 'transform'):
					x, y = object.transform[4]/scale, object.transform[5]/scale
					ox, oy = self.relative(object.baseline[0],
											object.baseline[1])
					transform = Trafo(object.transform[0]/65536.0,
										object.transform[1]/65536.0,
										object.transform[2]/65536.0,
										object.transform[3]/65536.0,
										ox + x, oy + y )
				else:
					transform = Translation(self.relative(object.baseline[0], object.baseline[1]) )

				# Write the text
				self.simple_text(object.text, transform)

			elif isinstance(object, drawfile.jpeg):

				# JPEG object
				n_objects = n_objects + 1

				# Transformation matrix
				x, y = self.relative(object.transform[4], object.transform[5])

				# Scale the object using the dpi information available, noting
				# that unlike Draw which uses 90 dpi, Sketch uses 72 dpi.
				# (I assume this since 90 dpi Drawfile JPEG objects appear 1.25
				# times larger in Sketch if no scaling is performed here.)
				scale_x = (object.transform[0]/65536.0) * (72.0 / object.dpi_x)
				scale_y = (object.transform[3]/65536.0) * (72.0 / object.dpi_y)

				transform = Trafo( scale_x, object.transform[1]/65536.0,
									object.transform[2]/65536.0, scale_y,
									x, y )

				# Decode the JPEG image
				image = Image.open(StringIO.StringIO(object.image))

#                # Read dimensions of images in pixels
#                width, height = image.size
#
#                # Divide these by the dpi values to obtain the size of the
#                # image in inches
#                width, height = width/float(object.dpi_x), \
#                height/float(object.dpi_y)

#                image.load()
				self.image(image, transform)

			elif isinstance(object, drawfile.sprite):

				# Sprite object
				n_objects = n_objects + 1

				# Transformation matrix

				if hasattr(object, 'transform'):
					x, y = self.relative(object.transform[4],
											object.transform[5])

					# Multiply the scale factor by that in the transformation matrix 
					scale_x = (object.transform[0]/65536.0) * (72.0 / object.sprite['dpi x'])
					scale_y = (object.transform[3]/65536.0) * (72.0 / object.sprite['dpi y'])

					transform = Trafo( scale_x,
										(object.transform[1]/65536.0) * \
										(72.0 / object.sprite['dpi y']),
										(object.transform[2]/65536.0) * \
										(72.0 / object.sprite['dpi x']),
										scale_y,
										x, y )
				else:
					x, y = self.relative(object.x1, object.y1)

					# Draw scales the Sprite to fit in the object's
					# bounding box. To do the same, we need to know the
					# actual size of the Sprite
					# In points:
#                    size_x = 72.0 * float(object.sprite['width']) / \
#                                           object.sprite['dpi x']
#                    size_y = 72.0 * float(object.sprite['height']) / \
#                                           object.sprite['dpi y']
#    
#                    # Bounding box dimensions in points:
#                    bbox_width = (object.x2 - object.x1)/scale
#                    bbox_height = (object.y2 - object.y1)/scale
#    
#                    # Scale factors
#                    scale_x = (bbox_width / size_x) * \
#                               (72.0 / object.sprite['dpi x'])
#                    scale_y = (bbox_height / size_y) * \
#                               (72.0 / object.sprite['dpi y'])
					scale_x = (object.x2 - object.x1) / (scale * object.sprite['width'])
					scale_y = (object.y2 - object.y1) / (scale * object.sprite['height'])
		
					transform = Trafo( scale_x, 0.0, 0.0, scale_y, x, y )

				# Create an Image object
				image = Image.fromstring(object.sprite['mode'],
											(object.sprite['width'],
											object.sprite['height']),
											object.sprite['image'])

				self.image(image, transform)

			elif isinstance(object, drawfile.options):

				# Options object
				n_objects = n_objects + 1

				# Read page size
				paper_size = object.options['paper size']
				orientation = object.options['paper limits']
				if paper_size in papersizes:

					if orientation == 'landscape':
						self.page_layout = pagelayout.PageLayout(
							object.options['paper size'],
							orientation = pagelayout.Landscape)
					else:
						self.page_layout = pagelayout.PageLayout(
							object.options['paper size'],
							orientation = pagelayout.Portrait)

				if object.options['grid locking'] == 'on':

					spacing = object.options['grid spacing']
					if object.options['grid units'] == 'in':
						spacing = spacing * 72.0
					else:
						spacing = spacing * 72.0 / 2.54

					if object.options['grid shown'] == 'on':
						visible = 1
					else:
						visible = 0

#                    self.begin_layer_class( GridLayer,
#                                (
#                                    (0, 0, int(spacing), int(spacing)),
#                                    visible,
#                                    CreateRGBColor(0.0, 0.0, 0.0),
#                                    _("Grid")
#                                ) )
#                    self.end_composite()

			elif isinstance(object, drawfile.text_area):

				# Text area
				n_objects = n_objects + 1

				# The text area object contains a number of columns.
				self.columns = len(object.columns)

				# Start in the first column and move to subsequent
				# columns as required, unless the number is overidden
				# by details in the text area.
				self.column = 0

				# The cursor position is initially undefined.
				cursor = [None, None]

				# The column margins
				self.margin_offsets = [1.0, 1.0]
				self.margins = [ (object.columns[self.column].x1 / scale) + \
									self.margin_offsets[0],
									(object.columns[self.column].x2 / scale) - \
									self.margin_offsets[1] ]

				# The column base
				self.column_base = object.columns[self.column].y1 / scale

				# Line and paragraph spacing
				self.linespacing = 0.0
				paragraph = 10.0

				# Current font name and dimensions
				font_name = ''
				font_size = 0.0
				font_width = 0.0

				# Text colours
				background = (255, 255, 255)
				foreground = (  0,   0,   0)

				# Build lines (lists of words) until the column width
				# is reached then write the line to the page.
				line = []
				width = 0.0

				# Current text alignment
				align = 'L'

				# Last command to be executed
				last_command = ''

				# Execute the commands in the text area:
				for command, args in object.commands:

					if command == '!':
						# Version number
#                        print 'Version number', args
						pass

					elif command == 'A':
#                        print 'Align:', args
						# Write current line
						self.ta_write_line(align, cursor, line, 0)
						# Empty the line list
						line = []
						# Set the line width
						width = 0.0
						# Align text
						align = args
						# Start new line
						cursor = self.ta_new_line(cursor, object, self.linespacing )

					elif command == 'B':
#                        print 'Background:', args
						# Background colour
						background = args

					elif command == 'C':
#                        print 'Foreground:', args
						# Foreground colour
						foreground = args

					elif command == 'D':
#                        print 'Columns:', args
						# Number of columns
						if self.column == 0 and cursor == [None, None]:
							# Nothing rendered yet, so change number of columns
							self.columns = args

					elif command == 'F':
#                        print 'Define font:', args
						# Define font (already defined in object.font_table)
						pass

					elif command == 'L':
#                        print 'Line spacing:', args
						# Set line spacing
						self.linespacing = args

					elif command == 'M':
#                        print 'Margins:', args
						# Change margins
						self.margin_offsets = [args[0], args[1]]
						self.margins = [
							(object.columns[self.column].x1 / scale) + args[0],
							(object.columns[self.column].x2 / scale) - args[1] ]

					elif command == 'P':
#                        print 'Paragraph spacing:', args
						# Change paragraph spacing
						paragraph = args

					elif command == 'U':
#                        print 'Underlining'
						# Underlining
						pass

					elif command == 'V':
#                        print 'Vertical displacement'
						# Vertical displacement
						pass

					elif command == '-':
#                        print 'Hyphen'
						# Hyphen
						pass

					elif command == 'newl':

#                        print 'New line'
						# New line
						# Write current line
						self.ta_write_line(align, cursor, line, 0)
						# Start new line
						cursor = self.ta_new_line(cursor, object, self.linespacing)

						# Can't position cursor?
						if cursor == [None, None]:
							break

						# Empty the line list
						line = []
						# Set the line width
						width = 0.0

					elif command == 'para':

#                        print 'New paragraph'
						# New paragraph
						# Write current line
						self.ta_write_line(align, cursor, line, 0)
						# Start new line
						if last_command != 'newl':
							cursor = self.ta_new_line(cursor, object, paragraph + self.linespacing)
						else:
							cursor = self.ta_new_line(cursor, object, paragraph)

						# Can't position cursor?
						if cursor == [None, None]:
							break

						# Empty the line list
						line = []
						# Set the line width
						width = 0.0

					elif command == ';':
#                        print 'Comment:', args
						# Comment
						pass

					elif command == 'font':
#                        print 'Use font:', args
						# Font change
						font_name, font_size, font_width = object.font_table[args]
						# Select font
						use_font = RISCOSFont(font_name)
						# Move cursor to start of a line if the cursor is
						# undefined
						if cursor == [None, None]:
							cursor[0] = self.margins[0]
							cursor[1] = (
								object.columns[self.column].y2 / scale
								) - font_size
						# Set line spacing
						self.linespacing = font_size
						

					elif command == 'text':

#                        print args
						# Text. Add it to the line, checking that the line
						# remains within the margins.
						text, space = self.make_safe(args[0]), args[1]

						# Add the width of the text to the current total width
						textobj=SimpleText()
						width = width + use_font.TextCoordBox(text, font_size, textobj.properties)[2]

#                        print width, margins[1] - margins[0]

						# Compare current total width with column width 
						while width > (self.margins[1] - self.margins[0]):

							# First write any text on this line
							if line != []:

								# Width will exceed column width
#                                print 'Width will exceed column width'
								# Write current line
								self.ta_write_line(align, cursor, line, 1)
								# Start new line
								cursor = self.ta_new_line(cursor, object,
															self.linespacing)

								# Can't position cursor?
								if cursor == [None, None]:
									break

								# Clear the list
								line = []
								# Reset the width
								width = 0.0

							# Now attempt to fit this word on the next line
							width = use_font.TextCoordBox(text, font_size, textobj.properties)[2]

							br = len(text)
							# Continue to try until the word fits, or none of it fits
							while width > (self.margins[1] - self.margins[0]) and br > 0:

								# Keep checking the size of the word
								width = use_font.TextCoordBox(text[:br], font_size, textobj.properties)[2]
								br = br - 1

							if br == 0:
								# Word couldn't fit in the column at all, so
								# break out of this loop
								break

							elif br < len(text):
								# Write the subword to the line
								self.ta_write_line( align, cursor,
											[ ( text[:br], font_name,
												font_size, font_width,
												self.ta_set_colour(foreground),
												self.ta_set_colour(background) )
											], 0 )

								# Start new line
								cursor = self.ta_new_line(cursor, object,
															self.linespacing)

								# Can't position cursor?
								if cursor == [None, None]:
									break

								# keep the remaining text
								text = text[br:]
								# The width is just the width of this text
								width = use_font.TextCoordBox(text, font_size, textobj.properties)[2]

							# If the whole string fit onto the line then
							# control will flow to the else clause which will
							# append the text to the line list for next time.
						else:
							# The text fits within the margins so add the text
							# to the line
							line.append( (text, font_name, font_size,
											font_width,
											self.ta_set_colour(
												foreground),
											self.ta_set_colour(background) ) )

							# Also append any trailing space
							if space != '':
								line.append( (space, font_name, font_size,
												font_width,
												self.ta_set_colour(foreground),
												self.ta_set_colour(background) ) )
								width = width + use_font.TextCoordBox(space, font_size, textobj.properties)[2]

						# Can't position cursor?
						if cursor == [None, None]:
							break

					# Remember this command
					last_command = command

				# Render any remaining text
				if line != [] and cursor != [None, None]:

					# Write current line
					self.ta_write_line(align, cursor, line, 0)

			else:
				pass

		# Return the number of recognised objects
		return n_objects


	def ta_write_line(self, align, cursor, line, wrapped):

#        print 'ta_write_line:', align, cursor, margins
		textobj=SimpleText()
		if line == [] or cursor == [None, None]:
			return

		# Remove leading and trailing spaces
		if line[0][0] == ' ':
			line = line[1:]
		if line != [] and line[-1][0] == ' ':
			line = line[:-1]
		if line == []:
			return

		# Depending on the justification of the text, either just write the
		# text to the page striaght from the line list (L, R, C) or space it
		# out appropriately (D)
		if align == 'L':

			# Left justification
			cursor[0] = self.margins[0]

			for word, font_name, font_size, font_width, fg, bg in line:

				# Set the font name
				self.style.font = RISCOSFont(font_name)
				# Set the font size
				self.style.font_size = font_size
				# Set the text colour
				self.style.line_pattern = bg
				self.style.fill_pattern = fg
				# Determine the horizontal position of the next word
				next = cursor[0] + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
				# Write the text to the page
				self.simple_text(word, Translation(cursor))
				# Reposition the cursor
				cursor[0] = next

		elif align == 'R':

			# Right justification
			line.reverse()
			cursor[0] = self.margins[1]

			for word, font_name, font_size, font_width, fg, bg in line:

				# Set the font name
				self.style.font = RISCOSFont(font_name)
				# Set the font size
				self.style.font_size = font_size
				# Set the text colour
				self.style.line_pattern = bg
				self.style.fill_pattern = fg
				# Determine the horizontal position of the this word
				cursor[0] = cursor[0] - self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
				# Write the text to the page
				self.simple_text(word, Translation(cursor))

		elif align == 'C':

			# Centred text
			# Determine the total width of the line

			total_width = 0.0

			for word, font_name, font_size, font_width, fg, bg in line:
				# Set the font
				self.style.font = RISCOSFont(font_name)
				# Increase the width
				total_width = total_width + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]

			# Place the cursor at a suitable place and render the text as if it
			# was left justified
			cursor[0] = self.margins[0] + (self.margins[1] - self.margins[0] - total_width)/2.0

			for word, font_name, font_size, font_width, fg, bg in line:

				# Set the font name
				self.style.font = RISCOSFont(font_name)
				# Set the font size
				self.style.font_size = font_size
				# Set the text colour
				self.style.line_pattern = bg
				self.style.fill_pattern = fg
				# Determine the horizontal position of the next word
				next = cursor[0] + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
				# Write the text to the page
				self.simple_text(word, Translation(cursor))
				# Reposition the cursor
				cursor[0] = next

		elif align == 'D' and wrapped == 1:

			# Text is wrapped due to an overflow

			# Double (full) justification
			# Take the width of each word which is not a space and create a
			# total width.
			# Subtract this from the column width and divide the remainder by
			# the number of spaces that should occur.
			# Also, remove the spaces from the list by creating a new list.

			total_width = 0.0
			new_line = []

			for word, font_name, font_size, font_width, fg, bg in line:

				if word != '':
					# Set the font
					self.style.font = RISCOSFont(font_name)
					# Increase the width
					total_width = total_width + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
					# Add this word to the new list
					new_line.append( (word, font_name, font_size, font_width, fg, bg) )

			# If there are no words then return to the caller
			if len(new_line) == 0:
				return

			# Determine the spacing required between each word
			if len(new_line) > 1:
				spacing = (self.margins[1] - self.margins[0] - total_width) / (len(new_line) - 1)
			else:
				spacing = 0.0

			# Place the cursor and render the new line
			cursor[0] = self.margins[0]

			for word, font_name, font_size, font_width, fg, bg in new_line:

				# Set the font name
				self.style.font = RISCOSFont(font_name)
				# Set the font size
				self.style.font_size = font_size
				# Set the text colour
				self.style.line_pattern = bg
				self.style.fill_pattern = fg
				# Determine the horizontal position of the end of this word
				next = cursor[0] + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
				# Write the text to the page
				self.simple_text(word, Translation(cursor))
				# Reposition the cursor
				cursor[0] = next + spacing

		elif align == 'D' and wrapped == 0:

			# Text is not wrapped due to an overflow

			# Left justification
			cursor[0] = self.margins[0]

			for word, font_name, font_size, font_width, fg, bg in line:

				# Set the font name
				self.style.font = RISCOSFont(font_name)
				# Set the font size
				self.style.font_size = font_size
				# Set the text colour
				self.style.line_pattern = bg
				self.style.fill_pattern = fg
				# Determine the horizontal position of the next word
				next = cursor[0] + self.style.font.TextCoordBox(word, font_size, textobj.properties)[2]
				# Write the text to the page
				self.simple_text(word, Translation(cursor))
				# Reposition the cursor
				cursor[0] = next
		else:
			# Can't align the text
			return


	def ta_new_line(self, cursor, object, vspacing):

		# Don't try to move to a new line if the cursor is undefined.
		if cursor == [None, None]:
			return [None, None]

		if (cursor[1] - vspacing) < self.column_base:

			# If below the column base then try to move to the next column
			cursor = self.ta_next_column(cursor, object)

			# Any more columns?
			if cursor != [None, None]:

				# Reset cursor to leftmost margin
				cursor = [self.margins[0], cursor[1] - self.linespacing]

		else:
			# Move cursor down by the specified amount
			cursor[1] = cursor[1] - vspacing

		return cursor


	def ta_next_column(self, cursor, object):

		# Try to move to the next column
		if self.column < (self.columns - 1):

			# Go to next column
			self.column = self.column + 1
	
			self.margins = [(object.columns[self.column].x1 / scale) + \
							self.margin_offsets[0],
							(object.columns[self.column].x2 / scale) - \
							self.margin_offsets[1]]
	
			cursor = [self.margins[0], object.columns[column].y2 / scale]
			self.column_base = self.columns[self.column].y1 / scale
		else:
			# No more columns to go to
			#print 'No more columns'
			cursor = [None, None]

		return cursor


	def ta_set_colour(self, colour):

		if tuple(colour) == (255, 255, 255):

			return EmptyPattern
		else:
			return SolidPattern(
				CreateRGBColor( float(colour[0]) / 255.0,
								float(colour[1]) / 255.0,
								float(colour[2]) / 255.0 ) )


	def make_safe(self, s):

		new = ''
		for i in s:
			if ord(i) >= 32:
				new = new + i
		return new


	def relative(self, x, y):

#        return (x - self.drawfile.x1)/scale, (y - self.drawfile.y1)/scale
		return x/scale, y/scale
