# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
# Part of the code for Arrow heads and text from Paul Giotta (2002)
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
#tk_file_type = ("Scalable Vector Graphics (SVG)", '.svg')
#extensions = '.svg'
format_name = 'SVG'
#unload = 1
###End

from string import join, replace
import re
from math import atan2, hypot, pi

from app import Bezier, EmptyPattern, Trafo, Rotation, Translation
from app.conf import const

def csscolor(color):
	return "#%02x%02x%02x" \
			% (255 * color.red, 255 * color.green, 255 * color.blue)

svg_joins = ('miter', 'round', 'bevel')
svg_caps = (None, 'butt', 'round', 'square')

def escape(data):
	"""Escape &, \", ', <, and > in the string data.
	"""
	data = replace(data, "&", "&amp;")
	data = replace(data, "<", "&lt;")
	data = replace(data, ">", "&gt;")
	data = replace(data, '"', "&quot;")
	data = replace(data, "'", "&apos;")
	return data


# FIXME: This is the definition of a simple triangular arrowhead It is
# copied directly from the an example in the SVG spec This is a
# prototype only. Do not consider this an acceptable long term solution
arrow_head_def = '''  <defs> 
	<marker id="ArrowEnd" viewBox="0 0 10 10" refX="0" refY="5" 
		markerUnits="strokeWidth" 
		markerWidth="4" 
		markerHeight="3" 
		orient="auto"> 
		<path d="M 0 0 L 10 5 L 0 10 z" /> 
	</marker>
	<marker id="ArrowStart" viewBox="0 0 10 10" refX="10" refY="5" 
		markerUnits="strokeWidth" 
		markerWidth="4" 
		markerHeight="3" 
		orient="auto"> 
		<path d="M 10 0 L 0 5 L 10 10 z" /> 
	</marker> </defs>
'''
	


