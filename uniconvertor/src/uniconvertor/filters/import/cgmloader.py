# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
# This CGMloader mostly by Antoon Pardon (2002)
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
# $Id: cgmloader.py,v 1.1.2.3 2003/05/17 18:22:14 bherzog Exp $
################################################################################


###Sketch Config
#type = Import
#class_name = 'CGMLoader'
rx_magic = '\\x00'
#tk_file_type = ('Computer Graphics Metafile', '.cgm')
#format_name = 'CGM'
#unload = 1
#standard_messages = 1
###End

#
#       Import Filter for CGM files
#
import sys, os, string
from math import sin, cos, pi, atan2
import struct
import operator
import copy
import types

from app import _, Trafo, Scale, Translation, Point, Polar, CreatePath, \
		CreateRGBColor, SolidPattern, EmptyPattern, LinearGradient, \
		MultiGradient, Style, const, StandardColors, GridLayer, GetFont, \
		HatchingPattern

from app.events.warn import INTERNAL, warn_tb
from app.io.load import GenericLoader, SketchLoadError
import sk1libs
from app.Graphics import text

basestyle = Style()
basestyle.fill_pattern = EmptyPattern
basestyle.fill_transform = 1
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
	0x0040: 'ENDMF',
	0x0060: 'BEGPIC',
	0x0080: 'BEGPICBODY',
	0x00A0: 'ENDPIC',
	0x1020: 'mfversion',
	0x1040: 'mfdesc',
	0x1060: 'vdctype',
	0x1080: 'integerprec',
	0x10a0: 'realprec',
	0x10c0: 'indexprec',
	0x10e0: 'colrprec',
	0x1100: 'colrindexprec',
	0x1120: 'maxcolrindex',
	0x1140: 'colrvalueext',
	0x1160: 'mfelemlist',
	0x1180: 'mfdfltrpl',
	0x11a0: 'fontlist',
	0x11c0: 'charsetlist',
	0x11e0: 'charcoding',
	0x2020: 'scalemode',
	0x2040: 'colrmode',
	0x2060: 'linewidthmode',
	0x2080: 'markersizemode',
	0x20a0: 'edgewidthmode',
	0x20c0: 'vdcext',
	0x20e0: 'backcolr',
	0x3020: 'vdcintegerprec',
	0x3040: 'vdcrealprec',
	0x3060: 'auxcolr',
	0x3080: 'transparency',
	0x30a0: 'cliprect',
	0x30c0: 'clip',
	0x4020: 'LINE',
	0x4040: 'DISJTLINE',
	0x4060: 'MARKER',
	0x4080: 'TEXT',
	0x40a0: 'RESTRTEXT',
	0x40c0: 'APNDTEXT',
	0x40e0: 'POLYGON',
	0x4100: 'POLYGONSET',
	0x4120: 'CELLARRAY',
	0x4140: 'GDP',
	0x4160: 'RECT',
	0x4180: 'CIRCLE',
	0x41a0: 'ARC3PT',
	0x41c0: 'ARC3PTCLOSE',
	0x41e0: 'ARCCTR',
	0x4200: 'ARCCTRCLOSE',
	0x4220: 'ELLIPSE',
	0x4240: 'ELLIPARC',
	0x4260: 'ELLIPARCCLOSE',
	0x5040: 'linetype',
	0x5060: 'linewidth',
	0x5080: 'linecolr',
	0x50c0: 'markertype',
	0x5100: 'markercolr',
	0x5140: 'textfontindex',
	0x5160: 'textprec',
	0x5180: 'charexpan',
	0x51a0: 'charspace',
	0x51c0: 'textcolr',
	0x51e0: 'charheight',
	0x5200: 'charori',
	0x5220: 'textpath',
	0x5240: 'textalign',
	0x5260: 'charsetindex',
	0x52c0: 'intstyle',
	0x52e0: 'fillcolr',
	0x5300: 'hatchindex',
	0x5320: 'patindex',
	0x5360: 'edgetype',
	0x5380: 'edgewidth',
	0x53a0: 'edgecolr',
	0x53c0: 'edgevis',
	0x5440: 'colrtable',
	0x5460: 'asf',
	0x6020: 'ESCAPE',
}
	

cp = copy.deepcopy

fntlst = map(lambda l: l[0], sk1libs.ft2engine.fontlist)
#print sk1libs.ft2engine.fontlist
#print fntlst

