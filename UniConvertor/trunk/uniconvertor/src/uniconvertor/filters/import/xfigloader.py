# -*- coding: utf-8 -*-
# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000 by Bernhard Herzog
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
#class_name = 'XFigLoader'
#rx_magic = r'^#FIG (?P<version>3\.[012])'
#tk_file_type = ('XFig', '.fig')
format_name = 'XFig'
#unload = 1
#standard_messages = 1
###End

(''"XFig")

#
# This is a simple import filter for Fig files.
#
# It is incomplete and may refuse to load some valid Fig files. It
# should work with versions 3.0, 3.1 and 3.2 of the Fig format.
#
# TODO (not in any particular order):
#
# - convert X-Splines (new in XFig 3.2) to bezier curves if that can be done
#
# - parse strings properly
#
# - use more of the header information: pagesize, orientation, ...
#
# - patterns, arrows, dashes
#


import sys
from string import strip, atoi, split, atof, lower
from operator import getitem
from math import atan2

from app import SketchLoadError
from app.conf import const
from app.events.warn import warn, INTERNAL, warn_tb

from app.io.load import SimplifiedLoader, EmptyCompositeError
from app import skread
from app.io import load
tokenize = skread.tokenize_line

from app import Scale, Trafo, Translation, Rotation, StandardColors, \
		XRGBColor, SolidPattern, EmptyPattern, Blend, GetFont, SimpleText, \
		CreatePath
from app.Graphics import text, pagelayout



std_colors = [StandardColors.black, StandardColors.blue, StandardColors.green,
				StandardColors.cyan, StandardColors.red, StandardColors.magenta,
				StandardColors.yellow, StandardColors.white] + \
				map(XRGBColor, ("#000090", "#0000b0", "#0000d0", "#87ceff",
								"#009000", "#00b000", "#00d000", "#009090",
								"#00b0b0", "#00d0d0", "#900000", "#b00000",
								"#d00000", "#900090", "#b000b0", "#d000d0",
								"#803000", "#a04000", "#c06000", "#ff8080",
								"#ffa0a0", "#ffc0c0", "#ffe0e0", "#ffd700"))

BLACK = 0
WHITE = 7
DEFAULT_COLOR = -1

xfig_join = (const.JoinMiter, const.JoinBevel, const.JoinRound)
xfig_cap = (const.CapButt, const.CapRound, const.CapProjecting)

psfonts = ("Times-Roman", "Times-Italic", "Times-Bold",
			"Times-BoldItalic", "AvantGarde-Book",
			"AvantGarde-BookOblique", "AvantGarde-Demi",
			"AvantGarde-DemiOblique", "Bookman-Light",
			"Bookman-LightItalic", "Bookman-Demi", "Bookman-DemiItalic",
			"Courier", "Courier-Oblique", "Courier-Bold",
			"Courier-BoldOblique", "Helvetica", "Helvetica-Oblique",
			"Helvetica-Bold", "Helvetica-BoldOblique",
			"Helvetica-Narrow", "Helvetica-Narrow-Oblique",
			"Helvetica-Narrow-Bold", "Helvetica-Narrow-BoldOblique",
			"NewCenturySchlbk-Roman", "NewCenturySchlbk-Italic",
			"NewCenturySchlbk-Bold", "NewCenturySchlbk-BoldItalic",
			"Palatino-Roman", "Palatino-Italic", "Palatino-Bold",
			"Palatino-BoldItalic", "Symbol", "ZapfChancery-MediumItalic",
			"ZapfDingbats", "Times-Roman")

texfonts = ('Times-Roman', 'Times-Roman', 'Times-Bold', 'Times-Italic',
			'Helvetica', 'Courier')
# for user messages:
tex_font_names = ('Default font', 'Roman', 'Bold', 'Italic', 'Sans Serif',
					'Typewriter')

align = (text.ALIGN_LEFT, text.ALIGN_CENTER, text.ALIGN_RIGHT)

def coords_to_points(coords, trafo):
	# Given a list coords of coordinate pairs [x1, y1, x2, y2, ...],
	# return a new list of point objects: [Point(x1, y1), Point(x2, y2),...]
	# TRAFO is applied to point.
	# coords must have an even length.
	if len(coords) % 2 != 0:
		raise ValueError("coordinate has odd length")
	num = len(coords)
	coords = [coords] * (num / 2)
	return map(trafo, map(getitem, coords, range(0, num, 2)),
				map(getitem, coords, range(1, num, 2)))