class SVGSaver:

	def __init__(self, file, filename, document, options):
		self.file = file
		self.filename = filename
		self.document = document
		self.options = options
		self.idcount = 0

	def close(self):
		self.file.close()

	def new_id(self):
		self.idcount = self.idcount + 1
		return self.idcount

	fontMap = {"Times"     : re.compile("Times-Roman.*"),
				"Helvetica" : re.compile("Helvetica.*"),
				"Courier"   : re.compile("Courier.*"),
				}

	def make_style(self, properties, bounding_rect = None,
					omit_stroke = 0):
		"""Return the properties as a value for the SVG style attribute

		If omit_stroke is true, ignore the line properties. This is
		needed when creating the style for text objects which can't be
		stroked in Sketch currently but may nevertheless have line
		properties (e.g. because of dynamic styles).
		"""
		style = []
		if not omit_stroke and properties.line_pattern is not EmptyPattern:
			if properties.line_pattern.is_Solid:
				color = properties.line_pattern.Color().RGB()
				style.append("stroke:" + csscolor(color))
			if properties.line_dashes != ():
				#FIXME: This could be much more intelligent, but this
				#quick hack will only produce one style of dashed line
				#for the moment.
				style.append("stroke-dasharray:" + "6,3")
			style.append('stroke-width:' + `properties.line_width`)
			if properties.line_join != const.JoinMiter:
				style.append('stroke-linejoin:'
								+ svg_joins[properties.line_join])
			if properties.line_cap != const.CapButt:
				style.append('stroke-linecap:' + svg_caps[properties.line_cap])

			# FIXME: when arrow heads are implemented properly, change
			# this accordingly
			# FIXME: currently the orientation of the arrow heads is
			# wrong.
			if properties.line_arrow1 <> None:
				style.append('marker-start:url(#ArrowStart)')
			if properties.line_arrow2 <> None:
				style.append('marker-end:url(#ArrowEnd)')
		else:
			style.append("stroke:none")
		if properties.fill_pattern is not EmptyPattern:
			pattern = properties.fill_pattern
			if pattern.is_Solid:
				style.append("fill:" + csscolor(pattern.Color().RGB()))
			elif pattern.is_Gradient and bounding_rect:
				if pattern.is_AxialGradient or pattern.is_RadialGradient:
					gradient_id = self.write_gradient((pattern, bounding_rect),
														style)
					style.append("fill:url(#%s)" % gradient_id)
				else:
					style.append("fill:black")
		else:
			style.append("fill:none")

		if properties.font is not None:
			font = properties.font.PostScriptName()
			size = properties.font_size

			for svgfont, pattern in self.fontMap.items():
				if pattern.match(font):
					font = svgfont
					break
			style.append("font-family:" + font)
			style.append("font-size:" + str(size))

		return join(style, '; ')

	def write_gradient(self, (pattern, rect), style):
		write = self.file.write
		gradient_id = self.new_id()
		stops = pattern.Gradient().Colors()
		write('<defs>')
		if pattern.is_AxialGradient:
			vx, vy = pattern.Direction()
			angle = atan2(vy, vx) - pi / 2
			center = rect.center()
			rot = Rotation(angle, center)
			left, bottom, right, top = rot(rect)
			height = (top - bottom) * (1.0 - pattern.Border())
			trafo = self.trafo(rot(Translation(center)))
			start = trafo(0, height / 2)
			end = trafo(0, - height / 2)
			write('<linearGradient id="%s" x1="%g" y1="%g" x2="%g" y2="%g"'
					' gradientUnits="userSpaceOnUse">\n'
					% ((gradient_id,) + tuple(start) + tuple(end)))
			tag = 'linearGradient'
		elif pattern.is_RadialGradient:
			cx, cy = pattern.Center()
			cx = cx * rect.right + (1 - cx) * rect.left
			cy = cy * rect.top   + (1 - cy) * rect.bottom
			radius = max(hypot(rect.left - cx, rect.top - cy),
							hypot(rect.right - cx, rect.top - cy),
							hypot(rect.right - cx, rect.bottom - cy),
							hypot(rect.left - cx, rect.bottom - cy))
			radius = radius * (1.0 - pattern.Border())
			cx, cy = self.trafo(cx, cy)
			write('<radialGradient id="%s" cx="%g" cy="%g" r="%g" fx="%g"'
					' fy="%g" gradientUnits="userSpaceOnUse">\n'
					% (gradient_id, cx, cy, radius, cx, cy))
			tag = 'radialGradient'
			stops = stops[:]
			stops.reverse()
			for i in range(len(stops)):
				pos, color = stops[i]
				stops[i] = 1.0 - pos, color
		for pos, color in stops:
			write('<stop offset="%g" style="stop-color:%s"/>\n'
					% (pos, csscolor(color)))
		write('</%s>\n' % tag)
		write('</defs>')
		return gradient_id

	def PolyBezier(self, paths, properties, bounding_rect):
		style = self.make_style(properties, bounding_rect)
		write = self.file.write
		write('<path style="%s" ' % style)
		data = []
		for path in paths:
			for i in range(path.len):
				type, control, p, cont = path.Segment(i)
				p = self.trafo(p)
				if type == Bezier:
					p1, p2 = control
					p1 = self.trafo(p1)
					p2 = self.trafo(p2)
					data.append('C %g %g %g %g %g %g' % (p1.x, p1.y,
															p2.x, p2.y,
															p.x, p.y))
				else:
					if i > 0:
						data.append('L %g %g' % tuple(p))
					else:
						data.append('M %g %g' % tuple(p))
			if path.closed:
				data.append('z')
		write('d="%s"/>\n' % join(data, ''))


	def SimpleText(self, object):
		style = self.make_style(object.Properties(), object.bounding_rect,
								omit_stroke = 1)

		# Char glyphs are inherently upside-down in SVG (compared to
		# sketch) since the y axis points toward the bottom of the page
		# in SVG, but the characters are oriented toward the top of the
		# page. This extra transform inverts them.
		textTrafo = Trafo(1, 0, 0, -1, 0, 0)

		tm = self.trafo(object.Trafo()(textTrafo)).coeff()

		beginText = '<text style="%s" transform="matrix(%g %g %g %g %g %g)">\n'
		endText = '</text >\n'

		self.file.write(beginText %  (( style, ) + tm) )
		self.file.write(escape(object.Text()))
		self.file.write("\n")
		self.file.write(endText)

	def BeginGroup(self):
		self.file.write('<g>\n')

	def EndGroup(self):
		self.file.write('</g>\n')

	def Save(self):
		self.file.write('<?xml version="1.0" encoding="ISO-8859-1" '
						'standalone="yes"?>\n')

		left, bottom, right, top = self.document.BoundingRect()
		width = right - left
		height = top - bottom
		self.trafo = Trafo(1, 0, 0, -1, -left, top)
		self.file.write('<svg width="%g" height="%g"' % (width, height))
		#self.file.write(' transform="matrix(%g,%g,%g,%g,%g,%g)">\n' % trafo)
		self.file.write('>\n')

		# Put the definition of a simple triangular arrowhead in the file,
		# whether it is used or not
		# FIXME: for a proper solution for arrow heads, we could walk
		# over the object tree, collect all arrow heads actually used
		# and write them out here.
		self.file.write( arrow_head_def )

		for layer in self.document.Layers():
			if not layer.is_SpecialLayer and layer.Printable():
				self.BeginGroup()
				self.save_objects(layer.GetObjects())
				self.EndGroup()
		self.file.write('</svg>')

	def save_objects(self, objects):
		for object in objects:
			if object.is_Compound:
				self.BeginGroup()
				self.save_objects(object.GetObjects())
				self.EndGroup()
			elif object.is_SimpleText:
				self.SimpleText(object)
			#elif object.is_Image:
			#    self.Image(object)
			elif object.is_Bezier or object.is_Rectangle or object.is_Ellipse:
				self.PolyBezier(object.Paths(), object.Properties(),
								object.bounding_rect)



def save(document, file, filename, options = {}):
	saver = SVGSaver(file, filename, document, options)
	saver.Save()
	saver.close()
