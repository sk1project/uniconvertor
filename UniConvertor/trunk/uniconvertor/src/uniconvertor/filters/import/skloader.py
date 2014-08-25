# -*- coding: utf-8 -*-
# Sketch - A Python-based interactive drawing program
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

###Sketch Config
#type = Import
#class_name = 'SKLoader'
#rx_magic = '^##Sketch 1 *(?P<minor>[0-9]+)'
#tk_file_type = ('Sketch Document', '.sk')
format_name = 'SK'
#standard_messages = 1
###End

(''"Sketch Document")

from types import StringType, TupleType
import os, sys
from string import atoi

from app.events.warn import warn, INTERNAL, pdebug, warn_tb

from app import SketchLoadError, SketchError
from sk1libs import filters
from app.io import load
from app.conf import const
from app import CreateRGBColor, SolidPattern, HatchingPattern,EmptyPattern,\
		LinearGradient, ConicalGradient, RadialGradient, ImageTilePattern, \
		Style, MultiGradient, Trafo, Translation, Point, \
		GridLayer, GuideLayer, GuideLine, Arrow, CreatePath, StandardColors, \
		GetFont

from app.io.load import GenericLoader

from app.Graphics import pagelayout, plugobj, blendgroup, text, image, eps, properties

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

# sanity check: does base_style have all properties?
for key in dir(properties.factory_defaults):
	if not hasattr(base_style, key):
		#warn(INTERNAL, 'added default for property %s', key)
		setattr(base_style, key, getattr(properties.factory_defaults, key))

papersizes = [#    'A0', 'A1', 'A2',
	'A3', 'A4', 'A5', 'A6', 'A7',
	'letter', 'legal', 'executive',
	]

		
