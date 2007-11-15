# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
# This CGMloader mostly by Antoon Pardon (2002)
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
# $Id: cgmloader.py,v 1.1.1.2 2002/05/16 14:22:46 apardon Exp apardon $


###Sketch Config
#type = Import
#class_name = 'CGMLoader'
rx_magic = '\\000'
#tk_file_type = ('Computer Graphics Metafile', '.cgm')
#format_name = 'CGM'
#unload = 1
#standard_messages = 1
###End

#
#       Import Filter for CGM files
#
# Status:
#
#    First implementation.

import sys, os, string
from math import sin, cos, pi
import struct
import operator

from app import _, Trafo, Scale, Translation, Point, Polar, CreatePath, \
		CreateRGBColor, SolidPattern, EmptyPattern, LinearGradient, \
		MultiGradient, Style, const, StandardColors, GridLayer

from app.events.warn import INTERNAL, warn_tb
from app.io.load import GenericLoader, SketchLoadError

basestyle = Style()
basestyle.fill_pattern = EmptyPattern
basestyle.fill_transform = 1
#baseline.line_pattern = SolidPattern(StandardColors.black)
basestyle.line_pattern = EmptyPattern
basestyle.line_width = 1.0
basestyle.line_join = const.JoinMiter
basestyle.line_cap = const.CapButt
basestyle.line_dashes = ()
basestyle.line_arrow1 = None
basestyle.line_arrow2 = None
basestyle.font = None
basestyle.font_size = 12.0


CGM_ID = {
	0x0020: 'BEGMF',
	0x0060: 'BEGPIC',
	0x0080: 'BEGPICBODY',
	0x00A0: 'ENDPIC',
	0x0040: 'ENDMF',
	0x1020: 'mfversion',
	0x1040: 'mfdesc',
	0x1060: 'vdctype',
	0x1080: 'integerprec',
	0x10e0: 'colrprec',
	0x1100: 'colrindexprec',
	0x1140: 'colrvalueext',
	0x1160: 'mfelemlist',
	0x2040: 'colrmode',
	0x2080: 'markersizemode',
	0x20a0: 'edgewidthmode',
	0x2060: 'linewidthmode',
	0x20c0: 'vdcext',
	0x20e0: 'backcolr',
	0x3020: 'vdcintegerprec',
	0x5040: 'linetype',
	0x5100: 'markercolr',
	0x51c0: 'textcolr',
	0x52e0: 'fillcolr',
	0x52c0: 'intstyle',
	0x5360: 'edgetype',
	0x5380: 'edgewidth',
	0x53c0: 'edgevis',
	0x53a0: 'edgecolr',
	0x5060: 'linewidth',
	0x5080: 'linecolr',
	0x40e0: 'POLYGON',
	0x4020: 'LINE',
}
	
def noop(self):
	pass


class cgminfo:
	def __init__(self):
		pass