fntalias = {
	'AvantGarde' : () ,
	'Bookman' : ('Brooklyn',) ,
	'Courier' : ('Fixed',) ,
	'Helvetica' : ('Arial' , 'Swiss' , 'Switzerland' , 'Monospace') ,
	'NewCenturySchlbk' : ('NewBrunswick' , 'NewCenturion') , 
	'Palatino' : ('PalmSprings' , 'Zapf Calligraphic') ,
	'Times' : ('Dutch' , 'Times New Roman') ,
	'Symbol' : ('GreekMathSYmbols',) ,
	'ZapfChancery' : ('ZurichCalligraphic',) ,
	'ZapfDingbats' : ('Dixieland',) ,
	'URWGothicL' : ('Block',) ,
	'CenturySchL' : ('NewBrunswick' , 'WordPerfect' , 'Centurion') , 
	'URWBookmanL' : () ,
	'Dingbats' : () ,
	'NimbusSanL' : () ,
	'NimbusRomNo9L' : () ,
	'NimbusMonL' : () ,
	'URWPalladioL' : () ,
	'StandardSymL' : () ,
	'URWChanceryL' : () ,
	'Utopia' : ('Univers' , ) ,
	'CharterBT' : ('Bernhard Modern BT' , 'Blackletter' , 'Brush' , 
					'GeometricSlabSerif' , 'Humanist' , 'Onyx') 
}
	
	
class cgminfo:
	def __init__(self):
		pass

def sign(num):
	return num/abs(num)

def cr(P1, P2):
	return P1.x * P2.y - P1.y * P2.x

def Angle(V):
	x, y = V
	return (atan2(y,x) % (2 * pi))

def Angle2(V1, V2):
	return Angle((V1*V2 , cr(V1,V2)))

def cr3(P1, P2, P3):
	return cr(P1, P2) + cr(P2, P3) + cr(P3, P1)

def Cnt3Pnt(P1, P2, P3):
	Q1 = Point(P1*P1 , P1.y)
	Q2 = Point(P2*P2 , P2.y)
	Q3 = Point(P3*P3 , P3.y)
	R1 = Point(P1.x , P1*P1)
	R2 = Point(P2.x , P2*P2)
	R3 = Point(P3.x , P3*P3)
	N = 2 * cr3(P1, P2, P3)
	Nx = cr3(Q1, Q2, Q3)
	Ny = cr3(R1, R2, R3)
	return Point(Nx/N , Ny/N)

def transform_base(po, px, py):
	return apply(Trafo, tuple(px - po) + tuple(py - po) + tuple(po))

def CreateColorTable(sz):

	Max = 1
	bs = 0
	while Max < sz:
		Max = Max * 2
		bs = bs + 1
	cb = bs / 3
	tb = bs % 3
	mc = (1 << (cb + tb)) - 1.0
	Table = Max * [(0.0, 0.0, 0.0)] 
	for i in range(Max):
		j =  i + Max - 1
		j = j % Max
		red, grn, blu = 0, 0, 0
		for k in range(cb):
			red = (red << 1) + j % 2
			j = j >> 1
			grn = (grn << 1) + j % 2
			j = j >> 1
			blu = (blu << 1) + j % 2
			j = j >> 1
		tint = j
		red = (red << tb) + tint
		grn = (grn << tb) + tint
		blu = (blu << tb) + tint
		Table[i] = (red / mc, grn / mc, blu / mc)
	return Table

def strmatch(s1, s2):

	s1 = list(s1.lower())
	s2 = list(s2.lower())
	len1 = len(s1)
	len2 = len(s2)
	for i in range(len1):
		if not s1[i].isalnum():
			s1[i] = ' '
	for i in range(len2):
		if not s2[i].isalnum():
			s2[i] = ' '
	mat = (len1 + 1) * [0]
	for i in range(len1 + 1):
		mat[i] = (len2 + 1) * [0]
	for i in range(len1 + 1):
		mat[i][0] =  i
	for i in range(len2 + 1):
		mat[0][i] =  i
	for i in range(1, len1 + 1):
		for j in range(1 , len2 + 1):
			t = min(mat[i - 1][j] , mat[i][j - 1]) + 1
			if s1[i - 1] == s2[j - 1]:
				t = min(t , mat[i - 1][j - 1])
			mat[i][j] = t
	x = len1
	y = len2
	dx = 0
	dy = 0
	while x * y != 0:
		if s1[x - 1] == s2[y - 1]:
			x = x - 1
			y = y - 1
		else:
			if mat[x - 1][y] < mat[x][y - 1]:
				x = x - 1
				dx = dx + 1
			else:
				y = y - 1
				dy = dy + 1
	dx = x + dx
	dy = y + dy
	return dx + dy

init = cgminfo()
dflt = cgminfo()
curr = cgminfo()
reff = dflt

