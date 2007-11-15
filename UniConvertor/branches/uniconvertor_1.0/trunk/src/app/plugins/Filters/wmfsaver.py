# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002, 2003 by Bernhard Herzog
# This WMFsaver by Lukasz Pankowski (2003)
# Based on CGMsaver mostly by Antoon Pardon (2002)
# and WMFloader by Bernhard Herzog (2002)
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
#
# $Id: wmfsaver.py,v 1.1.2.1 2003/06/09 17:56:13 bherzog Exp $

###Sketch Config
#type = Export
#tk_file_type = ("Windows Metafile", '.wmf')
#extensions = '.wmf'
format_name = 'WMF'
#unload = 1
###End

import struct

from app import Bezier, EmptyPattern, Point, Polar, Trafo
from app.conf import const



# Fault Tolerance for flattening Beziers.
# If you find the curves not smooth enough, lower this value.
EPS = 2

rx_magic = '\xd7\xcd\xc6\x9a'

struct_wmf_header = ('<'
						'H'        # Type
						'H'        # header size
						'H'        # Version
						'I'        # FileSize
						'H'        # Num. objects
						'I'        # Max. record size
						'H'        # Num. Parameters
						)

struct_placeable_header = ('<'
							'4s' # Key
							'H'  # handle
							'h'  # left
							'h'  # top
							'h'  # right
							'h'  # bottom
							'H'  # Inch
							'I'  # Reserved
							'H'  # Checksum
							)


EMPTY_PEN = 0
EMPTY_PATTERN = 1
MIN_OBJECT = 2                          # less are reserved
MAX_OBJECTS = 16


def rndtoint(num):
	return int(round(num))


def cr(P1, P2):

	return P1.x * P2.y - P1.y * P2.x


def FlattenPath(P0, P1, P2, P3):

	P4 = (P0 + P1) / 2
	P5 = (P1 + P2) / 2
	P6 = (P2 + P3) / 2
	P7 = (P4 + P5) / 2
	P8 = (P5 + P6) / 2
	P9 = (P7 + P8) / 2

	B = P3 - P0
	S = P9 - P0
	C1 = P1 - P0
	C2 = P2 - P3

	# I couldn't find an example of a flattening algorithm so I came up
	# with the following criteria for deciding to stop the approximation
	# or to continue.

	# if either control vector is larger than the base vector continue
	if abs(C1) > abs(B) or abs(C2) > abs(B):
		return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)

	# otherwise if the base is smaller than half the fault tolerance stop.
	elif abs(B) < EPS / 2:
		return (P9, P3)
	else:

		# if neither of the above applies, check for the following conditions.
		# if one of them is true continue the approximation otherwise stop
		#
		# The first constrol vector goes too far before the base
		# The seconde control vector goes too far behind the base
		# Both control vectors lie on either side of the base.
		# The midpoint is too far from base.

		N = B.normalized()
		if ((C1 * N) < -EPS or (C2 * N) > EPS or cr(C1,B)*cr(C2,B) < 0
			or abs(cr(N,S)) > EPS):
			return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)
		else:
			return (P9, P3)


