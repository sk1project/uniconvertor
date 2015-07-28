# -*- coding: utf-8 -*-

# Copyright (C) 2003-2008 by Igor Novikov
# Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
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
#type = Export
#tk_file_type = (_("sK1 Document"), '.sk1')
#extensions = '.sk1'
format_name = 'sK1'
#standard_messages = 1
###End


#
#	A class to save a document in sK1 format (sK1 own format)
#

#
# Functions used in an sk file:
#
# document()
#
#	Marks the beginning of the document. In the future, this
#	function may take some arguments that describe global properties
#	of the document
#
# layout(PAPER_FORMAT, ORIENTATION)
#
#	Defines the paper format. PAPER_FORMAT may be a string such 'A4'
#	or a tuple (WIDTH, HEIGHT) defining a non standard paper size.
#	ORIENTATION is 0 for portrait or 1 for landscape (see
#	pagelayout.py)
#
#
# Properties:
#
# gl([(POS1, COLOR1), (POS2, COLOR2), ...])
#
#	`gradient linear'
#
# pe()
#
#	`pattern empty'
#
# ps(COLOR)
#
#	`pattern solid'
#
# pgl(DX, DY, BORDER)
#
#	`pattern gradient linear'
#
# pgr(CX, CY, BORDER)
#
#	`pattern gradient radial'
#
# pgc(CX, CY, DX, DY)
#
#	`pattern gradient conical'
#
# phs(COLOR, BACKGROUND, DX, DY, GAP, WIDTH)
#
#	`pattern hatching simple'
#
# pit(ID, TRAFO)
#
#	`pattern image tile' (id as in `im')
#
# fp()	`fill pattern'
#
# fe()	`fill empty'
#
# ft(BOOL) `fill transform'
#
# lp()	`line pattern'
#
# le()	`line empty'
#
# lw()	`line width'
#
# lc(CAP)
#
#	`line cap'
#
# lj(JOIN)
#
#	`line join'
#
# ld(DASHES)
#
#	`line dashes'
#
# la1([ARROW])		# missing ARROW means explicit empty arrow
# la2([ARROW])
#
#	`line arrows'
#
# Fn(FONTNAME)
#
#	`font name'
#
# Fs(SIZE)
#
#	`font size'
#
# dstyle(NAME)
#
#	Define new dynamic style named NAME with the current properties
#
# style(name)
#
#	Use style NAME.
#
#
# Objects:
#
# layer(NAME, VISIBLE, PRINTABLE, LOCKED, OUTLINED, OUTLINE_COLOR)
#
#	Start a new layer named NAME.
#
# grid((XORIG, YORIG, XWIDTH, YWIDTH))
#
#	Insert the grid layer at this position and set the grid geometry.
#
# guidelayer(NAME, ...)
#
#	Start the guide layer
#
# guide(COORD, HOR)
#
#	Define a guide line. If HOR is true, it is horizontal, else it
#	is vertical. guide() is only allowed in a guide layer
#
# G()
# G_()
#
#	All objects defined between G() and the corresponding G_() are
#	part of a group. Groups may be nested.
#
# B()
# Bi(STEPS)
# B_()
#
#	A blend group
#
#
# M()
# M_()
#
#	A Mask group. the first object after M() is the mask
#
# PT()
# pt(TEXT[, MATRIX][, MODEL)
# PT_()
#
#	Text on a path. The path is the only object between the pt and
#	PT_ functions.
#
#
# b()
#	start a bezier obj
# bs(X, Y, CONT)			append a line segment
# bc(X1, Y1, X2, Y2, X3, Y3, CONT)	append a bezier segment
# bn()	start a new path
# bC()	close path
#
# r(TRAFO [, RADIUS1, RADIUS2])
#
#	Rectangle, described by the transformation needed to transform
#	the unit square into the rectangle.
#
# e(TRAFO, [start_angle, end_angle, arc_type])
#
#	Ellipse, described similarly to the rectangle.
#
# txt(TEXT, TRAFO[, HORIZ_ALIGN, VERT_ALIGN])
#
# bm(ID[, filename])
#
#	Bitmap image data. The bitmap data is either read from the file
#	given by filename of if that parameter is not present, follows
#	as a base64 encoded ppm file. (We should have compression here,
#	maybe by using png or a similar format)
#
# im(TRAFO, ID)
#
#	A bitmap image. ID has to be the id of a previously defined
#	bitmap data object (defined by bm).
#
# eps(TRAFO, FILENAME)
#
#	external EPS file
#
#
# PC(NAME[, arg1, arg2, ...][, kwarg, kwarg, ...])
# PC_()
#
#	A plugin compound object. The arguments to PC() should be
#	sufficient to describe the entire compound and to reconstruct
#	the objects in between PC and PC_. These contained objects are
#	meant for installations where the plugin is not available.


