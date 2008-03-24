# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
# This CGMsaver from Antoon Pardon (2002)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Libary General Public License as published
# by the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# $Id:  $

###Sketch Config
#type = Export
#tk_file_type = ("Computer Graphics Metafile (CGM)", '.cgm')
#extensions = '.cgm'
format_name = 'CGM'
#unload = 1
###End

import struct

import os.path

from app import Scale, Translation, Bezier, CreateRGBColor, EmptyPattern

# Fault Tolerance for flattening Beziers.
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
		if (C1 * N) < -EPS or (C2 * N) > EPS or cr(C1,B)*cr(C2,B) < 0 or abs(cr(N,S)) > EPS:  
			return FlattenPath(P0, P4, P7, P9) + FlattenPath(P9, P8, P6, P3)
		else:
			return (P9, P3)


class CGMSaver:

	def __init__(self, file, pathname, options):
		self.file = file
		self.pathname = pathname
		self.options = options
		self.white = CreateRGBColor(1.0 , 1.0 , 1.0)

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

	def putintseq(self , Id , seq):
		lng = len(seq)
		if 2 * lng < 31:
			self.pack("!H" , Id | 2 * lng)
		else:
			self.pack("!H" , Id | 31)
			self.pack("!H" , 2 * lng)
		fmt = '!' + `lng` + "h"
		args = (fmt,) + tuple(seq)
		apply(self.pack , args)

	def putcol(self , Id , color):
		red = rndtoint(255 * color.red)
		green = rndtoint(255 * color.green)
		blue = rndtoint(255 * color.blue)
		self.pack("!HBBBB" , Id , red , green , blue , 0)
		

	def close(self):
		self.file.close()

	def PolyBezier(self, Paths, Properties):

		line_pattern = Properties.line_pattern
		fill_pattern = Properties.fill_pattern
		if line_pattern is EmptyPattern:

			# Edge Visibility Off
			self.pack("!HH" , 0x53c2 , 0x0000)
		else:  
			
			# Edge Visibility On
			self.pack("!HH" , 0x53c2 , 0x0001)
			line_width = rndtoint(self.Scale * Properties.line_width)

			# Sketch doesn't distinghuish between Polylines and
			# Polygons. Instead of trying to figure out what
			# kind we are dealing with, we set the cgm linewidth
			# as well as the cgm edgewidth

			# Edge width
			self.pack("!HH" , 0x5382 , line_width)

			# Line width
			self.pack("!HH" , 0x5062 , line_width)
			if line_pattern.is_Solid:
				self.putcol(0x53a3 , line_pattern.Color())
				self.putcol(0x5083 , line_pattern.Color())

		if fill_pattern is EmptyPattern:

			# Fill type is Hollow
			self.pack("!HH" , 0x52c2 , 0x0004)
		else:
			
			# Fill type is Solid
			self.pack("!HH" , 0x52c2 , 0x0001)
			if fill_pattern.is_Solid:
				self.putcol(0x52e3 , fill_pattern.Color())
		for path in Paths:
			if path.closed:
				Id = 0x40e0 # Polygon
			else:
				Id = 0x4020 # Polyline
			parlst = ()
			for i in range(path.len):
				type, control, p, cont = path.Segment(i)
				if type == Bezier:
					p1 , p2 = control
					tmplst = FlattenPath(p0, p1, p2, p)
					for tp in tmplst:
						parlst = parlst + tuple(self.trafo(tp))
				else:
					parlst = parlst + tuple(self.trafo(p))
				p0 = p
			if Id == 0x40e0:
				parlst = parlst[:-2]
			self.putintseq(Id , map(rndtoint , parlst))

	def SaveObjects(self, Objects):

		for object in Objects:
			if object.is_Compound:
				self.SaveObjects(object.GetObjects())
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
				self.putintseq(0x20c0 , self.extend)

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
		sc = 65534 / max(width , hight)
		self.trafo = Translation(-32767,-32767)(Scale(sc)(Translation(-left , -bottom)))
		self.Scale = sc
		self.extend = map(rndtoint , tuple(self.trafo(left,bottom)) + tuple(self.trafo(right,top)))


		# Begin Metafile
		filename =  os.path.basename(self.pathname)
		title = filename + " generated by sK1"
		self.putstr(0x0020 , title)

		# Metafile Version
		self.pack("!H" , 0x1022)
		self.pack("!H" , 0x0001)

		# Metafile Description
		self.putstr(0x1040 , filename + "created by sk1")

		# Metafile Element List
		self.pack("!HHHH" , 0x1166 , 0x0001 , 0xffff , 0x0001)

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