class WMFSaver:

	def __init__(self, file, pathname, options):
		self.file = file
		self.pathname = pathname
		self.options = options
		self.numobj = 0
		self.maxrecord = 10

	def pack(self, *args):
		self.file.write(apply(struct.pack , args))

	def packrec(self, *args):
		if args[1] is None:
			# compute size of the record
			args = (args[0], struct.calcsize(args[0]) / 2) + args[2:]
		self.maxrecord = max(args[1], self.maxrecord)
		apply(self.pack, args)

	def putpolyrec(self, function, seq):
		fmt = '<LHh%dh' % len(seq)
		size = struct.calcsize(fmt) / 2
		args = (fmt, size, function, len(seq) / 2) + tuple(seq)
		self.maxrecord = max(size, self.maxrecord)
		apply(self.pack, args)

	def close(self):
		self.file.close()

	def SelectObject(self, num):
		type = self.objects[num][4]
		if type == '\xFA':
			if self.cur_pen == num:
				return
			self.cur_pen = num
		else:
			if self.cur_brush == num:
				return
			self.cur_brush = num
		self.packrec('<LHh', 4, 0x012D, num)

	def DeleteObject(self, num):
		self.packrec('<LHh', 4, 0x01f0, num)

	def add_select_object(self, s):
		try:
			idx = self.objects.index(s)
		except ValueError:
			if len(self.objects) < MAX_OBJECTS:
				self.objects.append(s)
				self.idx = idx = len(self.objects) - 1
				self.numobj = len(self.objects) + MIN_OBJECT + 10
			else:
				idx = self.idx + 1
				if idx == MAX_OBJECTS:
					idx = MIN_OBJECT
				self.idx = idx
				self.DeleteObject(idx)
			self.file.write(s)
			self.maxrecord = max(self.maxrecord, len(s) / 2)
		self.SelectObject(idx)

	def CreateSelectBrush(self, color):
		# BS_SOLID 0, BS_NULL 1
		red = rndtoint(255 * color.red)
		green = rndtoint(255 * color.green)
		blue = rndtoint(255 * color.blue)
		self.add_select_object(struct.pack('<LHhBBBxh', 7, 0x02FC,
											0, red, green, blue, 0))

	def CreateSelectPen(self, width, color, dashes):
		red = rndtoint(255 * color.red)
		green = rndtoint(255 * color.green)
		blue = rndtoint(255 * color.blue)
		if dashes == ():
			style = 0 # solid
		elif len(dashes) == 2:
			if dashes[0] >= 3:
				style = 1 # dash
			else:
				style = 2 # dot
		elif len(dashes) == 4:
			style = 3 # dash-dot
		else:
			style = 4 # dash-dot-dot
		self.add_select_object(struct.pack('<LHhhhBBBx', 8, 0x02FA,
											style, width, width,
											red, green, blue))

	def LineStyle(self, Props):
		if Props.line_pattern is EmptyPattern:
			self.SelectObject(EMPTY_PEN)
		else:
			width = rndtoint(self.Scale * Props.line_width)
			self.CreateSelectPen(width, Props.line_pattern.Color().RGB(),
									Props.line_dashes)

	def FillStyle(self, Props):
		fill_pattern = Props.fill_pattern
		self.LineStyle(Props)
		if fill_pattern is EmptyPattern:
			self.SelectObject(EMPTY_PATTERN)
		elif fill_pattern.is_Solid:
			self.CreateSelectBrush(Props.fill_pattern.Color().RGB())
		elif fill_pattern.is_Hatching:
			# XXX wmf supports hatching
			self.CreateSelectBrush(Props.fill_pattern.Foreground())
		elif fill_pattern.is_Gradient:
			# average color
			self.CreateSelectBrush(Props.fill_pattern.gradient.Sample(3)[1])
		elif fill_pattern.is_Image:
			self.SelectObject(EMPTY_PATTERN) # XXX

	def PathToSeq(self, Path):
		parlst = ()
		for i in range(Path.len):
			type, control, p, cont = Path.Segment(i)
			if type == Bezier:
				p1 , p2 = control
				tmplst = FlattenPath(p0, p1, p2, p)
				for tp in tmplst:
					parlst = parlst + tuple(self.trafo(tp))
			else:
				parlst = parlst + tuple(self.trafo(p))
			p0 = p
		return parlst

	def PolyBezier(self, Paths, Properties):
		line_pattern = Properties.line_pattern
		fill_pattern = Properties.fill_pattern
		line_width = rndtoint(self.Scale * Properties.line_width)
		if len(Paths) == 1:
			path = Paths[0]
			if fill_pattern is EmptyPattern and not path.closed:
				function = 0x0325 # Polyline
				self.LineStyle(Properties)
				lst = self.PathToSeq(path)
			else:
				function = 0x0324 # Polygon
				self.FillStyle(Properties)
				lst = self.PathToSeq(path)
				if path.closed:
					lst = lst[:-2]
			self.putpolyrec(function, map(rndtoint , lst))
		elif fill_pattern is EmptyPattern:
			self.LineStyle(Properties)
			self.FillStyle(Properties)
			for path in Paths:
				lst = self.PathToSeq(path)
				if path.closed:
					function = 0x0324 # Polygon
					lst = lst[:-2]
				else:
					function = 0x0325 # Polyline
				self.putpolyrec(function, map(rndtoint , lst))
		else: # The polygonset case
			self.FillStyle(Properties)
			set = []
			lens = []
			size = 4 + len(Paths)
			for path in Paths:
				lst = self.PathToSeq(path)
				if path.closed:
					lst = lst[:-2]
				set.append(lst)
				size = size + len(lst)
				lens.append(len(lst) / 2)
			self.packrec('<LHh', size, 0x0538, len(set))
			lens.insert(0, '<%dh' % len(set))
			apply(self.pack, lens)
			for lst in set:
				fmt = '<%dh' % len(lst)
				apply(self.pack, (fmt,) + tuple(lst))

	def rect_to_ltrb(self, rct, zero = Point(0,0)):
		trf = rct.trafo
		P1 = self.trafo(trf(zero))
		P2 = self.trafo(trf(Point(1,1)))
		left = rndtoint(min(P1.x, P2.x))
		bottom = rndtoint(max(P1.y, P2.y))
		right = rndtoint(max(P1.x, P2.x))
		top = rndtoint(min(P1.y, P2.y))
		return left, top, right, bottom

	def Rectangle(self, rct):
		trf = rct.trafo
		if (trf.m12 == 0 and trf.m21 == 0) or (trf.m11 == 0 and trf.m22 == 0):
			self.FillStyle(rct.Properties())
			left, top, right, bottom = self.rect_to_ltrb(rct)
			if rct.radius1 != 0 or rct.radius2 != 0:
				ell_h = abs(self.trafo.m11 * trf.m11 * rct.radius1)
				ell_w = abs(self.trafo.m22 * trf.m22 * rct.radius2)
				self.packrec('<LHhhhhhh', 9, 0x061C, ell_h, ell_w, bottom,
								right, top, left)
			else:
				self.packrec('<LHhhhh', 7, 0x041B, bottom, right, top, left)
		else:
			self.PolyBezier(rct.Paths(), rct.Properties())

	def Ellipse(self, ell):
		trf = ell.trafo
		if (trf.m12 == 0 and trf.m21 == 0) or (trf.m11 == 0 and trf.m22 == 0):
			self.FillStyle(ell.Properties())
			left, top, right, bottom = self.rect_to_ltrb(ell, Point(-1,-1))
			if ell.start_angle == ell.end_angle:
				self.packrec('<LHhhhh', 7, 0x0418, bottom, right, top, left)
			else:
				xe, ye = map(rndtoint,
								self.trafo(ell.trafo(Polar(1, ell.start_angle))))
				xs, ys = map(rndtoint,
								self.trafo(ell.trafo(Polar(1, ell.end_angle))))
				if ell.arc_type == const.ArcArc:
					function = 0x0817
				elif ell.arc_type == const.ArcPieSlice:
					function = 0x081A
				elif ell.arc_type == const.ArcChord:
					function = 0x0830
				self.packrec('<LHhhhhhhhh', 11, function,
								ye, xe, ys, xs, bottom, right, top, left)
		else:
			self.PolyBezier(ell.Paths(), ell.Properties())

	def Text(self, object):
		self.PolyBezier(object.Paths(), object.Properties())

	def SaveObjects(self, Objects):
		for object in Objects:
			if object.is_Compound:
				self.SaveObjects(object.GetObjects())
			elif object.is_Rectangle:
				self.Rectangle(object)
			elif object.is_Ellipse:
				self.Ellipse(object)
			elif object.is_Text:
				self.Text(object)
			elif object.is_curve:
				self.PolyBezier(object.Paths(), object.Properties())

	def SaveLayers(self, Layers):
		for layer in Layers:
			if not layer.is_SpecialLayer and layer.Printable():
				self.SaveObjects(layer.GetObjects())

	def get_placeable(self, checksum):
		left, bottom, right, top = self.extend
		return struct.pack(
			struct_placeable_header,
			rx_magic,
			0,                         # handle
			left, top, right, bottom,
			self.inch,
			0,                         # reserved
			checksum)

	def write_headers(self):
		self.file.seek(0, 2)
		filesize = max(0, (self.file.tell()
							- struct.calcsize(struct_placeable_header)) / 2)
		self.file.seek(0)

		placeable = self.get_placeable(0)
		sum = 0
		for word in struct.unpack('<10h', placeable[:20]):
			sum = sum ^ word
		self.file.write(self.get_placeable(sum))

		self.pack(struct_wmf_header,
					1,                    # on disk
					struct.calcsize(struct_wmf_header) / 2,
					0x300,
					filesize,
					self.numobj,
					self.maxrecord,
					0)                    # number of params


	def SaveDocument(self, doc):

		left, bottom, right, top = doc.BoundingRect()
		width = right - left
		height = top - bottom

		inch = 1440
		x = max(width, height)
		if x * (inch / 72.) > 32767:
			inch = 32767 / x
		sc = inch / 72.
		self.trafo = Trafo(sc, 0, 0, -sc, - sc * left, sc * top)
		self.Scale = sc
		self.inch = inch
		self.extend = map(rndtoint, tuple(self.trafo(left,bottom))
									+ tuple(self.trafo(right,top)))

		self.numobj = self.idx = MIN_OBJECT
		self.objects = []
		self.maxrecord = 0
		self.cur_pen = -1
		self.cur_brush = -1

		# Header
		self.write_headers()

		# SetWindowOrg
		self.packrec('<LHhh', 5, 0x020B, self.extend[3], self.extend[0])

		# SetWindowExt
		self.packrec('<LHhh', 5, 0x020C, self.extend[1], self.extend[2])

		# SetBkMode to 1 (transparent)
		self.packrec('<LHh', 4, 0x0102, 1)

		# SetROP2 to 13 (R2_COPYPEN)
		# me self.packrec('<LHl', 5, 0x0104, 13)
		self.packrec('<LHh', 4, 0x0104, 13) # oo

		# CreatePenIndirect: 5 -- PS_NULL
		self.add_select_object(struct.pack('<LHhhhBBBx', 8, 0x02FA,
											5, 0, 0, 0, 0, 0))

		# CreateBrushIndirect: 1 -- BS_NULL
		self.add_select_object(struct.pack('<LHhBBBxh', 7, 0x02FC,
											1, 0, 0, 0, 0))

		self.SaveLayers(doc.Layers())

		self.DeleteObject(0)
		self.DeleteObject(1)

		self.packrec('<LH', 3, 0)       # terminator

		# update some fields
		self.write_headers()
	#end

def save(document, file, filename, options = {}):
	saver = WMFSaver(file, filename, options)
	saver.SaveDocument(document)
	saver.close()
