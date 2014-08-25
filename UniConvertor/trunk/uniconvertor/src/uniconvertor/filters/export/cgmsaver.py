# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002, 2003 by Bernhard Herzog
# This CGMsaver mostly by Antoon Pardon (2002)
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# $Id: cgmsaver.py,v 1.1.2.4 2003/05/17 18:22:14 bherzog Exp $

###Sketch Config
#type = Export
#tk_file_type = ("Computer Graphics Metafile (CGM)", '.cgm')
#extensions = '.cgm'
format_name = 'CGM'
#unload = 1
###End

import struct

import os.path

from app import Scale, Translation, Bezier, CreateRGBColor, EmptyPattern, \
	Point

import app.events.warn

from math import sqrt, sin, cos

# Fault Tolerance for flattening Beziers.
# If you find the curves not smooth enough, lower this value.
EPS = 2


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
		if (C1 * N) < -EPS or (C2 * N) > EPS or cr(C1,B)*cr(C2,B) < 0 \
			or abs(cr(N,S)) > EPS:  
			return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)
		else:
			return (P9, P3)

class Incr:
	def __init__(self, Base = 0):
		self.Value = Base
	def __call__(self, delta = 1):
		Result = self.Value
		self.Value = self.Value + delta
		return Result

WarnTable = ["- CGM has no Bezier curves. These are flattened\n\n" ,
				"- CGM has no Gradients. These are filled black\n\n"  ,
				"- cgmaver doesn't handle Hatchings. These are filled black\n\n" ,
				"- cgmaver doesn't handle Tiles. These are filled black\n\n" ,
				"- cgmaver doesn't handle images. These are omitted\n\n" ,
				"- cgmaver doesn't save text. Text is converted\n   to Bezier curves"]

Next = Incr()

W_Bezier = Next()
W_Gradient = Next()
W_Hatched = Next()
W_Tiled = Next()
W_Image = Next()
W_Text = Next()

class Warnings:
	def __init__(self):
		self.set = 0
	def Incl(self, num):
		self.set = self.set | 1 << num
	def show(self):
		inx = 0
		msg = ""
		while self.set != 0:
			if self.set % 2 == 1:
				msg = msg + WarnTable[inx]
			inx = inx + 1
			self.set = self.set >> 1
		if msg != "":
			msg = "The design you tried to save in CGM Version 1 format\n" + \
					"hit some limitations\n\n" + msg
			app.events.warn.warn(app.events.warn.USER , msg)
			
