# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor E. Novikov
# Copyright (C) 1997, 1998, 2001 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

###Sketch Config
#type = Import
#class_name = 'SVGLoader'
#rx_magic = '.*\\<(\\?xml|svg)'
#tk_file_type = ('Scalable Vector Graphics (SVG)', ('.svg', '.xml'))
format_name = 'SVG'
#unload = 1
###End

from types import StringType
from math import pi, tan
import os, sys
import re
from string import strip, split, atoi, lower
import string
import operator

import streamfilter

from app import Document, Layer, CreatePath, ContSmooth, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient,\
		CreateRGBColor, CreateCMYKColor, MultiGradient, \
		Trafo, Translation, Rotation, Scale, Point, Polar, \
		StandardColors, GetFont, PathText, SimpleText, const, UnionRects, \
		Bezier, Line, load_image, skread

from app.events.warn import INTERNAL, USER, warn_tb

from app.io.load import GenericLoader, EmptyCompositeError

from app.Graphics import text, properties

from xml.sax import handler
import xml.sax
from xml.sax.xmlreader import InputSource

# beginning with Python 2.0, the XML modules return Unicode strings,
# while for older versions they're 'normal' 8-bit strings. Provide some
# functions to make this code work with both string types.

def as_latin1(s):
	# convert the string s to iso-latin-1 if it's a unicode string
	encode = getattr(s, "encode", None)
	if encode is not None:
		s = encode("iso-8859-1", "replace")
	return s


# Conversion factors to convert standard CSS/SVG units to userspace
# units.
factors = {'pt': 1.0, 'px': 1.0, 'in': 72.0,
			'cm': 72.0 / 2.54, 'mm': 7.20 / 2.54}

degrees = pi / 180.0


def csscolor(str):
	str = strip(str)
	if str[0] == '#':
		if len(str) == 7:
			r = atoi(str[1:3], 16) / 255.0
			g = atoi(str[3:5], 16) / 255.0
			b = atoi(str[5:7], 16) / 255.0
		elif len(str) == 4:
			# According to the CSS rules a single HEX digit is to be
			# treated as a repetition of the digit, so that for a digit
			# d the value is (16 * d + d) / 255.0 which is equal to d / 15.0
			r = atoi(str[1], 16) / 15.0
			g = atoi(str[2], 16) / 15.0
			b = atoi(str[3], 16) / 15.0
		color = CreateRGBColor(r, g, b)
	elif namedcolors.has_key(str):
		color = namedcolors[str]
	else:
		color = StandardColors.black
	return color


