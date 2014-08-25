# -*- coding: utf-8 -*-

# Copyright (C) 2009 by Barabash Maxim
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
#type=Import
#class_name='StitchLoader'
#rx_magic='^LA:|^#PES|^\x80\x04|^\xE3\x42|^\x14\xFF|^\x80\x02|^\x32[\x02,\x03].\x00'
#tk_file_type=('Embroidery file format - DST, PES, EXP, PCS', ('*.dst', '*.pes', '*.exp', '*.pcs'))
#format_name='DST'
#unload=1
#standard_messages=1
###End

#
#      Import Filter for DST (Tajima) Design format
#      Import Filter for PES (Brother) Embroidery file format
#      Import Filter for EXP (Melco) Embroidery file format
#      Import Filter for PCS (Pfaff home) Design format
#

# Spec file
# http://www.achatina.de/sewing/main/TECHNICL.HTM
# http://www.wotsit.org/download.asp?f=tajima&sc=312047744
# http://www.wotsit.org/download.asp?f=pes&sc=312131292
# http://www.wotsit.org/download.asp?f=melco&sc=313074501


import os
import app

from types import StringType
from string import atoi
from app import _, CreatePath, Style, const, SolidPattern, StandardColors, CreateRGBColor

from app.events.warn import INTERNAL, pdebug, warn_tb
from app.io.load import GenericLoader, SketchLoadError

from struct import unpack


def byte2bin(num):
		result = ""
		for i in xrange(0, 8):
			result = str(num >> i & 1) + result
			return result

def byte(num, i):
		return num >> i & 1

def csscolor(str):
	str = str.strip()
	if str[0] == '#' and len(str) == 7:
		r = atoi(str[1:3], 16) / 255.0
		g = atoi(str[3:5], 16) / 255.0
		b = atoi(str[5:7], 16) / 255.0
		color = CreateRGBColor(r, g, b)
	else:
		color = StandardColors.black
	return color

colors = {
		0:csscolor('#000000'),	1:csscolor('#0E1F7C'),	2:csscolor('#0A55A3'),
		3:csscolor('#308777'),	4:csscolor('#4B6BAF'),	5:csscolor('#ED171F'),
		6:csscolor('#D15C00'),	7:csscolor('#913697'),	8:csscolor('#E49ACB'),
		9:csscolor('#915FAC'),	10:csscolor('#9DD67D'),	11:csscolor('#E8A900'),
		12:csscolor('#FEBA35'),	13:csscolor('#FFFF00'),	14:csscolor('#70BC1F'),
		15:csscolor('#C09400'),	16:csscolor('#A8A8A8'),	17:csscolor('#7B6F00'),
		18:csscolor('#FFFFB3'),	19:csscolor('#4F5556'),	20:csscolor('#000000'),
		21:csscolor('#0B3D91'),	22:csscolor('#770176'),	23:csscolor('#293133'),
		24:csscolor('#2A1301'),	25:csscolor('#F64A8A'),	26:csscolor('#B27624'),
		27:csscolor('#FCBBC4'),	28:csscolor('#FE370F'),	29:csscolor('#F0F0F0'),
		30:csscolor('#6A1C8A'),	31:csscolor('#A8DDC4'),	32:csscolor('#2584BB'),
		33:csscolor('#FEB343'),	34:csscolor('#FFF08D'),	35:csscolor('#D0A660'),
		36:csscolor('#D15400'),	37:csscolor('#66BA49'),	38:csscolor('#134A46'),
		39:csscolor('#878787'),	40:csscolor('#D8CAC6'),	41:csscolor('#435607'),
		42:csscolor('#FEE3C5'),	43:csscolor('#F993BC'),	44:csscolor('#003822'),
		45:csscolor('#B2AFD4'),	46:csscolor('#686AB0'),	47:csscolor('#EFE3B9'),
		48:csscolor('#F73866'),	49:csscolor('#B54C64'),	50:csscolor('#132B1A'),
		51:csscolor('#C70155'),	52:csscolor('#FE9E32'),	53:csscolor('#A8DEEB'),
		54:csscolor('#00671A'),	55:csscolor('#4E2990'),	56:csscolor('#2F7E20'),
		57:csscolor('#FDD9DE'),	58:csscolor('#FFD911'),	59:csscolor('#905BA6'),
		60:csscolor('#F0F970'),	61:csscolor('#E3F35B'),	62:csscolor('#FFC864'),
		63:csscolor('#FFC896'),	64:csscolor('#FFC8C8'),	65:csscolor('#000000'),
		}