init.intprec = 1 # 16 bits
init.intsize = 2
init.inxprec = 1 # 16 bits
init.inxsize = 2
init.realprec = 0 # 32 bits fixed point
init.realsize = 4
init.color = cgminfo()
init.color.absstruct = "!BBB"
init.color.inxstruct = "!B"
init.color.mode = 0
init.color.maxindex = 63
init.color.table = CreateColorTable(64)
init.color.offset = (0.0, 0.0, 0.0)
init.color.scale = (255.0, 255.0, 255.0)
init.vdc = cgminfo()
init.vdc.type = 0 # integers
init.vdc.realprec = 0 # 32 bits fixed point
init.vdc.realsize = 4
init.vdc.intprec = 1 # 16 bits
init.vdc.intsize = 2
init.vdc.prec = None # integers , 16 bit
init.vdc.size = None
init.vdc.intextend = ((0,0),(32767,32767))
init.vdc.realextend = ((0.0,0.0),(1.0,1.0))
init.vdc.extend = None #((0,0),(32767,32767))
init.fill = cgminfo()
init.fill.type = 1
init.fill.color = (0.0, 0.0, 0.0)
init.line = cgminfo()
init.line.type = 1
init.line.color = (0.0, 0.0, 0.0)
init.line.widthmode = 0
init.line.width = None
init.line.dashtable = ((), (4,4) , (1,1) , (4,1,1,1) , (4,1,1,1,1,1))
init.edge = cgminfo()
init.edge.type = 1
init.edge.color = (0.0, 0.0, 0.0)
init.edge.widthmode = 0
init.edge.width = None
init.edge.dashtable = init.line.dashtable
init.edge.visible = 0
init.text = cgminfo()
init.text.fontindex = fntlst.index((sk1libs.ft2engine.fontlist[0])[0])
init.text.height = None
init.text.expansion = 1.0
init.text.spacing = 0.0
init.text.orientation = ((0.0 , 1.0),(1.0, 0.0)) # Up , Base vector
init.text.path = 0 # right
init.text.alignment = 0 # Dont understand this yet.
init.text.color = (0.0, 0.0, 0.0)
init.marker = cgminfo()
init.marker.sizemode = 0
init.marker.type = 3
init.marker.size = None
init.clip = cgminfo()
init.clip.mode = 1
init.clip.rect = init.vdc.extend
init.scale = cgminfo()
init.scale.mode = 0 # abstract
init.scale.metric = 0.0


class CGMLoader(GenericLoader):

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file = file
		self.verbosity = 15
		self.IntF = (self.i8, self.i16, self.i24, self.i32)
		self.CardF = (self.u8, self.u16, self.u24, self.u32)
		self.FloatF = (self.flp32, self.flp64)
		self.FixedF = (self.fip32, self.fip64)
		self.RealF = self.FixedF + self.FloatF
		self.VDCF = (self.IntF, self.RealF)

	def _print(self, pl , format, *args, **kw):
		if pl <= self.verbosity:
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
		size = struct.calcsize(format)
		return struct.unpack(format, self.file.read(size))

	def u8(self):
		return self.unpack("!B")[0]

	def u16(self):
		return self.unpack("!H")[0]

	def u24(self):
		t = self.unpack("!BH")
		return (t[0] << 16) | t[1]

	def u32(self):
		return self.unpack("!I")[0]

	def i8(self):
		return self.unpack("!b")[0]

	def i16(self):
		return self.unpack("!h")[0]

	def i24(self):
		t = self.unpack("!bH")
		return (t[0] << 16) | t[1]

	def i32(self):
		return self.unpack("!i")[0]

	def fip32(self):
		t = self.unpack("!hH")
		return t[0] + t[1] / 65536.0

	def fip64(self):
		t = self.unpack("!hH")
		return t[0] + t[1] / (65536.0 * 65536.0)

	def flp32(self):
		return self.unpack("!f")[0]

	def flp64(self):
		return self.unpack("!d")[0]

	def Int(self):
		return self.IntF[reff.intprec]()

	def Real(self):
		return self.RealF[reff.realprec]()

	def Inx(self):
		return self.IntF[reff.inxprec]()

	def Enum(self):
		return self.unpack("!h")[0]

	def VDC(self):
		return self.VDCF[reff.vdc.type][reff.vdc.prec]()

	def Pnt(self):
		return (self.VDC() , self.VDC())

	def getstr(self):
		lng = self.u8()
		return self.unpack("!" + `lng` + "s")[0]

	def getcol(self):
		if reff.color.mode == 1:
			cgmcol = self.unpack(reff.color.absstruct)
			cgmcol = map(operator.sub , cgmcol , reff.color.offset)
			cgmcol = map(operator.div , cgmcol , reff.color.scale)
			return cgmcol
		else:
			cgmcol = self.unpack(reff.color.inxstruct)[0]
			return reff.color.table[cgmcol % reff.color.maxindex]