class CGMSaver:

	def __init__(self, file, pathname, options):
		self.file = file
		self.pathname = pathname
		self.options = options
		self.white = CreateRGBColor(1.0 , 1.0 , 1.0)
		self.black = CreateRGBColor(0.0 , 0.0 , 0.0)
		self.Msg = Warnings()

	def w(self, str):
			self.file.write(str)

	def pack(self , *args):
		self.file.write(apply(struct.pack , args))

	def putstr(self, Id , str):
		lng = len(str)
		if lng < 30:
			self.pack("!H" , Id | (lng + 1))
		else:
			self.pack("!H" , Id | 31)
			self.pack("!H" , lng + 1)
		self.pack("!B" , lng)
		fmt = '!' + `lng` + 's'
		self.pack(fmt , str)
		if lng % 2 == 0:
			self.pack("!B" , 0)

	def putlongseq(self, Id , seq):
		lng = len(seq)
		if 4 * lng < 31:
			self.pack("!H" , Id | 4 * lng)
		else:
			self.pack("!H" , Id | 31)
			self.pack("!H" , 4 * lng)
		fmt = '!' + `lng` + "i"
		args = (fmt,) + tuple(seq)
		apply(self.pack , args)

	def putcol(self , Id , color):
		red = rndtoint(255 * color.red)
		green = rndtoint(255 * color.green)
		blue = rndtoint(255 * color.blue)
		self.pack("!HBBBB" , Id , red , green , blue , 0)
		

	def close(self):
		self.Msg.show()
		self.file.close()

	def PathToSeq(self, Path):
		parlst = ()
		for i in range(Path.len):
			type, control, p, cont = Path.Segment(i)
			if type == Bezier:
				self.Msg.Incl(W_Bezier)
				p1 , p2 = control
				tmplst = FlattenPath(p0, p1, p2, p)
				for tp in tmplst:
					parlst = parlst + tuple(self.trafo(tp))
			else:
				parlst = parlst + tuple(self.trafo(p))
			p0 = p
		return parlst

	def LineStyle(self, Props):
		# Line width
		self.pack("!Hi" , 0x5064 , rndtoint(self.Scale * Props.line_width))
		# Line color
		self.putcol(0x5083 , Props.line_pattern.Color().RGB())
	
	def FillStyle(self, Props):
		line_pattern = Props.line_pattern
		fill_pattern = Props.fill_pattern
		line_width = rndtoint(self.Scale * Props.line_width)
		if line_pattern is EmptyPattern:
			# Edge Visibility Off
			self.pack("!HH" , 0x53c2 , 0x0000)
		else:
			# Edge Visibility On
			self.pack("!HH" , 0x53c2 , 0x0001)
			# Edge width
			self.pack("!Hi" , 0x5384 , line_width)
			# Edge color
			self.putcol(0x53a3 , line_pattern.Color().RGB())
		if fill_pattern is EmptyPattern:
			# Fill type is Hollow
			self.pack("!HH" , 0x52c2 , 0x0004)
		elif fill_pattern.is_Gradient:
			self.pack("!HH" , 0x52c2 , 0x0001)
			self.putcol(0x52e3 , self.black)
			self.Msg.Incl(W_Gradient)
		elif fill_pattern.is_Hatching:
			self.pack("!HH" , 0x52c2 , 0x0001)
			self.putcol(0x52e3 , self.black)
			self.Msg.Incl(W_Hatched)
		elif fill_pattern.is_Tiled:
			self.pack("!HH" , 0x52c2 , 0x0001)
			self.putcol(0x52e3 , self.black)
			self.Msg.Incl(W_Tiled)
		else:
			# Fill type is Solid
			self.pack("!HH" , 0x52c2 , 0x0001)
			#if fill_pattern.is_Solid:
			self.putcol(0x52e3 , fill_pattern.Color().RGB())


	def PolyBezier(self, Paths, Properties):

		line_pattern = Properties.line_pattern
		fill_pattern = Properties.fill_pattern
		line_width = rndtoint(self.Scale * Properties.line_width)
		if len(Paths) == 1:
			path = Paths[0]
			if fill_pattern is EmptyPattern and not path.closed:
				Id = 0x4020 # Polyline
				self.LineStyle(Properties)
				lst = self.PathToSeq(path)
			else:
				Id = 0x40e0 # Polygon
				self.FillStyle(Properties)
				lst = self.PathToSeq(path)
				if path.closed:
					lst = lst[:-2]
			self.putlongseq(Id , map(rndtoint , lst))
		elif fill_pattern is EmptyPattern:
			self.LineStyle(Properties)
			self.FillStyle(Properties)
			for path in Paths:
				lst = self.PathToSeq(path)
				if path.closed:
					Id = 0x40e0 # Polygon
					lst = lst[:-2]
				else:
					Id = 0x4020 # Polyline
				self.putlongseq(Id , map(rndtoint , lst))
		else: # The polygonset case
			self.FillStyle(Properties)
			set = []
			size = 0
			for path in Paths:
				lst = self.PathToSeq(path)
				if path.closed:
					lst = lst[:-2]
				size = size + 5 * len(lst)
				set.append(lst)
			if size < 31:
				self.pack("!H" , 0x4100 | size)
			else:
				self.pack("!H" , 0x4100 | 31)
				self.pack("!H" , size)
			for lst in set:
				while lst <> ():
					Arg = tuple(map(rndtoint , lst[:2]))
					#Arg = lst[:2]
					lst = lst[2:]
					if lst == ():
						Arg = Arg + (3,)
					else:
						Arg = Arg + (1,)
					Arg = ("!iiH",) + Arg
					apply(self.pack , Arg)


	def Rectangle(self, rct):
		trf = rct.trafo
		if rct.radius1 != 0 or rct.radius2 != 0:
			self.PolyBezier(rct.Paths(), rct.Properties())
		elif (trf.m12 == 0 and trf.m21 == 0) or (trf.m11 == 0 and trf.m22 == 0):
			self.FillStyle(rct.Properties())
			P1 = trf(Point(0,0))
			P2 = trf(Point(1,1))
			self.putlongseq(0x4160 , map(rndtoint , tuple(self.trafo(P1)) \
				+ tuple(self.trafo(P2))))
		else:
			self.PolyBezier(rct.Paths(), rct.Properties())

	def Ellipse(self, ell):
		trf = ell.trafo
		if (abs(trf.m11 - trf.m22) < 0.001 and abs(trf.m21 + trf.m12) < 0.001) \
		or (abs(trf.m11 + trf.m22) < 0.001 and abs(trf.m21 - trf.m12) < 0.001):
			if ell.start_angle == ell.end_angle:
				self.FillStyle(ell.Properties())
				C = trf(Point(0,0))
				R = sqrt(trf.m11 * trf.m11 + trf.m12 * trf.m12)
				self.putlongseq(0x4180 , map(rndtoint , tuple(self.trafo(C)) \
					+ (R * self.Scale,)))
			else:
				C = trf(Point(0,0))
				S = Point(cos(ell.start_angle) , sin(ell.start_angle))
				E = Point(cos(ell.end_angle) , sin(ell.end_angle))
				R = sqrt(trf.m11 * trf.m11 + trf.m12 * trf.m12)
				if trf.m11 * trf.m22 - trf.m12 * trf.m21 > 0:
					S,E = trf.DTransform(S) , trf.DTransform(E)
				else:
					S,E = trf.DTransform(E) , trf.DTransform(S)
				S = 1000000 * S / abs(S)
				E = 1000000 * E / abs(E)
				if ell.arc_type == 0 \
					and ell.Properties().fill_pattern == EmptyPattern:
					self.LineStyle(ell.Properties())
					self.putlongseq(0x41e0 ,  map(rndtoint , tuple(self.trafo(C)) \
						+ tuple(S) + tuple(E) + (R * self.Scale,)))
				else:
					#self.PolyBezier(ell.Paths(), ell.Properties())
					self.FillStyle(ell.Properties())
					if ell.arc_type == 0:
						cp = 1
					else:
						cp = 2 - ell.arc_type
					Args = ["!H7iH" , 0x4200 + 30] + map(rndtoint , tuple(self.trafo(C)) \
							+ tuple(S) + tuple(E) + (R * self.Scale , cp))
					apply(self.pack , Args)
		else:
			if ell.start_angle == ell.end_angle:
				self.FillStyle(ell.Properties())
				C = trf(Point(0,0))
				P1 = trf(Point(1,0))
				P2 = trf(Point(0,1))
				self.putlongseq(0x4220 , map(rndtoint , tuple(self.trafo(C)) \
					+ tuple(self.trafo(P1)) + tuple(self.trafo(P2))))
			else: 
				C = trf(Point(0,0))
				P1 = trf(Point(1,0))
				P2 = trf(Point(0,1))
				S = trf.DTransform(Point(cos(ell.start_angle) , sin(ell.start_angle)))
				E = trf.DTransform(Point(cos(ell.end_angle) , sin(ell.end_angle)))
				S = 1000000 * S / abs(S)
				E = 1000000 * E / abs(E)
				if ell.arc_type == 0 and ell.Properties().fill_pattern == EmptyPattern:
					self.LineStyle(ell.Properties())
					self.putlongseq(0x4240 ,  map(rndtoint , tuple(self.trafo(C)) \
						+ tuple(self.trafo(P1)) + tuple(self.trafo(P2)) + tuple(S) \
						+ tuple(E)))
				else:
					#self.PolyBezier(ell.Paths(), ell.Properties())
					self.FillStyle(ell.Properties())
					if ell.arc_type == 0:
						cp = 1
					else:
						cp = 2 - ell.arc_type
					Args = ["!HH10iH" , 0x4260 + 31 , 42] + map(rndtoint , tuple(self.trafo(C)) \
							+ tuple(self.trafo(P1)) + tuple(self.trafo(P2)) + tuple(S) \
							+ tuple(E) + (cp,))
					apply(self.pack , Args)

	def Image(self, object):
		self.Msg.Incl(W_Image)

	def Text(self, object):
		self.Msg.Incl(W_Text)
		self.PolyBezier(object.Paths(), object.Properties())

	def SaveObjects(self, Objects):

		for object in Objects:
			if object.is_Compound:
				self.SaveObjects(object.GetObjects())
			elif object.is_Rectangle:
				self.Rectangle(object)
			elif object.is_Ellipse:
				self.Ellipse(object)
			elif object.is_Image:
				self.Image(object)
			elif object.is_Text:
				self.Text(object)
			elif object.is_curve:
				self.PolyBezier(object.Paths(), object.Properties())

	def SaveLayers(self, Layers):

		# We put each layer in a picture, that seems at the
		# moment to be the approach
		for layer in Layers:
			if not layer.is_SpecialLayer and layer.Printable():
				
				# Begin Picture
				self.putstr(0x0060 , layer.name)

				# Color Selection Mode: Direct
				self.pack("!HH" , 0x2042 , 0x0001)

				# Edge Width Specification: Absolute
				self.pack("!HH" , 0x20a2 , 0x0000)

				# Line Width Specification: Absolute
				self.pack("!HH" , 0x2062 , 0x0000)

				# VDC Extend
				self.putlongseq(0x20c0 , self.extend)

				# Background Colour
				self.putcol(0x20e3 , self.white)

				# Begin Picture Body
				self.pack("!H" , 0x0080)

				self.SaveObjects(layer.GetObjects())

				# End Picture
				self.pack("!H" , 0x00a0)
			#if
		#for
	#end

	def SaveDocument(self, doc):

		# A dillema
		# Should the design fill the CGM-file or
		# Should it be placed approximately in
		# the same place as it is put on the page.
		if 0:
			left, bottom, right, top = doc.BoundingRect()
			width = right - left
			hight = top - bottom
		else:
			left, bottom = 0, 0
			width = doc.page_layout.width
			hight = doc.page_layout.height
			right , top = width , hight
		#sc = 65534 / max(width , hight)
		sc = 1000
		#self.trafo = Translation(-32767,-32767)(Scale(sc)(Translation(-left , -bottom)))
		self.trafo = Scale(sc)(Translation(-left , -bottom))
		self.Scale = sc
		self.extend = map(rndtoint , \
							tuple(self.trafo(left,bottom)) + tuple(self.trafo(right,top)))

		# Begin Metafile
		filename =  os.path.basename(self.pathname)
		title = filename + " generated by sK1"
		self.putstr(0x0020 , title)

		# Metafile Version
		self.pack("!H" , 0x1022)
		self.pack("!H" , 0x0001)

		# Metafile Description
		self.putstr(0x1040 , filename + " created by sk1")

		# Metafile Element List
		self.pack("!HHHH" , 0x1166 , 0x0001 , 0xffff , 0x0001)

		# Default Replacements
		self.pack("!H" , 0x1184)
		# VDC Integer precision 32 bits
		self.pack("!Hh" , 0x3022 , 32)
				
		#Font List
		#

		self.SaveLayers(doc.Layers())

		# End Meta File
		self.pack("!H" , 0x0040)

	#end

def save(document, file, filename, options = {}):
	saver = CGMSaver(file, filename, options)
	saver.SaveDocument(document)
	saver.close()
