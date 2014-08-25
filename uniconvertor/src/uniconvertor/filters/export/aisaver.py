# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor Novikov
# Copyright (C) 1998, 1999, 2000, 2002 by Bernhard Herzog
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
#type = Export
#tk_file_type = (_("Adobe Illustrator v.5.0"), '.ai')
#extensions = '.ai'
format_name = 'Adobe Illustrator'
#unload = 1
#standard_messages = 1
###End

(''"Adobe Illustrator")

from math import floor, ceil, atan2, pi, hypot

from app import ContAngle, ContSmooth, ContSymmetrical, Bezier, Line, \
		StandardColors, EmptyPattern, TransformRectangle, UnitRect, \
		RectanglePath, approx_arc, _sketch, Rotation, Translation
from app.Lib.psmisc import quote_ps_string
from app.Lib import encoding

def cmyk(color):
	return color.getCMYK()
	#c = 1.0 - color.red
	#m = 1.0 - color.green
	#y = 1.0 - color.blue
	#k = min(c, m, y)
	#return c - k, m - k, y - k, k
	

ps_join = (0, 1, 2)
ps_cap = (None, 0, 1, 2)



class AISaver:

	def __init__(self, file, filename, document, options):
		self.file = file
		self.filename = filename
		self.document = document
		self.options = options
		self.init_style()
		self.layers_as_groups = options.get('layers_as_groups', 0)
		self.gradients = {}
		self.fonts = {}
		document.WalkHierarchy(self.analyze, all = 1)
		self.write_header(document)

	def init_style(self):
		self.line_color = None
		self.line_width = None
		self.line_join = None
		self.line_cap = None
		self.line_dashes = None
		self.fill_color = None
		

	def analyze(self, object):
		if object.has_fill:
			fill = object.properties.fill_pattern
			if fill.is_Gradient:
				key = self.gradient_id(fill)
				if key is not None:
					self.gradients[key[0]] = key
		if object.has_font:
			font = object.properties.font
			self.fonts[font.PostScriptName()] = 1

	def gradient_id(self, fill):
		gradient = fill.Gradient()
		if fill.is_AxialGradient:
			type = 0
			name = '(Linear Gradient %d)'
		elif fill.is_RadialGradient:
			type = 1
			name = '(Radial Gradient %d)'
		else:
			type = -1
		if type >= 0:
			name = name % id(gradient)
			return (name, type, gradient)
		return None

	def write_header(self, document):
		write = self.file.write
		write('%!PS-Adobe-3.0 EPSF\n')
		# Illustrator seems to require 'Adobe Illustrator' in the
		# Creator comment.
		write('%%Creator: Adobe Illustrator exported by sK1\n')
		llx, lly, urx, ury = document.BoundingRect()
		write('%%%%BoundingBox: %d %d %d %d\n' % (floor(llx), floor(lly),
												ceil(urx), ceil(ury)))
		write('%%%%HiResBoundingBox: %g %g %g %g\n' % (llx, lly, urx, ury))
		write('%AI5_FileFormat 3\n') # necessary for gradients
		write('%%EndComments\n')
		write('%%BeginProlog\n%%EndProlog\n')

		# Setup section
		write('%%BeginSetup\n')
		
		if self.gradients:
			write('%d Bn\n' % len(self.gradients))
			for name, type, gradient in self.gradients.values():
				colors = gradient.Colors()[:]
				write('%%AI5_BeginGradient: %s\n' % name)
				write('%s %d %d Bd\n' % (name, type, len(colors)))
				write('[\n')
				# reverse the colors for radial gradients
				if type == 1:
					for i in range(len(colors)):
						pos, color = colors[i]
						colors[i] = 1.0 - pos, color
				# also reverse for linear gradients because for some
				# reason Illustrator only accepts linear gradients when
				# they are stored with decreasing position.
				colors.reverse()
				for pos, color in colors:
					c, m, y, k = cmyk(color)
					write('%f %f %f %f 1 50 %d %%_Bs\n'
							% (c, m, y, k, 100*pos))
				write('BD\n%AI5_EndGradient\n')

		if self.fonts:
			self.write_standard_encoding(encoding.iso_latin_1)
			for key in self.fonts.keys():
				new_name = '_' + key
				write("%%AI3_BeginEncoding: %s %s\n" % (new_name, key))
				# assume horizontal writing, roman typefaces, TE encoding:
				write("[/%s/%s %d %d %d TZ\n" % (new_name, key, 0, 0, 1))
				write("%AI3_EndEncoding AdobeType\n")
		write('%%EndSetup\n')

		write('1 XR\n')

	def write_standard_encoding(self, new):
		write = self.file.write
		standard = encoding.adobe_standard
		last = None
		write("[")
		for i in range(len(standard)):
			if standard[i] != new[i]:
				if last != i - 1:
					if last is not None:
						write("\n")
					write("%d" % i)
				write("/%s" % new[i])
				last = i
		write(" TE\n")

	def close(self):
		self.file.write('%%Trailer\n')
		self.file.write('%%EOF\n')
		self.file.close()

	def write_properties(self, properties, bounding_rect = None):
		write = self.file.write
		style = 0; gradient = None
		if properties.line_pattern is not EmptyPattern:
			style = style | 0x01
			if properties.line_pattern.is_Solid:
				color = properties.line_pattern.Color()
				if color != self.line_color:
					self.line_color = color
					write('%f %f %f %f K\n' % cmyk(color))
			if properties.line_dashes != self.line_dashes:
				self.line_dashes = properties.line_dashes
				write('[')
				for d in self.line_dashes:
					write('%d ')
				write('] 0 d\n')
			if properties.line_width != self.line_width:
				self.line_width = properties.line_width
				write('%f w\n' % self.line_width)
			if properties.line_join != self.line_join:
				self.line_join = properties.line_join
				write('%d j\n' % ps_join[self.line_join])
			if properties.line_cap != self.line_cap:
				self.line_cap = properties.line_cap
				write('%d J\n' % ps_cap[self.line_cap])
		if properties.fill_pattern is not EmptyPattern:
			style = style | 0x02
			pattern = properties.fill_pattern
			if pattern.is_Solid:
				color = pattern.Color()
				if color != self.fill_color:
					self.fill_color = color
					write('%f %f %f %f k\n' % cmyk(color))
			elif pattern.is_Gradient and bounding_rect:
				if pattern.is_AxialGradient or pattern.is_RadialGradient:
					self.write_gradient((pattern, bounding_rect), style)
					self.fill_color = None
					#gradient = pattern, bounding_rect

		return style, gradient

	def write_gradient(self, gradient, style):
		pattern, rect = gradient
		key = self.gradient_id(pattern)
		write = self.file.write
		#write('Bb\n')
		if pattern.is_AxialGradient:
			vx, vy = pattern.Direction()
			angle = atan2(vy, vx) - pi / 2
			center = rect.center()
			rot = Rotation(angle, center)
			left, bottom, right, top = rot(rect)
			height = (top - bottom) * (1.0 - pattern.Border())
			trafo = rot(Translation(center))
			start = trafo(0, height / 2)
			write("1 %s %g %g %g %g 1 0 0 1 0 0 Bg\n"
					% (key[0], start.x, start.y, atan2(-vy, -vx) * 180.0 / pi,
						height))
		elif pattern.is_RadialGradient:
			cx, cy = pattern.Center()
			cx = cx * rect.right + (1 - cx) * rect.left
			cy = cy * rect.top   + (1 - cy) * rect.bottom
			radius = max(hypot(rect.left - cx, rect.top - cy),
							hypot(rect.right - cx, rect.top - cy),
							hypot(rect.right - cx, rect.bottom - cy),
							hypot(rect.left - cx, rect.bottom - cy))
			radius = radius * (1.0 - pattern.Border())
			write("0 0 0 0 Bh\n")
			write("1 %s %g %g 0 %g 1 0 0 1 0 0 Bg\n" % (key[0], cx, cy,radius))

		#write("f\n") # XXX
		#if style == 0x07:
		#    write("2 BB\n")
		#elif style == 0x03:
		#    write("1 BB\n")
		#else:
		#    write("0 BB\n")

	def PolyBezier(self, paths, properties, bounding_rect):
		write = self.file.write
		style, gradient = self.write_properties(properties, bounding_rect)
		if len(paths) > 1:
			write('*u\n')
		for path in paths:
			for i in range(path.len):
				type, control, p, cont = path.Segment(i)
				if type == Bezier:
					p1, p2 = control
					write('%g %g %g %g %g %g ' % (p1.x, p1.y, p2.x, p2.y,
													p.x, p.y))
					if cont == ContAngle:
						write('C')
					else:
						write('c')
				else:
					write('%g %g ' % tuple(p))
					if i > 0:
						if cont == ContAngle:
							write('L')
						else:
							write('l')
					else:
						write('m')
				write('\n')
			if path.closed:
				style = style | 0x04
			if path is not paths[-1] or gradient is None:
				write('nSFBNsfb'[style] + '\n')
			else:
				self.write_gradient(gradient, style)
			style = style & ~0x04
		if len(paths) > 1:
			write('*U\n')

	def SimpleText(self, object):
		properties = object.Properties()
		style, gradient = self.write_properties(properties,
												object.bounding_rect)
		write = self.file.write
		write("0 To\n")         # point text
		trafo = object.FullTrafo()
		write("%g %g %g %g %g %g 0 Tp\n" % trafo.coeff())
		write("TP\n")
		write("0 Tr\n")         # fill text
		font = properties.font
		size = properties.font_size
		write("/_%s %g Tf\n" % (font.PostScriptName(), size))
		write("(%s) Tx\n" % quote_ps_string(object.Text()))
		write("TO\n")

	def Image(self, object):
		write = self.file.write
		write("%AI5_File:\n%AI5_BeginRaster\n")
		write("[%g %g %g %g %g %g] " % object.Trafo().coeff())
		bbox = object.bounding_rect
		image = object.Data().image # .image is the PIL image
		write("0 0 %d %d " % image.size)
		write("%d %d " % image.size)
		write("8 %d 0 0 0 0 XI\n" % len(image.mode))
		_sketch.write_ps_hex(image.im, self.file, 72, '%')
		write("%AI5_EndRaster\n")
		# for whatever reason an image has to be followed by a N operator
		write("N\n")

	def BeginGroup(self):
		self.file.write('u\n')

	def EndGroup(self):
		self.file.write('U\n')

	def BeginLayer(self, layer):
		if self.layers_as_groups:
			self.BeginGroup()
		else:
			write = self.file.write
			write('%AI5_BeginLayer\n')
			write('%d 1 %d %d 0 0 ' % (layer.Visible(),
										not layer.Locked(),
										layer.Printable()))
			color = layer.OutlineColor()
			write('-1 %d %d %d Lb\n' % (255 * color.red, 255 * color.green,
										255 * color.blue))
			write('(%s) Ln\n' % quote_ps_string(layer.Name()))
		self.init_style()

	def EndLayer(self):
		if self.layers_as_groups:
			self.EndGroup()
		else:
			self.file.write('LB\n')
			self.file.write('%AI5_EndLayer--\n')

	def Save(self):
		for layer in self.document.Layers():
			if not layer.is_SpecialLayer:
				self.BeginLayer(layer)
				self.save_objects(layer.GetObjects())
				self.EndLayer()

	def save_objects(self, objects):
		for object in objects:
			if object.is_Compound:
				self.BeginGroup()
				self.save_objects(object.GetObjects())
				self.EndGroup()
			elif object.is_SimpleText:
				self.SimpleText(object)
			elif object.is_Image:
				self.Image(object)
			elif object.is_Bezier or object.is_Rectangle or object.is_Ellipse:
				self.PolyBezier(object.Paths(), object.Properties(),
								object.bounding_rect)

	
def save(document, file, filename, options = {}):
	#options['layers_as_groups'] = 1
	saver = AISaver(file, filename, document, options)
	saver.Save()
	saver.close()
	