namedcolors = {
	'aliceblue': csscolor('#f0f8ff'),
	'antiquewhite': csscolor('#faebd7'),
	'aqua': csscolor('#00ffff'),
	'aquamarine': csscolor('#7fffd4'),
	'azure': csscolor('#f0ffff'),
	'beige': csscolor('#f5f5dc'),
	'bisque': csscolor('#ffe4c4'),
	'black': csscolor('#000000'),
	'blanchedalmond': csscolor('#ffebcd'),
	'blue': csscolor('#0000ff'),
	'blueviolet': csscolor('#8a2be2'),
	'brown': csscolor('#a52a2a'),
	'burlywood': csscolor('#deb887'),
	'cadetblue': csscolor('#5f9ea0'),
	'chartreuse': csscolor('#7fff00'),
	'chocolate': csscolor('#d2691e'),
	'coral': csscolor('#ff7f50'),
	'cornflowerblue': csscolor('#6495ed'),
	'cornsilk': csscolor('#fff8dc'),
	'crimson': csscolor('#dc143c'),
	'cyan': csscolor('#00ffff'),
	'darkblue': csscolor('#00008b'),
	'darkcyan': csscolor('#008b8b'),
	'darkgoldenrod': csscolor('#b8860b'),
	'darkgray': csscolor('#a9a9a9'),
	'darkgreen': csscolor('#006400'),
	'darkgrey': csscolor('#a9a9a9'),
	'darkkhaki': csscolor('#bdb76b'),
	'darkmagenta': csscolor('#8b008b'),
	'darkolivegreen': csscolor('#556b2f'),
	'darkorange': csscolor('#ff8c00'),
	'darkorchid': csscolor('#9932cc'),
	'darkred': csscolor('#8b0000'),
	'darksalmon': csscolor('#e9967a'),
	'darkseagreen': csscolor('#8fbc8f'),
	'darkslateblue': csscolor('#483d8b'),
	'darkslategray': csscolor('#2f4f4f'),
	'darkslategrey': csscolor('#2f4f4f'),
	'darkturquoise': csscolor('#00ced1'),
	'darkviolet': csscolor('#9400d3'),
	'deeppink': csscolor('#ff1493'),
	'deepskyblue': csscolor('#00bfff'),
	'dimgray': csscolor('#696969'),
	'dimgrey': csscolor('#696969'),
	'dodgerblue': csscolor('#1e90ff'),
	'firebrick': csscolor('#b22222'),
	'floralwhite': csscolor('#fffaf0'),
	'forestgreen': csscolor('#228b22'),
	'fuchsia': csscolor('#ff00ff'),
	'gainsboro': csscolor('#dcdcdc'),
	'ghostwhite': csscolor('#f8f8ff'),
	'gold': csscolor('#ffd700'),
	'goldenrod': csscolor('#daa520'),
	'gray': csscolor('#808080'),
	'green': csscolor('#008000'),
	'greenyellow': csscolor('#adff2f'),
	'grey': csscolor('#808080'),
	'honeydew': csscolor('#f0fff0'),
	'hotpink': csscolor('#ff69b4'),
	'indianred': csscolor('#cd5c5c'),
	'indigo': csscolor('#4b0082'),
	'ivory': csscolor('#fffff0'),
	'khaki': csscolor('#f0e68c'),
	'lavender': csscolor('#e6e6fa'),
	'lavenderblush': csscolor('#fff0f5'),
	'lawngreen': csscolor('#7cfc00'),
	'lemonchiffon': csscolor('#fffacd'),
	'lightblue': csscolor('#add8e6'),
	'lightcoral': csscolor('#f08080'),
	'lightcyan': csscolor('#e0ffff'),
	'lightgoldenrodyellow': csscolor('#fafad2'),
	'lightgray': csscolor('#d3d3d3'),
	'lightgreen': csscolor('#90ee90'),
	'lightgrey': csscolor('#d3d3d3'),
	'lightpink': csscolor('#ffb6c1'),
	'lightsalmon': csscolor('#ffa07a'),
	'lightseagreen': csscolor('#20b2aa'),
	'lightskyblue': csscolor('#87cefa'),
	'lightslategray': csscolor('#778899'),
	'lightslategrey': csscolor('#778899'),
	'lightsteelblue': csscolor('#b0c4de'),
	'lightyellow': csscolor('#ffffe0'),
	'lime': csscolor('#00ff00'),
	'limegreen': csscolor('#32cd32'),
	'linen': csscolor('#faf0e6'),
	'magenta': csscolor('#ff00ff'),
	'maroon': csscolor('#800000'),
	'mediumaquamarine': csscolor('#66cdaa'),
	'mediumblue': csscolor('#0000cd'),
	'mediumorchid': csscolor('#ba55d3'),
	'mediumpurple': csscolor('#9370db'),
	'mediumseagreen': csscolor('#3cb371'),
	'mediumslateblue': csscolor('#7b68ee'),
	'mediumspringgreen': csscolor('#00fa9a'),
	'mediumturquoise': csscolor('#48d1cc'),
	'mediumvioletred': csscolor('#c71585'),
	'midnightblue': csscolor('#191970'),
	'mintcream': csscolor('#f5fffa'),
	'mistyrose': csscolor('#ffe4e1'),
	'moccasin': csscolor('#ffe4b5'),
	'navajowhite': csscolor('#ffdead'),
	'navy': csscolor('#000080'),
	'oldlace': csscolor('#fdf5e6'),
	'olive': csscolor('#808000'),
	'olivedrab': csscolor('#6b8e23'),
	'orange': csscolor('#ffa500'),
	'orangered': csscolor('#ff4500'),
	'orchid': csscolor('#da70d6'),
	'palegoldenrod': csscolor('#eee8aa'),
	'palegreen': csscolor('#98fb98'),
	'paleturquoise': csscolor('#afeeee'),
	'palevioletred': csscolor('#db7093'),
	'papayawhip': csscolor('#ffefd5'),
	'peachpuff': csscolor('#ffdab9'),
	'peru': csscolor('#cd853f'),
	'pink': csscolor('#ffc0cb'),
	'plum': csscolor('#dda0dd'),
	'powderblue': csscolor('#b0e0e6'),
	'purple': csscolor('#800080'),
	'red': csscolor('#ff0000'),
	'rosybrown': csscolor('#bc8f8f'),
	'royalblue': csscolor('#4169e1'),
	'saddlebrown': csscolor('#8b4513'),
	'salmon': csscolor('#fa8072'),
	'sandybrown': csscolor('#f4a460'),
	'seagreen': csscolor('#2e8b57'),
	'seashell': csscolor('#fff5ee'),
	'sienna': csscolor('#a0522d'),
	'silver': csscolor('#c0c0c0'),
	'skyblue': csscolor('#87ceeb'),
	'slateblue': csscolor('#6a5acd'),
	'slategray': csscolor('#708090'),
	'slategrey': csscolor('#708090'),
	'snow': csscolor('#fffafa'),
	'springgreen': csscolor('#00ff7f'),
	'steelblue': csscolor('#4682b4'),
	'tan': csscolor('#d2b48c'),
	'teal': csscolor('#008080'),
	'thistle': csscolor('#d8bfd8'),
	'tomato': csscolor('#ff6347'),
	'turquoise': csscolor('#40e0d0'),
	'violet': csscolor('#ee82ee'),
	'wheat': csscolor('#f5deb3'),
	'white': csscolor('#ffffff'),
	'whitesmoke': csscolor('#f5f5f5'),
	'yellow': csscolor('#ffff00'),
	'yellowgreen': csscolor('#9acd32'),
}

