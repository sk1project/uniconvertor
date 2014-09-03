# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor Novikov
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
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

###Sketch Config
#type = Import
#class_name = 'AILoader'
#rx_magic = '^\\xC5\\xD0\\xD3\\xC6|^%!PS-Adobe-[23]\.0'
#tk_file_type = ("Adobe Illustrator (up to 7 ver.)", '.ai')
format_name = 'Adobe Illustrator'
#unload = 1
#standard_messages = 1
###End

#
#       Import Filter for Adobe Illustrator files
#
#
# Status:
#
# This filter is work in progress, and not everything works yet. Here's
# an outline of what should work, what will be implemented in future
# versions and what is not currently possible in Sketch.
#
# If this filter fails to import a file that it should be able to
# handle, please contact me (see the Sketch README for the email
# address).
#
#
# - Path construction:
#
#   The filters understands all path construction operators including
#   compound paths.
#
# - Path attributes:
#
#   The filter handles line width, dash pattern (without the phase),
#   line join and line cap. Miter limit is restricted to the value
#   implied by the X-server (11 degrees). Flatness is ignored. Likewise
#   the winding order, because Sketch currently only supports the
#   even-odd-rule for filled paths.
#
# - Stroke/Fill color
#
#   The filter handles the colormodels gray scale, CMYK, RGB, custom
#   CMYK and custom RGB.
#
# - Patterns/Gradients
#
#   The filter understands Gradients, but they may not always look
#   exactly like in Illustrator because Sketch's model is a bit more
#   limited than Illustrator's in some respects (but this may change)
#   and not all of Illustrator's colormodels are implemented yet here.
#
#   Patterns are not implemented, since Sketch doesn't have Vector
#   patterns yet.
#
# - Containers
#
#   The filter handles groups and layers.
#
# - Text
#
#   The filter can handle point text and path text to some degree. It
#   doesn't handle encodings at the moment.
#
#   Because of Sketch's limited Text capabilities it can't handle area
#   text and ignores spacing information.
#
# - Raster Images
#
#   Sketch doesn't handle all variants yet
#
# - Guides
#
#   The filter puts all guides it finds into the guide layer, regardless
#   of where they are defined in the file.
#
#
# - As yet unimplemented Features that could be handled by Sketch
#
#   - Masks
#
#   - Embedded EPS files


(''"Adobe Illustrator")

import string, re
from math import pi, hypot
from types import IntType, StringType, ListType
import string

from PIL import Image

import streamfilter

from app import Document, Layer, CreatePath, ContSmooth, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient,\
		CreateRGBColor, CreateCMYKColor, MultiGradient, Trafo, Point, Polar, \
		StandardColors, GetFont, PathText, SimpleText, const, UnionRects

from app.Graphics import text

from app.events.warn import INTERNAL, warn_tb
from app.Lib import encoding

from app.io.load import GenericLoader, EmptyCompositeError
from app.pstokenize import PSTokenizer, DSC_COMMENT, OPERATOR, END, \
		MAX_DATA_TOKEN

from struct import unpack

struct_eps_header = ('<'
			'I'	# Must be hex C5D0D3C6
			'I'	# Byte position in file for start of PostScript language code section.
			'I'	# Byte length of PostScript language section.
			'I'	# Byte position in file for start of Metafile screen representation.
			'I'	# Byte length of Metafile section.
			'I'	# Byte position of TIFF representation.
			'I'	# Byte length of TIFF section.
			'I'	# Checksum of header (XOR of bytes 0-27). 
				# If Checksum is FFFF then ignore it.
			)

def cmyk_custom_color(c, m, y, k, t):
	# t = tint
	t = 1.0 - t
	return CreateCMYKColor(t * c, t * m, t * y, t * k)

def rgb_custom_color(r, g, b, t):
	t = 1.0 - t
	return CreateRGBColor(1 - (t * (1 - r)),
							1 - (t * (1 - g)),
							1 - (t * (1 - b)))