#   0x0020: 
	def BEGMF(self, size):
		self._print(10 ,  '======= 0.1 =======')
		global dflt, reff
		dflt = cp(init)
		reff = dflt
		self.document()
		self.fntmap = range(78)
		self.fntmap.insert(0,0)

#   0x0040: 
	def ENDMF(self, size):
		pass

#   0x0060:
	def BEGPIC(self, size):
		global curr, reff
		curr = cp(dflt)
		reff = curr
		if reff.vdc.extend == None:
			if reff.vdc.type == 0:
				reff.vdc.extend = reff.vdc.intextend
				reff.vdc.size = reff.vdc.intsize
				reff.vdc.prec = reff.vdc.intprec
			else:
				reff.vdc.extend = reff.vdc.realextend
				reff.vdc.size = reff.vdc.realsize
				reff.vdc.prec = reff.vdc.realprec
		if reff.vdc.prec == None:
			if reff.vdc.type == 0:
				reff.vdc.size = reff.vdc.intsize
				reff.vdc.prec = reff.vdc.intprec
			else:
				reff.vdc.size = reff.vdc.realsize
				reff.vdc.prec = reff.vdc.realprec
		Hgt = reff.vdc.extend[1][1] - reff.vdc.extend[0][1]
		Wdt = reff.vdc.extend[1][0] - reff.vdc.extend[0][0]
		LS = max(abs(Hgt),abs(Wdt))
		if reff.clip.rect == None:
			reff.clip.rect = reff.vdc.extend
		if reff.marker.size == None:
			if reff.marker.sizemode == 0:
				reff.marker.size = LS / 100.0
			else:
				reff.marker.size = 3
		if reff.text.height == None:
			reff.text.height = LS / 100.0
		if reff.edge.width == None:
			if reff.edge.widthmode == 0:
				reff.edge.width = LS / 1000.0
			else:
				reff.edge.width = 1
		if reff.line.width == None:
			if reff.line.widthmode == 0:
				reff.line.width = LS / 1000.0
			else:
				reff.line.width = 1
		ln = self.getstr()
		self.layer(name = ln)

#   0x0080:
	def BEGPICBODY(self, size):
		self.mktrafo(reff.vdc.extend)

#   0x00A0:
	def ENDPIC(self, size):
		pass

#   0x1020:
	def mfversion(self, size):
		if self.u16() != 1:
			raise SketchLoadError("Can only load CGM version 1")

#   0x1040:
	def mfdesc(self,size):
		pass

#   0x1060:
	def vdctype(self,size):
		reff.vdc.type = self.Enum()
		if reff.vdc.type == 0:
			reff.vdc.size = reff.vdc.intsize
			reff.vdc.prec = reff.vdc.intprec
			reff.vdc.extend = reff.vdc.intextend
		else:
			reff.vdc.size = reff.vdc.realsize
			reff.vdc.prec = reff.vdc.realprec
			reff.vdc.extend = reff.vdc.realextend

#   0x1080:
	def integerprec(self, size):
		bits = self.Int()
		if bits in (8,16,24,32):
			reff.intsize = (bits / 8) 
			reff.intprec = reff.intsize - 1
		else:
			raise SketchLoadError("This implementation can't work with %d bit integers" % (bits,))

#   0x10a0:
	def realprec(self, size):
		type = self.Enum()
		prec = (self.Int(), self.Int())
		if type == 1:
			if prec == (16, 16):
				reff.realprec = 0 # 32 bit fixed precision
			elif prec == (32, 32):
				reff.realprec = 1 # 64 bit fixed precision
			else:
				raise SketchLoadError("This implementation can't work with %d,%d bit fixed points" % prec)
		else:
			if prec == (9, 23):
				reff.realprec = 2 # 32 bit floating point
			elif prec == (12, 52):
				reff.realprec = 3 # 64 bit floating point
			else:
				raise SketchLoadError("This implementation can't work with %d,%d bit floatingpoints" % prec)


#   0x10c0: 'indexprec',
	def indexprec(self, size):
		bits = self.Int()
		if bits in (8,16,24,32):
			reff.inxsize = (bits / 8) 
			reff.inxprec = reff.inxsize - 1
		else:
			raise SketchLoadError("This implementation can't work with %d bit indices" % (bits,))

