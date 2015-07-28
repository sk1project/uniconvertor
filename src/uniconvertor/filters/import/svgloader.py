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

from types import StringType, TupleType, ListType
from math import pi, tan
import os, sys, copy
import re
from string import strip, split, atoi, lower, atof
import string
import operator
from StringIO import StringIO
from PIL import Image

import streamfilter

from app import Document, Layer, CreatePath, ContSmooth, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient,\
		CreateRGBColor, CreateCMYKColor, MultiGradient, \
		Trafo, Translation, Rotation, Scale, Point, Polar, \
		StandardColors, GetFont, PathText, SimpleText, const, UnionRects, \
		Bezier, Line, load_image, skread

from app.events.warn import INTERNAL, USER, warn_tb

from app.io.load import GenericLoader, EmptyCompositeError

from app.Graphics import text, properties, pagelayout

from xml.sax import handler
import xml.sax
from xml.sax.xmlreader import InputSource

# beginning with Python 2.0, the XML modules return Unicode strings,
# to avoid non ascii symbols for string.translate() this
# function encodes characters into latin-1

def as_latin1(s):
	# convert the string s to iso-latin-1 if it's a unicode string
	encode = getattr(s, "encode", None)
	if encode is not None:
		s = encode("iso-8859-1", "replace")
	return s


# Conversion factors to convert standard CSS/SVG units to userspace
# units.
factors = {'pt': 1.25, 'px': 1.0, 'pc': 15, 'in': 90.0, 
			'cm': 90.0 / 2.54, 'mm': 9.00 / 2.54, 'em': 150.0}

degrees = pi / 180.0


def csscolor(str):
	#set default color black
	color = StandardColors.black
	
	parts = str
	parts = parts.replace(',', ' ')
	parts = parts.replace('(', ' ')
	parts = parts.replace(')', ' ')
	parts = parts.split()
	
	i = 0
	while i < len(parts):
		part = parts[i]
		if part[0] == '#' and len(part) == 7:
			r = atoi(part[1:3], 16) / 255.0
			g = atoi(part[3:5], 16) / 255.0
			b = atoi(part[5:7], 16) / 255.0
			color = CreateRGBColor(r, g, b)
			i += 1
		
		elif part[0] == '#' and len(part) == 4:
			# According to the CSS rules a single HEX digit is to be
			# treated as a repetition of the digit, so that for a digit
			# d the value is (16 * d + d) / 255.0 which is equal to d / 15.0
			r = atoi(part[1], 16) / 15.0
			g = atoi(part[2], 16) / 15.0
			b = atoi(part[3], 16) / 15.0
			color = CreateRGBColor(r, g, b)
			i += 1
		
		elif namedcolors.has_key(part):
			color = namedcolors[part]
			i += 1
		
		elif part == 'rgb':
			if parts[i+1][-1] == '%':
				r = atof(parts[i+1][:-1]) / 100.0
			else:
				r = atof(parts[i+1]) / 255.0
			
			if parts[i+2][-1] == '%':
				g = atof(parts[i+2][:-1]) / 100.0
			else:
				g = atof(parts[i+2]) / 255.0
			
			if parts[i+3][-1] == '%':
				b = atof(parts[i+3][:-1]) / 100.0
			else:
				b = atof(parts[i+3]) / 255.0
			color = CreateRGBColor(r, g, b)
			i += 4
		
		elif part == 'icc-color':
			#icc = parts[i+1]
			c = atof(parts[i+2])
			m = atof(parts[i+3])
			y = atof(parts[i+4])
			k = atof(parts[i+5])
			color = CreateCMYKColor(c, m, y, k)
			i += 6
		
		elif part == 'device-gray':
			gray = 1.0 - atof(parts[i+1])
			color = CreateCMYKColor(0, 0, 0, gray)
			i += 2
		
		elif part == 'device-cmyk':
			c = atof(parts[i+1])
			m = atof(parts[i+2])
			y = atof(parts[i+3])
			k = atof(parts[i+4])
			color = CreateCMYKColor(c, m, y, k)
			i += 5
		
		else:
			i += 1
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

rx_command = re.compile(r'[a-df-zA-DF-Z]((\s*[-+0-9.e]+)*)\s*')
rx_trafo = re.compile(r'\s*([a-zA-Z]+)\(([^)]*)\)')