UNKNOWN = 0
NORMAL = 1
CHANGECOLOR = 2
JUMP = 3
END = 4

#####################################################################
# DST (Tajima) Design format
#####################################################################

class Palette:
	def __init__(self, file=None):
		self.index = 1
		self.items = {}
		self.order = []
		self.load_palette(file)
	
	def	load_palette(self, file = None, count = 255):
		filename = None
		if type(file) == StringType:
			if os.path.exists(file + '.edr'):
				filename = file + '.edr'
			elif os.path.exists(file + '.EDR'):
				filename = file + '.EDR'
			else:
				self.items = {}
				self.items.update(colors)
				self.from_file = False
				return
		if filename is not None:
			file = open(filename, 'rb')
		index = 1
		while index <= count:
			data = file.read(4)
			if len(data) < 4:
				break
			r, g, b, nn = unpack('BBBB', data)
			self.items[index] = CreateRGBColor(r/ 255.0, g/ 255.0, b/ 255.0)
			index += 1
		self.from_file = True
		if filename is not None:
			file.close()
	
	def next_color(self, index=None):
		if index is None:
			index = self.index + 1
		self.index = index

		if not self.from_file and self.order:
			index = self.order[self.index - 1]

		if index in self.items:
			color = self.items[index]
		else:
			color = StandardColors.black
		return SolidPattern(color)


#####################################################################
#
#####################################################################
class DSTLoader(GenericLoader):
	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.file=file
		self.basename, self.ext = os.path.splitext(filename)
	
	def initialize(self):
		self.draw = 0
		self.scale = .283464566929
		self.cur_x = 0.0
		self.cur_y = 0.0
		self.palette = Palette(self.basename)
		self.path = CreatePath()
		self.cur_style = Style()
		self.cur_style.line_width = 0.6
		self.cur_style.line_join = const.JoinRound
		self.cur_style.line_cap = const.CapRound
		self.cur_style.line_pattern = self.palette.next_color(1)
	
	def readInt32(self, file):
		try:
			data = unpack('<I', file.read(4))[0]
		except:
			data = None
		return data
	
	def readInt8(self, file):
		try:
			data = int(unpack('B', file.read(1))[0])
		except:
			data = None
		return data
	
	def get_position(self, x = None, y = None):
		if x is  None:
			x = self.cur_x
		else:
			x = float(x) * self.scale + self.cur_x
		if y is None:
			y = self.cur_y
		else:
			y = float(y) * self.scale + self.cur_y
		return x, y
	
	def bezier(self):
		if self.path.len > 1:
			self.prop_stack.AddStyle(self.cur_style.Duplicate())
			GenericLoader.bezier(self, paths = (self.path,))
		self.path = CreatePath()
	
	def jump(self, x, y):
		x, y = self.get_position(x, y)
		self.cur_x = x
		self.cur_y = y
	
	def needle_move(self, x, y):
		if self.draw == 1:
			self.path.AppendLine(x, y)
		else:
			self.bezier()
			self.path.AppendLine(x, y)
		self.cur_x = x
		self.cur_y = y
	
	def needle_down(self, x = None, y = None):
		self.draw = 1
		x, y = self.get_position(x, y)
		self.needle_move(x, y)
	
	def needle_up(self, x = None, y = None):
		if self.draw == 1:
			self.bezier()
		self.draw = 0
		x, y = self.get_position(x, y)
		self.needle_move(x, y)
	
	def decode_x(self, d1, d2, d3):
		x =   1 * byte(d1,7)  -1 * byte(d1,6)  +9 * byte(d1,5)  -9 * byte(d1,4)
		x +=  3 * byte(d2,7)  -3 * byte(d2,6) +27 * byte(d2,5) -27 * byte(d2,4)
		x += 81 * byte(d3,5) -81 * byte(d3,4)
		return x
	
	def decode_y(self, d1, d2, d3):
		y =   1 * byte(d1,0)  -1 * byte(d1,1)  +9 * byte(d1,2)  -9 * byte(d1,3)
		y +=  3 * byte(d2,0)  -3 * byte(d2,1) +27 * byte(d2,2) -27 * byte(d2,3) 
		y += 81 * byte(d3,2) -81 * byte(d3,3)
		return y
	
	def decode_flag(self, d3):
		if d3 == 243:
			return END
		if d3 & 195 == 3:
			return NORMAL
		elif d3 & 195 == 131:
			return JUMP
		elif d3 & 195 == 195:
			return CHANGECOLOR
		else:
			return UNKNOWN
	
	def readheader(self, file):
		file.seek(0)
		header = file.read(512).split('\r')
		dict = {}
		for i in header:
			if i[2] == ':':
				dict[i[0:2]] = i[3:].replace(' ', '')
		x = int(dict['-X'])
		y = int(dict['-Y'])
		self.jump(x , y )
	
	def Load(self):
		file = self.file
		fileinfo=os.stat(self.filename)
		totalsize=fileinfo[6]
		self.initialize()
		self.readheader(file)
		self.document()
		self.layer(name=_("DST_objects"))
		parsed=0
		parsed_interval=totalsize/99+1
		flag = UNKNOWN
		while 1:
			
			interval_count=file.tell()/parsed_interval
			if interval_count > parsed:
				parsed+=10 # 10% progress
				app.updateInfo(inf2='%u'%parsed+'% of file is parsed...',inf3=parsed)
			
			data = file.read(3)
			if len(data) < 3 or flag == 'END':
				self.needle_up()
				## END INTERPRETATION
				app.updateInfo(inf2=_('Parsing is finished'),inf3=100)
				break
				
			d1, d2, d3 = unpack('BBB', data)
			x = self.decode_x(d1, d2, d3)
			y = self.decode_y(d1, d2, d3)
			#XXX swap coordinate 
			x, y = y, x
			
			flag = self.decode_flag(d3)
			if flag == NORMAL:
				self.needle_down(x, y)
			elif flag == CHANGECOLOR:
				self.needle_up(x, y)
				self.cur_style.line_pattern = self.palette.next_color()
			elif flag == JUMP:
				#self.bezier() # cut the rope
				self.jump(x, y)

		self.end_all()
		self.object.load_Completed()
		return self.object