#   0x10e0:
	def colrprec(self, size):
		bits = self.Int()
		if bits == 8:
			reff.color.absstruct = "!BBB"
		elif bits == 16:
			reff.color.absstruct = "!HHH"
		elif bits == 32:
			reff.color.absstruct = "!III"
		else:
			raise SketchLoadError("This implementation can't work with %d bit color components" % (bits,))

#   0x1100:
	def colrindexprec(self, size):
		bits = self.Int()
		if bits == 8:
			reff.color.inxstruct = "!B"
		elif bits == 16:
			reff.color.inxstruct = "!H"
		elif bits == 32:
			reff.color.inxstruct = "!I"
		else:
			raise SketchLoadError("This implementation can't work with %d bit color indices" % (bits,))

#   0x1120: 'maxcolrindex',
	def maxcolrindex(self, size):
		reff.color.maxindex = self.unpack(reff.color.inxstruct)[0]
		reff.color.table = CreateColorTable(reff.color.maxindex)

#   0x1140:
	def colrvalueext(self, size):
		bottom = self.unpack(reff.color.absstruct)
		top = self.unpack(reff.color.absstruct)
		reff.color.offset = map(operator.mul , bottom , (1.0, 1.0, 1.0))
		reff.color.scale = map(operator.sub, top , reff.color.offset)

#   0x1160:
	def mfelemlist(self, size):
		pass

#   0x1180:
	def mfdfltrpl(self, size):
		self.interpret(size)

#   0x11a0:
	def fontlist(self, size):
		tot = 0
		fntinx = 1
		while tot < size:
			fontname = self.getstr()
			bsteval = 100
			bstinx = 0
			for inx in range(len(fntlst)):
				fntname = fntlst[inx]
				if fntname is not None:
					baseinx = fntname.find('-')
					if baseinx == -1:
						baseinx = len(fntname)
					basename = fntname[0:baseinx]
					postfix = fntname[baseinx:]
					self._print(20 , "fontname = %s; basename = %s; postfix = %s\n" , fntname , basename , postfix)
					self._print(30 , "base = %s; baselst = %s\n" , basename , fntalias.get(basename , ()))
					baselst = (basename,) + fntalias.get(basename , ())
					for suffix in ["" , "-Roman" , "-Regular" , "-Book"]:
						for base in baselst:
							score = strmatch(fontname + suffix , base + postfix)
							if score < bsteval:
								bsteval = score
								bstinx = inx
			self.fntmap[fntinx] = bstinx
			tot = tot + len(fontname) + 1
			self._print(10 , 'font[%d]: %s => %s = %s\n' , fntinx , fontname , fntlst[bstinx] , fntlst[self.fntmap[fntinx]])
			fntinx = fntinx + 1


#   0x2020: 'scalemode',
	def scalemode(self,size):
		reff.scale.mode = self.Enum()
		if reff.realprec in (2,3):  # floatingpoint precision
			reff.scale.metric = self.Real()
		else:
			reff.scale.metric = self.flp32()
		if reff.scale.mode == 1 and reff.scale.metric == 0:
			self._print(10 , "Scale metric set to zero; mode set back to absolute")
			reff.scale.mode = 0

#   0x2040:
	def colrmode(self, size):
		reff.color.mode = self.Enum()
		
#   0x2060:
	def linewidthmode(self, size):
		reff.line.widthmode = self.Enum()
		
#   0x2080:
	def markersizemode(self, size):
		reff.marker.sizemode = self.Enum()

#   0x20a0:
	def edgewidthmode(self, size):
		reff.edge.widthmode = self.Enum()


	def mktrafo(self, extend):
		if reff.scale.mode == 0:
			left, bottom = extend[0]
			right, top = extend[1]
			width = right - left
			height = top - bottom
			sc = 841 / (1.0 * max(abs(width) , abs(height)))
		else:
			left = 0
			bottom = 0
			width = 1
			height = 1
			sc = reff.scale.metric * 72 / 25.4
		self.Scale = sc
		self.trafo = Scale(sign(width)*sc , sign(height)*sc)(Translation(-left , -bottom))
		
#   0x20c0:
	def vdcext(self, size):
		ll = self.Pnt()
		ur = self.Pnt()
		reff.vdc.extend = (ll,ur)
		
#   0x20e0:
	def backcolr(self, size):
		self.getcol()

#   0x3020:
	def vdcintegerprec(self, size):
		bits = self.Int()
		if bits in (8,16,24,32):
			reff.vdc.intsize = (bits / 8) 
			reff.vdc.intprec = reff.vdc.intsize - 1
			if reff.vdc.type == 0:
				reff.vdc.size = reff.vdc.intsize
				reff.vdc.prec = reff.vdc.intprec
		else:
			raise SketchLoadError("This implementation can't work with %d bit integers" % (bits,))