class SVGHandler(handler.ContentHandler):

	dispatch_start = {'svg': 'begin_svg',
						'g': 'begin_group',
						'symbol': 'begin_symbol',
						'line': 'line',
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
						'linearGradient': 'start_linearGradient',
						'radialGradient': 'start_radialGradient',
						'stop': 'stop',
						}
	dispatch_end = {'svg': 'end_svg',
					'g': 'end_group',
					'symbol': 'end_symbol',
					'path': 'end_path',
					'defs': 'end_defs',
					'text': 'end_text',
					'linearGradient': 'stop_linearGradient',
					'radialGradient': 'stop_radialGradient',
					}
	
	opacity=None
	stops=[]
	gradients={}
	grad_patters={}
	current_gradient=0
	
	def __init__(self, loader):
		self.loader = loader
		self.trafo = self.basetrafo = None
		self.state_stack = ()
		self.style = loader.style.Copy()
		self.style.line_pattern = EmptyPattern
		self.style.fill_pattern = SolidPattern(StandardColors.black)
		self.current_text = None
		self.style.font = GetFont("Times-Roman")
		self.style.font_size = 12
		self.halign = text.ALIGN_LEFT
		self.elements_id = {}
		self.elements = []
		self.in_defs = 0
		self.in_use = 0
		self.paths = None
		self.path = None
		self.depth = 0
		self.indent = '    '
		self.viewPort = (0, 0, 210*factors['mm'], 297*factors['mm'])

	def _print(self, *args):
		return
#		if args:
#			print self.depth * self.indent + args[0],
#		for s in args[1:]:
#			print s,
#		print

	def start_linearGradient(self, attrs):
		if attrs.has_key('xlink:href') or attrs.has_key('x2'):
			x2=atof(attrs['x2'])
			x1=atof(attrs['x1'])
			y2=atof(attrs['y2'])
			y1=atof(attrs['y1'])
			point1=Point(x1, y1)
			point2=Point(x2, y2)
			
			trafo=None
			if attrs.has_key('xlink:href'):
				id=attrs['xlink:href'][1:]
			else:
				id=None

			if attrs.has_key('gradientTransform'):
#				trafo=parse_transform(attrs['gradientTransform'])
				trafo_str=attrs['gradientTransform']
				if trafo_str[:9]=='translate':
					trafo=attrs['gradientTransform']
					parts=filter(None, map(strip, split(trafo_str[10:-1], ',')))
					trafo=Translation(atof(parts[1]),atof(parts[0]))
				if trafo_str[:6]=='matrix':
					parts=filter(None, map(strip, split(trafo_str[7:-1], ',')))
					trafo=Trafo(atof(parts[0]),atof(parts[1]),atof(parts[2]),
							atof(parts[3]),atof(parts[4]),atof(parts[5]))

			if not trafo is None:
				point1=trafo(point1)
				point2=trafo(point2)
			
			grad=['LinearGradient',id, (point1,point2)]
			self.grad_patters[attrs['id']]=grad
			
			if not attrs.has_key('xlink:href'):
				self.current_gradient=grad
		else:
			self.current_gradient=attrs['id']

	
	def stop_linearGradient(self):
		if len(self.stops):
			if self.current_gradient:
				if type(self.current_gradient)==ListType:
					self.current_gradient[1]=MultiGradient(self.stops)
				else:
					self.gradients[self.current_gradient]=MultiGradient(self.stops)
			self.current_gradient=0
			self.stops=[]	
			
	def start_radialGradient(self, attrs):
		if attrs.has_key('xlink:href') or attrs.has_key('cx'):
			fx=atof(attrs['fx'])
			cx=atof(attrs['cx'])
			fy=atof(attrs['fy'])
			cy=atof(attrs['cy'])
			point1=Point(cx, cy)
			point2=Point(fx, fy)
			r=atof(attrs['r'])

			if attrs.has_key('xlink:href'):
				id=attrs['xlink:href'][1:]
			else:
				id=None
			
			trafo=None
			if attrs.has_key('gradientTransform'):