#
# Default properties in an sk-file:
#
#	Fill Properties:
#
#	fill_pattern	EmptyPattern
#	fill_transform	1
#
#	Line Properties:
#
#	line_pattern	solid black
#	line_width	0pt
#	line_join	JoinMiter
#	line_cap	CapButt
#	line_dashes	()
#
#	Font Properties:
#
#	font		None
#	font_size	12pt

#
#

import os

from uniconvertor.utils.fs import relpath
from uniconvertor.utils import Empty
from app import IdentityMatrix, EmptyPattern, SolidPattern, Style, \
		StandardColors, SketchError, const
from app.Graphics import properties, papersize
from app.Graphics.image import CMYK_IMAGE
from app.Lib.units import m_to_pt, in_to_pt



base_style = Style()
base_style.fill_pattern = EmptyPattern
base_style.fill_transform = 1
base_style.line_pattern = SolidPattern(StandardColors.black)
base_style.line_width = 0.0
base_style.line_join = const.JoinMiter
base_style.line_cap = const.CapButt
base_style.line_dashes = ()
base_style.line_arrow1 = None
base_style.line_arrow2 = None
base_style.font = None
base_style.font_size = 12.0

#papersizes = {
#	'A0': (0.841 * m_to_pt, 1.189 * m_to_pt),
#	'A1': (0.594 * m_to_pt, 0.841 * m_to_pt),
#	'A2': (0.420 * m_to_pt, 0.594 * m_to_pt),
#	'A3': (0.297 * m_to_pt, 0.420 * m_to_pt),
#	'A4': (0.210 * m_to_pt, 0.297 * m_to_pt),
#	'A5': (0.148 * m_to_pt, 0.210 * m_to_pt),
#	'A6': (0.105 * m_to_pt, 0.148 * m_to_pt),
#	'A7': (0.074 * m_to_pt, 0.105 * m_to_pt),
#	'letter': (8.5  * in_to_pt, 11   * in_to_pt),
#	'legal': (8.5  * in_to_pt, 14   * in_to_pt),
#	'executive': (7.25 * in_to_pt, 10.5 * in_to_pt)
#	}

def make_papersizes():
	result={}
	ps_list=papersize.PapersizesList
	for item in ps_list:
		result[item[0]]=(item[1],item[2])
	return result
	

papersizes = make_papersizes()


class SketchSaveError(SketchError):
	pass

def color_repr(color):
# 	return '(%g,%g,%g)' % tuple(color.RGB())
	return color.toSave()

default_options = {'full_blend' : 0}