#####################################################################
#
#####################################################################
class PESLoader(DSTLoader):
	def __init__(self, file, filename, match):
		DSTLoader.__init__(self, file, filename, match)
	
	def readheader(self, file):
		file.seek(8)
		self.pecstart = self.readInt32(file)
		#No. of colors in file
		file.seek(self.pecstart + 48)
		numColors = self.readInt8(file) + 1
		self.palette.order = []
		for i in xrange(0, numColors):
			self.palette.order.append(self.readInt8(file))

		
	def Load(self):
		file = self.file
		fileinfo=os.stat(self.filename)
		totalsize=fileinfo[6]
		self.initialize()
		self.readheader(file)
		self.cur_style.line_pattern = self.palette.next_color(1)
		self.document()
		self.layer(name=_("PES_objects"))
		
		#Beginning of stitch data
		file.seek(self.pecstart + 532)
		parsed = 0
		parsed_interval=totalsize/99+1
		while 1:
			
			interval_count=file.tell()/parsed_interval
			if interval_count > parsed:
				parsed+=10 # 10% progress
				app.updateInfo(inf2='%u'%parsed+'% of file is parsed...',inf3=parsed)
			
			val1 = self.readInt8(file)
			val2 = self.readInt8(file)
			
			if val1 is None or val2 is None:
				break
			elif val1 == 255 and val2 == 0:
				#end of stitches
				flag = END
				app.updateInfo(inf2=_('Parsing is finished'),inf3=100)
			elif val1 == 254 and val2 == 176:
				# color switch, start a new block
				flag = CHANGECOLOR
				nn = self.readInt8(file)
			else:
				if val1 & 128 == 128: # 0x80
					#this is a jump stitch
					flag = JUMP
					x = ((val1 & 15) * 256) + val2
					if x & 2048 == 2048: # 0x0800
						x= x - 4096
					#read next byte for Y value
					val2 = self.readInt8(file)
				else:
					#normal stitch
					flag = NORMAL
					x = val1
					if x > 63:
						x = x - 128
				
				if val2 & 128 == 128: # 0x80
					#this is a jump stitch
					flag = JUMP
					val3 = self.readInt8(file)
					y = ((val2 & 15) * 256) + val3
					if y & 2048 == 2048: # 0x0800
						y = y - 4096
				else:
					#normal stitch
					flag = NORMAL
					y = val2
					if y > 63:
						y = y - 128
				#XXX flip vertical coordinate 
				x, y = x, -y
				
			if flag == NORMAL:
				self.needle_down(x, y)
			elif flag == CHANGECOLOR:
				self.needle_up()
				#self.bezier()
				self.cur_style.line_pattern = self.palette.next_color()
			elif flag == JUMP:
				#self.bezier() # cut the rope
				#self.jump(x, y)
				self.needle_down(x, y)
			elif flag == END:
				self.needle_up()
				break
		self.end_all()
		self.object.load_Completed()
		return self.object

