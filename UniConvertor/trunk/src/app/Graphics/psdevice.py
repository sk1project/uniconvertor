# Sketch - A Python-based interactive drawing program
# Copyright (C) 1996, 1997, 1998, 1999, 2000, 2002, 2003 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

#
# PostScriptDevice:
#
# A graphics device which outputs to a postscript file. The postscript
# file can be an EPS file.
#

import os
from types import StringType
from math import pi, sqrt
from string import join, strip, lstrip, split

from sk1libs.utils import Empty

from app import _, config, _sketch, Scale, sKVersion
from app.events.warn import pdebug, warn_tb, warn, USER, INTERNAL
from app.Lib.psmisc import quote_ps_string, make_textline

from app import IdentityMatrix
from app.Lib import type1

from graphics import CommonDevice
import color
import pagelayout
from sk1libs import ft2engine as font


class _DummyLineStyle:
	def Execute(device):
		device.SetLineColor(color.ExtStandardColors.black)
		device.SetLineAttributes(1, 0, 1, 0)

defaultLineStyle = _DummyLineStyle()

ps_join = (0, 1, 2)
ps_cap = (None, 0, 1, 2)

# header comments. Currently the type of all parameters is <textline>
HeaderComments = [('For', '%%%%For: %s\n'),
					('CreationDate', '%%%%CreationDate: %s\n'),
					('Title', '%%%%Title: %s\n')]