join = {'miter': const.JoinMiter,
		'round': const.JoinRound,
		'bevel': const.JoinBevel}
cap = {'butt': const.CapButt,
		'round': const.CapRound,
		'square': const.CapProjecting}

commatospace = string.maketrans(',', ' ')

rx_command = re.compile(r'[a-df-zA-DF-Z]((\s*[-0-9.e]+)*)\s*')
rx_trafo = re.compile(r'\s*([a-zA-Z]+)\(([^)]*)\)')

class SVGHandler(handler.ContentHandler):

	dispatch_start = {'svg': 'initsvg',
						'g': 'begin_group',
						'circle': 'circle',
						'ellipse': 'ellipse',
						'rect': 'rect',
						'polyline': 'polyline',
						'polygon': 'polygon',
						'path':   'begin_path',
						'text':   'begin_text',
						'image':   'image',
						'data':   'data',
						'use':   'use',
						'defs':   'begin_defs',
						}
	dispatch_end = {'g': 'end_group',
					'path': 'end_path',
					'defs': 'end_defs',
					'text': 'end_text'
					}
	
	def __init__(self, loader):
		self.loader = loader
		self.trafo = self.basetrafo = Trafo()
		self.state_stack = ()
		self.style = loader.style.Copy()
		self.style.line_pattern = EmptyPattern
		self.style.fill_pattern = SolidPattern(StandardColors.black)
		self.current_text = ""
		#self.style.font = GetFont("Times-Roman")
		self.style.font_size = 12
		self.halign = text.ALIGN_LEFT
		self.named_objects = {}
		self.in_defs = 0
		self.paths = None
		self.path = None
		self.depth = 0
		self.indent = '    '

	def _print(self, *args):
		return
		if args:
			print self.depth * self.indent + args[0],
		for s in args[1:]:
			print s,
		print

	def parse_transform(self, trafo_string):
		trafo = self.trafo
		#print trafo
		trafo_string = as_latin1(trafo_string)
		while trafo_string:
			#print trafo_string
			match = rx_trafo.match(trafo_string)
			if match:
				function = match.group(1)
				args = string.translate(match.group(2), commatospace)
				args = map(float, split(args))
				trafo_string = trafo_string[match.end(0):]
				if function == 'matrix':
					trafo = trafo(apply(Trafo, tuple(args)))
				elif function == 'scale':
					trafo = trafo(Scale(args[0]))
				elif function == 'translate':
					dx, dy = args
					trafo = trafo(Translation(dx, dy))
				elif function == 'rotate':
					trafo = trafo(Rotation(args[0] * degrees))
				elif function == 'skewX':
					trafo = trafo(Trafo(1, 0, tan(args[0] * degrees), 1, 0, 0))
				elif function == 'skewY':
					trafo = trafo(Trafo(1, tan(args[0] * degrees), 0, 1, 0, 0))
			else:
				trafo_string = ''
		#print trafo
		self.trafo = trafo

	def startElement(self, name, attrs):
		self._print('(', name)
		for key, value in attrs.items():
			self._print('  -', key, `value`)
		self.depth = self.depth + 1
		self.push_state()
		if attrs.has_key('transform'):
			self.parse_transform(attrs['transform'])
		self._print("applied transormation", self.trafo)
		method = self.dispatch_start.get(name)
		if method is not None:
			getattr(self, method)(attrs)
		
	def endElement(self, name):
		self.depth = self.depth - 1
		self._print(')', name)
		method = self.dispatch_end.get(name)
		if method is not None:
			getattr(self, method)()
		self.pop_state()

	def characters(self, data):
		self.current_text = self.current_text + as_latin1(data)

	def error(self, exception):
		print 'error', exception

	def fatalError(self, exception):
		print 'fatalError', exception

	def warning(self, exception):
		print 'warning', exception

	def initsvg(self, attrs):
		width = self.user_length(attrs.get('width', '100%'))
		height = self.user_length(attrs.get('height', '100%'))
		self._print('initsvg', width, height)
		self.trafo = Trafo(1, 0, 0, -1, 0, height)
		self.basetrafo = self.trafo
		# evaluate viewBox
		# FIXME: Handle preserveAspectRatio as well
		viewbox = attrs.get("viewBox", "")
		if viewbox:
			vx, vy, vwidth, vheight = map(float, split(viewbox))
			t = Scale(width / vwidth, height / vheight)
			t = t(Translation(-vx, -vy))
			self.trafo = self.trafo(t)
		self._print("basetrafo", self.basetrafo)

	def parse_style(self, style):
		parts = filter(None, map(strip, split(style, ';')))
		for part in parts:
			key, val = map(strip, split(part, ':', 1))
			self._print('style', key, val)

			# only try to parse the value if it's not empty
			if val:
				self.try_add_style(key, val)
			else:
				# FIXME: we should probably print a message or something
				pass
			
	def try_add_style(self,key,val):
		if key == 'fill':
			if val == 'none':
				self.style.fill_pattern = EmptyPattern
			else:
				color = csscolor(val)
				self._print('fill', color)
				self.style.fill_pattern = SolidPattern(color)
		elif key == 'stroke':
			if val == 'none':
				self.style.line_pattern = EmptyPattern
			else:
				color = csscolor(val)
				self._print('stroke', color)
				self.style.line_pattern = SolidPattern(color)
		elif key == 'stroke-width':
			width = self.user_length(val)
			# Multiply the width with a value taken from the
			# transformation matrix because so far transforming an
			# object in Sketch does not affect the stroke width in any
			# way. Thus we have to do that explicitly here.
			# FIXME: using m11 is not really the best approach but in
			# many cases better than using the width as is.
			width = self.trafo.m11 * width
			self._print('width', width)
			self.style.line_width = width
		elif key == 'stroke-linejoin':
			self.style.line_join = join[val]
		elif key == 'stroke-linecap':
			self.style.line_cap = cap[val]
		elif key == 'font-family':
			try:
				# convert val to 8bit string.
				self.style.font = GetFont(str(val))
			except UnicodeError:
				# If it's not ASCII we probably won't have the font, so
				# use the default one.
				# FIXME: Give a warning
				pass
		elif key == 'font-size':
			self.style.font_size = self.user_length(val)
			####self.style.font_size = float(val)
		elif key == 'text-anchor':
			if val=='start':
				self.halign = text.ALIGN_LEFT
			elif val == 'middle':
				self.halign = text.ALIGN_CENTER
			elif val == 'end':
				self.halign = text.ALIGN_RIGHT

	def set_loader_style(self, allow_font = 0):
		# Copy self.style to loader.
		# If allow_font is false (the default) do not copy the font
		# properties.
		property_types = properties.property_types
		style = self.style.Copy()
		if not allow_font:
			for name in style.__dict__.keys():
				if property_types.get(name)==properties.FontProperty:
					delattr(style, name)
		self.loader.style = style

	def push_state(self):
		self.state_stack = self.style, self.trafo, self.state_stack
		self.style = self.style.Copy()
		
	def pop_state(self):
		self.style, self.trafo, self.state_stack = self.state_stack

	def user_length(self, str):
		# interpret string as a length and return the appropriate value
		# user coordinates
		str = strip(str)
		factor = factors.get(str[-2:])
		if factor is not None:
			str = str[:-2]
		elif str[-1] == '%':
			# FIXME: this case depends on the width/height attrs of the
			# SVG element
			str = str[:-1]
			factor = 1.0
		else:
			factor = 1.0
		return float(str) * factor

	def user_point(self, x, y):
		# Return the point described by the SVG coordinates x and y as
		# an SKPoint object in user coordinates. x and y are expected to
		# be strings.
		x = strip(x)
		y = strip(y)

		# extract the units from the coordinate values if any and
		# determine the appropriate factor to convert those units to
		# user space units.
		xunit = x[-2:]
		factor = factors.get(xunit)
		if factor is not None:
			x = x[:-2]
		elif x[-1] == '%':
			# XXX this is wrong
			x = x[:-1]
			xunit = '%'
			factor = 1
		else:
			xunit = ''
			factor = 1.0
		x = float(x) * factor
		
		yunit = y[-2:]
		factor = factors.get(yunit)
		if factor is not None:
			y = y[:-2]
		elif y[-1] == '%':
			y = y[:-1]
			yunit = '%'
			factor = 1.0
		else:
			yunit = ''
			factor = 1.0
		y = float(y) * factor

		return Point(x, y)


	def point(self, x, y, relative = 0):
		# Return the point described by the SVG coordinates x and y as
		# an SKPoint object in absolute, i.e. document coordinates. x
		# and y are expected to be strings. If relative is true, they're
		# relative coordinates.
		x, y = self.user_point(x, y)

		if relative:
			p = self.trafo.DTransform(x, y)
		else:
			p = self.trafo(x, y)
		return p


	def circle(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'circle', attrs)
			return
		if attrs.has_key('cx'):
			x = attrs['cx']
		else:
			x = '0'
		if attrs.has_key('cy'):
			y = attrs['cy']
		else:
			y = '0'
		x, y = self.point(x, y)
		r = self.point(attrs['r'], '0', relative = 1).x
		t = Trafo(r, 0, 0, r, x, y)
		self._print('circle', t)
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		apply(self.loader.ellipse, t.coeff())
			

	def ellipse(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'ellipse', attrs)
			return
		if attrs.has_key('cx'):
			x = attrs['cx']
		else:
			x = '0'
		if attrs.has_key('cy'):
			y = attrs['cy']
		else:
			y = '0'
		x, y = self.point(x, y)
		rx, ry = self.point(attrs['rx'], attrs['ry'], relative = 1)
		t = Trafo(rx, 0, 0, ry, x, y)
		self._print('ellipse', t)
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		apply(self.loader.ellipse, t.coeff())

	def rect(self, attrs):
		#print 'rect', attrs.map
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'rect', attrs)
			return
		if attrs.has_key('x'):
			x = attrs['x']
		else:
			x = '0'
		if attrs.has_key('y'):
			y = attrs['y']
		else:
			y = '0'
		x, y = self.point(x, y)
		wx, wy = self.point(attrs['width'], "0", relative = 1)
		hx, hy = self.point("0", attrs['height'], relative = 1)
		t = Trafo(wx, wy, hx, hy, x, y)
		self._print('rect', t)
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		apply(self.loader.rectangle, t.coeff())

	def polyline(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'polyline', attrs)
			return
		points = as_latin1(attrs['points'])
		points = string.translate(points, commatospace)
		points = split(points)
		path = CreatePath()
		point = self.point
		for i in range(0, len(points), 2):
			path.AppendLine(point(points[i], points[i + 1]))
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		self.loader.bezier(paths = (path,))

	def polygon(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'polygon', attrs)
			return
		points = as_latin1(attrs['points'])
		points = string.translate(points, commatospace)
		points = split(points)
		path = CreatePath()
		point = self.point
		for i in range(0, len(points), 2):
			path.AppendLine(point(points[i], points[i + 1]))
		path.AppendLine(path.Node(0))
		path.ClosePath()
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		self.loader.bezier(paths = (path,))

	def parse_path(self, str):
		paths = self.paths
		path = self.path
		trafo = self.trafo
		str = strip(string.translate(as_latin1(str), commatospace))
		last_quad = None
		last_cmd = cmd = None
		f13 = 1.0 / 3.0; f23 = 2.0 / 3.0
		#print '*', str
		while 1:
			match = rx_command.match(str)
			#print match
			if match:
				last_cmd = cmd
				cmd = str[0]
				str = str[match.end():]
				#print '*', str
				points = match.group(1)
				#print '**', points
				if points:
					# use tokenize_line to parse the arguments so that
					# we deal with signed numbers following another
					# number without intervening whitespace other
					# characters properls.
					# FIXME: tokenize_line works but is not the best way
					# to do it because it accepts input that wouldn't be
					# valid here.
					points = filter(operator.isNumberType,
									skread.tokenize_line(points))
				#print cmd, points
				if cmd in 'mM':
					path = CreatePath()
					paths.append(path)
					if cmd == 'M' or len(paths) == 1:
						path.AppendLine(trafo(points[0], points[1]))
					else:
						p = trafo.DTransform(points[0], points[1])
						path.AppendLine(paths[-2].Node(-1) + p)
					if len(points) > 2:
						if cmd == 'm':
							for i in range(2, len(points), 2):
								p = trafo.DTransform(points[i], points[i + 1])
								path.AppendLine(path.Node(-1) + p)
						else:
							for i in range(2, len(points), 2):
								path.AppendLine(trafo(points[i], points[i+1]))
				elif cmd == 'l':
					for i in range(0, len(points), 2):
						p = trafo.DTransform(points[i], points[i + 1])
						path.AppendLine(path.Node(-1) + p)
				elif cmd == 'L':
					for i in range(0, len(points), 2):
						path.AppendLine(trafo(points[i], points[i+1]))
				elif cmd =='H':
					for num in points:
						path.AppendLine(Point(num, path.Node(-1).y))
				elif cmd =='h':
					for num in points:
						x, y = path.Node(-1)
						dx, dy = trafo.DTransform(num, 0)
						path.AppendLine(Point(x + dx, y + dy))
				elif cmd =='V':
					for num in points:
						path.AppendLine(Point(path.Node(-1).x, num))
				elif cmd =='v':
					for num in points:
						x, y = path.Node(-1)
						dx, dy = trafo.DTransform(0, num)
						path.AppendLine(Point(x + dx, y + dy))
				elif cmd == 'C':
					if len(points) % 6 != 0:
						self.loader.add_message("number of parameters of 'C'"\
												"must be multiple of 6")
					else:
						for i in range(0, len(points), 6):
							p1 = trafo(points[i], points[i + 1])
							p2 = trafo(points[i + 2], points[i + 3])
							p3 = trafo(points[i + 4], points[i + 5])
							path.AppendBezier(p1, p2, p3)
				elif cmd == 'c':
					if len(points) % 6 != 0:
						self.loader.add_message("number of parameters of 'c'"\
												"must be multiple of 6")
					else:
						for i in range(0, len(points), 6):
							p = path.Node(-1)
							p1 = p + trafo.DTransform(points[i], points[i + 1])
							p2 = p + trafo.DTransform(points[i+2], points[i+3])
							p3 = p + trafo.DTransform(points[i+4], points[i+5])
							path.AppendBezier(p1, p2, p3)
				elif cmd == 'S':
					if len(points) % 4 != 0:
						self.loader.add_message("number of parameters of 'S'"\
												"must be multiple of 4")
					else:
						for i in range(0, len(points), 4):
							type, controls, p, cont = path.Segment(-1)
							if type == Bezier:
								q = controls[1]
							else:
								q = p
							p1 = 2 * p - q
							p2 = trafo(points[i], points[i + 1])
							p3 = trafo(points[i + 2], points[i + 3])
							path.AppendBezier(p1, p2, p3)
				elif cmd == 's':
					if len(points) % 4 != 0:
						self.loader.add_message("number of parameters of 's'"\
												"must be multiple of 4")
					else:
						for i in range(0, len(points), 4):
							type, controls, p, cont = path.Segment(-1)
							if type == Bezier:
								q = controls[1]
							else:
								q = p
							p1 = 2 * p - q
							p2 = p + trafo.DTransform(points[i], points[i + 1])
							p3 = p + trafo.DTransform(points[i+2], points[i+3])
							path.AppendBezier(p1, p2, p3)
				elif cmd == 'Q':
					if len(points) % 4 != 0:
						self.loader.add_message("number of parameters of 'Q'"\
												"must be multiple of 4")
					else:
						for i in range(0, len(points), 4):
							q = trafo(points[i], points[i + 1])
							p3 = trafo(points[i + 2], points[i + 3])
							p1 = f13 * path.Node(-1) + f23 * q
							p2 = f13 * p3 + f23 * q
							path.AppendBezier(p1, p2, p3)
							last_quad = q
				elif cmd == 'q':
					if len(points) % 4 != 0:
						self.loader.add_message("number of parameters of 'q'"\
												"must be multiple of 4")
					else:
						for i in range(0, len(points), 4):
							p = path.Node(-1)
							q = p + trafo.DTransform(points[i], points[i + 1])
							p3 = p + trafo.DTransform(points[i+2], points[i+3])
							p1 = f13 * p + f23 * q
							p2 = f13 * p3 + f23 * q
							path.AppendBezier(p1, p2, p3)
							last_quad = q
				elif cmd == 'T':
					if len(points) % 2 != 0:
						self.loader.add_message("number of parameters of 'T'"\
												"must be multiple of 4")
					else:
						if last_cmd not in 'QqTt' or last_quad is None:
							last_quad = path.Node(-1)
						for i in range(0, len(points), 2):
							p = path.Node(-1)
							q = 2 * p - last_quad
							p3 = trafo(points[i], points[i + 1])
							p1 = f13 * p + f23 * q
							p2 = f13 * p3 + f23 * q
							path.AppendBezier(p1, p2, p3)
							last_quad = q
				elif cmd == 't':
					if len(points) % 2 != 0:
						self.loader.add_message("number of parameters of 't'"\
												"must be multiple of 4")
					else:
						if last_cmd not in 'QqTt' or last_quad is None:
							last_quad = path.Node(-1)
						for i in range(0, len(points), 2):
							p = path.Node(-1)
							q = 2 * p - last_quad
							p3 = p + trafo.DTransform(points[i], points[i + 1])
							p1 = f13 * p + f23 * q
							p2 = f13 * p3 + f23 * q
							path.AppendBezier(p1, p2, p3)
							last_quad = q

				elif cmd in 'zZ':
					path.AppendLine(path.Node(0))
					path.ClosePath()
			else:
				break
		self.path = path

	def begin_path(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'path', attrs)
			return
		self.paths = []
		self.path = None
		self.parse_path(attrs['d'])
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style()
		
	def end_path(self):
		if self.in_defs:
			return
		self.loader.bezier(paths = tuple(self.paths))
		self.paths = None
		
	def image(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'image', attrs)
			return
		href = attrs['xlink:href']
		if os.path.isfile(os.path.join(self.loader.directory, href)):			
			image = load_image(os.path.join(self.loader.directory, href)).image
			if attrs.has_key('x'):
				x = attrs['x']
			else:
				x = '0'
			if attrs.has_key('y'):
				y = attrs['y']
			else:
				y = '0'
			x, y = self.user_point(x, y)
			
			width = self.user_length(attrs['width'])
			scalex =  width / image.size[0]
	
			height = self.user_length(attrs['height']) 
			scaley = -height / image.size[1]
	
			style = attrs.get('style', '')
			if style:
				self.parse_style(style)
			self.set_loader_style()
			t = self.trafo(Trafo(scalex, 0, 0, scaley, x, y + height))
			self._print('image', t)
			self.loader.image(image, t)

	def begin_text(self, attrs):
		if self.in_defs:
			id = attrs.get('id', '')
			if id:
				self.named_objects[id] = ('object', 'text', attrs)
			return

		# parse the presentation attributes if any.
		# FIXME: this has to be implemented for the other elements that
		# can have presentation attributes as well.
		for key,value in attrs.items():
			self.try_add_style(key,value)
			
		if attrs.has_key('x'):
			x = attrs['x']
		else:
			x = '0'
		if attrs.has_key('y'):
			y = attrs['y']
		else:
			y = '0'
		x, y = self.user_point(x, y)
		self.text_trafo = self.trafo(Trafo(1, 0, 0, -1, x, y))
		self._print('text', self.text_trafo)
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.set_loader_style(allow_font = 1)
		self.current_text=''

	def end_text(self):
		self.loader.simple_text(strip(self.current_text), self.text_trafo,
								halign = self.halign)

	def data(self, attrs):
		pass

	def begin_group(self, attrs):
		style = attrs.get('style', '')
		if style:
			self.parse_style(style)
		self.loader.begin_group()
		
	def end_group(self):
		try:
			self.loader.end_group()
		except EmptyCompositeError:
			pass

	def use(self, attrs):
		#print 'use', attrs.map
		if attrs.has_key('xlink:href'):
			name = attrs['xlink:href']
		else:
			name = attrs.get('href', '<none>')
		if name:
			data = self.named_objects.get(name[1:])
			if data[0] == 'object':
				if attrs.has_key('style'):
					self.parse_style(attrs['style'])
				self.startElement(data[1], data[2])
				self.endElement(data[1])
			

	def begin_defs(self, attrs):
		self.in_defs = 1

	def end_defs(self):
		self.in_defs = 0

class SVGLoader(GenericLoader):

	format_name = format_name

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		if self.filename:
			self.directory = os.path.split(filename)[0]
		else:
			self.directory = ''
		
	def __del__(self):
		pass

	def Load(self):
		try:
			self.document()
			self.layer()
			
			error_handler = ErrorHandler()
			entity_resolver = EntityResolver()
			dtd_handler = DTDHandler()
			
			input = open(self.filename, "r")
			input_source = InputSource()
			input_source.setByteStream(input)
			xml_reader = xml.sax.make_parser()
			xml_reader.setContentHandler(SVGHandler(self))
			xml_reader.setErrorHandler(error_handler)
			xml_reader.setEntityResolver(entity_resolver)
			xml_reader.setDTDHandler(dtd_handler)
			xml_reader.parse(input_source)
			input.close

			self.end_all()
			self.object.load_Completed()
			return self.object
		except:
			warn_tb('INTERNAL')
			raise

class ErrorHandler(handler.ErrorHandler): pass
class EntityResolver(handler.EntityResolver): pass
class DTDHandler(handler.DTDHandler): pass      