#   0x3040:
	def vdcrealprec(self, size):
		type = self.Enum()
		prec = (self.Int(), self.Int())
		if type == 1:
			if prec == (16, 16):
				reff.vdc.realprec = 0 # 32 bit fixed precision
			elif prec == (32, 32):
				reff.vdc.realprec = 1 # 64 bit fixed precision
			else:
				raise SketchLoadError("This implementation can't work with %d,%d bit fixed points" % prec)
		else:
			if prec == (9, 23):
				reff.vdc.realprec = 2 # 32 bit floating point
			elif prec == (12, 52):
				reff.vdc.realprec = 3 # 64 bit floating point
			else:
				raise SketchLoadError("This implementation can't work with %d,%d bit floatingpoints" % prec)
		if reff.vdc.type == 1:
			reff.vdc.size = reff.vdc.realsize
			reff.vdc.prec = reff.vdc.realprec


#   0x30a0:
	def cliprect(self, size):
		reff.clip.rect = (self.Pnt(), self.Pnt())

	def Path(self, size):
		path = CreatePath()
		for i in range(size / (2 * reff.vdc.size)):
			path.AppendLine(self.trafo(self.Pnt()))
		return path

	def setlinestyle(self):
		style = basestyle.Duplicate()
		style.line_pattern = SolidPattern(apply(CreateRGBColor , reff.line.color))
		style.line_width = reff.line.width
		if reff.line.widthmode == 0:
			style.line_width = style.line_width * self.Scale
		style.line_dashes = reff.line.dashtable[reff.line.type - 1]
		self.prop_stack.AddStyle(style)

			
#   0x4020:
	def LINE(self, size):
		path = self.Path(size)
		self.setlinestyle()
		self.bezier((path,))
			
#   0x4040:
	def DISJTLINE(self, size):
		path = ()
		for i in range(size / (4 * reff.vdc.size)):
			subpath = CreatePath()
			P = self.Pnt()
			subpath.AppendLine(self.trafo(P))
			P = self.Pnt()
			subpath.AppendLine(self.trafo(P))
			path = path + (subpath,)
		self.setlinestyle()
		self.bezier(path)

#   0x4080:
	def TEXT(self, size):
		P = self.Pnt()
		F = self.Enum()
		S = self.getstr()
		T = Translation(self.trafo(P))
		Py = Point(reff.text.orientation[0]).normalized()
		Px = Point(reff.text.orientation[1]).normalized()
		B = transform_base(Point(0.0, 0.0) , reff.text.expansion * Px , Py)
		self.style = basestyle.Duplicate()
		self.style.font = GetFont(fntlst[self.fntmap[reff.text.fontindex]])
		self.style.font_size = reff.text.height * self.Scale
		self.style.fill_pattern = SolidPattern(apply(CreateRGBColor , reff.text.color))
		O = text.SimpleText(text = S, trafo = T(B),
							halign = text.ALIGN_LEFT, valign = text.ALIGN_BASE,
							properties = self.get_prop_stack())
		self.append_object(O)

	def setfillstyle(self):
		style = basestyle.Duplicate()
		if reff.fill.type == 1:
			style.fill_pattern = SolidPattern(apply(CreateRGBColor , reff.fill.color))
		elif reff.fill.type == 3:
			style.fill_pattern = HatchingPattern(apply(CreateRGBColor , reff.fill.color),
													StandardColors.white,
													Point(2.0, 1.0), 5 , 1)
		if reff.edge.visible:
			style.line_pattern = SolidPattern(apply(CreateRGBColor , reff.edge.color))
			style.line_width = reff.edge.width
			if reff.edge.widthmode == 0:
				style.line_width = style.line_width * self.Scale
			style.line_dashes = reff.edge.dashtable[reff.edge.type - 1]
		self.prop_stack.AddStyle(style)

#   0x40e0:
	def POLYGON(self, size):
		path = self.Path(size)
		if path.Node(-1) != path.Node(0):
			path.AppendLine(path.Node(0))
		path.load_close()
		self.setfillstyle()
		self.bezier((path,))

#   0x4100:
	def POLYGONSET(self, size):
		path = ()
		subpath = CreatePath()
		for i in range(size / (2 * reff.vdc.size + 2)):
			P = self.Pnt()
			F = self.Enum()
			subpath.AppendLine(self.trafo(P))
			if F in (2,3):
				if subpath.Node(-1) != subpath.Node(0):
					subpath.AppendLine(subpath.Node(0))
				subpath.load_close()
				path = path + (subpath,)
				subpath = CreatePath()
		if subpath.len != 0:
			if subpath.Node(-1) != subpath.Node(0):
				subpath.AppendLine(subpath.Node(0))
			subpath.load_close()
			path = path + (subpath,)
		self.setfillstyle()
		self.bezier(path)

	def bugmark(self, P):
		P = P - Point(1,1)
		style = basestyle.Duplicate()
		style.fill_pattern = SolidPattern(StandardColors.black)
		style.line_pattern = SolidPattern(StandardColors.black)
		self.prop_stack.AddStyle(style)
		self.rectangle(2, 0, 0, 2, P.x, P.y)

