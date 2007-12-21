# Sketch - A Python-based interactive drawing program
# Copyright (C) 1999, 2002 by Bernhard Herzog
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

###Sketch Config
#type = Import
#class_name = 'WMFLoader'
rx_magic = '\xd7\xcd\xc6\x9a'
#tk_file_type = ('Windows Metafile', '.wmf')
#format_name = 'WMF'
#unload = 1
#standard_messages = 1
###End

#
#       Import Filter for Windows WMF files
#
# Status:
#
# The filter only handles the 16 bit WMF files of Windows 3.1
#
# Things it can't handle:
#
#  - Text. Some text support would be possible, I guess, but there would
#    probably be problems with TrueType fonts, because Sketch doesn't
#    support them yet.
#
#  - Winding number rule for Polygons.
#
#  - Clip-Regions
#



import sys, os, string
from math import sin, cos, pi
from struct import unpack, calcsize
import struct

from app import _, Trafo, Scale, Translation, Point, Polar, CreatePath, \
		CreateRGBColor, SolidPattern, EmptyPattern, LinearGradient, \
		MultiGradient, Style, const, StandardColors

from app.events.warn import INTERNAL, warn_tb
from app.io.load import GenericLoader, SketchLoadError


struct_wmf_header = ('<'
						'H'	# Type
						'H'	# header size
						'H'	# Version
						'I'	# FileSize
						'H'	# Num. objects
						'I'	# Max. record size
						'H'	# Num. Parameters
						)

struct_placeable_header = ('<'
							'4s'	# Key
							'H'	# handle
							'h'	# left
							'h'	# top
							'h'	# right
							'h'	# bottom
							'H'	# Inch
							'I'	# Reserved
							'H'	# Checksum
							)

wmf_functions = {
	0x0052: 'AbortDoc',
	0x0817: 'Arc',
	0x0830: 'Chord',
	0x01f0: 'DeleteObject',
	0x0418: 'Ellipse',
	0x005E: 'EndDoc',
	0x0050: 'EndPage',
	0x0415: 'ExcludeClipRect',
	0x0548: 'ExtFloodFill',
	0x0228: 'FillRegion',
	0x0419: 'FloodFill',
	0x0429: 'FrameRegion',
	0x0416: 'IntersectClipRect',
	0x012A: 'InvertRegion',
	0x0213: 'LineTo',
	0x0214: 'MoveTo',
	0x0220: 'OffsetClipRgn',
	0x0211: 'OffsetViewportOrg',
	0x020F: 'OffsetWindowOrg',
	0x012B: 'PaintRegion',
	0x061D: 'PatBlt',
	0x081A: 'Pie',
	0x0035: 'RealizePalette',
	0x041B: 'Rectangle',
	0x014C: 'ResetDc',
	0x0139: 'ResizePalette',
	0x0127: 'RestoreDC',
	0x061C: 'RoundRect',
	0x001E: 'SaveDC',
	0x0412: 'ScaleViewportExt',
	0x0410: 'ScaleWindowExt',
	0x012C: 'SelectClipRegion',
	0x012D: 'SelectObject',
	0x0234: 'SelectPalette',
	0x012E: 'SetTextAlign',
	0x0201: 'SetBkColor',
	0x0102: 'SetBkMode',
	0x0d33: 'SetDibToDev',
	0x0103: 'SetMapMode',
	0x0231: 'SetMapperFlags',
	0x0037: 'SetPalEntries',
	0x041F: 'SetPixel',
	0x0106: 'SetPolyFillMode',
	0x0105: 'SetRelabs',
	0x0104: 'SetROP2',
	0x0107: 'SetStretchBltMode',
	0x012E: 'SetTextAlign',
	0x0108: 'SetTextCharExtra',
	0x0209: 'SetTextColor',
	0x020A: 'SetTextJustification',
	0x020E: 'SetViewportExt',
	0x020D: 'SetViewportOrg',
	0x020C: 'SetWindowExt',
	0x020B: 'SetWindowOrg',
	0x014D: 'StartDoc',
	0x004F: 'StartPage',
	#
	0x0436: 'AnimatePalette',
	0x0922: 'BitBlt',
	0x06FE: 'CreateBitmap',
	0x02FD: 'CreateBitmapIndirect',
	0x00F8: 'CreateBrush',
	0x02FC: 'CreateBrushIndirect',
	0x02FB: 'CreateFontIndirect',
	0x00F7: 'CreatePalette',
	0x01F9: 'CreatePatternBrush',
	0x02FA: 'CreatePenIndirect',
	0x06FF: 'CreateRegion',
	0x01F0: 'DeleteObject',
	0x0940: 'DibBitblt',
	0x0142: 'DibCreatePatternBrush',
	0x0B41: 'DibStretchBlt',
	0x062F: 'DrawText',
	0x0626: 'Escape',
	0x0A32: 'ExtTextOut',
	0x0324: 'Polygon',
	0x0538: 'PolyPolygon',
	0x0325: 'Polyline',
	0x0521: 'TextOut',
	0x0B23: 'StretchBlt',
	0x0F43: 'StretchDIBits'
}