def fix_gradient(array, factor, offset):
	array = array[:]
	for i in range(len(array)):
		pos, color = array[i]
		array[i] = factor * pos + offset, color
	if factor < 0:
		array.reverse()
	if array[0][0] < 0:
		if array[-1][0] > 0:
			while array[0][0] < 0:
				pos, color = array[0]
				del array[0]
			if array[0][0] > 0:
				frac = -pos / (array[0][0] - pos)
				array.insert(0, (0.0, color.Blend(array[0][1], 1-frac, frac)))
		else:
			color = array[-1][1]
			array = [(0.0, color), (1.0, color)]
	elif array[0][0] > 0:
		array.insert(0, (0.0, array[0][1]))
	if array[-1][0] > 1:
		if array[0][0] < 1:
			while array[-1][0] > 1:
				pos, color = array[-1]
				del array[-1]
			if array[-1][0] < 1:
				frac = (pos - 1) / (pos - array[-1][0])
				array.append((1.0, color.Blend(array[-1][1], 1-frac, frac)))
		else:
			color = array[0][1]
			array = [(0.0, color), (1.0, color)]
	elif array[-1][0] < 1:
		array.append((1.0, array[-1][1]))
		
	return array

# arrays to convert AI join and cap to Sketch's join and cap. In AI
# files they're given as small ints so we just use a tuple where we can
# use the AI cap/join value as index to get the corresponding value in
# Sketch.
_ai_join = (const.JoinMiter, const.JoinRound, const.JoinBevel)
_ai_cap =  (const.CapButt, const.CapRound, const.CapProjecting)

# The same for text alignment. The last two values are two variants of
# justified text, which Sketch doesn't have, so we're just using
# centered for now.
_ai_text_align = (text.ALIGN_LEFT, text.ALIGN_CENTER, text.ALIGN_RIGHT,
					text.ALIGN_CENTER, text.ALIGN_CENTER)

artboard_trafo = Trafo(1, 0, 0, -1, 4014, 4716)
artboard_trafo_inv = artboard_trafo.inverse()

class FontInfo:

	def __init__(self, psname, newname, encoding):
		self.psname = psname
		self.newname = newname
		self.encoding = encoding
		self.reencoder = None

	def Reencode(self, text):
		if self.reencoder is None:
			self.reencoder = encoding.Reencoder(self.encoding,
												encoding.iso_latin_1)
		return self.reencoder(text)
		


grow_join = [5.240843064, 0.5, 0.5]
grow_cap = [None, 0.5, 0.5, 0.70710678]

def fix_bounding_rect(rect, style):
	return rect.grown(style.line_width * max(grow_cap[style.line_cap],
												grow_join[style.line_join]))


		