class SKSaver:

	def __init__(self, file, filename, kw):
		self.file = file
		self.filename = filename
		if self.filename:
			self.directory = os.path.split(filename)[0]
		else:
			self.directory = ''
		self.style_dict = {}
		self.write_header()
		options = default_options.copy()
		options.update(kw)
		self.options = apply(Empty, (), options)
		self.saved_ids = {}

	def __del__(self):
		self.Close()

	def Close(self):
		pass
		#if not self.file.closed:
		#    self.file.close()

	def write_header(self):
		self.file.write('##sK1 1 2\n')

	def BeginDocument(self):
		self.file.write('document()\n')

	def EndDocument(self):
		pass

	def BeginLayer(self, name, visible, printable, locked, outlined, color):
		self.file.write('layer(%s,%d,%d,%d,%d,%s)\n'
						% (`name`, visible, printable, locked, outlined,
							color_repr(color)))	
		
	def BeginMasterLayer(self, name, visible, printable, locked, outlined, color):
		self.file.write('masterlayer(%s,%d,%d,%d,%d,%s)\n'
						% (`name`, visible, printable, locked, outlined,
							color_repr(color)))		

	def EndLayer(self):
		pass
	
	def Page(self,name, format, width, height, orientation):
		self.file.write('page(%s,%s,(%g,%g),%d)\n' % (`name`,`format`, width, height, orientation))

	def BeginGuideLayer(self, name, visible, printable, locked, outlined,
						color):
		self.file.write('guidelayer(%s,%d,%d,%d,%d,%s)\n'
						% (`name`, visible, printable, locked, outlined,
							color_repr(color)))
	EndGuideLayer = EndLayer

	def BeginGridLayer(self, geometry, visible, outline_color, name):
		self.file.write('grid((%g,%g,%g,%g),%d,%s,%s)\n'
						% (geometry
							+ (visible, color_repr(outline_color), `name`)))
	EndGridLayer = EndLayer

	def PageLayout(self, format, width, height, orientation):
		self.file.write('layout(%s,(%g,%g),%d)\n' % (`format`, width, height, orientation))