#####################################################################
#
#####################################################################
class EXPLoader(DSTLoader):
	def __init__(self, file, filename, match):
		DSTLoader.__init__(self, file, filename, match)
	

	def Load(self):
		file = self.file
		fileinfo=os.stat(self.filename)
		totalsize=fileinfo[6]
		self.initialize()
		self.document()
		self.layer(name=_("EXP_objects"))
		
		#Beginning of stitch data
		file.seek(0)
		parsed = 0
		parsed_interval=totalsize/99+1
		flag = UNKNOWN
		while 1:
			
			interval_count=file.tell()/parsed_interval
			if interval_count > parsed:
				parsed+=10 # 10% progress
				app.updateInfo(inf2='%u'%parsed+'% of file is parsed...',inf3=parsed)
			
			val1 = self.readInt8(file)
			val2 = self.readInt8(file)
			#print val1, val2
			if val1 is None or val2 is None:
				flag = END
			elif val1 == 0x80 and val2 == 0x01:
				flag = CHANGECOLOR
				val1 = self.readInt8(file)
				val2 = self.readInt8(file)
			elif val1 == 0x80 and val2 > 0x01:
				flag = JUMP
				val1 = self.readInt8(file)
				val2 = self.readInt8(file)
			else:
				flag = NORMAL
			
			x, y = val1, val2
			if val1 > 0x7F:
				x = -1 * (0x100 - val1)
			if val2 > 0x7F:
				y = -1 * (0x100 - val2)
				
			if flag == NORMAL:
				self.needle_down(x, y)
			elif flag == CHANGECOLOR:
				self.needle_up()
				self.needle_down(x, y)
				#self.bezier()
				self.cur_style.line_pattern = self.palette.next_color()
			elif flag == JUMP:
				#self.bezier() # cut the rope
				self.jump(x, y)
				#self.needle_down(x, y)
			elif flag == END:
				self.needle_up()
				break
		self.end_all()
		self.object.load_Completed()
		return self.object
#####################################################################
#
#####################################################################
class PCSLoader(DSTLoader):
	def __init__(self, file, filename, match):
		DSTLoader.__init__(self, file, filename, match)
	
	def readheader(self, file):
		file.seek(0)
		pcs = unpack('<H', file.read(2))[0]
		#No. of colors in file
		numColors = unpack('<H', file.read(2))[0]
		self.palette.load_palette(file, numColors)
		#Nr. of stitches in file, LSB
		self.LSB = unpack('<H', file.read(2))[0]

	def Load(self):
		file = self.file
		fileinfo=os.stat(self.filename)
		totalsize=fileinfo[6]
		self.initialize()
		self.readheader(file)
		self.scale = .472440944882
		self.document()
		self.layer(name=_("PCS_objects"))
		
		parsed = 0
		parsed_interval=totalsize/99+1
		for i in xrange(self.LSB):
			interval_count=file.tell()/parsed_interval
			if interval_count > parsed:
				parsed+=10 # 10% progress
				app.updateInfo(inf2='%u'%parsed+'% of file is parsed...',inf3=parsed)
				
			data = file.read(9)
			
			if len(data) < 9:
				break
			val1, val2, val4, val5, val6, val7, val9 = unpack('<BHBBHBB', data)
			if val9 == 0x03:
				self.needle_up()
				self.cur_style.line_pattern = self.palette.next_color(val1+1)
			else:
				x = val2
				y = val6
				self.cur_x = self.cur_y = 0
				self.needle_down(x, y)

		self.needle_up()
		self.end_all()
		self.object.load_Completed()
		return self.object
#####################################################################
#
#####################################################################
class StitchLoader(GenericLoader):
	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.basename, self.ext = os.path.splitext(filename)
	
	def Load(self):
		doc = None
		if self.ext.upper() == '.DST':
			loader = DSTLoader(self.file, self.filename, self.match)
			doc = loader.Load()
		elif self.ext.upper() == '.PES':
			loader = PESLoader(self.file, self.filename, self.match)
			doc = loader.Load()
		elif self.ext.upper() == '.EXP':
			loader = EXPLoader(self.file, self.filename, self.match)
			doc = loader.Load()
		elif self.ext.upper() == '.PCS':
			loader = PCSLoader(self.file, self.filename, self.match)
			doc = loader.Load()
		else:
			raise SketchLoadError(_("unrecognised file type"))
		return doc