class AILoader(GenericLoader):

	format_name = format_name

	functions = {"C": 'curveto',
					"c": 'curveto_smooth',
					"V": 'curveto_v',
					"v": 'curveto_v_smooth',
					"Y": 'curveto_y',
					"y": 'curveto_y_smooth',
					"m": 'moveto',
					"l": 'lineto',
					"L": 'lineto',
					"w": 'set_line_width',
					"j": 'set_line_join',
					"J": 'set_line_cap',
					"d": 'set_line_dash',
					"G": 'set_line_gray',
					"K": 'set_line_cmyk',
					"XA": 'set_line_rgb',
					"X": 'set_line_cmyk_custom',
					"XX": 'set_line_generic_custom',
					"P": 'set_line_pattern',
					"g": 'set_fill_gray',
					"k": 'set_fill_cmyk',
					"cmyk": 'set_fill_cmyk',
					"Xa": 'set_fill_rgb',
					"rgb": 'set_fill_rgb',
					"x": 'set_fill_cmyk_custom',
					"Xx": 'set_fill_generic_custom',
					"p": 'set_fill_pattern',
					"F": 'fill',
					"f": 'fill_close',
					"S": 'stroke',
					"s": 'stroke_close',
					"B": 'fill_stroke',
					"b": 'fill_stroke_close',
					"closepath": 'fill_stroke_close',
					"N": 'invisible',        # an invisible open path
					"n": 'invisible_close',  # a invisible closed path
					"u": 'begin_group',
					"U": 'end_group',
					"*u": 'begin_compound_path',
					"newpath": 'begin_compound_path',
					"*U": 'end_compound_path',
					"gsave": 'end_compound_path',
					"*": 'guide',
					"[": 'mark',
					"]": 'make_array',
					"@": 'ignore_operator',
					"&": 'ignore_operator',
					"Bd": 'begin_gradient',
					"Bs": 'gradient_stop',
					"BS": 'dummy_gradient_stop',
					"Br": 'gradient_ramps',
					"BD": 'end_gradient',
					"Bb": 'begin_gradient_instance',
					"Bg": 'gradient_geometry',
					"BB": 'end_gradient_instance',
					"Lb": 'begin_ai_layer',
					"Ln": 'name_layer',
					"LB": 'end_ai_layer',
					"Pb": 'begin_palette',
					"PB": 'end_palette',
					"TE": 'set_standard_encoding',
					"TZ": 'reencode_font',
					"To": 'begin_text',
					"TO": 'end_text',
					"Tr": 'set_text_render',
					"Tf": 'set_text_font',
					"Ta": 'set_text_align',
					"Tp": 'begin_text_path',
					"TP": 'end_text_path',
					"Tx": 'render_text',
					"TX": 'render_text_inv',
					"XI": 'raster_image',
					}

	def __init__(self, file, filename, match,
					treat_toplevel_groups_as_layers = 1,
					flatten_groups = 1):
		GenericLoader.__init__(self, file, filename, match)
		self.line_color = StandardColors.black
		self.fill_color = StandardColors.black
		self.line_width = 0.0
		self.line_join  = const.JoinMiter
		self.line_cap  = const.CapButt
		self.line_dashes = ()
		self.cur_x = self.cur_y = 0.0
		self.treat_toplevel_groups_as_layers = treat_toplevel_groups_as_layers
		self.flatten_groups = flatten_groups
		self.guess_continuity = 1
		self.path = CreatePath()
		self.compound_path = None # If compound_path is None, we're
									# outside of a compound path,
									# otherwise it's a possibly empty list
									# of paths
		self.compound_render = ''
		self.stack = []
		self.gradients = {}
		self.in_gradient_instance = 0
		self.gradient_geo = None # set to a true value after Bg, and set
									# to false by make_gradient_pattern
		self.gradient_rect = None
		self.in_palette = 0
		self.in_text = 0
		self.ignore_fill = 0
		self.text_type = 0      # 0: point text, 1: area text, 2 = path text
		self.text_render = 0    # filled
		self.text_font = None
		self.text_size = 12

		# Test alignment. Possible values: 0: left, 1: center, 2:right,
		# 3: justified, 4: justified including last line
		self.text_align = 0

		self.text_string = []
		self.standard_encoding = encoding.adobe_standard
		self.font_map = {}
		self.guides = []
		self.format_version = 0.0

	def __del__(self):
		pass

	def warn(self, level, *args, **kw):
		message = apply(warn, (level,) + args, kw)
		self.add_message(message)

	def get_compiled(self):
		funclist = {}
		for char, name in self.functions.items():
			method = getattr(self, name)
			argc = method.im_func.func_code.co_argcount - 1
			funclist[char] = (method, argc)
		return funclist

	def pop(self):
		value = self.stack[-1]
		del self.stack[-1]
		return value

	def pop_multi(self, num):
		value = self.stack[-num:]
		del self.stack[-num:]
		return value

	def pop_to_mark(self):
		s = self.stack[:]
		s.reverse()
		try:
			idx = s.index(None)
			if idx:
				array = self.stack[-idx:]
				del self.stack[-idx - 1:]
			else:
				array = []
				del self.stack[-1]
			return array
		except:
			raise RuntimeError, 'No mark on stack'

	def ignore_operator(self):
		pass

	def mark(self):
		self.stack.append(None)

	def make_array(self):
		array = self.pop_to_mark()
		self.stack.append(array)

	def convert_color(self, color_spec):
		c = apply(CreateRGBColor, color_spec)
		return c

	def set_line_join(self, join):
		self.line_join = _ai_join[join]

	def set_line_cap(self, cap):
		self.line_cap = _ai_cap[cap]

	def set_line_width(self, w):
		self.line_width = w

	def set_line_dash(self, array, phase):
		self.line_dashes = tuple(array)

	def set_line_gray(self, k):
		self.line_color = CreateRGBColor(k, k, k)

	def set_line_cmyk(self, c, m, y, k):
		self.line_color = CreateCMYKColor(c, m, y, k)
		
	def set_line_rgb(self, r, g, b):
		self.line_color = CreateRGBColor(r, g, b)

	def set_line_cmyk_custom(self, c, m, y, k, name, tint):
		self.line_color = cmyk_custom_color(c, m, y, k, tint)
		
	def set_line_generic_custom(self, name, tint, type):
		if type == 0:
			# cmyk
			c, m, y, k = self.pop_multi(4)
			self.line_color = cmyk_custom_color(c, m, y, k, tint)
		else:
			# rgb
			r, g, b = self.pop_multi(3)
			self.line_color = rgb_custom_color(r, g, b, tint)

	def set_line_pattern(self, name, px, py, sx, sy, angle, rf, r, k, ka,
							matrix):
		if not self.in_palette:
			self.add_message(_("Vector patterns not supported. Using black"))
		self.line_color = StandardColors.black
			
	def set_fill_gray(self, k):
		self.fill_color = CreateRGBColor(k, k, k)

	def set_fill_cmyk(self, c, m, y, k):
		self.fill_color = CreateCMYKColor(c, m, y, k)
		
	def set_fill_rgb(self, r, g, b):
		self.fill_color = CreateRGBColor(r, g, b)

	def set_fill_cmyk_custom(self, c, m, y, k, name, tint):
		self.fill_color = cmyk_custom_color(c, m, y, k, tint)
		
	def set_fill_generic_custom(self, name, tint, type):
		if type == 0:
			# cmyk
			c, m, y, k = self.pop_multi(4)
			self.fill_color = cmyk_custom_color(c, m, y, k, tint)
		else:
			# rgb
			r, g, b = self.pop_multi(3)
			self.fill_color = rgb_custom_color(r, g, b, tint)

	def set_fill_pattern(self, name, px, py, sx, sy, angle, rf, r, k, ka,
							matrix):
		if not self.in_palette:
			self.add_message(_("Vector patterns not supported. Using black"))
		self.fill_color = StandardColors.black

	def ls(self):
		style = self.style
		style.line_pattern = SolidPattern(self.line_color)
		style.line_width = self.line_width
		style.line_join = self.line_join
		style.line_cap = self.line_cap
		style.line_dashes = self.line_dashes

	def lsnone(self):
		self.style.line_pattern = EmptyPattern

	def fs(self):
		if self.gradient_geo:
			pattern = self.make_gradient_pattern()
		else:
			pattern = SolidPattern(self.fill_color)
		self.style.fill_pattern = pattern

	def fsnone(self):
		self.style.fill_pattern = EmptyPattern

	def stroke(self):
		if self.compound_path is not None:
			self.compound_render = 'stroke'
		else:
			self.ls()
			self.fsnone()
		self.bezier()

	def stroke_close(self):
		self.bezier_close()
		self.stroke()

	def fill(self):
		if self.ignore_fill:
			return
		if self.compound_path is not None:
			self.compound_render = 'fill'
		else:
			self.lsnone()
			self.fs()
		self.bezier()

	def fill_close(self):
		self.bezier_close()
		self.fill()

	def fill_stroke(self):
		if self.compound_path is not None:
			self.compound_render = 'fill_stroke'
		else:
			self.ls()
			self.fs()
		self.bezier()

	def fill_stroke_close(self):
		self.bezier_close()
		self.fill_stroke()

	def invisible(self):
		if self.compound_path is not None:
			self.compound_render = 'invisible'
		else:
			self.lsnone()
			self.fsnone()
		self.bezier()

	def invisible_close(self):
		self.bezier_close()
		self.invisible()

	# Gradient functions
	def begin_gradient(self, name, type, ncolors):
		self.gradient_info = name, type, ncolors

	def gradient_stop(self, color_style, mid_point, ramp_point):
		if color_style == 0:
			# gray scale
			k = self.pop()
			color = CreateRGBColor(k, k, k)
		elif color_style == 1:
			# CMYK
			color = apply(CreateCMYKColor, tuple(self.pop_multi(4)))
		elif color_style == 2:
			# RGB Color
			args = tuple(self.pop_multi(7))
			# The cmyk and rgb values usually differ slightly because AI
			# does some color correction. Which values should we choose
			# here?
			color = apply(CreateRGBColor, args[-3:])
			color = apply(CreateCMYKColor, args[:4])
		elif color_style == 3:
			# CMYK Custom Color
			args = self.pop_multi(6)
			color = apply(CreateCMYKColor, tuple(args[:4]))
		else:
			self.add_message(_("Gradient ColorStyle %d not yet supported."
								"substituted black")
								% color_style)
			if color_style == 4:
				n = 10
			else:
				self.add_message(_("Unknown ColorStyle %d")
									% color_style)
			self.pop_multi(n)
			color = StandardColors.black # XXX
		#color = apply(CreateRGBColor, color)
		self.stack.append((ramp_point / 100.0, color))

	def dummy_gradient_stop(self, color_style, mid_point, ramp_point):
		# same as gradient_stop but ignore all arguments. Illustrator 8
		# seems to introduce this one for printing (i.e. Illustrator 8
		# files with printing info contain the gradient stops *twice* in
		# exactly the same format but once with the Bs operator and once
		# with BS. I guess this has something to do with support for
		# PostScript Level 3 and backwards compatibility with older
		# Illustrator versions.
		if color_style == 0:
			# gray scale
			k = self.pop()
		elif color_style == 1:
			# CMYK
			self.pop_multi(4)
		elif color_style == 2:
			# RGB Color
			self.pop_multi(7)
		elif color_style == 3:
			# CMYK Custom Color
			self.pop_multi(6)
		elif color_style == 4:
			self.pop_multi(10)
		else:
			self.add_message(_("Unknown ColorStyle %d") % color_style)

	def gradient_ramps(self, ramp_type):
		# defines the ramp colors with a bunch of strings for printing.
		# Here we just pop all the strings off the stack
		num = (1, 4, 5, 6, 7, 8, 9)[ramp_type]
		self.pop_multi(num)

	def end_gradient(self):
		self.make_array()
		array = self.pop()
		if len(array) < 2:
			self.add_message(_("less than two color stops in gradient"))
		else:
			# sometimes the ramp_point values are increasing, sometimes
			# decreasing... what's going on here? The docs say they are
			# increasing.
			if array[0][0] > array[-1][0]:
				array.reverse()
			name, type, ncolors = self.gradient_info
			self.gradients[name] = (type, array)
		del self.stack[:]
		#self.pop_to_mark()

	def begin_gradient_instance(self):
		self.in_gradient_instance = 1
		self.ignore_fill = 1

	def gradient_geometry(self, flag, name, xorig, yorig, angle, length,
							a, b, c, d, tx, ty):
		trafo = Trafo(a, b, c, d, tx, ty)
		trafo = artboard_trafo_inv(trafo(artboard_trafo))
		start = Point(xorig, yorig)
		end = start + Polar(length, (pi * angle) / 180.0)
		self.gradient_geo = (name, trafo, start, end)

	def make_gradient_pattern(self):
		name, trafo, start, end = self.gradient_geo
		self.gradient_geo = None
		type, array = self.gradients[name]
		array = array[:]
		if type == 0:
			# linear (axial) gradient
			origdir = end - start
			start = trafo(start)
			end = trafo(end)
			dir = end - start
			try:
				# adjust endpoint to accomodate trafo
				v = trafo.DTransform(origdir.y, -origdir.x).normalized()
				v = Point(v.y, -v.x) # rotate 90 degrees
				end = start + (v * dir) * v
				dir = end - start
			except ZeroDivisionError:
				pass

			trafo2 = Trafo(dir.x, dir.y, dir.y, -dir.x, start.x, start.y)
			trafo2 = trafo2.inverse()
			left, bottom, right, top = trafo2(self.current_bounding_rect())
			if right > left:
				factor = 1 / (right - left)
				offset = -left * factor
			else:
				factor = 1
				offset = 0
			array = fix_gradient(array, factor, offset)
			pattern = LinearGradient(MultiGradient(array),
										(start - end).normalized())
		elif type == 1:
			# radial gradient
			start = trafo(start)
			end = trafo(end)
			left, bottom, right, top = self.current_bounding_rect()
			if left == right or top == bottom:
				# an empty coord_rect????
				center = Point(0, 0)
			else:
				center = Point((start.x - left) / (right - left),
								(start.y - bottom) / (top - bottom))
			radius = max(hypot(left - start.x,  top - start.y),
							hypot(right - start.x, top - start.y),
							hypot(right - start.x, bottom - start.y),
							hypot(left - start.x,  bottom - start.y))
			if radius:
				factor = -abs(start - end) / radius
				array = fix_gradient(array, factor, 1)
			pattern = RadialGradient(MultiGradient(array), center)
		else:
			self.add_message(_("Unknown gradient type %d"), type)
			pattern = EmptyPattern
		return pattern

	def current_bounding_rect(self):
		if self.gradient_rect is not None:
			rect = self.gradient_rect
		else:
			rect = self.path.accurate_rect()
		if not self.style.line_pattern.is_Empty:
			rect = fix_bounding_rect(rect, self.style)
		return rect

	def end_gradient_instance(self, flag):
		self.ignore_fill = 0
		if flag == 2:
			self.fill_stroke_close()
		elif flag == 1:
			self.fill_stroke()
		else:
			self.fill()
		self.in_gradient_instance = 0
			

	# Path construction
	def moveto(self, x, y):
		self.cur_x = x
		self.cur_y = y
		self.path.AppendLine(x, y)

	def lineto(self, x, y):
		self.cur_x = x
		self.cur_y = y
		self.path.AppendLine(x, y)

	def curveto(self, x1, y1, x2, y2, x3, y3):
		self.path.AppendBezier(x1, y1, x2, y2, x3, y3)
		self.cur_x = x3
		self.cur_y = y3

	def curveto_smooth(self, x1, y1, x2, y2, x3, y3):
		self.path.AppendBezier(x1, y1, x2, y2, x3, y3, ContSmooth)
		self.cur_x = x3
		self.cur_y = y3

	def curveto_v(self, x2, y2, x3, y3):
		# current point and first control point are identical
		self.path.AppendBezier(self.cur_x, self.cur_y, x2, y2, x3, y3)
		self.cur_x = x3
		self.cur_y = y3

	def curveto_v_smooth(self, x2, y2, x3, y3):
		# current point and first control point are identical
		self.path.AppendBezier(self.cur_x, self.cur_y, x2, y2, x3, y3,
								ContSmooth)
		self.cur_x = x3
		self.cur_y = y3

	def curveto_y(self, x1, y1, x3, y3):
		# endpoint and last controlpoint are identical
		self.path.AppendBezier(x1, y1, x3, y3, x3, y3)
		self.cur_x = x3
		self.cur_y = y3

	def curveto_y_smooth(self, x1, y1, x3, y3):
		# endpoint and last controlpoint are identical
		self.path.AppendBezier(x1, y1, x3, y3, x3, y3, ContSmooth)
		self.cur_x = x3
		self.cur_y = y3

	def bezier_close(self):
		if self.path.len > 1:
			self.path.AppendLine(self.path.Node(0))
			self.path.load_close(1)

	def bezier(self):
		if self.guess_continuity:
			self.path.guess_continuity()
		if self.path.len > 0:
			if self.compound_path is not None:
				self.compound_path.append(self.path)
			else:
				GenericLoader.bezier(self, paths = (self.path,))
		self.path = CreatePath()

	# compound paths

	def begin_compound_path(self):
		self.compound_path = []

	def end_compound_path(self):
		paths = tuple(self.compound_path)
		self.compound_path = None
		if paths:
			# XXX ugly
			if self.gradient_geo:
				rect = paths[0].accurate_rect()
				for path in paths[1:]:
					rect = UnionRects(rect, path.accurate_rect())
				self.gradient_rect = rect
			else:
				self.gradient_rect = None
			getattr(self, self.compound_render)()
			GenericLoader.bezier(self, paths = paths)
		
	# Groups
	
	def begin_group(self):
		if self.compound_path is None:
			# a normal group
			if self.treat_toplevel_groups_as_layers:
				if self.composite_class == Document:
					self.begin_layer()
					return
			GenericLoader.begin_group(self)
		else:
			# a `compound group'. Ignored since Sketch doesn't have this.
			pass

	def end_group(self):
		if self.compound_path is None:
			# a normal group
			if self.composite_class == Layer:
				self.end_composite()
			else:
				try:
					GenericLoader.end_group(self)
					if self.flatten_groups:
						if self.object.NumObjects() == 1:
							obj = self.object.GetObjects()[0]
							del self.composite_items[-1]
							self.append_object(obj)
				except EmptyCompositeError:
					pass
		else:
			# a `compound group'. Ignored since Sketch doesn't have this.
			pass

	# Layers

	def begin_layer(self):
		self.layer(_("Layer %d") % (len(self.composite_items) + 1))

	def begin_ai_layer(self):
		if self.format_version >= 4.0:
			visible, preview, enabled, printing, dimmed, unused, has_mlm,\
					color, red, green, blue, unused, unused = self.pop_multi(13)
		else:
			visible, preview, enabled, printing, dimmed, has_mlm, \
						color, red, green, blue = self.pop_multi(10)
		color = CreateRGBColor(red / 255.0, green / 255.0, blue / 255.0)
		self.layer_kw_args = {'printable': printing,
								'visible': visible,
								'locked': not enabled,
								'outline_color': color}

	def end_ai_layer(self):
		self.end_layer()

	def name_layer(self, name):
		apply(self.layer, (name,), self.layer_kw_args)

	# Guides

	def guide(self, op):
		#print 'guide', op
		method = getattr(self, self.functions[op])
		method()
		guide = self.pop_last()
		self.guides.append(guide)

	# Palette

	def begin_palette(self):
		self.in_palette = 1

	def end_palette(self):
		self.in_palette = 0

	# Text

	def set_standard_encoding(self):
		encoding = list(self.standard_encoding)
		pos = 0
		defs = self.pop_to_mark()
		for item in defs:
			if type(item) == IntType:
				pos = item
			elif type(item) == StringType:
				encoding[pos] = item
				pos = pos + 1
			else:
				self.add_message('unknown item %s in encoding' % `item`)
		self.standard_encoding = tuple(encoding)

	def define_font(self, psname, newname, encoding = None):
		if encoding is None:
			encoding = self.standard_encoding[:]
		self.font_map[newname] = FontInfo(psname, newname, encoding)

	def reencode_font(self):
		args = self.pop_to_mark()
		if type(args[-1]) == ListType:
			self.add_message(_("Multiple Master fonts not supported. "
								"Using Times Roman"))
			newname = args[-6]
			self.define_font('Times Roman', newname)
		else:
			newname, psname, direction, script, usedefault = args[-5:]
			if len(args) > 5:
				self.add_message(_("Additional encoding ignored"))
			self.define_font(psname, newname)


	def begin_text(self, text_type):
		self.in_text = 1
		self.text_type = text_type
		self.text_string = []
		if text_type == 1:
			self.add_message(_("Area text not supported"))
		if text_type == 2:
			GenericLoader.begin_group(self)

	def end_text(self):
		# we don't support area text (text_type 1) at all. Return
		# immediately in that case.
		if self.text_type == 1:
			return

		# first, turn the text accumulated in the list text_string into
		# a single string and unify line endings to newline characters.
		text = string.join(self.text_string, '')
		text = string.replace(text, '\r\n', '\n')
		text = string.replace(text, '\r', '\n')

		# remove a trailing newline. Many Illustrator files contain a
		# trailing newline as 'overflow' text, there's probably a better
		# way to deal with this...
		if text[-1:] == "\n":
			text = text[:-1]

		# Re-encode to Latin1
		text = self.text_font.Reencode(text)

		if not string.strip(text):
			if self.text_type == 2:
				self.end_composite()
				del self.composite_items[-1]
				if len(self.composite_items) > 0:
					self.object = self.composite_items[-1]
			return

		# first create a simple text object
		self.fs()
		self.style.font = GetFont(self.text_font.psname)
		self.style.font_size = self.text_size
		self.simple_text(text, self.text_trafo,
							halign = _ai_text_align[self.text_align])

		# if we're actually supposed to create a path-text object, turn
		# the text object just created into a path-text object
		if self.text_type == 2:
			GenericLoader.end_group(self)
			group = self.pop_last()
			objects = group.GetObjects()
			if len(objects) == 2:
				path, text = objects
				self.append_object(PathText(text, path,
											start_pos = self.text_start_pos))
				#self.composite_items[-1] = self.object

		# we've finished the text object
		self.in_text = 0

	def set_text_render(self, render):
		self.text_render = render

	def set_text_align(self, align):
		self.text_align = align

	def set_text_font(self):
		# In Illustrator < 7, the operator has two arguments, new
		# fontname and size. In Illustrator >= 7, there are two
		# additional arguments, ascent and descent.
		args = self.pop_multi(2)
		if type(args[0]) != StringType:
			newname, size = self.pop_multi(2)
		else:
			newname, size = args
		if self.font_map.has_key(newname):
			self.text_font = self.font_map[newname]
		elif newname[0] == '_':
			# special case for ai files generated by ps2ai. They don't
			# use the TZ operator to reencode the fonts and define the _
			# names.
			self.define_font(newname[1:], newname)
			self.text_font = self.font_map[newname]
		else:
			self.add_message(_("No font %s.") % newname)
		self.text_size = size


	def begin_text_path(self, a, b, c, d, tx, ty, start_pos):
		self.text_trafo = Trafo(a, b, c, d, tx, ty)
		self.text_start_pos = start_pos

	def end_text_path(self):
		pass

	def render_text(self, text):
		if self.text_type != 2:
			# in a path text only the invisible render operators count
			self.text_string.append(text)

	def render_text_inv(self, text):
		self.text_string.append(text)


	# Raster Image

	def raster_image(self, trafo, llx, lly, urx, ury, width, height,
						bits, mode, alpha, reserved, encoding, mask):
		if bits != 8 or mode not in (1, 3):
			self.add_message(_("Only images with 1 or 3 components "
								"and 8 bits/component supported"))
			self.skip_to_dsc("AI5_EndRaster")
			return
		decode = streamfilter.SubFileDecode(self.tokenizer.source,
											'%AI5_EndRaster')
		if encoding == 0:
			decode = streamfilter.HexDecode(decode)
		data_length = mode * width * height
		data = decode.read(data_length)
		#f = open("/tmp/dump.ppm", "w")
		#if mode == 1:
		#    f.write("P5\n%d %d\n255\n" % (width, height))
		#else:
		#    f.write("P6\n%d %d\n255\n" % (width, height))
		#f.write(data)
		#f.close()
		if mode == 1:
			mode = 'L'
		elif mode == 3:
			mode = 'RGB'
		elif mode == 4:
			mode == 'CMYK'
		image = Image.fromstring(mode, (width, height), data, 'raw', mode)
		self.image(image, apply(Trafo, tuple(trafo)))
		
	#

	def append_object(self, object):
		if self.composite_class == Document \
			and object.__class__ != Layer:
			self.begin_layer()
		self.composite_items.append(object)
		self.object = object

	#
	#

	def skip_to_dsc(self, *endcomments):
		next_dsc = self.tokenizer.next_dsc; split = string.split
		while 1:
			value = next_dsc()
			if not value:
				return
			if ':' in value:
				keyword, value = split(value, ':', 1)
			else:
				keyword = value
			if keyword in endcomments:
				return

	def read_prolog(self):
		next = self.tokenizer.next
		DSC = DSC_COMMENT; split = string.split
		while 1:
			token, value = next()
			if token == DSC:
				if ':' in value:
					keyword, value = split(value, ':', 1)
				else:
					keyword = value
				if keyword in ('EndProlog', 'BeginSetup'):
					return keyword
				if keyword[:14] == "AI5_FileFormat":
					self.format_version = string.atof(keyword[14:])
				elif keyword == 'BeginProcSet':
					# some ai files exported by corel draw don't have an
					# EndProcSet comment after a BeginProcSet...
					self.skip_to_dsc('EndProcSet', 'EndProlog')
				elif keyword == 'BeginResource':
					self.skip_to_dsc('EndResource', 'EndProlog')
				#elif keyword == 'Creator':
					## try to determine whether the file really is an
					## illustrator file as opposed to some other EPS
					## file. It seems that Illustrator itself only
					## accepts EPS files as illustrator files if they
					## contain "Adobe Illustrator" in their Create
					## DSC-comment
					#if string.find(value, "Adobe Illustrator") == -1:
						#self.add_message("This is probably not an"
											#" Illustrator file."
											#" Try embedding it as EPS")
			if token == END:
				return

	def Load(self):
		# Begin read EPS Binary File Header
		header = self.match.string[0:32]
		if header[0] == chr(0xC5):
			if len(header) < 32:
				header += self.file.read(32 - len(header))
			filetype, startPS, sizePS, startWMF, sizeWMF, \
			startTIFF, sizeTIFF, Checksum = unpack(struct_eps_header, header)
			self.file.seek(startPS)
		# End read EPS Binary File Header
	
		funclist = self.get_compiled()
		# binding frequently used functions to local variables speeds up
		# the process considerably...
		a = apply; t = tuple
		DSC = DSC_COMMENT; MAX = MAX_DATA_TOKEN; split = string.split
		stack = self.stack; push = self.stack.append
		unknown_operator = (None, None)

		decoder = streamfilter.StringDecode(self.match.string, self.file)
		self.tokenizer = PSTokenizer(decoder)
		self.tokenizer.ai_pseudo_comments = 1
		self.tokenizer.ai_dsc = 1
		next = self.tokenizer.next
		
		self.document()

		value = self.read_prolog()

		while 1:
			token, value = next()
			if token <= MAX:
				push(value)
			elif token == DSC:
				if ':' in value:
					keyword, value = split(value, ':', 1)
				else:
					keyword = value
				if keyword in ('PageTrailer', 'Trailer'):
					break
				elif keyword == 'AI5_BeginPalette':
					self.skip_to_dsc('AI5_EndPalette', 'EndSetup')
				elif keyword == "AI8_BeginBrushPattern":
					self.skip_to_dsc('AI8_EndBrushPattern', 'EndSetup')

			elif token == END:
				break
			elif token == OPERATOR:
				method, argc = funclist.get(value, unknown_operator)
				#if method is not None:
				#    name = method.__name__
				#else:
				#    name = `method`
				if method is None:
					del stack[:]
				else:
					try:
						if argc:
							args = t(stack[-argc:])
							del stack[-argc:]
							a(method, args)
						else:
							method()
					except:
						warn_tb(INTERNAL, 'AILoader: error')

		self.end_all()
		self.object.load_Completed()
		for obj in self.guides:
			self.object.guide_layer.Insert(obj, None)

		return self.object