class XFigLoader(SimplifiedLoader):

	format_name = format_name
	
	functions = [('define_color',	0),
					('read_ellipse',       1),
					('read_polyline',      2),
					('read_spline',        3),
					('read_text',          4),
					('read_arc',           5),
					('begin_compound',     6),
					('end_compound',       -6)]

	def __init__(self, file, filename, match):
		SimplifiedLoader.__init__(self, file, filename, match)
		self.layout = None
		self.format_version = atof(match.group('version'))
		self.trafo = Trafo(1.0, 0.0, 0.0, -1.0, 0.0, 800)
		self.colors = std_colors + [StandardColors.black] * 512
		self.depths = {} # map object ids to depth
		self.guess_cont()

	def readline(self):
		line = SimplifiedLoader.readline(self)
		while line[:1] == '#':
			line = SimplifiedLoader.readline(self)
		return line

	def get_compiled(self):
		funclist = {}
		for name, rx in self.functions:
			funclist[rx] = getattr(self, name)
		return funclist

	def set_depth(self, depth):
		self.depths[id(self.object)] = -depth

	def define_color(self, line):
		idx, color = split(line, None, 1)
		self.colors[atoi(idx)] = XRGBColor(color)

	def get_pattern(self, color, style = None):
		if style == -1:
			return EmptyPattern
		rgb = self.colors[color]
		if style is not None:
			if color in (BLACK, DEFAULT_COLOR):
				if style > 0 and style <= 20:
					rgb = Blend(self.colors[WHITE], rgb, (20 - style) / 20.0)
				elif style == 0:
					rgb = self.colors[WHITE]
			else:
				if style >= 0 and style < 20:
					rgb = Blend(self.colors[BLACK], rgb, (20 - style) / 20.0)
				elif style > 20 and style <= 40:
					rgb = Blend(self.colors[WHITE], rgb, (style - 20) / 20.0)
		return SolidPattern(rgb)

	def line(self, color, width, join, cap, style = 0, style_val = 0):
		if width:
			val = style_val / width
			width = width * 72.0/80.0
			pattern = self.get_pattern(color)
			dashes = ()
			if style == 1:
				# dashed
				dashes = (val, val)
			elif style == 2:
				# dotted
				dashes = (1 / width, val)
			elif style == 3:
				# dash-dot
				dashes = (val, 0.5 * val, 1 / width, 0.5 * val)
			elif style == 4:
				# dash-dot-dot
				dashes = (val, 0.45 * val, 1 / width, 0.333 * val,
							1 / width, 0.45 * val)
			elif style == 5:
				# dash-dot-dot-dot
				dashes = (val, 0.4 * val,
							1 / width, 0.333 * val, 1 / width, 0.333 * val,
							1 / width, 0.4 * val)
			try:
				self.set_properties(line_pattern = pattern,
									line_width = width,
									line_join = xfig_join[join],
									line_cap = xfig_cap[cap],
									line_dashes = dashes)
			except:
				raise SketchLoadError("can't assign line style: %s:%s"
										% sys.exc_info()[:2])
		else:
			self.empty_line()

	def fill(self, color, style):
		pattern = self.get_pattern(color, style)
		try:
			self.set_properties(fill_pattern = pattern)
		except:
			raise SketchLoadError("can't assign fill style: %s:%s"
									% sys.exc_info()[:2])

	def font(self, font, size, flags):
		if flags & 4:
			# A PostScript font
			name = psfonts[font]
		else:
			# A TeX font. map to psfont
			name = texfonts[font]
			self.add_message(_("PostScript font `%(ps)s' substituted for "
								"TeX-font `%(tex)s'")
								% {'ps':name, 'tex':tex_font_names[font]})
								
		self.set_properties(font = GetFont(name), font_size = size)

	def read_tokens(self, num):
		# read NUM tokens from the input file. return an empty list if
		# eof met before num items are read
		readline = self.readline; tokenize = skread.tokenize_line
		tokens = []
		while len(tokens) < num:
			line = readline()
			if not line:
				return []
			tokens = tokens + tokenize(line)
		return tokens

	def read_arc(self, line):
		readline = self.readline; tokenize = skread.tokenize_line
		args = tokenize(line)
		if len(args) != 21:
			raise SketchLoadError('Invalid Arc specification')
		sub_type, line_style, thickness, pen_color, fill_color, depth, \
					pen_style, area_fill, style, cap, direction, \
					forward_arrow, backward_arrow, \
					cx, cy, x1, y1, x2, y2, x3, y3 = args
		self.fill(fill_color, area_fill)
		self.line(pen_color, thickness, const.JoinMiter, cap,
					line_style, style)
		
		if forward_arrow: readline() # XXX: implement this
		if backward_arrow:readline() # XXX: implement this

		trafo = self.trafo
		center = trafo(cx, cy); start = trafo(x1, y1); end = trafo(x3, y3)
		radius = abs(start - center)
		start_angle = atan2(start.y - center.y, start.x - center.x)
		end_angle = atan2(end.y - center.y, end.x - center.x)
		if direction == 0:
			start_angle, end_angle = end_angle, start_angle
		if sub_type == 1:
			sub_type = const.ArcArc
		else:
			sub_type = const.ArcPieSlice
		self.ellipse(radius, 0, 0, radius, center.x, center.y,
						start_angle, end_angle, sub_type)
		self.set_depth(depth)

	def read_ellipse(self, line):
		readline = self.readline; tokenize = skread.tokenize_line
		args = tokenize(line)
		if len(args) != 19:
			raise SketchLoadError('Invalid Ellipse specification')
		sub_type, line_style, thickness, pen_color, fill_color, depth, \
					pen_style, area_fill, style, direction, angle, \
					cx, cy, rx, ry, sx, sy, ex, ey = args
		self.fill(fill_color, area_fill)
		self.line(pen_color, thickness, const.JoinMiter, const.CapButt,
					line_style, style)
		
		center = self.trafo(cx, cy); radius = self.trafo.DTransform(rx, ry)
		trafo = Trafo(radius.x, 0, 0, radius.y)
		trafo = Rotation(angle)(trafo)
		trafo = Translation(center)(trafo)
		apply(self.ellipse, trafo.coeff())
		self.set_depth(depth)

	def read_polyline(self, line):
		readline = self.readline; tokenize = skread.tokenize_line
		args = tokenize(line)
		if len(args) != 15:
			raise SketchLoadError('Invalid PolyLine specification')
		sub_type, line_style, thickness, pen_color, fill_color, depth, \
					pen_style, area_fill, style, join, cap, \
					radius, forward_arrow, backward_arrow, npoints = args
		self.fill(fill_color, area_fill)
		self.line(pen_color, thickness, join, cap, line_style, style)

		if forward_arrow: readline() # XXX: implement this
		if backward_arrow:readline() # XXX: implement this
		if sub_type == 5: readline() # imported picture

		ncoords = npoints * 2
		pts = self.read_tokens(ncoords)
		if not pts:
			raise SketchLoadError('Missing points for polyline')
		if len(pts) > ncoords:
			del pts[ncoords:]
		
		trafo = self.trafo
		
		if sub_type in (1, 3, 5):
			path = CreatePath()
			map(path.AppendLine, coords_to_points(pts, trafo))
			if sub_type == 3:
				path.load_close(1)
			self.bezier(paths = path)
			self.set_depth(depth)
			
		elif sub_type in (2, 4):
			wx, wy = trafo(pts[2], pts[3]) - trafo(pts[0], pts[1])
			hx, hy = trafo(pts[4], pts[5]) - trafo(pts[2], pts[3])
			x, y =  trafo(pts[0], pts[1])
			if sub_type == 4 and radius > 0:
				radius1 = (radius * 72.0/80.0) / max(abs(wx),abs(wy))
				radius2 = (radius * 72.0/80.0) / max(abs(hx),abs(hy))
			else:
				radius1 = radius2 = 0
			self.rectangle(wx, wy, hx, hy, x, y, radius1 = radius1, radius2 = radius2)
			self.set_depth(depth)

	def read_spline(self, line):
		readline = self.readline; tokenize = skread.tokenize_line
		args = tokenize(line)
		if len(args) != 13:
			raise SketchLoadError('Invalid Spline specification')
		sub_type, line_style, thickness, pen_color, fill_color, depth, \
					pen_style, area_fill, style, cap, \
					forward_arrow, backward_arrow, npoints = args
		closed = sub_type & 1
		if forward_arrow: readline()
		if backward_arrow:readline()

		# in 3.2 all splines are stored as x-splines...
		if self.format_version == 3.2:
			if sub_type in (0, 2):
				sub_type = 4
			else:
				sub_type = 5
		
		self.fill(fill_color, area_fill)
		self.line(pen_color, thickness, 0, cap, line_style, style)
		
		ncoords = npoints * 2
		pts = self.read_tokens(ncoords)
		if not pts:
			raise SketchLoadError('Missing points for spline')
		if len(pts) > ncoords:
			del pts[ncoords:]
		pts = coords_to_points(pts, self.trafo)
		
		path = CreatePath()
		if sub_type in (2, 3):
			# interpolated spline, read 2 control points for each node
			ncontrols = 4 * npoints
			controls = self.read_tokens(ncontrols)
			if not controls:
				raise SketchLoadError('Missing control points for spline')
			if len(controls) > ncontrols:
				del controls[ncontrols:]
			controls = coords_to_points(controls[2:-2], self.trafo)
			path.AppendLine(pts[0])
			ncontrols = 2 * (npoints - 1)
			controls = [controls] * (npoints - 1)
			map(path.AppendBezier,
				map(getitem, controls, range(0, ncontrols, 2)),
				map(getitem, controls, range(1, ncontrols, 2)),
				pts[1:])
		elif sub_type in (0, 1):
			# approximated spline
			f13 = 1.0 / 3.0; f23 = 2.0 / 3.0
			curve = path.AppendBezier
			straight = path.AppendLine
			last = pts[0]
			cur = pts[1]
			start = node = (last + cur) / 2
			if closed:
				straight(node)
			else:
				straight(last)
				straight(node)
			last = cur
			for cur in pts[2:]:
				c1 = f13 * node + f23 * last
				node = (last + cur) / 2
				c2 = f13 * node + f23 * last
				curve(c1, c2, node)
				last = cur
			if closed:
				curve(f13 * node + f23 * last, f13 * start + f23 * last, start)
			else:
				straight(last)
		elif sub_type in (4, 5):
			# An X-spline. Treat it like a polyline for now.
			# read and discard the control info
			self.read_tokens(npoints)
			self.add_message(_("X-Spline treated as PolyLine"))
			map(path.AppendLine, pts)
			if closed:
				path.AppendLine(path.Node(0))
		if closed:
			path.load_close(1)
		self.bezier(paths = path)
		self.set_depth(depth)

	def read_text(self, line):
		args = tokenize(line, 12) # don't tokenize the text itself
		if len(args) != 13: # including the unparsed rest of the line
			raise SketchLoadError('Invalid text specification')
		sub_type, color, depth, pen_style, font, size, angle, flags, \
					height, length, x, y, rest = args
		self.fill(color, None)
		self.font(font, size * 0.9, flags)
		
		if len(rest) > 2: #at least a space and a newline
			# read the actual text. This implementation may fail in
			# certain cases!
			string = rest[1:]
			while string[-5:] != '\\001\n':
				line = self.readline()
				if not line:
					raise SketchLoadError('Premature end of string')
				string = string + line
			globals = {'__builtins__': {}}
			try:
				# using eval here might be a security hole!
				string = eval('"""' + string[:-5] + '"""', globals)
			except:
				string = eval("'''" + string[:-5] + "'''", globals)
		else:
			raise SketchLoadError('Invalid text string')
			
		trafo = Translation(self.trafo(x, y))(Rotation(angle))
		self.simple_text(string, trafo = trafo, halign = align[sub_type])
		self.set_depth(depth)

	def begin_compound(self, line):
		self.begin_group()

	def end_compound(self, line):
		try:
			self.end_group()
		except EmptyCompositeError:
			pass

	def end_composite(self):
		# sort composite_items by their depth
		items = self.composite_items
		depths = map(self.depths.get, map(id, items), [-10000]*len(items))
		depths = map(None, depths, range(len(items)), items)
		depths.sort()
		self.composite_items = map(getitem, depths, [2] * len(items))
		SimplifiedLoader.end_composite(self)

	def read_header(self):
		format = orientation = None
		if self.format_version >= 3.0:
			line = strip(self.readline())
			if line:
				# portrait/landscape
				if lower(line) == 'landscape':
					orientation = pagelayout.Landscape
				else:
					orientation = pagelayout.Portrait
			else:
				raise SketchLoadError('No format specification')
			line = strip(self.readline())
			if line:
				# centering
				line = lower(line)
				if line == 'center' or line == 'flush left':
					line = lower(strip(self.readline()))
			if not line:
				raise SketchLoadError(
					'No Center/Flushleft or Units specification')
			if line == 'metric':
				# ignore for now
				pass
			if self.format_version >= 3.2:
				self.readline() # papersize
				self.readline() # magnification
				self.readline() # pages
				self.readline() # transparent color
		line = strip(self.readline())
		if line:
			try:
				ppi, coord = map(atoi, split(line))
			except:
				raise SketchLoadError('Invalid Resolution specification')
			self.trafo = self.trafo(Scale(72.0 / ppi))


	def Load(self):
		file = self.file
		funclist = self.get_compiled()
		# binding frequently used functions to local variables speeds up
		# the process considerably...
		readline = file.readline; tokenize = skread.tokenize_line
		self.document()
		self.layer(_("Layer 1"))
		try:
			self.read_header()
			line = self.readline()
			while line:
				tokens = tokenize(line, 1)
				if len(tokens) > 1:
					function, rest = tokens
				else:
					function = tokens[0]
					rest = ''
				if type(function) == type(0):
					function = funclist.get(function)
					if function:
						function(rest)
				line = self.readline()
				
		except SketchLoadError, value:
			warn_tb(INTERNAL)
			raise SketchLoadError('%d:%s' % (self.lineno, str(value))), None,\
					sys.exc_traceback
		except:
			if load._dont_handle_exceptions:
				warn(INTERNAL, 'XFigLoader: error reading line %d:%s',
						self.lineno, `line`)
				raise
			raise SketchLoadError(_("error in line %d:\n%s")
									% (self.lineno, `line`)), None,\
									sys.exc_traceback
		self.end_all()
		self.object.load_Completed()
		return self.object