class SKLoader(GenericLoader):

	format_name = format_name

	base_style = base_style

	functions = ['document', 'layer', ('bezier', 'b'), ('rectangle', 'r'),
					('ellipse', 'e'),
					'group', ('group', 'G'), 'endgroup', ('endgroup', 'G_'),
					'guess_cont']

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		if atoi(match.group('minor')) > 2:
			self.add_message(_("The file was created by a newer version"
								" of Sketch, there might be inaccuracies."))
		if self.filename:
			self.directory = os.path.split(filename)[0]
		else:
			self.directory = ''
		self.style_dict = {}
		self.id_dict = {}
		self.page_layout = None
		self.pattern = None
		self.gradient = None
		self.arrow1 = None
		self.arrow2 = None
		self.font = None
		self.font_size = 1.0
		self.color_cache = {}

	def __del__(self):
		pass

	def warn(self, level, *args, **kw):
		message = apply(warn, (level,) + args, kw)
		self.add_message(message)

	def get_func_dict(self):
		func_dict = {}
		for name in self.functions:
			if type(name) == StringType:
				func_dict[name] = getattr(self, name)
			else:
				func_dict[name[1]] = getattr(self, name[0])
		return func_dict

	functions.append('layout')
	def layout(self, format, orientation):
		if type(format) == StringType:
			if format not in papersizes:
				# The format is given by name but it's not one of the
				# standard papersizes. The file may be corrupted.
				self.add_message(_("Unknown paper format '%s', "
									"using A4 instead") % format)
				format = "A4"
			layout = pagelayout.PageLayout(format, orientation=orientation)
		else:
			w, h = format
			layout = pagelayout.PageLayout(width = w, height = h,
											orientation = orientation)
		self.page_layout = layout

	functions.append('grid')
	def grid(self, geometry, visible = 0, color = None, name = None):
		if name is None:
			name = _("Grid")
		self.begin_layer_class(GridLayer,
								(geometry, visible, self.convert_color(color),
								name))
		self.end_composite()

	def convert_color(self, color_spec):
		try:
			c = self.color_cache.get(color_spec)
			if c:
				return c
			c = apply(CreateRGBColor, color_spec)
			self.color_cache[color_spec] = c
		except:
			# This should only happen if the color_spec is invalid
			type, value = sys.exc_info()[:2]
			warn(INTERNAL, 'Color allocation failed: %s: %s', type, value)
			c = StandardColors.black
		return c

	functions.append('gl')
	def gl(self, colors):
		c = []
		for pos, color in colors:
			c.append((pos, self.convert_color(color)))
		self.gradient = MultiGradient(c)

	functions.append('pe')
	def pe(self):
		self.pattern = EmptyPattern

	functions.append('ps')
	def ps(self, color):
		self.pattern = SolidPattern(self.convert_color(color))

	functions.append('pgl')
	def pgl(self, dx, dy, border = 0):
		if not self.gradient:
			raise SketchLoadError(_("No gradient for gradient pattern"))
		self.pattern = LinearGradient(self.gradient, Point(dx, dy), border)

	functions.append('pgr')
	def pgr(self, dx, dy, border = 0):
		if not self.gradient:
			raise SketchLoadError(_("No gradient for gradient pattern"))
		self.pattern = RadialGradient(self.gradient, Point(dx, dy), border)

	functions.append('pgc')
	def pgc(self, cx, cy, dx, dy):
		if not self.gradient:
			raise SketchLoadError(_("No gradient for gradient pattern"))
		self.pattern = ConicalGradient(self.gradient,
										Point(cx, cy), Point(dx, dy))

	functions.append('phs')
	def phs(self, color, background, dx, dy, dist, width):
		self.pattern = HatchingPattern(self.convert_color(color),
										self.convert_color(background),
										Point(dx, dy), dist, width)

	functions.append('pit')
	def pit(self, id, trafo):
		trafo = apply(Trafo, trafo)
		self.pattern = ImageTilePattern(self.id_dict[id], trafo)

	functions.append('fp')
	def fp(self, color = None):
		if color is None:
			self.style.fill_pattern =  self.pattern
		else:
			self.style.fill_pattern = SolidPattern(self.convert_color(color))

	functions.append('fe')
	def fe(self):
		self.style.fill_pattern =  EmptyPattern

	functions.append('ft')
	def ft(self, bool):
		self.style.fill_transform =  bool

	functions.append('lp')
	def lp(self, color = None):
		if color is None:
			self.style.line_pattern = self.pattern
		else:
			self.style.line_pattern = SolidPattern(self.convert_color(color))

	functions.append('le')
	def le(self):
		self.style.line_pattern = EmptyPattern

	functions.append('lw')
	def lw(self, width):
		self.style.line_width = width

	functions.append('lj')
	def lj(self, join):
		self.style.line_join = join

	functions.append('lc')
	def lc(self, cap):
		if not 1 <= cap <= 3:
			self.add_message('line cap corrected from %d to 1' % cap)
			cap = 1
		self.style.line_cap = cap

	functions.append('ld')
	def ld(self, dashes):
		self.style.line_dashes = dashes

	functions.append('la1')
	def la1(self, args = None):
		if args is not None:
			self.style.line_arrow1 = apply(Arrow, args)
		else:
			self.style.line_arrow1 = None

	functions.append('la2')
	def la2(self, args = None):
		if args is not None:
			self.style.line_arrow2 = apply(Arrow, args)
		else:
			self.style.line_arrow2 = None

	functions.append('dstyle')
	def dstyle(self, name = ''):
		if not name:
			raise SketchLoadError(_("unnamed style"))
		style = self.style.AsDynamicStyle()
		style.SetName(name)
		self.style_dict[name] = style
		self.style = Style()

	functions.append(('use_style', 'style'))
	def use_style(self, name = ''):
		if not name:
			raise SketchLoadError(_("unnamed style"))
		if not self.style.IsEmpty():
			self.prop_stack.load_AddStyle(self.style)
			self.style = Style()
		style = self.style_dict[name]
		self.prop_stack.load_AddStyle(style)

	functions.append('Fn')
	def Fn(self, name):
		self.style.font = GetFont(name)

	functions.append('Fs')
	def Fs(self, size):
		self.style.font_size = size

	functions.append('guide')
	def guide(self, pos, horizontal):
		if horizontal:
			p = Point(0, pos)
		else:
			p = Point(pos, 0)
		self.append_object(GuideLine(p, horizontal))

	functions.append('guidelayer')
	def guidelayer(self, *args, **kw):
		self.begin_layer_class(GuideLayer, args, kw)

	def bezier_load(self, line):
		bezier = self.object
		while 1:
			try:
				bezier.paths[-1].append_from_string(line)
				line = bezier.paths[-1].append_from_file(self.file)
			except:
				warn(INTERNAL, _("Error reading line %s"), `line`)
				line = self.file.readline()
			if line[:2] == 'bC':
				bezier.paths[-1].load_close()
				line = self.file.readline()
			if line[:2] == 'bn':
				bezier.paths = bezier.paths + (CreatePath(),)
				line = self.file.readline()
			else:
				break
			if line[:2] not in ('bs', 'bc'):
				break
		return line

	functions.append('txt')
	def txt(self, thetext, trafo, halign = text.ALIGN_LEFT,
			valign = text.ALIGN_BASE):
		if len(trafo) == 2:
			trafo = Translation(trafo)
		else:
			trafo = apply(Trafo, trafo)
		object = text.SimpleText(text = thetext, trafo = trafo,
									halign = halign, valign = valign,
									properties = self.get_prop_stack())
		self.append_object(object)

	functions.append('im')
	def im(self, trafo, id):
		if len(trafo) == 2:
			trafo = Translation(trafo)
		else:
			trafo = apply(Trafo, trafo)
		if self.id_dict[id] is not None:
			self.append_object(image.Image(self.id_dict[id], trafo = trafo))

	functions.append('bm')
	def bm(self, id, filename = None):
		if filename is None:
			from streamfilter import Base64Decode, SubFileDecode
			decoder = Base64Decode(SubFileDecode(self.file, '-'))
			data = image.load_image(decoder)
		elif os.path.isfile(os.path.join(self.directory, filename)):
			data = image.load_image(os.path.join(self.directory, filename))
		else:
			self.add_message(_("File not found: %s") % os.path.join(self.directory, filename))
			data = None
		self.id_dict[id] = data

	functions.append('eps')
	def eps(self, trafo, filename):
		if len(trafo) == 2:
			trafo = Translation(trafo)
		else:
			trafo = apply(Trafo, trafo)
		if not os.path.isabs(filename):
			if self.directory:
				filename = os.path.join(self.directory, filename)
			else:
				filename = os.path.join(os.getcwd(), filename)
		self.append_object(eps.EpsImage(filename = filename, trafo = trafo))

	functions.append('B')
	def B(self, *args, **kw):
		self.begin_composite(blendgroup.BlendGroup, args, kw)

	functions.append('B_')
	def B_(self):
		self.end_composite()

	functions.append('Bi')
	def Bi(self, *args, **kw):
		self.begin_composite(blendgroup.BlendInterpolation, args, kw)
		self.end_composite()

	group = GenericLoader.begin_group
	endgroup = GenericLoader.end_group

	functions.append('M')
	def M(self, *args, **kw):
		from app.Graphics import maskgroup
		self.begin_composite(maskgroup.MaskGroup, args, kw)

	functions.append('M_')
	def M_(self):
		self.end_composite()

	functions.append('PT')
	def PT(self, *args, **kw):
		self.begin_composite(text.PathText, args, kw)

	functions.append('pt')
	def pt(self, thetext, *args):
		matrix = ()
		model = text.PATHTEXT_ROTATE
		start_pos = 0.0
		if args:
			if type(args[0]) == TupleType:
				matrix = args[0]
				args = args[1:]
			if args:
				model = args[0]
				if len(args) > 1:
					start_pos = args[1]

		if matrix:
			trafo = apply(Trafo, matrix)
		else:
			trafo = None

		self.append_object(text.InternalPathText(thetext, trafo = trafo,
													model = model,
													start_pos = start_pos,
											properties = self.get_prop_stack()))

	functions.append('PT_')
	def PT_(self):
		self.end_composite()

	functions.append('PC')
	def PC(self, class_name, *args, **kw):
		kw['loading'] = 1
		info = filters.find_object_plugin(class_name)
		if info is not None:
			try:
				theclass = info.Constructor()
				self.begin_composite(theclass, args, kw)
				return
			except SketchError:
				pass
		# constructing the plugin object failed. Use an UnknownPlugin
		# object.
		self.add_message(_("Unknown Plugin: %s") % class_name)
		self.begin_composite(plugobj.UnknownPlugin, (class_name,) + args, kw)

	functions.append('PC_')
	def PC_(self):
		self.end_composite()

	#
	#	The loader driver
	#

	def Load(self):
		file = self.file
		if type(file) == StringType:
			file = open(file, 'r')
		dict = self.get_func_dict()
		from app import skread
		parse = skread.parse_sk_line2
		readline = file.readline
		bezier_load = self.bezier_load
		num = 1
		line = '#'
		if __debug__:
			import time
			start_time = time.clock()
		try:
			line = readline()
			while line:
				num = num + 1
				if line[0] == 'b' and line[1] in 'sc':
					line = bezier_load(line)
					continue
				#parse(line, dict)
				funcname, args, kwargs = parse(line)
				if funcname is not None:
					function = dict.get(funcname)
					if function is not None:
						try:
							apply(function, args, kwargs)
						except TypeError:
							tb = sys.exc_info()[2]
							try:
								if tb.tb_next is None:
									# the exception was raised by apply
									# and not within the function. Try to
									# invoke the function with fewer
									# arguments
									if call_function(function, args, kwargs):
										message = _("Omitted some arguments "
													"for function %s")
									else:
										message = _("Cannot call function %s")
									self.add_message(message
														% function.__name__)

								else:
									raise
							finally:
								del tb
					else:
						self.add_message(_("Unknown function %s") % funcname)
					
				line = readline()

		except (SketchLoadError, SyntaxError), value:
			# a loader specific error occurred
			warn_tb(INTERNAL, 'error in line %d', num)
			if load._dont_handle_exceptions:
				raise
			else:
				raise SketchLoadError('%d:%s' % (num, value))
		except:
			# An exception was not converted to a SketchLoadError.
			# This should be considered a bug.
			warn_tb(INTERNAL, 'error in line %d:\n%s', num, `line`)
			if load._dont_handle_exceptions:
				raise
			else:
				raise SketchLoadError(_("error %s:%s in line %d:\n%s")
										% (sys.exc_info()[:2] +(num, `line`)))

		self.end_all()
		if self.page_layout:
			self.object.load_SetLayout(self.page_layout)
		for style in self.style_dict.values():
			self.object.load_AddStyle(style)
		self.object.load_Completed()

		self.object.meta.native_format = 1

		if __debug__:
			pdebug('timing', 'time:', time.clock() - start_time)
		return self.object


def call_function(function, args, kwargs):
	if hasattr(function, 'im_func'):
		args = (function.im_self,) + args
		function = function.im_func
	code = function.func_code
	if code.co_flags & 0x000C:
		# uses *args or **kwargs
		return 0
	args = args[:code.co_argcount]
	argnames = code.co_varnames[:code.co_argcount]
	for key in kwargs.keys():
		if key not in argnames:
			del kwargs[key]
	try:
		apply(function, args, kwargs)
	except:
		warn_tb(INTERNAL, 'Trying to call function %s with reduced arglist',
				function.func_name)
		return 0
	return 1