def noop(self):
	pass


class WMFLoader(GenericLoader):

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file = file
		self.curstyle = Style()
		self.verbosity = 0
		self.gdiobjects = []
		self.dcstack = []
		self.curpoint = Point(0, 0)

	def _print(self, format, *args, **kw):
		if self.verbosity:
			try:
				if kw:
					text = format % kw
				elif args:
					text = format % args
				else:
					text = format
			except:
				text = string.join([format] + map(str, args))
			if text[-1] != '\n':
				text = text + '\n'
			sys.stdout.write(text)

	def get_struct(self, format):
		size = calcsize(format)
		return unpack(format, self.file.read(size))

	def get_int16(self):
		return self.get_struct('<h')[0]

	def get_int32(self):
		return self.get_struct('<i')[0]

	def read_headers(self):
		self.file.seek(0)
		placeable = self.file.read(calcsize(struct_placeable_header))
		key, handle, left, top, right, bottom, inch, reserved, checksum\
				= unpack(struct_placeable_header, placeable)
		if key != rx_magic:
			raise SketchLoadError(_("The file is not a placeable "
									"windows metafile"))
			self._print("The file is not a placeable windows metafile")
		sum = 0
		for word in unpack('<10h', placeable[:20]):
			sum = sum ^ word
		if sum != checksum:
			#raise SketchLoadError(_("The file has an incorrect checksum"))
			self._print("The file has an incorrect checksum")

		self.inch = inch
		self.bbox = (left, top, right, bottom)
		factor = 72.0 / self.inch
		self.wx = self.wy = 0
		self.wwidth = right - left
		self.wheight = bottom - top
		self.vx = self.vy = 0
		self.vwidth = self.wwidth
		self.vheight = self.wheight
		self.base_trafo = Trafo(factor, 0, 0, -factor,
								0, factor * self.vheight)
		self.update_trafo()

		header = self.file.read(calcsize(struct_wmf_header))
		filetype, headersize, version, filesize, numobj, maxrecord, numparams\
					= unpack(struct_wmf_header, header)

		self._print('\nHeader\n------\n')
		fmt = '% 10s: %s\n'
		self._print(fmt, 'inch', self.inch)
		self._print(fmt, 'bbox', self.bbox)
		self._print(fmt, 'headersize', headersize)
		self._print(fmt, 'version', version)
		self._print(fmt, 'numobj', numobj)
		self._print(fmt, 'numparams', numparams)
		self._print(fmt, 'maxrecord', maxrecord)
		self._print('\n')

	def update_trafo(self):
		wt = Translation(-self.wx, -self.wy)
		vt = Translation(self.vx, self.vy)
		scale = Scale(float(self.vwidth) / self.wwidth,
						float(self.vheight) / self.wheight)
		self.trafo = self.base_trafo(vt(scale(wt)))

	def add_gdiobject(self, object):
		try:
			idx = self.gdiobjects.index(None)
		except ValueError:
			self.gdiobjects.append(object)
		else:
			self.gdiobjects[idx] = object

	def delete_gdiobject(self, idx):
		self.gdiobjects[idx] = None

	def SelectObject(self):
		idx = self.get_int16()
		try:
			object = self.gdiobjects[idx]
		except IndexError:
			print 'Index Error:', idx, self.gdiobjects
			raise
		for property, value in object:
			setattr(self.curstyle, property, value)
		self._print('->', idx, object)

	def DeleteObject(self):
		idx = self.get_int16()
		self.delete_gdiobject(idx)
		self._print('->', idx)

	def get_dc(self):
		return self.curstyle.Duplicate(), self.trafo, self.curpoint

	def set_dc(self, dc):
		self.curstyle, self.trafo, self.curpoint = dc

	def SaveDC(self):
		self.dcstack.append(self.get_dc())

	def RestoreDC(self):
		self.set_dc(self.dcstack[-1])
		del self.dcstack[-1]

	def SetMapMode(self):
		mode = self.get_int16()
		self._print('->', mode)

	def SetWindowOrg(self):
		self.wy, self.wx = self.get_struct('<hh')
		self.update_trafo()
		self._print('->', self.wx, self.wy)

	def SetWindowExt(self):
		self.wheight, self.wwidth = self.get_struct('<hh')
		self.update_trafo()
		self._print('->', self.wwidth, self.wheight)

	def SetPolyFillMode(self):
		mode = self.get_int16()
		self._print('->', mode)

	SetBkMode = noop
	SetBkColor = noop
	SetROP2 = noop

	def CreateBrushIndirect(self):
		style, r, g, b, hatch = self.get_struct('<hBBBxh')
		if style == 1:
			pattern = EmptyPattern
		else:
			pattern = SolidPattern(CreateRGBColor(r/255.0, g/255.0, b/255.0))
		self.add_gdiobject((('fill_pattern', pattern),))

		self._print('->', style, r, g, b, hatch)

	def DibCreatePatternBrush(self):
		self.add_message(_("Bitmap brushes not yet implemented. Using black"))
		pattern = SolidPattern(StandardColors.black)
		self.add_gdiobject((('fill_pattern', pattern),))

	def CreatePenIndirect(self):
		style, widthx, widthy, r, g, b = self.get_struct('<hhhBBBx')
		cap = (style & 0x0F00) >> 8
		join = (style & 0x00F0) >> 4
		style = style & 0x000F
		if style == 5:
			pattern = EmptyPattern
		else:
			pattern = SolidPattern(CreateRGBColor(r/255.0, g/255.0, b/255.0))
		width = abs(widthx * self.trafo.m11)
		self.add_gdiobject((('line_pattern', pattern,),
							('line_width',  width)))
		self._print('->', style, widthx, widthy, r, g, b, cap, join)

	def CreatePalette(self):
		self.add_gdiobject((('ignore', None),))

	def CreateRegion(self):
		self.add_gdiobject((('ignore', None),))

	CreateFontIndirect = CreatePalette
	SelectPalette = noop
	RealizePalette = noop
	
	SetTextColor = noop
	SetTextAlign = noop
	SetTextJustification = noop

	SetStretchBltMode = noop
	
	def read_points(self, num):
		coords = self.get_struct('<' + num * 'hh')
		points = [];
		append = points.append
		trafo = self.trafo
		for i in range(0, 2 * num, 2):
			append(trafo(coords[i], coords[i + 1]))
		return points

	def Polyline(self):
		points = self.read_points(self.get_int16())
		if points:
			path = CreatePath()
			map(path.AppendLine, points)
			self.prop_stack.AddStyle(self.curstyle.Duplicate())
			self.prop_stack.SetProperty(fill_pattern = EmptyPattern)
			self.bezier((path,))

		#for i in range(len(points)):
		#    self._print('->', points[i])

	def Polygon(self):
		points = self.read_points(self.get_int16())
		if points:
			path = CreatePath()
			map(path.AppendLine, points)
			if path.Node(-1) != path.Node(0):
				#print 'correct polygon'
				path.AppendLine(path.Node(0))
			path.load_close()
			self.prop_stack.AddStyle(self.curstyle.Duplicate())
			self.bezier((path,))

		#for i in range(len(points)):
		#    self._print('->', points[i])

	def PolyPolygon(self):
		nr_of_polygons = self.get_int16()
		nr_of_points = []
		for i in range(nr_of_polygons):
			nr_of_points.append(self.get_int16())
		path = ()
		for i in nr_of_points:
			points = self.read_points(i)
			if points:
				subpath = CreatePath()
				map(subpath.AppendLine, points)
				if subpath.Node(-1) != subpath.Node(0):
					subpath.AppendLine(subpath.Node(0))
				subpath.load_close()
				path = path + (subpath,)
		if path:
			self.prop_stack.AddStyle(self.curstyle.Duplicate())
			self.bezier(path)

	def MoveTo(self):
		y, x = self.get_struct('<hh')
		self.curpoint = self.trafo(x, y)
		self._print('->', self.curpoint)
	
	def LineTo(self):
		y, x = self.get_struct('<hh')
		p = self.trafo(x, y)
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		self.prop_stack.SetProperty(fill_pattern = EmptyPattern)
		path = CreatePath()
		path.AppendLine(self.curpoint)
		path.AppendLine(p)
		self.bezier((path,))
		self.curpoint = p
		self._print('->', self.curpoint)

	def Ellipse(self):
		bottom, right, top, left = self.get_struct('<hhhh')
		left, top = self.trafo(left, top)
		right, bottom = self.trafo(right, bottom)
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		self.ellipse((right - left) / 2, 0, 0, (bottom - top) / 2,
						(right + left) / 2, (top + bottom) / 2)

	def Arc(self, arc_type = const.ArcArc):
		ye, xe, ys, xs, bottom, right, top, left = self.get_struct('<hhhhhhhh')
		left, top = self.trafo(left, top)
		right, bottom = self.trafo(right, bottom)
		xs, ys = self.trafo(xs, ys)
		xe, ye = self.trafo(xe, ye)
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		if arc_type == const.ArcArc:
			self.prop_stack.SetProperty(fill_pattern = EmptyPattern)
		if left != right and top != bottom:
			t = Trafo((right - left) / 2, 0, 0, (bottom - top) / 2,
						(right + left) / 2, (top + bottom) / 2).inverse()
			# swap start and end-angle
			end_angle = t(xs, ys).polar()[1]
			start_angle = t(xe, ye).polar()[1]
		else:
			start_angle = end_angle = 0.0
		self.ellipse((right - left) / 2, 0, 0, (bottom - top) / 2,
						(right + left) / 2, (top + bottom) / 2,
						start_angle = start_angle, end_angle = end_angle,
						arc_type = arc_type)
	def Pie(self):
		self.Arc(const.ArcPieSlice)

	def Rectangle(self):
		bottom, right, top, left = self.get_struct('<hhhh')
		left, top = self.trafo(left, top)
		right, bottom = self.trafo(right, bottom)
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		self.rectangle(right - left, 0, 0, bottom - top, left, top)

	def RoundRect(self):
		ellh, ellw, bottom, right, top, left = self.get_struct('<hhhhhh')
		left, top = self.trafo(left, top)
		right, bottom = self.trafo(right, bottom)
		ellw, ellh = self.trafo.DTransform(ellw, ellh)
		self._print('->', left, top, right, bottom, ellw, ellh)
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		self.rectangle(right - left, 0, 0, bottom - top, left, top,
						radius1 = abs(ellw / (right - left)),
						radius2 = abs(ellh / (bottom - top)))
		

	def Escape(self):
		pass

	def interpret(self):
		tell = self.file.tell
		function = -1
		while function:
			pos = tell()
			size, function = self.get_struct('<ih')
			self._print('%5d: %4x: %s' % (size, function,
											wmf_functions.get(function, '')))
			if hasattr(self, wmf_functions.get(function, '')):
				getattr(self, wmf_functions[function])()
			else:
				if function:
					self.file.read(2 * (size - 3))
					self._print('*** unimplemented:',
								wmf_functions.get(function, ''))
			pos = pos + 2 * size
			if tell() < pos:
				self.file.read(pos - tell())
			elif tell() > pos:
				self._print('read too many bytes')
				self.file.seek(pos - tell(), 1)

	def Load(self):
		self.document()
		self.layer(name = _("WMF objects"))
		self.read_headers()
		self.interpret()
		self.end_all()
		self.object.load_Completed()
		return self.object