class CGMLoader(GenericLoader):

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file = file
		self.cgm = cgminfo()
		self.verbosity = 1

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

	def unpack(self, format):
		# self._print(format)
		size = struct.calcsize(format)
		return struct.unpack(format, self.file.read(size))

	def get_u8(self):
		return self.unpack("!B")[0]

	def get_u16(self):
		return self.unpack("!H")[0]

	def get_int32(self):
		return self.get_struct('!i')[0]

	def getstr(self):
		lng = self.get_u8()
		return self.unpack("!" + `lng` + "s")[0]

	def getcol(self):
		cgmcol = self.unpack(self.cgm.color.struct)
		cgmcol = map(operator.sub , cgmcol , self.cgm.color.offset)
		cgmcol = map(operator.div , cgmcol , self.cgm.color.scale)
		#self._print("color %3d %3d %3d" % cgmcol)
		return apply(CreateRGBColor , cgmcol)

	def BEGMF(self, size):
		# self._print (self.getstr())
		self.cgm.color = cgminfo()
		self.cgm.color.struct = "!BBB"
		self.cgm.color.offset = (0.0, 0.0, 0.0)
		self.cgm.color.scale = (255.0, 255.0, 255.0)
		self.cgm.line = cgminfo()
		self.cgm.fill = cgminfo()
		self.cgm.edge = cgminfo()
		self.cgm.text = cgminfo()
		self.cgm.marker = cgminfo()
		self.document()

	def mfversion(self, size):
		if self.get_u16() != 1:
			raise SketchLoadError("Can only load CGM version 1")

	def mfdesc(self,size):
		pass
		# self._print(self.getstr())

	def vdctype(self,size):
		if size != 2:
			raise SketchLoadError("Size for vdctype is %d" % (size,))
		if self.get_u16() != 0:
			raise SketchLoadError("This implementation only works with integer VDC's")

	def integerprec(self, size):
		if size != 2:
			raise SketchLoadError("Size for integer precision is %d" % (size,))
		bits = self.get_u16()
		if bits != 16:
			raise SketchLoadError("This implementation only allows 16 bit integers not %d" % (bits,))

	def vdcintegerprec(self, size):
		if size != 2:
			raise SketchLoadError("Size for integer precision is %d" % (size,))
		bits = self.get_u16()
		if bits != 16:
			raise SketchLoadError("This implementation only allows 16 bit VDC integers not %d" % (bits,))

	def colrvalueext(self, size):
		bottom = self.unpack(self.cgm.color.struct)
		top = self.unpack(self.cgm.color.struct)
		# self._print('bottom =' , bottom)
		# self._print('top =' , top)
		self.cgm.color.offset = map(operator.mul , bottom , (1.0, 1.0, 1.0))
		self.cgm.color.scale = map(operator.sub, top , self.cgm.color.offset)
		# self._print('offset =' , self.cgm.color.offset)
		# self._print('scale =' , self.cgm.color.scale)

	def colrprec(self, size):
		if size != 2:
			raise SketchLoadError("Size for colour index precision is %d" % (size,))
		bits = self.get_u16()
		if bits == 8:
			self.cgm.color.struct = "!BBB"
		elif bits == 16:
			self.cgm.color.struct = "!HHH"
		elif bits == 32:
			self.cgm.color.struct = "!III"
		else:
			raise SketchLoadError("This implementation can't work with %d bit colour components" % (bits,))

	def colrindexprec(self, size):
		if size != 2:
			raise SketchLoadError("Size for colour index precision is %d" % (size,))
		bits = self.get_u16()
		if bits != 16:
			raise SketchLoadError("This implementation only allows 16 colour indices not %d" % (bits,))


	def mfelemlist(self, size):
		pass

	def BEGPIC(self, size):
		ln = self.getstr()
		self.layer(name = ln)
		# self._print("layer:" , ln)

	def colrmode(self, size):
		self.cgm.color.mode = self.get_u16()
		if self.cgm.color.mode != 1:
			raise SketchLoadError("Only direct color mode is implemented")
		
	def linewidthmode(self, size):
		self.cgm.line.widthmode = self.get_u16()
		if self.cgm.line.widthmode != 0:
			raise SketchLoadError("Only absolute width mode is implemented")
		
	def edgewidthmode(self, size):
		self.cgm.edge.widthmode = self.get_u16()
		if self.cgm.edge.widthmode != 0:
			raise SketchLoadError("Only absolute width mode is implemented")
		
	def markersizemode(self, size):
		self.cgm.marker.sizemode = self.get_u16()
		if self.cgm.marker.sizemode != 0:
			raise SketchLoadError("Only absolute size mode is implemented")

	def vdcext(self, size):
		left, bottom, right, top = self.unpack("!hhhh")
		width = right - left
		height = top - bottom
		sc = 841 / (1.0 * max(abs(width) , abs(height)))
		self.Scale = sc
		# self._print("Scale =" , sc)
		self.trafo = Scale(sc)(Translation(-left , -bottom))
		# self._print("(%d %d) => %s" % (left , bottom , self.trafo(left,bottom)))
		
	def backcolr(self, size):
		self.getcol()

	def BEGPICBODY(self, size):
		self.cgm.fill.type = 1
		self.cgm.edge.visible = 1
		self.cgm.fill.color = StandardColors.black 
		self.cgm.edge.color = StandardColors.black
		self.cgm.line.color = StandardColors.black

	def ENDPIC(self, size):
		pass

	def ENDMF(self, size):
		pass

	def edgevis(self, size):
		self.cgm.edge.visible = self.get_u16()

	def edgewidth(self, size):
		self.cgm.edge.width = self.get_u16() * self.Scale

	def linewidth(self, size):
		self.cgm.line.width = self.get_u16() * self.Scale

	def linetype(self, size):
		self.cgm.line.type = self.get_u16()

	def edgetype(self, size):
		self.cgm.edge.type = self.get_u16()

	def edgecolr(self, size):
		self.cgm.edge.color = self.getcol()

	def linecolr(self, size):
		self.cgm.line.color = self.getcol()

	def textcolr(self, size):
		self.cgm.text.color = self.getcol()

	def markercolr(self, size):
		self.cgm.marker.color = self.getcol()

	def intstyle(self, size):
		self.cgm.fill.type = self.get_u16()

	def fillcolr(self, size):
		self.cgm.fill.color = self.getcol()

	def Path(self, size):
		path = CreatePath()
		for i in range(size / 4):
			path.AppendLine(self.trafo(self.unpack("!hh")))
		return path
			

	def POLYGON(self, size):
		path = self.Path(size)
		if path.Node(-1) != path.Node(0):
			path.AppendLine(path.Node(0))
		path.load_close()
		style = basestyle.Duplicate()
		if self.cgm.fill.type == 1:
			style.fill_pattern = SolidPattern(self.cgm.fill.color)
		if self.cgm.edge.visible:
			style.line_pattern = SolidPattern(self.cgm.edge.color)
			style.line_pattern.line_width = self.edgewidth
		self.prop_stack.AddStyle(style)
		self.bezier((path,))

	def LINE(self, size):
		path = self.Path(size)
		style = basestyle.Duplicate()
		style.line_pattern = SolidPattern(self.cgm.line.color)
		style.line_pattern.line_width = self.cgm.line.width
		self.prop_stack.AddStyle(style)
		self.bezier((path,))
			

	def interpret(self):
		tell = self.file.tell
		Id = -1
		while Id != 0x40:
			pos = tell()
			head = self.get_u16()
			Id = head & 0xffe0
			size = head & 0x001f
			hdsz = 2
			if size == 31:
				size = self.get_u16()
				hdsz = 4
			pdsz = ((size + 1) / 2) * 2
			#self._print('%5d(%5d): %4x: %s' % (size, pdsz, Id, CGM_ID.get(Id, '')))
			if hasattr(self, CGM_ID.get(Id, '')):
				# self._print('Calling %s' % (CGM_ID.get(Id, '')))
				getattr(self, CGM_ID[Id])(size)
			else:
				if Id:
					self.file.read(pdsz)
					name = CGM_ID.get(Id, '')
					Class = Id >> 12
					Elem = (Id & 0x0fff) >> 5
					self._print('*** unimplemented: %4x; class = %d, element = %2d  %s' 
										% (Id , Class , Elem, name))
			pos = pos + hdsz + pdsz
			if tell() < pos:
				self.file.read(pos - tell())
			elif tell() > pos:
				self._print('read too many bytes')
				self.file.seek(pos - tell(), 1)

	def Load(self):

		self.file.seek(0)
		self.interpret()
		# self.begin_layer_class(GridLayer, ((0,0,20,20), 0 , StandardColors.blue , "Grid"))
		# self.end_composite()
		self.end_all()
		self.object.load_Completed()
		return self.object