#		if format and papersizes.has_key(format):
#			self.file.write('layout(%s,%d)\n' % (`format`, orientation))
#		else:
#			self.file.write('layout((%g,%g),%d)\n'
#							% (width, height, orientation))

	def BeginGroup(self):
		self.file.write('G()\n')

	def EndGroup(self):
		self.file.write('G_()\n')

	def Gradient(self, colors):
		write = self.file.write
		write('gl([')
		write_comma = 0
		for pos, color in colors:
			if write_comma:
				write(',')
			else:
				write_comma = 1
			write('(%g,%s)' % (pos, color_repr(color)))
		write('])\n')

	def EmptyPattern(self):
		self.file.write('pe()\n')

	def SolidPattern(self, color):
		self.file.write('ps(%s)\n' % color_repr(color))

	def LinearGradientPattern(self, gradient, direction, border):
		gradient.SaveToFile(self)
		self.file.write('pgl(%g,%g,%g)\n'
						% (round(direction.x, 10), round(direction.y, 10),
							border))

	def RadialGradientPattern(self, gradient, center, border):
		gradient.SaveToFile(self)
		self.file.write('pgr(%g,%g,%g)\n' % (center.x, center.y, border))

	def ConicalGradientPattern(self, gradient, center, direction):
		gradient.SaveToFile(self)
		self.file.write('pgc(%g,%g,%g,%g)\n'
						% (tuple(center) + (round(direction.x, 10),
											round(direction.y, 10))))

	def HatchingPattern(self, color, background, direction, distance, width):
		self.file.write('phs(%s,%s,%g,%g,%g,%g)\n'
						% (color_repr(color), color_repr(background),
							direction.x, direction.y, distance, width))

	def ImageTilePattern(self, image, trafo, relative_filename = 1):
		self.write_image(image, relative_filename)
		self.file.write('pit(%d,(%g,%g,%g,%g,%g,%g))\n'
						% ((id(image),) + trafo.coeff()))

	def write_style(self, style):
		write = self.file.write
		if hasattr(style, 'fill_pattern'):
			pattern = style.fill_pattern
			if pattern is EmptyPattern:
				write('fe()\n')
			elif isinstance(pattern, SolidPattern):
				write('fp(%s)\n' % color_repr(pattern.Color()))
			else:
				pattern.SaveToFile(self)
				write('fp()\n')
		if hasattr(style, 'fill_transform'):
			write('ft(%d)\n' % style.fill_transform)
		if hasattr(style, 'line_pattern'):
			pattern = style.line_pattern
			if pattern is EmptyPattern:
				write('le()\n')
			elif isinstance(pattern, SolidPattern):
				write('lp(%s)\n' % color_repr(pattern.Color()))
			else:
				pattern.SaveToFile(self)
				write('lp()\n')
		if hasattr(style, 'line_width') :
			write('lw(%g)\n' % style.line_width)
		if hasattr(style, 'line_cap'):
			write('lc(%d)\n' % style.line_cap)
		if hasattr(style, 'line_join'):
			write('lj(%d)\n' % style.line_join)
		if hasattr(style, 'line_dashes'):
			write('ld(%s)\n' % `style.line_dashes`)
		if hasattr(style, 'line_arrow1'):
			if style.line_arrow1 is not None:
				write('la1(%s)\n' % `style.line_arrow1.SaveRepr()`)
			else:
				write('la1()\n')
		if hasattr(style, 'line_arrow2'):
			if style.line_arrow2 is not None:
				write('la2(%s)\n' % `style.line_arrow2.SaveRepr()`)
			else:
				write('la2()\n')
		if hasattr(style, 'font'):
			write('Fn(%s)\n' % `style.font.PostScriptName()`)
		if hasattr(style, 'font_size'):
			write('Fs(%g)\n' % style.font_size)

	def DynamicStyle(self, style):
		self.write_style(style)
		self.file.write('dstyle(%s)\n' % `style.Name()`)

	def write_style_no_defaults(self, style):
		style = style.Copy()
		for key, value in base_style.__dict__.items():
			if hasattr(style, key) and getattr(style, key) == value:
				delattr(style, key)
		self.write_style(style)

	def Properties(self, properties):
		styles = properties.stack[:]
		styles.reverse()
		if styles[0].is_dynamic:
			self.file.write('style(%s)\n' % `style[0].Name()`)
		else:
			self.write_style_no_defaults(styles[0])
		for style in styles[1:]:
			if style.is_dynamic:
				self.file.write('style(%s)\n' % `style.Name()`)
			else:
				self.write_style(style)

	def Rectangle(self, trafo, radius1 = 0, radius2 = 0):
		if radius1 == radius2 == 0:
			self.file.write('r(%g,%g,%g,%g,%g,%g)\n' % trafo.coeff())
		else:
			self.file.write('r(%g,%g,%g,%g,%g,%g,%g,%g)\n'
							% (trafo.coeff() + (radius1, radius2)))

	def Ellipse(self, trafo, start_angle, end_angle, arc_type):
		if start_angle == end_angle:
			self.file.write('e(%g,%g,%g,%g,%g,%g)\n' % trafo.coeff())
		else:
			self.file.write('e(%g,%g,%g,%g,%g,%g,%g,%g,%d)\n'
							% (trafo.coeff()+(start_angle,end_angle,arc_type)))


	def PolyBezier(self, paths):
		write = self.file.write
		write('b()\n')
		for path in paths:
			if path is not paths[0]:
				write('bn()\n')
			try:
				path.write_to_file(self.file)
			except TypeError:
				# self.file is no ordinary file (not tested!)
				list = path.get_save()
				for item in list:
					if len(item) == 3:
						write('bs(%g,%g,%d)\n' % item)
					elif len(item) == 7:
						write('bc(%g,%g,%g,%g,%g,%g,%d)\n' % item)
					else:
						raise SketchSaveError('got invalid item: ' + `item`)
			if path.closed:
				write("bC()\n")

	def SimpleText(self, text, trafo, halign, valign, chargap, wordgap, linegap):
		text = self.unicode_encoder(text)
		write = self.file.write
		write('txt(%s,' % `text`)
		if trafo.matrix() != IdentityMatrix:
			write('(%g,%g,%g,%g,%g,%g)' % trafo.coeff())
		else:
			write('(%g,%g)' % (trafo.v1, trafo.v2))		
		write(',%d,%d' % (halign, valign))
		write(',%g,%g,%g' % (chargap, wordgap, linegap))
		
		write(')\n')
		
	def unicode_encoder(self, text):
		output=''
		for char in text:
			output+='\u0%x'%ord(char)
		return output

	def write_image(self, image, relative_filename = 1):
		write = self.file.write
		if not self.saved_ids.has_key(id(image)):
			imagefile = image.Filename()
			if not imagefile:
				from streamfilter import Base64Encode
				write('bm(%d)\n' % id(image))
				file = Base64Encode(self.file)
				if image.image_mode == CMYK_IMAGE:
					image.orig_image.save(file, 'JPEG', quality=100)
				else:
					image.orig_image.save(file, 'PNG')
				file.close()
				write('-\n')
			else:
				if self.directory and relative_filename:
					imagefile = relpath(self.directory, imagefile)
				write('bm(%d,%s)\n' % (id(image), `imagefile`))
			self.saved_ids[id(image)] = image

	def Image(self, image, trafo, relative_filename = 1):
		self.write_image(image, relative_filename)

		write = self.file.write
		write('im(')
		if trafo.matrix() != IdentityMatrix:
			write('(%g,%g,%g,%g,%g,%g)' % trafo.coeff())
		else:
			write('(%g,%g)' % (trafo.v1, trafo.v2))
		write(',%d)\n' % id(image))

	def EpsFile(self, data, trafo, relative_filename = 1):
		write = self.file.write
		write('eps(')
		if trafo.matrix() != IdentityMatrix:
			write('(%g,%g,%g,%g,%g,%g)' % trafo.coeff())
		else:
			write('(%g,%g)' % (trafo.v1, trafo.v2))
		filename = data.Filename()
		if self.directory and relative_filename:
			filename = relpath(self.directory, filename)
		write(',%s)\n' % `filename`)

	def BeginBlendGroup(self):
		self.file.write('B()\n')

	def EndBlendGroup(self):
		self.file.write('B_()\n')

	def BeginBlendInterpolation(self, steps):
		self.file.write('blendinter(%d)\n' % steps)

	def EndBlendInterpolation(self):
		self.file.write('endblendinter()\n')

	def BlendInterpolation(self, steps):
		self.file.write('Bi(%d)\n' % steps)

	def BeginMaskGroup(self):
		self.file.write('M()\n')

	def EndMaskGroup(self):
		self.file.write('M_()\n')

	def BeginPathText(self):
		self.file.write('PT()\n')

	def InternalPathText(self, text, trafo, model, start_pos = 0):
		matrix = trafo.matrix()
		if matrix != IdentityMatrix:
			self.file.write('pt(%s,(%g,%g,%g,%g),%d'
							% ((`text`,) + matrix + (model,)))
		else:
			self.file.write('pt(%s,%d' % (`text`, model))
		if start_pos > 0:
			self.file.write(',%g)\n' % start_pos)
		else:
			self.file.write(')\n')

	def EndPathText(self):
		self.file.write('PT_()\n')

	def GuideLine(self, point, horizontal):
		if horizontal:
			args = point.y, 1
		else:
			args = point.x, 0
		self.file.write('guide(%g,%d)\n' % args)

	def BeginPluginCompound(self, plugin_name, *args, **kw):
		write = self.file.write
		write('PC(%s' % `plugin_name`)
		for arg in args:
			write(',%s' % `arg`)
		for key, value in kw.items():
			write(',%s=%s' % (key, `value`))
		write(')\n')

	def EndPluginCompound(self):
		self.file.write('PC_()\n')


def save(document, file, filename, options = {}):
	saver = SKSaver(file, filename, options)
	document.SaveToFile(saver)
	
