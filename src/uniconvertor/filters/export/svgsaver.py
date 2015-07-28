# -*- coding: utf-8 -*-

# Copyright (C) 2007, 2008 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

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
from app._sketch import RGBColor

from PIL import Image
import base64


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
	
svg_options={
				'ver':1.1,
			}

class SVGSaver:
	
	def __init__(self, file, filename, document, options):
		self.file = file
		self.filename = filename
		self.document = document
		self.options = {}
		self.options.update(svg_options)
		self.options.update(options)
		self.idcount = 0

	def csscolor(self, color):
		r, g, b = color.RGB()
		result = "#%02x%02x%02x" % (r * 255, g * 255, b * 255)
		
		# Uncalibrated device color
		# http://www.w3.org/TR/SVGColor12/#device
		if self.options['ver'] >= 1.2 and color.model == 'CMYK':
			c, m, y, k = color.getCMYK()
			result += " device-cmyk(%1.3f,%1.3f,%1.3f,%1.3f)" % (c, m, y, k)
		
		return result

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
				color = properties.line_pattern.Color()
				style.append("stroke:" + self.csscolor(color))
			if properties.line_dashes != ():
				dash=[]
				for d in properties.line_dashes:
					dd=d*properties.line_width
					dash.append ('%g' % dd)
				style.append("stroke-dasharray:" + join(dash,','))
			style.append('stroke-width:%g' % properties.line_width)
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
				style.append("fill:" + self.csscolor(pattern.Color()))
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
					% (pos, self.csscolor(color)))
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
		self.file.write(escape(object.Text().encode("utf-8")))
		self.file.write("\n")
		self.file.write(endText)

	def Image(self, object):
		from streamfilter import Base64Encode
		write = self.file.write
		image = object.Data()
		m11, m12, m21, m22, v1, v2 = object.Trafo().coeff()
		write('<image ')
		write('transform="matrix(%g %g %g %g %g %g)"\n' % \
			(m11, -m12, -m21, m22, v1, self.document.page_layout.height - v2 ))
		write('xlink:href="data:image/png;base64,')
		file = Base64Encode(self.file)
		if image.orig_image.mode == "CMYK":
			tempimage = image.Convert('RGB')
			tempimage.orig_image.save(file, 'PNG')
		else:
			image.orig_image.save(file, 'PNG')
		
		file.close()
		write('"\n')
		width = image.orig_image.size[0]
		height = image.orig_image.size[1]
		x = 0.0
		y = -height
		write('width="%g"\n' % width)
		write('height="%g"\n' % height)
		write('x="%g"\n' % x)
		write('y="%g"\n' % y)
		write('/>')

	def BeginGroup(self):
		self.file.write('<g>\n')

	def EndGroup(self):
		self.file.write('</g>\n')

	def Save(self):
		self.file.write('<?xml version="1.0" encoding="UTF-8" '
						'standalone="yes"?>\n')
		self.file.write('<!-- Created with sK1/UniConvertor (http://sk1project.org/) -->\n')
		left, bottom, right, top = self.document.PageRect()
		width = right - left
		height = top - bottom
		self.trafo = Trafo(1, 0, 0, -1, -left, top)
		self.file.write('<svg xmlns="http://www.w3.org/2000/svg" '
						'xmlns:xlink="http://www.w3.org/1999/xlink"')
		self.file.write('\n')
		self.file.write ('  width="%gpt" height="%gpt" viewBox="0 0 %g %g"' % (width, height, width, height))
		self.file.write('\n')
		self.file.write ('  fill-rule="evenodd"')
		self.file.write('>\n')
		
		# Put the definition of a simple triangular arrowhead in the file,
		# whether it is used or not
		# FIXME: for a proper solution for arrow heads, we could walk
		# over the object tree, collect all arrow heads actually used
		# and write them out here.
		#self.file.write( arrow_head_def )

		for layer in self.document.Layers():
			if not layer.is_SpecialLayer and layer.Printable() and len(layer.GetObjects()) > 0:
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
			elif object.is_Image:
				self.Image(object)
			elif object.is_Bezier or object.is_Rectangle or object.is_Ellipse:
				self.PolyBezier(object.Paths(), object.Properties(),
								object.bounding_rect)



def save(document, file, filename, options = {}):
	saver = SVGSaver(file, filename, document, options)
	saver.Save()
	saver.close()