#				trafo=parse_transform(attrs['gradientTransform'])
				trafo_str=attrs['gradientTransform']
				if trafo_str[:9]=='translate':
					parts=filter(None, map(strip, split(trafo_str[10:-1], ',')))
					trafo=Translation(atof(parts[1]),atof(parts[0]))
				if trafo_str[:6]=='matrix':
					parts=filter(None, map(strip, split(trafo_str[7:-1], ',')))
					trafo=Trafo(atof(parts[0]),atof(parts[1]),atof(parts[2]),
							atof(parts[3]),atof(parts[4]),atof(parts[5]))

			if not trafo is None:
				point1=trafo(point1)
				point2=trafo(point2)
			
			grad=['RadialGradient',id, (point1,point2),r]
			self.grad_patters[attrs['id']]=grad
			
			if not attrs.has_key('xlink:href'):
				self.current_gradient=grad
		else:
			self.current_gradient=attrs['id']
	
	def stop_radialGradient(self):
		if len(self.stops):		
			if self.current_gradient:
				if type(self.current_gradient)==ListType:
					self.current_gradient[1]=MultiGradient(self.stops)
				else:
					self.gradients[self.current_gradient]=MultiGradient(self.stops)
			self.current_gradient=0
			self.stops=[]	
			
	def stop(self, attrs):
		offset=atof(attrs['offset'])
		style=attrs['style']
		stop_color=None
		stop_opacity=1
		parts = filter(None, map(strip, split(style, ';')))
		for part in parts:
			key, val = map(strip, split(part, ':', 1))
			if key=='stop-color':stop_color=csscolor(val)
			if key=='stop-opacity':stop_opacity=atof(val)
		stop_color.alpha=stop_opacity
		stop_color.update()
		self.stops.append((1.0-offset,stop_color))		

	def parse_transform(self, trafo_string):
		trafo = self.trafo
		trafo_string = as_latin1(trafo_string)
		while trafo_string:
			match = rx_trafo.match(trafo_string)
			if match:
				function = match.group(1)
				args = argsf = string.translate(match.group(2), commatospace)
				args = map(str, split(args))
				trafo_string = trafo_string[match.end(0):]
				if function == 'matrix':
					args = map(float, split(argsf))
					trafo = trafo(apply(Trafo, tuple(args)))
				elif function == 'scale':
					if len(args) == 1:
						sx = sy = args[0]
					else:
						sx, sy = args
					sx, sy = self.user_point(sx, sy)
					trafo = trafo(Scale(sx, sy))
				elif function == 'translate':
					if len(args) == 1:
						dx, dy = args[0], '0'
					else:
						dx, dy = args
					dx, dy = self.user_point(dx, dy)
					trafo = trafo(Translation(dx, dy))
				elif function == 'rotate':
					if len(args) == 1:
						trafo = trafo(Rotation(float(args[0]) * degrees))
					else:
						angle, cx, cy = args
						cx, cy = self.user_point(cx, cy)
						trafo = trafo(Rotation(float(angle) * degrees, Point(cx, cy)))
				elif function == 'skewX':
					trafo = trafo(Trafo(1, 0, tan(float(args[0]) * degrees), 1, 0, 0))
				elif function == 'skewY':
					trafo = trafo(Trafo(1, tan(float(args[0]) * degrees), 0, 1, 0, 0))
			else:
				trafo_string = ''
		self.trafo = trafo

	def startElement(self, name, attrs):
		self._print('(', name)
		for key, value in attrs.items():
			self._print('  -', key, `value`)
		self.depth = self.depth + 1
		
		if name == 'text':
			self.current_text = ''
		
		if not self.in_use:
			id = attrs.get('id', '')
			if id:
				self.elements_id['#' + id] = len(self.elements)
			self.elements.append([name, attrs, self.current_text])
		
	def endElement(self, name):
		self.depth = self.depth - 1
		self._print(')', name)
		
		if not self.in_use:
			self.elements.append([name, None, self.current_text])
		
		if name == 'text':
			self.current_text = None


	def endDocument(self):
		#for id in self.elements_id:
			#print id, self.elements_id[id]
		for element in self.elements:
			self.parseElements(element)
	
	
	def parseElements(self, element):
		name, attrs, self.current_text = element
		if attrs is not None:
			#startElement
			self._print('(', name)
			for key, value in attrs.items():
				self._print('  -', key, `value`)
			
			self.depth += 1
			self.push_state()
			
			if attrs.has_key('transform'):
				self.parse_transform(attrs['transform'])
				self._print("applied transormation", self.trafo)
			
			method = self.dispatch_start.get(name)
			if method is not None:
				getattr(self, method)(attrs)
		else:
			#endElement
			self.depth -= 1
			self._print(')', name)
			method = self.dispatch_end.get(name)
			if method is not None:
				getattr(self, method)()
			self.pop_state()


	def characters(self, data):
		if self.current_text is not None:
			self.current_text = self.current_text + data

	def error(self, exception):
		print 'error', exception

	def fatalError(self, exception):
		print 'fatalError', exception

	def warning(self, exception):
		print 'warning', exception

	def begin_svg(self, attrs):
		self.svgView(attrs)
		self.parse_attrs(attrs)

	def end_svg(self):
		self._print("trafo", self.trafo)
	
	def svgView(self, attrs):
		self._print("basetrafo", self.basetrafo)
		viewbox = attrs.get("viewBox", "")
		if viewbox:
			# In early viewPort = viewBox
			self._print('viewBox', viewbox)
			viewbox = viewbox.replace(',',' ')
			self.viewPort = map(float, split(viewbox))
		
		x, y = self.user_point(attrs.get('x', '0'), attrs.get('y', '0'))
		width, height = self.user_point(attrs.get('width', '100%'), \
									    attrs.get('height', '100%'))
		self._print('svgView', x, y, width, height)
		
		if self.loader.page_layout is None:
				self.loader.page_layout = pagelayout.PageLayout(
						width = width * 0.8, height = height * 0.8)
		
		if self.trafo is None:
			# adjustment of the coordinate system and taking into account 
			# the difference between 90dpi in svg against 72dpi in sk1
			self.trafo = self.basetrafo = Trafo(0.8, 0, 0, -0.8, 0, height*0.8)
			# initial values of x and y are ignored
			x = y = 0
			
		# adjust to the values x, y in self.trafo 
		self.trafo = self.trafo(Translation(x, y))
		# evaluate viewBox
		# FIXME: Handle preserveAspectRatio as well
		if viewbox:
			t = Scale(width/self.viewPort[2], height/self.viewPort[3])
			t = t(Translation(-self.viewPort[0], -self.viewPort[1]))
			self.trafo = self.trafo(t)
		# set viewPort taking into account the transformation
		self.viewPort = (x, y, width/(self.trafo.m11/self.basetrafo.m11),\
						height/(self.trafo.m22/self.basetrafo.m22))

		self._print("trafo", self.trafo)
		self._print("viewPort", self.viewPort)
		
	def parse_attrs(self, attrs):
		for name in attrs.getNames():
			val = attrs.getValue(name)
			if name == 'style':
				self.parse_style(val)
			else:
				self.try_add_style(name, val)
		

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
		self.opacity=None
	
	def try_add_style(self,key,val):
		if key == 'fill':
			if val == 'none':
				self.style.fill_pattern = EmptyPattern
			elif val[:3] == 'url' and self.grad_patters.has_key(val[5:-1]):
				grad=self.grad_patters[val[5:-1]]
				try:
					if grad[0]=='LinearGradient':
						point1,point2=grad[2]
						point1=self.trafo(point1)
						point2=self.trafo(point2)	
						point=Point(point2.x-point1.x, point2.y-point1.y)
						if not grad[1].__class__ == MultiGradient:
							if self.gradients.has_key(grad[1]):
								self.style.fill_pattern = LinearGradient(self.gradients[grad[1]].Duplicate(),point)
						else:
							self.style.fill_pattern = LinearGradient(grad[1].Duplicate(),point)
					if grad[0]=='RadialGradient':
						point1,point2=grad[2]
						point1=self.trafo(point1)
						point2=self.trafo(point2)
						point1=Point(0.5,0.5)						
						if not grad[1].__class__ == MultiGradient:
							if self.gradients.has_key(grad[1]):
								self.style.fill_pattern = RadialGradient(self.gradients[grad[1]].Duplicate(),point1)
						else:
							self.style.fill_pattern = RadialGradient(grad[1].Duplicate(),point1)
				except:
					pass
					
			else:
				color = csscolor(val)
				self._print('fill', color)
				self.style.fill_pattern = SolidPattern(color)
		elif key == 'fill-opacity':
			value=atof(val)
			if self.style.fill_pattern.__class__ == SolidPattern:
				self.style.fill_pattern.Color().alpha*=value
				self.style.fill_pattern.Color().update()
		elif key == 'stroke':
			if val == 'none':
				self.style.line_pattern = EmptyPattern
			else:
				color = csscolor(val)
				self._print('stroke', color)
				self.style.line_pattern = SolidPattern(color)
				if not self.opacity is None:
					self.style.line_pattern.Color().alpha=self.opacity
					self.style.line_pattern.Color().update()
		elif key == 'stroke-opacity':
			value=atof(val)
			if self.style.line_pattern.__class__ == SolidPattern:
				self.style.line_pattern.Color().alpha*=value
				self.style.line_pattern.Color().update()
		elif key == 'opacity':
			value=atof(val)
			self.opacity=value
			if self.style.fill_pattern.__class__ == SolidPattern:
				self.style.fill_pattern.Color().alpha=value
				self.style.fill_pattern.Color().update()
			if self.style.line_pattern.__class__ == SolidPattern:
				self.style.line_pattern.Color().alpha=self.opacity
				self.style.line_pattern.Color().update()			
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
			self.style.line_width = abs(width)
		elif key == 'stroke-linejoin':
			self.style.line_join = join[val]
		elif key == 'stroke-linecap':
			self.style.line_cap = cap[val]
		elif key == 'font-family':
			self.style.font = GetFont(val)
		elif key == '-inkscape-font-specification':
			self.style.font = GetFont(val)			
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
			x = x[:-1]
			xunit = '%'
			factor = self.viewPort[2] / 100.0
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
			factor = self.viewPort[3] / 100.0
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

	def line(self, attrs):
		if self.in_defs:
			return
		x1, y1 = attrs.get('x1', '0'), attrs.get('y1', '0')
		x2, y2 = attrs.get('x2', '0'), attrs.get('y2', '0')
		path = CreatePath()
		path.AppendLine(self.point(x1, y1))
		path.AppendLine(self.point(x2, y2))
		
		self.parse_attrs(attrs)
		self.set_loader_style()
		self.loader.bezier(paths = (path,))

	def circle(self, attrs):
		if self.in_defs:
			return
		x, y = self.user_point(attrs.get('cx', '0'), attrs.get('cy', '0'))
		r = self.user_point(attrs['r'], '0').x
		t = self.trafo(Trafo(r, 0, 0, r, x, y))
		self._print('circle', t)
		self.parse_attrs(attrs)
		self.set_loader_style()
		apply(self.loader.ellipse, t.coeff())
			

	def ellipse(self, attrs):
		if self.in_defs:
			return
		x, y = self.user_point(attrs.get('cx', '0'), attrs.get('cy', '0'))
		rx, ry = self.user_point(attrs['rx'], attrs['ry'])
		t = self.trafo(Trafo(rx, 0, 0, ry, x, y))
		self._print('ellipse', t)
		self.parse_attrs(attrs)
		self.set_loader_style()
		apply(self.loader.ellipse, t.coeff())

	def rect(self, attrs):
		if self.in_defs:
			return
		x, y = self.point(attrs.get('x', '0'), attrs.get('y', '0'))
		wx, wy = self.point(attrs['width'], "0", relative = 1)
		hx, hy = self.point("0", attrs['height'], relative = 1)
		t = Trafo(wx, wy, hx, hy, x, y)
		rx = ry = '0'
		if attrs.has_key('rx') and attrs.has_key('ry'):
			rx, ry = attrs['rx'], attrs['ry']
		elif attrs.has_key('rx'):
			rx = ry = attrs['rx']
		elif attrs.has_key('ry'):
			rx = ry = attrs['ry']
		rx, ry = self.user_point(rx, ry)
		width, height = self.user_point(attrs['width'], attrs['height'])
		if width:
			rx = min(rx / width, 0.5)
		else:
			rx = 0
		if height:
			ry = min(ry / height, 0.5)
		else:
			ry = 0 
		#wx, wy, hx, hy, x, y = t.coeff()
		self._print('rect', t)
		self.parse_attrs(attrs)
		self.set_loader_style()
		apply(self.loader.rectangle, (wx, wy, hx, hy, x, y, rx, ry))

	def polyline(self, attrs):
		if self.in_defs:
			return
		points = as_latin1(attrs['points'])
		points = string.translate(points, commatospace)
		points = split(points)
		path = CreatePath()
		point = self.point
		for i in range(0, len(points), 2):
			path.AppendLine(point(points[i], points[i + 1]))
		self.parse_attrs(attrs)
		self.set_loader_style()
		self.loader.bezier(paths = (path,))

	def polygon(self, attrs):
		if self.in_defs:
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
		self.parse_attrs(attrs)
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
					if round(path.Node(0).x, 3) != round(path.Node(-1).x, 3) or \
					            round(path.Node(0).y, 3) != round(path.Node(-1).y, 3):
						path.AppendLine(path.Node(0))
					path.ClosePath()
			else:
				break
		self.path = path

	def begin_path(self, attrs):
		if self.in_defs:
			return
		self.paths = []
		self.path = None
		self.parse_path(attrs['d'])
		self.parse_attrs(attrs)
		self.set_loader_style()
		
	def end_path(self):
		if self.in_defs:
			return
		self.loader.bezier(paths = tuple(self.paths))
		self.paths = None
		
	def image(self, attrs):
		if self.in_defs:
			return
		href = attrs['xlink:href']
		image = None
		
		if href[:5] == 'data:':
			# embed image
			coma = href.find(',')
			semicolon = href.find(';')
			mime = href[5:semicolon]
			if mime in ['image/png','image/jpg','image/jpeg','image/gif','image/bmp']:
				import base64
				image = Image.open(StringIO(base64.decodestring(href[coma:])))
				if image.mode == 'P':
					image = image.convert('RGBA')
		else:
			# linked image
			import urlparse, urllib
			path = urlparse.urlparse(href).path
			href = urllib.unquote(path.encode('utf-8'))
			path = os.path.realpath(href)
			if os.path.isfile(path):
				image = load_image(path).image
			else:
				self.loader.add_message(_('Cannot find linked image file %s') % path)

		if image:
			x, y = self.user_point(attrs.get('x', '0'), attrs.get('y', '0'))
			
			width = self.user_length(attrs['width'])
			scalex =  width / image.size[0]
	
			height = self.user_length(attrs['height']) 
			scaley = -height / image.size[1]
	
			self.parse_attrs(attrs)
			self.set_loader_style()
			t = self.trafo(Trafo(scalex, 0, 0, scaley, x, y + height))
			self._print('image', t)
			self.loader.image(image, t)

	def begin_text(self, attrs):
		if self.in_defs:
			return
		# parse the presentation attributes if any.
		# FIXME: this has to be implemented for the other elements that
		# can have presentation attributes as well.
		for key,value in attrs.items():
			self.try_add_style(key,value)
			
		x, y = self.user_point(attrs.get('x', '0'), attrs.get('y', '0'))
		self.text_trafo = self.trafo(Trafo(1, 0, 0, -1, x, y))
		self._print('text', self.text_trafo)
		self.parse_attrs(attrs)
		self.set_loader_style(allow_font = 1)

	def end_text(self):
		if self.in_defs:
			return
		self.loader.simple_text(strip(self.current_text), self.text_trafo,
								halign = self.halign)

	def data(self, attrs):
		pass

	def begin_group(self, attrs):
		if self.in_defs:
			return
		self.parse_attrs(attrs)
		self.loader.begin_group()
		
	def end_group(self):
		if self.in_defs:
			return
		try:
			self.loader.end_group()
		except EmptyCompositeError:
			pass

	def use(self, attrs):
		if self.in_use:
			return
		self.in_use = 1
		#print 'use', attrs.map
		if attrs.has_key('xlink:href'):
			name = attrs['xlink:href']
		else:
			name = attrs.get('href', '<none>')
		if name:
			data = self.elements_id[name]
			if data is not None:
				self.push_state()
				# FIXME: to add attributes width and height
				x, y = self.user_point(attrs.get('x', '0'), attrs.get('y', '0'))
				self.parse_attrs(attrs)
				self.trafo = self.trafo(Translation(x,y))
				cur_depth = self.depth
				while True:
					self.parseElements(self.elements[data])
					data += 1
					if cur_depth >= self.depth:
						break
				self.pop_state()
				
			#FIXME: '!!! PASS IN USE ELEMENT', name
		
		self.in_use = 0

	def begin_defs(self, attrs):
		self.in_defs = 1
		self.stops=[]

	def end_defs(self):
		self.in_defs = 0

	def begin_symbol(self, attrs):
		# FIXME: to add attributes viewBox and preserveAspectRatio 
		pass

	def end_symbol(self):
		pass

class SVGLoader(GenericLoader):

	format_name = format_name

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		if self.filename:
			self.directory = os.path.split(filename)[0]
		else:
			self.directory = ''
		self.page_layout = None

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
			xml_reader.setFeature(handler.feature_external_ges, False)
			xml_reader.parse(input_source)
			input.close

			self.end_all()
			
			if self.page_layout:
				self.object.load_SetLayout(self.page_layout)
			
			self.object.load_Completed()
			return self.object
		except:
			warn_tb('INTERNAL')
			raise

class ErrorHandler(handler.ErrorHandler): pass
class EntityResolver(handler.EntityResolver): pass
class DTDHandler(handler.DTDHandler): pass      