#   0x4160:
	def RECT(self,size):
		ll = self.trafo(self.Pnt())
		ur = self.trafo(self.Pnt())
		lr = Point(ur.x , ll.y)
		ul = Point(ll.x , ur.y)
		T = transform_base(ll , lr , ul)
		self.setfillstyle()
		apply(self.rectangle , T.coeff())

#   0x4180: 
	def CIRCLE(self,size):
		centre = self.trafo(self.Pnt())
		radius = self.VDC() * self.Scale
		self.setfillstyle()
		self.ellipse(radius, 0, 0, radius, centre.x, centre.y)

#   0x41a0:
	def ARC3PT(self, size):
		Po = self.trafo(self.Pnt())
		Pm = self.trafo(self.Pnt())
		Pe = self.trafo(self.Pnt())
		Pc = Cnt3Pnt(Po, Pm, Pe)
		radius = abs(Po - Pc)
		if Angle2(Po - Pc , Pm - Pc) < Angle2(Po - Pc, Pe - Pc):
			Ao = Angle(Po - Pc)
			Ae = Angle(Pe - Pc)
		else:
			Ao = Angle(Pe - Pc)
			Ae = Angle(Po - Pc)
		self.setlinestyle()
		self.ellipse(radius, 0, 0, radius, Pc.x, Pc.y, Ao, Ae, 0)

#   0x41c0:
	def ARC3PTCLOSE(self, size):
		Po = self.trafo(self.Pnt())
		Pm = self.trafo(self.Pnt())
		Pe = self.trafo(self.Pnt())
		closetype = self.Enum()
		Pc = Cnt3Pnt(Po, Pm, Pe)
		radius = abs(Po - Pc)
		if Angle2(Po - Pc , Pm - Pc) < Angle2(Po - Pc, Pe - Pc):
			Ao = Angle(Po - Pc)
			Ae = Angle(Pe - Pc)
		else:
			Ao = Angle(Pe - Pc)
			Ae = Angle(Po - Pc)
		self.setfillstyle()
		self.ellipse(radius, 0, 0, radius, Pc.x, Pc.y, Ao, Ae, 2 - closetype)

#   0x41e0: 
	def ARCCTR(self,size):
		centre = self.trafo(self.Pnt())
		Vo = self.trafo.DTransform(self.Pnt())
		Ve = self.trafo.DTransform(self.Pnt())
		radius = self.VDC() * self.Scale
		Ao = Angle(Vo)
		Ae = Angle(Ve)
		self.setlinestyle()
		self.ellipse(radius, 0, 0, radius, centre.x, centre.y, Ao, Ae, 0)

#   0x4200: 'ARCCTRCLOSE',
	def ARCCTRCLOSE(self,size):
		centre = self.trafo(self.Pnt())
		Vo = self.trafo.DTransform(self.Pnt())
		Ve = self.trafo.DTransform(self.Pnt())
		radius = self.VDC() * self.Scale
		closetype = self.Enum()
		Ao = Angle(Vo)
		Ae = Angle(Ve)
		self.setfillstyle()
		self.ellipse(radius, 0, 0, radius, centre.x, centre.y, Ao, Ae, 2 - closetype)

#   0x4220:
	def ELLIPSE(self,size):
		centre = self.trafo(self.Pnt())
		cdp1 = self.trafo(self.Pnt())
		cdp2 = self.trafo(self.Pnt())
		T = transform_base(centre , cdp1 , cdp2)
		self.setfillstyle()
		apply(self.ellipse , T.coeff())
	
#   0x4240: 
	def ELLIPARC(self, size):
		centre = self.trafo(self.Pnt())
		cdp1 = self.trafo(self.Pnt())
		cdp2 = self.trafo(self.Pnt())
		Vo = self.trafo.DTransform(self.Pnt())
		Ve = self.trafo.DTransform(self.Pnt())
		T = transform_base(centre , cdp1 , cdp2)
		Vo = T.inverse().DTransform(Vo)
		Ve = T.inverse().DTransform(Ve)
		Ao = Angle(Vo)
		Ae = Angle(Ve)
		self.setlinestyle()
		apply(self.ellipse , T.coeff() + (Ao, Ae, 0))