class PostScriptDevice(CommonDevice):

	draw_visible = 0
	draw_printable = 1

	file = None # default value for file in case open fails.
	
	def __init__(self, file, as_eps = 1, bounding_box = None,
					document = None, printable = 1, visible = 0, rotate = 0,
					embed_fonts = 0, **options):
		if as_eps and not bounding_box:
			raise ValueError, 'bounding_box required for EPS'

		self.fill = 0; self.line = 0
		self.properties = None
		self.line = defaultLineStyle
		self.as_eps = as_eps
		self.needed_resources = {}
		self.include_resources = {}
		self.supplied_resources = []
		self.draw_visible = visible
		self.draw_printable = printable
		self.gradient_steps = config.preferences.gradient_steps_print
		self.init_props()

		if document:
			document.WalkHierarchy(self.add_obj_resources,
									visible = self.draw_visible,
									printable = self.draw_printable)
			self.needed_resources.update(self.include_resources)

		# take care of the case where we're writing to an EPS that's
		# referenced by the document. This is a bit tricky. If the file
		# argument is an already opened file object, all hope is lost.
		# If it's a filename we look at all EPS files contained in the
		# document and load them into memory if and only if they are the
		# file we're writing into.

		# dictionary used as a set of ids of EpsData objects.
		self.loaded_eps_files = {}

		# the original contents of the file we're writing to if it is
		# actually referenced.
		self.loaded_eps_contents = None

		# search through the document if file is a string with the name
		# of an existing file.
		if isinstance(file, StringType) and os.path.exists(file):
			self.filename = file
			document.WalkHierarchy(self.handle_writes_to_embedded_eps,
									visible = self.draw_visible,
									printable = self.draw_printable)

		if type(file) == StringType:
			file = open(file, 'w')
			self.close_file = 1
		else:
			self.close_file = 0
		self.file = file

		if rotate:
			width, height = document.PageSize()
			llx, lly, urx, ury = bounding_box
			bounding_box = (height - ury, llx, height - lly, urx)

		write = file.write
		if as_eps:
			write("%!PS-Adobe-3.0 EPSF-3.0\n")
		else:
			write("%!PS-Adobe-3.0\n")
		# header comments
		for name, format in HeaderComments:
			if options.has_key(name):
				value = options[name]
				if value:
					write(format % make_textline(value))
		write("%%%%Creator: sK1 %s\n" % sKVersion)
		write("%%Pages: 1\n")	# there is exactly one page
		if bounding_box:
			[llx, lly, urx, ury] = map(int, bounding_box)
			write('%%%%BoundingBox: %d %d %d %d\n'
					% (llx - 1, lly - 1, urx + 1, ury + 1))

		if rotate and document.Layout().Orientation() == pagelayout.Landscape:
			write("%%Orientation: Landscape\n")

		# XXX The Extensions comment should take embedded EPS files into
		# account. (the colorimage operator should be optional)
		write("%%Extensions: CMYK\n")

		write("%%DocumentSuppliedResources: (atend)\n")

		if self.needed_resources:
			start_written = 0
			for restype, value in self.needed_resources.keys():
				if restype == 'font' and embed_fonts:
					continue
				if not start_written:
					write('%%%%DocumentNeededResources: %s %s\n'
							% (restype, value))
				else:
					write('%%%%+ %s %s\n' % (restype, value))

		write("%%EndComments\n\n")

		write('%%BeginProlog\n')
		#procfile = os.path.join(config.user_config_dir, config.postscript_prolog)
		procfile=config.postscript_prolog
		procfile = open(procfile, 'r')
		line = procfile.readline()
		self.supplied_resources.append(join(split(strip(line))[1:]))
		write(line)
		for line in map(lstrip, procfile.readlines()):
			if line and line[0] != '%':
				write(line)
		write('%%EndResource\n')
		procfile.close()

		write('%%EndProlog\n\n')

		write('%%BeginSetup\n')
		if self.needed_resources:
			for res in self.include_resources.keys():
				restype, value = res
				if restype == 'font' and embed_fonts:
					fontfile = font.GetFont(value).FontFileName()
					if fontfile:
						try:
							fontfile = open(fontfile, 'rb')
							write("%%%%BeginResource: %s %s\n" % res)
							type1.embed_type1_file(fontfile, self.file)
							write("\n%%EndResource\n")
						except IOError, exc:
							warn(USER, _("Can't embed font '%s': %s")
									% (value, exc))
						del self.needed_resources[res]
						self.supplied_resources.append(join(res))
						continue
					else:
						warn(USER,
								_("Can't find file for font '%s' for embedding")
								% value)
				write('%%%%IncludeResource: %s %s\n' % res)
		write('\n10.433 setmiterlimit\n')	# 11 degree
		write('%%EndSetup\n\n')

		write('%%Page: 1 1\n')
		write('SketchDict begin\n')
		if rotate:
			self.Rotate(pi/2)
			self.Translate(0, -height)

	def init_props(self):
		self.init_line_props()
		self.init_color_props()
		self.init_font_props()

	def add_obj_resources(self, obj):
		# append reources from OBJ to self.needed_resources
		if obj.has_font:
			res = ('font', obj.Font().PostScriptName())
			self.include_resources[res] = 1
		if obj.is_Eps:
			self.needed_resources.update(obj.PSNeededResources())

	def handle_writes_to_embedded_eps(self, obj):
		if obj.is_Eps:
			data = obj.Data()
			# we only need to investigate this if we've not processed it yet
			if not self.loaded_eps_files.has_key(id(data)):
				filename = data.Filename()
				if os.path.samefile(self.filename, filename):
					# it's the same file we're going to write into, so load it
					self.loaded_eps_files[id(data)] = 1
					if self.loaded_eps_contents is None:
						self.loaded_eps_contents = open(filename).read()

	trailer_written = 0
	def Close(self):
		if self.file is not None and not self.file.closed:
			if not self.trailer_written:
				write = self.file.write
				write('%%PageTrailer\n')
				write('showpage\n')
				write('%%Trailer\n')
				write('end\n')
				if self.supplied_resources:
					write('%%%%DocumentSuppliedResources: %s\n'
							% self.supplied_resources[0])
					for res in self.supplied_resources[1:]:
						write('%%%%+ %s\n' % res)

				write('%%EOF\n')
				self.trailer_written = 1
			if self.close_file:
				self.file.close()

	def __del__(self):
		try:
			self.Close()
		except:
			warn_tb(INTERNAL, "In __del__ of psdevice")

	def PushTrafo(self):
		self.file.write('pusht\n')

	def Concat(self, trafo):
		self.file.write('[%g %g %g %g %g %g] concat\n'
						% (trafo.m11, trafo.m21, trafo.m12, trafo.m22,
							trafo.v1, trafo.v2))

	def Translate(self, x, y = None):
		if y is None:
			x, y = x
		self.file.write('%g %g translate\n' % (x, y))

	def Rotate(self, angle):
		self.file.write('%g rotate\n' % (angle * 180 / pi))

	def Scale(self, scale):
		self.file.write('%g dup scale\n' % scale)

	def PopTrafo(self):
		self.file.write('popt\n')

	def PushClip(self):
		self.file.write('pushc\n')

	def PopClip(self):
		self.file.write('popc\n')
		# popc is grestore. make sure properties are set properly again
		# after this.
		self.init_props()

	def init_color_props(self):
		self.current_color = None

	def _set_color(self, color):
		if self.current_color != color:
			if color.model == 'CMYK':
				c, m, y, k = color.getCMYK()
				self.file.write('%g %g %g %g cmyk\n' % (round(c, 3), round(m, 3), round(y, 3), round(k, 3)))
			else:
				r, g, b = color.getRGB()
				self.file.write('%g %g %g rgb\n' % (round(r, 3), round(g, 3), round(b, 3)))
			self.current_color = color

	SetFillColor = _set_color
	SetLineColor = _set_color

	def init_line_props(self):
		self.current_width = self.current_cap = self.current_join = None
		self.current_dash = None

	def SetLineAttributes(self, width, cap = 1, join = 0, dashes = ()):
		write = self.file.write
		if self.current_width != width:
			width_changed = 1
			write('%g w\n' % width)
			self.current_width = width
		else:
			width_changed = 0
		join = ps_join[join]
		if self.current_join != join:
			write('%d j\n' % join)
			self.current_join = join
		cap = ps_cap[cap]
		if self.current_cap != cap:
			write('%d J\n' % cap)
			self.current_cap = cap

		if self.current_dash != dashes or width_changed:
			# for long dashes tuples this could theoretically produce
			# lines longer than 255 chars, which means that the file
			# would not conform to the DSC
			if width < 1:
				width = 1
			write('[')
			for dash in dashes:
				dash = width * dash
				if dash < 0.001:
					dash = 0.001
				write('%g ' % dash)
			write('] 0 d\n')
			self.current_dash = dashes

	def SetLineSolid(self):
		self.file.write('[ ] 0 d\n')
		self.current_dash = ()

	def DrawLine(self, start, end):
		self.file.write('%g %g m %g %g l s\n' % (tuple(start) + tuple(end)))

	def DrawLineXY(self, x1, y1, x2, y2):
		self.file.write('%g %g m %g %g l s\n' % (x1, y1, x2, y2))

	def DrawRectangle(self, start, end):
		self.file.write('%g %g %g %g R s\n' % (tuple(start) + tuple(end)))

	def FillRectangle(self, left, bottom, right, top):
		self.file.write('%g %g %g %g R f\n' % (left, bottom, right, top))

	def DrawCircle(self, center, radius):
		self.file.write('%g %g %g C s\n' % (center.x, center.y, radius))

	def FillCircle(self, center, radius):
		self.file.write('%g %g %g C f\n' % (center.x, center.y, radius))

	def FillPolygon(self, pts):
		write = self.file.write
		if len(pts) > 1:
			write('%g %g m\n' % pts[0])
			for p in pts[1:]:
				write('%g %g l\n' % p)
			write('f\n')

	def DrawBezierPath(self, path, rect = None):
		self.write_path(path.get_save())
		self.file.write('S\n')

	def FillBezierPath(self, path, rect = None):
		self.write_path(path.get_save())
		self.file.write('F\n')

	def fill_path(self, clip = 0):
		write = self.file.write
		if self.proc_fill:
			if not clip:
				self.PushClip()
			write('eoclip newpath\n')
			self.properties.ExecuteFill(self, self.pattern_rect)
			if not clip:
				self.PopClip()
				write('newpath\n')
		else:
			self.properties.ExecuteFill(self, self.pattern_rect)
			if not clip:
				write('F\n')
			else:
				write('gsave F grestore eoclip newpath\n')

	def stroke_path(self):
		self.properties.ExecuteLine(self, self.pattern_rect)
		self.file.write('S\n')

	def fill_and_stroke(self, clip = 0):
		write = self.file.write

		if not clip and self.line:
			if self.fill:
				write('gsave\n')
				self.fill_path()
				write('grestore\n')
				self.init_props()
				self.stroke_path()
			else:
				self.stroke_path()
		else:
			if self.fill:
				self.fill_path(clip)
			elif clip:
				write('eoclip newpath\n')


	def write_path(self, list):
		write = self.file.write
		write('%g %g m\n' % list[0][:-1])
		for item in list[1:]:
			if len(item) == 3:
				write('%g %g l\n' % item[:-1])
			elif len(item) == 7:
				write('%g %g %g %g %g %g c\n' % item[:-1])
			else:
				if __debug__:
					pdebug('PS', 'PostScriptDevice: invalid bezier item:',item)

	def MultiBezier(self, paths, rect = None, clip = 0):
		# XXX: try to write path only once
		write = self.file.write
		line = self.line; fill = self.fill

		if line or fill or clip:
			open = 0
			for path in paths:
				open = open or not path.closed

			write('newpath\n')
			if fill or clip:
				if not open:
					# all subpaths are closed
					for path in paths:
						self.write_path(path.get_save())
						write('closepath\n')
					self.fill_and_stroke(clip)
					line = 0
				else:
					# some but not all sub paths are closed
					for path in paths:
						self.write_path(path.get_save())
						if not path.closed:
							write('closepath\n')
					self.fill_path(clip)

			if line:
				for path in paths:
					self.write_path(path.get_save())
					if path.closed:
						write('closepath\n')
				self.stroke_path()
				self.draw_arrows(paths)

	def Rectangle(self, trafo, clip = 0):
		if self.fill or self.line or clip:
			self.file.write('[%g %g %g %g %g %g] rect\n' % trafo.coeff())
			self.fill_and_stroke(clip)

	def RoundedRectangle(self, trafo, radius1, radius2, clip = 0):
		if self.fill or self.line or clip:
			self.file.write('[%g %g %g %g %g %g] %g %g rect\n'
							% (trafo.coeff() + (radius1, radius2)))
			self.fill_and_stroke(clip)

	def SimpleEllipse(self, trafo, start_angle, end_angle, arc_type,
						rect = None, clip = 0):
		if self.fill or self.line or clip:
			if start_angle == end_angle:
				self.file.write('[%g %g %g %g %g %g] ellipse\n'
								% trafo.coeff())
				self.fill_and_stroke(clip)
			else:
				self.file.write('[%g %g %g %g %g %g] %g %g %d ellipse\n' %
								(trafo.coeff()
									+ (start_angle, end_angle, arc_type)))
				self.fill_and_stroke(clip)
			self.draw_ellipse_arrows(trafo, start_angle, end_angle, arc_type,
										rect)

	def init_font_props(self):
		self.current_font = None

	def set_font(self, font, size):
		spec = (font.PostScriptName(), size)
		if self.current_font != spec:
			self.file.write('/%s %g sf\n' % spec)
			self.current_font = spec

	def DrawText(self, text, trafo, clip = 0, cache = None):
		# XXX: should make sure that lines in eps file will not be
		# longer than 255 characters.
		font = self.properties.font
		if font:
			write = self.file.write
			self.set_font(font, self.properties.font_size)
			write('(%s)\n' % quote_ps_string(text))
			if trafo.matrix() == IdentityMatrix:
				write('%g %g ' % tuple(trafo.offset()))
			else:
				write('[%g %g %g %g %g %g] ' % trafo.coeff())
			if self.proc_fill:
				write('P ')
				write('gsave clip newpath\n')
				self.properties.ExecuteFill(self, self.pattern_rect)
				write('grestore ')
				if clip:
					write('clip ')
				write('newpath\n')
			else:
				self.properties.ExecuteFill(self, self.pattern_rect)
				if clip:
					write('TP clip newpath\n')
				else:
					write('T\n')

	complex_text = None
	def BeginComplexText(self, clip = 0, cache = None):
		# XXX clip does not work yet...
		self.complex_text = Empty(clip = clip, fontname = '', size = None)
		if self.proc_fill or clip:
			self.PushClip()
		else:
			self.properties.ExecuteFill(self, self.pattern_rect)

	def DrawComplexText(self, text, trafo, font, font_size):
		write = self.file.write
		complex_text = self.complex_text
		self.set_font(font, font_size)
		write('(%s) ' % quote_ps_string(text))
		if trafo.matrix() == IdentityMatrix:
			write('%g %g ' % tuple(trafo.offset()))
		else:
			write('[%g %g %g %g %g %g] ' % trafo.coeff())
		if self.proc_fill:
			write('P\n')
		else:
			write('T\n')

	def EndComplexText(self):
		if self.proc_fill:
			self.file.write('eoclip newpath\n')
			self.properties.ExecuteFill(self, self.pattern_rect)
			self.PopClip()
		self.complex_text = None


	def DrawImage(self, image, trafo, clip = 0):
		write = self.file.write
		w, h = image.size
		if len(image.mode) >= 3:
			# compute number of hex lines. 80 hex digits per line. 3 bytes
			# per pixel
			digits = w * h * 6	# 3 bytes per pixel, 2 digits per byte
			if digits <= 0:
				# an empty image. (it should never be < 0 ...)
				return
			lines = (digits - 1) / 80 + 1
			write('%d %d ' % image.size)
			write('[%g %g %g %g %g %g] true\n' % trafo.coeff())
			write('%%%%BeginData: %d Hex Lines\n' % (lines + 1))
			write('skcimg\n')
		else:
			digits = w * h * 2	# 2 digits per byte
			if digits <= 0:
				# an empty image. (it should never be < 0 ...)
				return
			lines = (digits - 1) / 80 + 1
			write('%d %d ' % image.size)
			write('[%g %g %g %g %g %g] true\n' % trafo.coeff())
			write('%%%%BeginData: %d Hex Lines\n' % (lines + 1))
			write('skgimg\n')

		_sketch.write_ps_hex(image.im, self.file)
		write('%%EndData\n')
		if clip:
			write('pusht [%g %g %g %g %g %g] concat\n' % trafo.coeff())
			write('%d %d scale\n' % image.size)
			write('0 0 m  1 0 l	 1 1 l	0 1 l closepath popt clip\n')


	def DrawEps(self, data, trafo):
		write = self.file.write
		write('%g %g %g %g ' % (data.Start() + data.Size()))
		write('[%g %g %g %g %g %g]\n' % trafo.coeff())
		write('skeps\n')
		write('%%%%BeginDocument: %s\n' % data.Filename())
		if self.loaded_eps_files.has_key(id(data)):
			write(self.loaded_eps_contents)
		else:
			data.WriteLines(self.file)
		write('\n%%EndDocument\n')
		write('skepsend\n')

	def DrawGrid(self, orig_x, orig_y, xwidth, ywidth, rect):
		pass

	def DrawGuideLine(self, *args):
		pass

	def SetProperties(self, properties, rect = None):
		self.properties = properties
		self.line = properties.HasLine()
		self.fill = properties.HasFill()
		self.pattern_rect = rect
		self.proc_fill = properties.IsAlgorithmicFill()
		self.proc_line = properties.IsAlgorithmicLine()


	def write_gradient(self, gradient):
		# self.current_color is implicitly reset because gradients are
		# nested in a PushClip/PopClip, so we don't have to update that
		write = self.file.write
		samples = gradient.Sample(self.gradient_steps)
		write('%d gradient\n' % len(samples))
		last = None
		for color in samples:
			if color != last:
				r, g, b = last = color
				write('%g %g %g $\n' % (round(r, 3), round(g, 3), round(b, 3)))
			else:
				write('!\n')

	has_axial_gradient = 1
	def AxialGradient(self, gradient, p0, p1):
		# must accept p0 and p1 as PointSpecs
		self.write_gradient(gradient)
		self.file.write('%g %g %g %g axial\n' % (tuple(p0) + tuple(p1)))

	has_radial_gradient = 1
	def RadialGradient(self, gradient, p, r0, r1):
		# must accept p as PointSpec
		self.write_gradient(gradient)
		self.file.write('%g %g %g %g radial\n' % (tuple(p) + (r0, r1)))

	has_conical_gradient = 1
	def ConicalGradient(self, gradient, p, angle):
		# must accept p as PointSpec
		self.write_gradient(gradient)
		self.file.write('%g %g %g conical\n' % (tuple(p) + (angle,)))

	def TileImage(self, image, trafo):
		width, height = image.size
		if image.mode == 'RGBA':
			# We don't support transparency in textures, so we simply
			# treat RGBA as as RGB images
			mode = 'RGB'
		else:
			mode = image.mode
		length = width * height * len(mode)
		if length > 65536:
			# the tile image is too large to fit into a PostScript
			# string. Resize it.
			#warn(USER, "Image data to big for tiling, resizing...")
			ratio = float(width) / height
			max_size = 65536 / len(mode)
			width = int(sqrt(max_size * ratio))
			height = int(sqrt(max_size / ratio))
			tile = image.im.resize((width, height))
			length = width * height * len(mode)
			trafo = trafo(Scale(float(image.size[0]) / width,
								float(image.size[1]) / height))
		else:
			tile = image.im
		write = self.file.write
		write('%d %d %d [%g %g %g %g %g %g]\n'
				% ((width, height, len(mode)) + trafo.coeff()))
		digits = length * 2	# 2 digits per byte
		lines = (digits - 1) / 80 + 1
		write('%%%%BeginData: %d Hex Lines\n' % (lines + 1))
		write("tileimage\n")
		# write_ps_hex treats RGBA like RGB
		_sketch.write_ps_hex(tile, self.file)
		write('%%EndData\n')

	#
	#	Outline Mode
	#	This will be ignored in PostScript devices
	#

	def StartOutlineMode(self, *rest):
		pass

	def EndOutlineMode(self, *rest):
		pass

	def IsOutlineActive(self, *rest):
		return 0