#   0x4260: 
	def ELLIPARCCLOSE(self, size):
		centre = self.trafo(self.Pnt())
		cdp1 = self.trafo(self.Pnt())
		cdp2 = self.trafo(self.Pnt())
		Vo = self.trafo.DTransform(self.Pnt())
		Ve = self.trafo.DTransform(self.Pnt())
		closetype = self.Enum()
		T = transform_base(centre , cdp1 , cdp2)
		Vo = T.inverse().DTransform(Vo)
		Ve = T.inverse().DTransform(Ve)
		Ao = Angle(Vo)
		Ae = Angle(Ve)
		self.setfillstyle()
		apply(self.ellipse , T.coeff() + (Ao, Ae, 2 - closetype))

#   0x5040
	def linetype(self, size):
		reff.line.type = self.Inx()

#   0x5060:
	def linewidth(self, size):
		if reff.line.widthmode == 0:
			reff.line.width = self.VDC() 
		else:
			reff.line.width = self.Real()

#   0x5080:
	def linecolr(self, size):
		reff.line.color = self.getcol()

#   0x5100:
	def markercolr(self, size):
		reff.marker.color = self.getcol()

#   0x5140: 'textfontindex',
	def textfontindex(self, size):
		reff.text.fontindex = self.Inx()
		self._print(10 , 'font[%d]: => %s\n' , reff.text.fontindex , fntlst[self.fntmap[reff.text.fontindex]])

#   0x5180: 'charexpan',
	def charexpan(self,size):
		reff.text.expansion = self.Real()


#   0x51c0:
	def textcolr(self, size):
		reff.text.color = self.getcol()

#   0x51e0:
	def charheight(self, size):
		reff.text.height = self.VDC()

#   0x5200:
	def charori(self, size):
		reff.text.orientation = (self.Pnt(), self.Pnt())

#   0x52c0:
	def intstyle(self, size):
		reff.fill.type = self.Enum()

#   0x52e0:
	def fillcolr(self, size):
		reff.fill.color = self.getcol()

#   0x5360:
	def edgetype(self, size):
		reff.edge.type = self.Inx()

#   0x5380:
	def edgewidth(self, size):
		if reff.edge.widthmode == 0:
			reff.edge.width = self.VDC()
		else:
			reff.edge.width = self.Real()

#   0x53a0:
	def edgecolr(self, size):
		reff.edge.color = self.getcol()

#   0x53c0:
	def edgevis(self, size):
		reff.edge.visible = self.Enum()

#   0x5440: 'colrtable',
	def colrtable(self, size):
		i = self.unpack(reff.color.inxstruct)[0]
		size = size - struct.calcsize(reff.color.inxstruct)
		while size > struct.calcsize(reff.color.absstruct):
			cgmcol = self.unpack(reff.color.absstruct)
			cgmcol = map(operator.sub , cgmcol , reff.color.offset)
			cgmcol = map(operator.div , cgmcol , reff.color.scale)
			reff.color.table[i] = cgmcol
			size = size - struct.calcsize(reff.color.absstruct)
			i = i + 1

	def interpret(self, sz):
		tell = self.file.tell
		Id = -1
		pos = tell()
		start = pos
		while Id != 0x40 and pos < start + sz:
			head = self.u16()
			Id = head & 0xffe0
			size = head & 0x001f
			hdsz = 2
			if size == 31:
				size = self.u16()
				hdsz = 4
			pdsz = ((size + 1) / 2) * 2
			self._print(20 , '%4x at %5d) %5d(%5d): %4x: %s' , head, pos, size, pdsz, Id, CGM_ID.get(Id, ''))
			if hasattr(self, CGM_ID.get(Id, '')):
				self._print(30 , 'Calling %s' % (CGM_ID.get(Id, '')))
				getattr(self, CGM_ID[Id])(size)
			else:
				if Id:
					self.file.read(pdsz)
					name = CGM_ID.get(Id, '')
					Class = Id >> 12
					Elem = (Id & 0x0fff) >> 5
					self._print(2, '*** unimplemented: %4x; class = %d, element = %2d  %s' 
										, Id , Class , Elem, name)
			pos = pos + hdsz + pdsz
			if tell() < pos:
				self.file.read(pos - tell())
			elif tell() > pos:
				self._print(2, 'read too many bytes')
				self.file.seek(pos - tell(), 1)
			if pos != tell():
				raise SketchLoadError("Lost position in File")


	def Load(self):

		self.file.seek(0,2)
		where = self.file.tell()
		self.file.seek(0,0)
		self.interpret(where)
		self.end_all()
		self.object.load_Completed()
		return self.object

