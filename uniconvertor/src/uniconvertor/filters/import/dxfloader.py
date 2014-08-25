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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307	USA

###Sketch Config
#type = Import
#class_name='DXFLoader'
#rx_magic = r'^\x30|^\x20\x30|^\x09\x30|^\x20\x20\x30|999'
#tk_file_type=('DXF - acad file', ('.dxf', '.DXF'))
#format_name='DXF'
#unload = 1
#standard_messages = 1
###End

#
#    Import Filter for DXF files
#



import sys, os, string

from types import StringType, TupleType
from app import _, CreatePath, Style

from app.events.warn import INTERNAL, pdebug, warn_tb
from app.io.load import GenericLoader, SketchLoadError
import app

from string import strip, atoi, upper

from math import sqrt, atan, atan2
from math import pi, cos, sin


degrees = pi / 180.0

from app import Document, Layer, CreatePath, ContSmooth, \
		SolidPattern, EmptyPattern, RadialGradient,\
		CreateRGBColor, Point, Polar, \
		StandardColors, GetFont, PathText, SimpleText, const, UnionRects, \
		Scale, Trafo, Translation, Rotation
		
from app import Scale, Trafo, Translation, Rotation

from app.conf.const import ArcArc, ArcChord, ArcPieSlice, \
		ALIGN_BASE, ALIGN_CENTER, ALIGN_TOP, ALIGN_BOTTOM, \
		ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT

##base_style = Style()
##base_style.fill_pattern = EmptyPattern
##base_style.fill_transform = 1
##base_style.line_pattern = SolidPattern(StandardColors.black)
##base_style.line_width = 0.0
##base_style.line_join = const.JoinMiter
##base_style.line_cap = const.CapButt
##base_style.line_dashes = ()
##base_style.line_arrow1 = None
##base_style.line_arrow2 = None
##base_style.font = None
##base_style.font_size = 12.0

def csscolor(str):
	str = str.strip()

	if str[0] == '#':
		if len(str) == 7:
			r = atoi(str[1:3], 16) / 255.0
			g = atoi(str[3:5], 16) / 255.0
			b = atoi(str[5:7], 16) / 255.0
		elif len(str) == 4:
			# According to the CSS rules a single HEX digit is to be
			# treated as a repetition of the digit, so that for a digit
			# d the value is (16 * d + d) / 255.0 which is equal to d / 15.0
			r = atoi(str[1], 16) / 15.0
			g = atoi(str[2], 16) / 15.0
			b = atoi(str[3], 16) / 15.0
		color = CreateRGBColor(r, g, b)
	elif namedcolors.has_key(str):
		color = namedcolors[str]
	else:
		color = StandardColors.black
	return color

colors = {
		0: csscolor('#000000'),
		1: csscolor('#FF0000'),
		2: csscolor('#FFFF00'),
		3: csscolor('#00FF00'),
		4: csscolor('#00FFFF'),
		5: csscolor('#0000FF'),
		6: csscolor('#FF00FF'),
		7: csscolor('#000000'), #7: csscolor('#FFFFFF'),
		8: csscolor('#414141'),
		9: csscolor('#808080'),
		10: csscolor('#FF0000'),
		11: csscolor('#FFAAAA'),
		12: csscolor('#BD0000'),
		13: csscolor('#BD7E7E'),
		14: csscolor('#810000'),
		15: csscolor('#815656'),
		16: csscolor('#680000'),
		17: csscolor('#684545'),
		18: csscolor('#4F0000'),
		19: csscolor('#4F3535'),
		20: csscolor('#FF3F00'),
		21: csscolor('#FFBFAA'),
		22: csscolor('#BD2E00'),
		23: csscolor('#BD8D7E'),
		24: csscolor('#811F00'),
		25: csscolor('#816056'),
		26: csscolor('#681900'),
		27: csscolor('#684E45'),
		28: csscolor('#4F1300'),
		29: csscolor('#4F3B35'),
		30: csscolor('#FF7F00'),
		31: csscolor('#FFD4AA'),
		32: csscolor('#BD5E00'),
		33: csscolor('#BD9D7E'),
		34: csscolor('#814000'),
		35: csscolor('#816B56'),
		36: csscolor('#683400'),
		37: csscolor('#685645'),
		38: csscolor('#4F2700'),
		39: csscolor('#4F4235'),
		40: csscolor('#FFBF00'),
		41: csscolor('#FFEAAA'),
		42: csscolor('#BD8D00'),
		43: csscolor('#BDAD7E'),
		44: csscolor('#816000'),
		45: csscolor('#817656'),
		46: csscolor('#684E00'),
		47: csscolor('#685F45'),
		48: csscolor('#4F3B00'),
		49: csscolor('#4F4935'),
		50: csscolor('#FFFF00'),
		51: csscolor('#FFFFAA'),
		52: csscolor('#BDBD00'),
		53: csscolor('#BDBD7E'),
		54: csscolor('#818100'),
		55: csscolor('#818156'),
		56: csscolor('#686800'),
		57: csscolor('#686845'),
		58: csscolor('#4F4F00'),
		59: csscolor('#4F4F35'),
		60: csscolor('#BFFF00'),
		61: csscolor('#EAFFAA'),
		62: csscolor('#8DBD00'),
		63: csscolor('#ADBD7E'),
		64: csscolor('#608100'),
		65: csscolor('#768156'),
		66: csscolor('#4E6800'),
		67: csscolor('#5F6845'),
		68: csscolor('#3B4F00'),
		69: csscolor('#494F35'),
		70: csscolor('#7FFF00'),
		71: csscolor('#D4FFAA'),
		72: csscolor('#5EBD00'),
		73: csscolor('#9DBD7E'),
		74: csscolor('#408100'),
		75: csscolor('#6B8156'),
		76: csscolor('#346800'),
		77: csscolor('#566845'),
		78: csscolor('#274F00'),
		79: csscolor('#424F35'),
		80: csscolor('#3FFF00'),
		81: csscolor('#BFFFAA'),
		82: csscolor('#2EBD00'),
		83: csscolor('#8DBD7E'),
		84: csscolor('#1F8100'),
		85: csscolor('#608156'),
		86: csscolor('#196800'),
		87: csscolor('#4E6845'),
		88: csscolor('#134F00'),
		89: csscolor('#3B4F35'),
		90: csscolor('#00FF00'),
		91: csscolor('#AAFFAA'),
		92: csscolor('#00BD00'),
		93: csscolor('#7EBD7E'),
		94: csscolor('#008100'),
		95: csscolor('#568156'),
		96: csscolor('#006800'),
		97: csscolor('#456845'),
		98: csscolor('#004F00'),
		99: csscolor('#354F35'),
		100: csscolor('#00FF3F'),
		101: csscolor('#AAFFBF'),
		102: csscolor('#00BD2E'),
		103: csscolor('#7EBD8D'),
		104: csscolor('#00811F'),
		105: csscolor('#568160'),
		106: csscolor('#006819'),
		107: csscolor('#45684E'),
		108: csscolor('#004F13'),
		109: csscolor('#354F3B'),
		110: csscolor('#00FF7F'),
		111: csscolor('#AAFFD4'),
		112: csscolor('#00BD5E'),
		113: csscolor('#7EBD9D'),
		114: csscolor('#008140'),
		115: csscolor('#56816B'),
		116: csscolor('#006834'),
		117: csscolor('#456856'),
		118: csscolor('#004F27'),
		119: csscolor('#354F42'),
		120: csscolor('#00FFBF'),
		121: csscolor('#AAFFEA'),
		122: csscolor('#00BD8D'),
		123: csscolor('#7EBDAD'),
		124: csscolor('#008160'),
		125: csscolor('#568176'),
		126: csscolor('#00684E'),
		127: csscolor('#45685F'),
		128: csscolor('#004F3B'),
		129: csscolor('#354F49'),
		130: csscolor('#00FFFF'),
		131: csscolor('#AAFFFF'),
		132: csscolor('#00BDBD'),
		133: csscolor('#7EBDBD'),
		134: csscolor('#008181'),
		135: csscolor('#568181'),
		136: csscolor('#006868'),
		137: csscolor('#456868'),
		138: csscolor('#004F4F'),
		139: csscolor('#354F4F'),
		140: csscolor('#00BFFF'),
		141: csscolor('#AAEAFF'),
		142: csscolor('#008DBD'),
		143: csscolor('#7EADBD'),
		144: csscolor('#006081'),
		145: csscolor('#567681'),
		146: csscolor('#004E68'),
		147: csscolor('#455F68'),
		148: csscolor('#003B4F'),
		149: csscolor('#35494F'),
		150: csscolor('#007FFF'),
		151: csscolor('#AAD4FF'),
		152: csscolor('#005EBD'),
		153: csscolor('#7E9DBD'),
		154: csscolor('#004081'),
		155: csscolor('#566B81'),
		156: csscolor('#003468'),
		157: csscolor('#455668'),
		158: csscolor('#00274F'),
		159: csscolor('#35424F'),
		160: csscolor('#003FFF'),
		161: csscolor('#AABFFF'),
		162: csscolor('#002EBD'),
		163: csscolor('#7E8DBD'),
		164: csscolor('#001F81'),
		165: csscolor('#566081'),
		166: csscolor('#001968'),
		167: csscolor('#454E68'),
		168: csscolor('#00134F'),
		169: csscolor('#353B4F'),
		170: csscolor('#0000FF'),
		171: csscolor('#AAAAFF'),
		172: csscolor('#0000BD'),
		173: csscolor('#7E7EBD'),
		174: csscolor('#000081'),
		175: csscolor('#565681'),
		176: csscolor('#000068'),
		177: csscolor('#454568'),
		178: csscolor('#00004F'),
		179: csscolor('#35354F'),
		180: csscolor('#3F00FF'),
		181: csscolor('#BFAAFF'),
		182: csscolor('#2E00BD'),
		183: csscolor('#8D7EBD'),
		184: csscolor('#1F0081'),
		185: csscolor('#605681'),
		186: csscolor('#190068'),
		187: csscolor('#4E4568'),
		188: csscolor('#13004F'),
		189: csscolor('#3B354F'),
		190: csscolor('#7F00FF'),
		191: csscolor('#D4AAFF'),
		192: csscolor('#5E00BD'),
		193: csscolor('#9D7EBD'),
		194: csscolor('#400081'),
		195: csscolor('#6B5681'),
		196: csscolor('#340068'),
		197: csscolor('#564568'),
		198: csscolor('#27004F'),
		199: csscolor('#42354F'),
		200: csscolor('#BF00FF'),
		201: csscolor('#EAAAFF'),
		202: csscolor('#8D00BD'),
		203: csscolor('#AD7EBD'),
		204: csscolor('#600081'),
		205: csscolor('#765681'),
		206: csscolor('#4E0068'),
		207: csscolor('#5F4568'),
		208: csscolor('#3B004F'),
		209: csscolor('#49354F'),
		210: csscolor('#FF00FF'),
		211: csscolor('#FFAAFF'),
		212: csscolor('#BD00BD'),
		213: csscolor('#BD7EBD'),
		214: csscolor('#810081'),
		215: csscolor('#815681'),
		216: csscolor('#680068'),
		217: csscolor('#684568'),
		218: csscolor('#4F004F'),
		219: csscolor('#4F354F'),
		220: csscolor('#FF00BF'),
		221: csscolor('#FFAAEA'),
		222: csscolor('#BD008D'),
		223: csscolor('#BD7EAD'),
		224: csscolor('#810060'),
		225: csscolor('#815676'),
		226: csscolor('#68004E'),
		227: csscolor('#68455F'),
		228: csscolor('#4F003B'),
		229: csscolor('#4F3549'),
		230: csscolor('#FF007F'),
		231: csscolor('#FFAAD4'),
		232: csscolor('#BD005E'),
		233: csscolor('#BD7E9D'),
		234: csscolor('#810040'),
		235: csscolor('#81566B'),
		236: csscolor('#680034'),
		237: csscolor('#684556'),
		238: csscolor('#4F0027'),
		239: csscolor('#4F3542'),
		240: csscolor('#FF003F'),
		241: csscolor('#FFAABF'),
		242: csscolor('#BD002E'),
		243: csscolor('#BD7E8D'),
		244: csscolor('#81001F'),
		245: csscolor('#815660'),
		246: csscolor('#680019'),
		247: csscolor('#68454E'),
		248: csscolor('#4F0013'),
		249: csscolor('#4F353B'),
		250: csscolor('#333333'),
		251: csscolor('#505050'),
		252: csscolor('#696969'),
		253: csscolor('#828282'),
		254: csscolor('#BEBEBE'),
		255: csscolor('#FFFFFF')
		}


#	unit to pt
unit = {0:  72, # Unitless 
		1 : 72.0,# Inches
		2 : 72.0 * 12,# Feet
		3 : 72.0 * 63360,# Miles
		4 : 72 / 2.54 / 10,# Millimeters
		5 : 72 / 2.54,# Centimeters
		6 : 100 * 72 / 2.54,# Meters
		7 : 1000 * 100 * 72 / 2.54,# Kilometers
		8 : 1/1000000 * 72,# Microinches
		9 : 1/1000 * 72.0,# Mils
		10 : 72.0 * 36,# Yards
		11 : 0.00000000001 * 100 * 72 / 2.54,# Angstroms
		12 : 0.0000000001 * 100 * 72 / 2.54,# Nanometers
		13 : 0.0000001 * 100 * 72 / 2.54,# Microns
		14 : 10 * 72 / 2.54,# Decimeters
		15 : 10 * 100 * 72 / 2.54,# Decameters
		16 : 100 * 100 * 72 / 2.54,# Hectometers
		17 : 1000000 * 100 * 72 / 2.54,# Gigameters
		18 : 1.49600 * 1000000000000 * 100 * 72 / 2.54,# Astronomical units
		19 : 9.46050 * 10000000000000000 * 100 * 72 / 2.54,#  Light years
		20 : 3.08570 * 100000000000000000 * 100 * 72 / 2.54 # Parsecs
		}
		
def convert(code, value, encoding = 'latin1'):
	"""Convert a string to the correct Python type based on its dxf code.
		code types:
		ints = 60-79, 170-179, 270-289, 370-389, 400-409, 1060-1070
		longs = 90-99, 420-429, 440-459, 1071
		floats = 10-39, 40-59, 110-139, 140-149, 210-239, 460-469, 1010-1059
		hex = 105, 310-379, 390-399
		strings = 0-9, 100, 102, 300-309, 410-419, 430-439, 470-479, 999, 1000-1009
		"""
	if type(code) == StringType:
		code = int(code)
	if 59 < code < 80 or 169 < code < 180 or 269 < code < 290 or 369 < code < 390 or 399 < code < 410 or 1059 < code < 1071:
		value = int(float(value))
	elif 89 < code < 100 or 419 < code < 430 or 439 < code < 460 or code == 1071:
		value = long(float(value))
	elif 9 < code < 60 or 109 < code < 150 or 209 < code < 240 or 459 < code < 470 or 1009 < code < 1060:
		value = float(value)
	elif code == 105 or 309 < code < 380 or 389 < code < 400:
		value = int(value, 16) # should be left as string?
	elif 1 < code < 10:
		value = unicode_decoder(value, encoding).encode('utf-8')
	else:
		pass
	
	return value

def unicode_decoder(text, encoding):
	try:
		result = text.decode('utf-8')
	except UnicodeDecodeError:
		# print 'UnicodeDecodeError. Use',  self.DWGCODEPAGE
		result = text.decode(encoding)
	return result

class DXFLoader(GenericLoader):

	functions={	"POP_TRAFO": 'pop_trafo',
				"TABLE": 'load_TABLE',
				"BLOCK": 'load_BLOCK',
				"LINE": 'load_line',
				"LWPOLYLINE": 'load_lwpolyline',
				"POLYLINE": 'load_polyline',
				"SEQEND": 'load_seqend',
				"VERTEX": 'load_vertex',
				"CIRCLE": 'load_circle',
				"ARC": 'load_arc',
				"ELLIPSE": 'load_ellips',
				"POINT": 'load_point',
				"SOLID": 'load_solid',
				"INSERT": 'load_insert',
				"TEXT": 'load_text',
				#"MTEXT": 'load_text',
				"3DFACE": 'load_3dface',
				"SPLINE": 'load_spline',
				"VIEWPORT": 'load_bypass',
				
					}

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		
		self.file = file
		
		self.DWGCODEPAGE = 'latin1'
		self.unit_to_pt = 2.83464566929
		self.dynamic_style_dict = {}
		self.style_dict = {}
		self.ltype_dict = {'CONTINUOUS': { '2': 'CONTINUOUS', # Linetype name
											'3': 'Solid line', # Descriptive text for linetype
											'49': [], # Dash, dot or space length 
													  #(one entry per element)
										  }
						  }
		self.layer_dict = {'0': { '2': '0', # Layer name
								  '6': 'CONTINUOUS', #Linetype name
								  '62': 0, # Color number
								  '370': None, #Line weight
								  }
							}
		self.block_dict = {}
		self.stack = []
		self.stack_trafo = []
		self.default_layer = '0'
		self.default_style = 'STANDARD'
		self.default_block = None
		self.default_line_width = 30
		self.EXTMIN = (1e+20, 1e+20)
		self.EXTMAX = (-1e+20, -1e+20)
		self.PEXTMIN = (1e+20, 1e+20)
		self.PEXTMAX = (-1e+20, -1e+20)
		
		self.general_param = {
				'8': self.default_layer, # Layer name
				'6': 'BYLAYER', # Linetype name 
				'62': 256, # Color number 
				'48': 1.0, # Linetype scale 
				#'60': 0, # Object visibility. If 1 Invisible
				}
		
		self.curstyle = Style()
		self.update_trafo()


	def update_trafo(self, scale = 1):
		EXT_hight = self.EXTMAX[0] - self.EXTMIN[0]
		EXT_width = self.EXTMAX[1] - self.EXTMIN[1]
		PEXT_hight = self.PEXTMAX[0] - self.PEXTMIN[0]
		PEXT_width = self.PEXTMAX[1] - self.PEXTMIN[1]
		
		if EXT_hight > 0:
			scale = 840 / max(EXT_hight, EXT_width)
			self.unit_to_pt = scale
			x = self.EXTMIN[0] * scale
			y = self.EXTMIN[1] * scale
		elif PEXT_hight > 0:
			scale = 840 / max(PEXT_hight, PEXT_width)
			self.unit_to_pt = scale
			x = self.PEXTMIN[0] * scale
			y = self.PEXTMIN[1] * scale
		else:
			x = 0
			y = 0
		self.trafo = Trafo(scale, 0, 0, scale, -x, -y)

	def push_trafo(self, trafo = None):
		# save trafo in stack_trafo
		if trafo is None:
			trafo = self.trafo
		self.stack_trafo.append(trafo)

	def pop_trafo(self):
		self.trafo = self.stack_trafo.pop()

	def get_pattern(self, color_index):
		# 0 = Color BYBLOCK
		if color_index == 0:
			block_name = self.default_block
			if block_name is None:
				layer_name = '0'
			else:
				layer_name = self.block_dict[block_name]['8']
			color_index = self.layer_dict[layer_name]['62']
		# 256 = Color BYLAYER
		if  color_index == 256 or color_index is None:
			layer_name = self.default_layer
			color_index = self.layer_dict[layer_name]['62']
		## FIXMY 257 = Color BYENTITY
		
		if color_index < 0:
			pattern = EmptyPattern
		else:
			pattern = SolidPattern(colors[color_index])
		
		return pattern


	def get_line_width(self, layer_name = None):
		if layer_name is None:
			layer_name = self.default_layer
		layer = self.layer_dict[layer_name]
		if '370' in layer:
			width = layer['370']
		if width == -3 or width is None:
			width = self.default_line_width
		
		width = width * 72.0 / 2.54 /1000 # th 100 mm to pt
		if width <= 0.0: # XXX
			width = 0.1
		return width 


	def get_line_type(self, linetype_name = None, scale = 1.0, width = 1.0, layer_name = None):
		#if linetype_name == 'BYBLOCK':
			#block_name = self.default_block
			#layer_name = self.block_dict[block_name]['8']

		if layer_name is None:
			layer_name = self.default_layer

		if linetype_name is None or linetype_name == 'BYLAYER' or linetype_name == 'BYBLOCK': 
			linetype_name = self.layer_dict[layer_name]['6']
		
		linetype = self.ltype_dict[upper(linetype_name)]['49']
		
		lscale = scale * self.unit_to_pt / width 
		dashes = map(lambda i : abs(linetype[i]) * lscale, xrange(len(linetype)))
		
		return tuple(dashes)


	def get_line_style(self, **kw):
		if kw['8'] in self.layer_dict:
			self.default_layer = layer_name = kw['8']
		else:
			layer_name = self.default_layer

		linetype_name = upper(kw['6'])
		scale = kw['48']
		color_index = kw['62']
		
		
		style = Style()
		style.line_width = self.get_line_width()
		style.line_join = const.JoinRound
		style.line_cap = const.CapRound
		style.line_dashes = self.get_line_type(linetype_name = linetype_name, scale = scale, width = style.line_width)
		style.line_pattern = self.get_pattern(color_index)

		return style

	################
	# HEADER Section
	#
	def load_HEADER(self):
		return_code = False
		header_dict = {}
		variable = None
		params = {}
		line1, line2 = self.read_record()
		while line1 or line2:
			if variable and (line1 == '9' or line1 == '0'):
				header_dict[variable] = params
			else:
				params[line1] = line2
			
			if line1 == '0' and line2 == 'ENDSEC':
				return_code = True
				break
			elif line1 == '9':
				params = {}
				variable = line2
			line1, line2 = self.read_record()
		return return_code, header_dict


	def process_header(self, header):
		
		if '$DWGCODEPAGE' in header:
			self.DWGCODEPAGE = 'cp'+ upper(header['$DWGCODEPAGE']['3']).replace('ANSI_', '').replace('DOS','')
		
		if '$INSUNITS' in header:
			INSUNITS = convert('70', header['$INSUNITS']['70'])
			if INSUNITS in unit:
				self.unit_to_pt = unit[INSUNITS]
				
		if '$EXTMIN' in header:
				param10 = convert('10', header['$EXTMIN']['10'])
				param20 = convert('20', header['$EXTMIN']['20'])
				self.EXTMIN = (param10, param20)
				
		if '$EXTMAX' in header:
				param10 = convert('10', header['$EXTMAX']['10'])
				param20 = convert('20', header['$EXTMAX']['20'])
				self.EXTMAX = (param10, param20)
				
		if '$PEXTMIN' in header:
				param10 = convert('10', header['$PEXTMIN']['10'])
				param20 = convert('20', header['$PEXTMIN']['20'])
				self.PEXTMIN = (param10, param20)

		if '$PEXTMAX' in header:
				param10 = convert('10', header['$PEXTMAX']['10'])
				param20 = convert('20', header['$PEXTMAX']['20'])
				self.PEXTMAX = (param10, param20)
		
		self.update_trafo()
		
		if '$CLAYER' in header:
				self.default_layer = convert('8', header['$CLAYER']['8'], self.DWGCODEPAGE)

	
	################
	# TABLES Section
	#

	def load_TABLE(self):
		param={	'2': '', # Table name
				'70': 0 # Maximum number of entries in table
				}
		param = self.read_param(param)
		table_name = param['2']
		table_number = param['70']
		print '****', table_name, table_number
		
		line1, line2 = self.read_record()
		while line1 or line2:
			if line1 == '0' and line2 == 'ENDTAB':
				break
			if table_name == 'LTYPE':
				self.load_LTYPE()
			elif table_name == 'LAYER':
				self.load_LAYER()
			elif table_name == 'STYLE':
				self.load_STYLE()
			line1, line2 = self.read_record()


	def load_LTYPE(self):
		param={ '2': '', # Linetype name
				'3': '', # Descriptive text for linetype
				#'73': 0, # The number of linetype elements
				#'40': 0, # Total pattern length
				'49': [], # Dash, dot or space length (one entry per element)
				}
		param = self.read_param(param, [0])
		
		name = upper(param['2'])
		if name:
			self.ltype_dict[name] = param
			dashes = []
			for i in xrange(len(param['49'])):
				dashes.append(abs(param['49'][i]) * self.unit_to_pt)
			
			name3 = param['3']
			#print name3, dashes
			if name3 and dashes:
				style = Style()
				style.line_dashes = tuple(dashes)
				style = style.AsDynamicStyle()
				style.SetName(name + name3)
				self.dynamic_style_dict[name] = style


	def load_LAYER(self):
		param={ '2': None, # Layer name
				'6': None, #Linetype name
				'62': 0, # Color number
				'370': None, #Line weight
				}
		param = self.read_param(param, [0])

		layer_name = param['2']
		if layer_name:
			self.layer_dict[layer_name]=param
			self.layer(name = layer_name)


	def load_STYLE(self):
		param={ '2': None, # Style name
				'70': 0, # Flag
				'40': 0.0, # Fixed text height; 0 if not fixed
				'41': 0.0, # Width factor
				'42': 0.0, # Last height used
				'50': 0.0, # Oblique angle
				'71': 0, # Text generation flags
				'3': None, # Primary font file name
				'4': None, # Bigfont file name
				'1000': None,
				}
		param = self.read_param(param, [0])

		style_name = upper(param['2'])
		self.style_dict[style_name] = param


	################
	# BLOCKS Section
	#
	
	def load_BLOCK(self):
		param={	'2': '', # Block name
				'10': 0.0, # X Base point
				'20': 0.0, # Y Base point
				#'30': 0.0, # Z Base point 
				'8': self.default_layer, # Layer name
				'data': [], # block data
				}
		param = self.read_param(param)
		block_name = param['2']
		print '****', block_name
		
		line1, line2 = self.read_record()
		while line1 or line2:
			if line1 == '0' and line2 == 'ENDBLK':
				param = self.read_param(param)
				break
			param['data'].append(line1)
			param['data'].append(line2)
			
			line1, line2 = self.read_record()
		
		param['data'].reverse()
		self.block_dict[block_name] = param
#		print self.block_dict[block_name]


	################
	#  ENTITIES Section
	#
	
	def load_line(self):
		param={	'10': None, # X coordinat
				'20': None, # y coordinat
				#'30': None, # Z coordinat
				
				'11': None, # X coordinat endpoint
				'21': None, # y coordinat endpoint
				#'31': None, # z coordinat endpoint
				}
		param.update(self.general_param)
		param = self.read_param(param)
		self.path = CreatePath()
		self.path.AppendLine(self.trafo(param['10'], param['20']))
		self.path.AppendLine(self.trafo(param['11'], param['21']))
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		self.bezier(self.path,)


	def load_lwpolyline(self):
		param={ '90': 0, # Number of vertices
				'70': 0, # bit codes for Polyline entity
				'40': None, # Starting width
				'43': 0,
				'370': None, #Line weight
				}
		param.update(self.general_param)
		param = self.read_param(param,[10,20,42])
		
		if param['40'] is not None:
			line_width = param['40'] * self.unit_to_pt
		else:
			line_width = param['43'] * self.unit_to_pt
			
		if param['370'] is not None:
			line_width = param['370'] * self.unit_to_pt * 72.0 / 2.54 /1000
		
		self.curstyle = self.get_line_style(**param)
		
		# if Group 70 Flag bit value set 1 This is a closed Polyline
		path_flag = param['70']
		vertex_path = []
		for i in xrange(param['90']):
			vertex={ '10': None, # X coordinat
					'20': None, # Y coordinat
					'42': 0.0  # Bulge 
					}
			# 10
			line1, line2 = self.read_record()
			vertex[line1] = convert(line1, line2, self.DWGCODEPAGE)
			# 20
			line1, line2 = self.read_record()
			vertex[line1] = convert(line1, line2, self.DWGCODEPAGE)
			# 42
			line1, line2 = self.read_record()
			if line1 == '42':
				vertex[line1] = convert(line1, line2, self.DWGCODEPAGE)
			else:
				self.push_record(line1, line2)
			
			vertex_path.append((vertex['10'], vertex['20'], vertex['42']))
			
		self.load_seqend(vertex_path, path_flag)


	def load_polyline(self):
		param={	'70': 0, # bit codes for Polyline entity
				'40': 0.01, #XXX FIXMY
				}
		param.update(self.general_param)
		param = self.read_param(param)
		self.vertex_path = []
		self.curstyle.line_width=param['40'] * 72 # XXX self.unit_to_pt
		self.curstyle.line_pattern = self.get_pattern(param['62'])
		
		# if Group 70 Flag bit value set 1 This is a closed Polyline
		self.path_flag = param['70']


	def load_vertex(self):
		param={#'62': 7, # color
				#'6': 'CONTINUOUS', # style
				'10': None, # X coordinat
				'20': None, # Y coordinat
				'42': 0.0  # Bulge 
				}
		param = self.read_param(param)
		self.vertex_path.append((param['10'], param['20'], param['42']))


	def load_seqend(self, line = None, path_flag = None):
		if line is None:
			line = self.vertex_path
		
		if  path_flag is None:
			path_flag = self.path_flag
		
		if path_flag > 1:
			print 'FIXMY. Curves and smooth surface type', path_flag
		
		close_path = path_flag & 1 == 1
		
		path = CreatePath()
		if len(line):
			for i in line:
				x, y, bulge = i
				#print x, y, bulge
				path.AppendLine(self.trafo(x, y))
		
		if close_path:
			if path.Node(0) != path.Node(-1):
				path.AppendLine(path.Node(0))
				path.ClosePath()
		self.prop_stack.AddStyle(self.curstyle.Duplicate())
		self.bezier(path,)


	def load_circle(self):
		param={	'10': None, # X coordinat center
				'20': None, # Y coordinat center
				#'30': None, # Z coordinat center
				'40': 0.0  # radius
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		x = param['10']
		y = param['20']
		r = param['40']
		
		t = self.trafo(Trafo(r,0,0,r,x,y))
		
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		
		apply(self.ellipse, t.coeff())


	def load_arc(self):
		param={	'10': None, # X coordinat center
				'20': None, # Y coordinat center
				#'30': None, # Z coordinat center
				'40': 0.0, # radius
				'50': 0.0, # Start angle
				'51': 0.0 # End angle
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		cx = param['10']
		cy = param['20']
		rx = ry = param['40']
		start_angle = param['50'] * degrees
		end_angle = param['51'] * degrees
		
		trafo = self.trafo(Trafo(rx, 0, 0, ry, cx, cy))
		rx, w1, w2, ry, cx, cy = trafo.coeff()
		
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		
		apply(self.ellipse, (rx, w1, w2, ry, cx, cy, start_angle, end_angle, ArcArc))
		

	def load_ellips(self):
		param={	'10': 0.0, # X coordinat center
				'20': 0.0, # Y coordinat center
				#'30': 0.0, # Z coordinat center
				'11': 0.0, # Endpoint of major axis, relative to the center
				'21': 0.0,
				#'31': 0.0,
				'40': 0.0, # Ratio of minor axis to major axis
				'41': 0.0, # Start parameter (this value is 0.0 for a full ellipse)
				'42': 0.0, # End parameter (this value is 2pi for a full ellipse)
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		cx = param['10']
		cy = param['20']
		
		rx = sqrt(param['21']**2 + param['11']**2)
		ry = rx * param['40']
		
		start_angle = param['41']
		end_angle = param['42']
		
		angle=atan2(param['21'], param['11'])
		
		center = self.trafo(cx, cy)
		radius = self.trafo.DTransform(rx, ry)
		trafo = Trafo(radius.x, 0, 0, radius.y)
		trafo = Rotation(angle)(trafo)
		trafo = Translation(center)(trafo)
		rx, w1, w2, ry, cx, cy = trafo.coeff()
		
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		
		apply(self.ellipse, (rx, w1, w2, ry, cx, cy, start_angle, end_angle, ArcArc))


	def load_point(self):
		param={	'10': None, # X coordinat center
				'20': None, # Y coordinat center
				#'30': None, # Z coordinat center
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		x = param['10']
		y = param['20']
		r = 0.3
		
		t = self.trafo(Trafo(r,0,0,r,x,y))
		
		style = self.curstyle.Duplicate()
		style.line_pattern = EmptyPattern
		style.fill_pattern = self.get_pattern(param['62'])
		
		self.prop_stack.AddStyle(style.Duplicate())
		apply(self.ellipse, t.coeff())


	def load_solid(self):
		param={	'10': None, 
				'20': None, 
				#'30': None, 
				'11': None, 
				'21': None, 
				#'31': None,
				'12': None, 
				'22': None, 
				#'32': None,
				'13': None, 
				'23': None,
				#'33': None, 
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		style = self.curstyle.Duplicate()
		style.line_pattern = EmptyPattern
		style.fill_pattern = self.get_pattern(param['62'])
		
		self.path = CreatePath()
		self.path.AppendLine(self.trafo(param['10'], param['20']))
		self.path.AppendLine(self.trafo(param['11'], param['21']))
		self.path.AppendLine(self.trafo(param['12'], param['22']))
		self.path.AppendLine(self.trafo(param['13'], param['23']))
		
		self.path.ClosePath()
		
		self.prop_stack.AddStyle(style.Duplicate())
		self.bezier(self.path,)


	def load_insert(self):
		param={ '2': None, # Block name
				'10': 0.0, # X coordinat
				'20': 0.0, # Y coordinat
				#'30': 0.0, # Z coordinat
				'41': 1.0, # X scale factor 
				'42': 1.0, # Y scale factor 
				#'43': 1.0, # Z scale factor 
				'50': 0.0, # Rotation angle
				'66': 0, # Attributes-follow flag
				}
		param = self.read_param(param)
		
		block_name = self.default_block = param['2']
		
		if block_name:
			self.stack +=  ['POP_TRAFO', '0'] + self.block_dict[block_name]['data'] 
			self.push_trafo()
			
			x = param['10']
			y = param['20']
			block_x = self.block_dict[block_name]['10']
			block_y = self.block_dict[block_name]['20']
			
			scale_x = param['41'] * self.trafo.m11
			scale_y = param['42'] * self.trafo.m22
			angle = param['50'] * degrees
			
			translate = self.trafo(x, y)
			trafo = Trafo(1, 0, 0, 1, -block_x, -block_y)
			trafo = Scale(scale_x,scale_y)(trafo)
			trafo = Rotation(angle)(trafo)
			trafo = Translation(translate)(trafo)
			self.trafo = trafo
			
		if param['66'] != 0:
			line1, line2 = self.read_record()
			while line1 or line2:
				if line1 == '0' and line2 == 'SEQEND':
					break
				else:
					if line1 == '0':
						self.run(line2)
				line1, line2 = self.read_record()


	def load_text(self):
		param={ '10': 0.0, 
				'20': 0.0, 
				'40': None, # Text height
				'1': '', # Default value
				'50': 0, # Text rotation
				'41': 1, # Relative X scale factor—width
#				'8': self.default_layer, # Layer name
				'7': self.default_style, # Style name
				'72': 0, #Horizontal text justification type
				}
		param.update(self.general_param)
		param = self.read_param(param)
		

		x = param['10']
		y = param['20']
		scale_x = param['41']
		scale_y = 1
		angle = param['50'] * pi / 180
		font_size = param['40'] * self.trafo.m11
		

		halign = [ALIGN_LEFT, ALIGN_CENTER, ALIGN_RIGHT, \
					ALIGN_LEFT, ALIGN_LEFT, ALIGN_LEFT][param['72']]
		text = unicode_decoder(param['1'], self.DWGCODEPAGE)
		#style = self.style_dict[param['7']]
#		print style
		
		style_text = self.curstyle.Duplicate()
		style_text.line_pattern = EmptyPattern
		style_text.fill_pattern = self.get_pattern(param['62'])
		style_name = upper(param['7'])
		style = self.style_dict[style_name]
		font_name = style['1000']
		if font_name == 'Arial': # XXX
			font_name = 'ArialMT'
		style_text.font = GetFont(font_name)
#		print style_text.font
		style_text.font_size = font_size
		
		trafo_text = Translation(self.trafo(x, y))(Rotation(angle))(Scale(scale_x, scale_y))
		self.prop_stack.AddStyle(style_text.Duplicate())
		self.simple_text(strip(text), trafo_text, halign = halign)
		
	def load_3dface(self):
		param={	'10': None, 
				'20': None, 
				#'30': None, 
				'11': None, 
				'21': None, 
				#'31': None,
				'12': None, 
				'22': None, 
				#'32': None,
				'13': None, 
				'23': None,
				#'33': None, 
				'70': 0, # Invisible edge flags
				
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		self.path = CreatePath()
		if param['70'] != 0:
			print 'FIXMY. 3dface Invisible edge flags', param['70']
		self.path.AppendLine(self.trafo(param['10'], param['20']))
		self.path.AppendLine(self.trafo(param['11'], param['21']))
		self.path.AppendLine(self.trafo(param['12'], param['22']))
		self.path.AppendLine(self.trafo(param['13'], param['23']))
		
		self.path.ClosePath()
		
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		
		self.bezier(self.path,)

	def load_spline(self):
		param={	'70': 0, # Spline flag 
				'71': 0, # Degree of the spline curve
				'72': 0, # Number of knots
				'73': 0, # Number of control points
				'74': 0, # Number of fit points
				'40': [], # Knot value 
				'10': [], # Control points X
				'20': [], # Control points Y
				#'30': [], # Control points Z
				}
		param.update(self.general_param)
		param = self.read_param(param)
		
		closed = param['70']  & 1
		
		path = CreatePath()
		f13 = 1.0 / 3.0
		f23 = 2.0 / 3.0
		curve = path.AppendBezier
		straight = path.AppendLine

		pts = map(lambda x, y: self.trafo(x, y), param['10'],param['20'])
		print 'SPLINE', param['70'], len(pts)

		#for i in range(0, len(pts)-1):
			#self.ellipse(.2, 0, 0, .2, pts[i][0],pts[i][1])

		
		if param['70'] <= 1:
			
			straight(pts[0])
			for i in range(1, len(pts) / 4):
				node = pts[i * 4]
				c1 = pts[i * 4 - 3]
				c2 = pts[i * 4 - 2]
				print c1, c2, node

				curve(c1, c2, node)
				#straight(node)
			if closed:
				curve(pts[-3], pts[-2], pts[0])
			else:
				curve(pts[-4], pts[-4], pts[-1])

		if param['70'] & 4 == 4:
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

		if param['70'] & 8 == 8:
			node = pts[0]
			c1 = pts[1]
			c2 = pts[2]
			# first node
			straight(node)
			
			if len(pts) > 4:
				c2 = (pts[2] + pts[1]) / 2
				c3 = pts[3] * f13 + pts[2] * f23
				node = (c3 + c2) / 2
				curve(c1, c2, node)
				c1 = c3
				for i in range(3, len(pts) - 3):
					c2 = pts[i - 1] * f13 + pts[i] * f23
					c3 = pts[i] * f23 + pts[i + 1] * f13
					node = (c3 + c2) / 2
					curve(c1, c2, node)
					c1 = c3

				c2 = pts[-4] * f13 + pts[-3] * f23
				c3 = (pts[-3]  + pts[-2]) / 2 
				node = (c3 + c2) / 2
				curve(c1, c2, node)
				c1 = c3
			
			# last node
			curve(c1, pts[-2], pts[-1])
			
		style = self.get_line_style(**param)
		self.prop_stack.AddStyle(style.Duplicate())
		self.bezier(path,)
			

	def load_bypass(self):
		pass

###########################################################################

	def get_compiled(self):
		funclist={}
		for char, name in self.functions.items():
			method = getattr(self, name)
			argc = method.im_func.func_code.co_argcount - 1
			funclist[char] = (method, argc)
		return funclist

	def push_record(self, line1, line2):
		# save data in stack
		self.stack.append(line2)
		self.stack.append(line1)
		

	def read_record(self):
		# if the stack is empty read two lines from a file
		if self.stack:
			line1 = self.stack.pop()
			line2 = self.stack.pop()
		else:
			line1 = self.file.readline().strip()
			line2 = self.file.readline().strip()
		return line1, line2

	def read_param(self, param, stop=None):
		# read data and fill in the dictionary
		if stop is None:
			stop = [0, 9]
		line1, line2 = self.read_record()
		while line1 or line2:
			if int(line1) in stop:
				self.push_record(line1, line2)
				return param
			else:
				if line1 in param:
					value = convert(line1, line2, self.DWGCODEPAGE)
					if type(param[line1]) == list:
						param[line1].append(value)
					else:
						param[line1] = value
			line1,line2 = self.read_record()
		return False

	def find_record(self, code1, code2):
		# read data until to not overlap line1 == code1 and line2 == code2
		# return True
		# else return False
		
		line1, line2 = self.read_record()
		while line1 or line2:
			if line1 == code1 and line2 == code2:
				return True
			line1, line2 = self.read_record()
		return False


	def load_section(self):
		return_code = False
		file = self.file
		parsed = self.parsed
		parsed_interval = self.parsed_interval
		line1, line2 = self.read_record()
		while line1 or line2:
			interval_count = file.tell() / parsed_interval
			if interval_count > parsed:
				parsed += 10 # 10% progress
				app.updateInfo(inf2 = '%u' % parsed + _('% of file is parsed...'), inf3 = parsed)
				
			if line1 == '0' and line2 == 'ENDSEC':
				return_code = True
				break
			elif line1 == '0':
				self.run(line2)
			line1, line2 = self.read_record()
		self.parsed = parsed
		return return_code
	

	def load_sections(self):
		return_code = False
		param={	'2': '', # name section
				}
		param = self.read_param(param)
		name=param['2']
		print '**',name
		if name == 'HEADER':
			return_code, header_dict = self.load_HEADER()
			self.process_header(header_dict)
		elif name == 'CLASSES':
			return_code = self.find_record('0','ENDSEC')
		elif name == 'OBJECTS':
			return_code = self.find_record('0','ENDSEC')
		elif name == 'THUMBNAILIMAGE':
			return_code = self.find_record('0','ENDSEC')
		else:
			return_code = self.load_section()
		
		return return_code


	def interpret(self):
		file = self.file
		if type(file) == StringType:
			file = open(file, 'r')
		file.seek(0)
		readline = file.readline
		fileinfo = os.stat(self.filename)
		totalsize = fileinfo[6]
		self.parsed = 0
		self.parsed_interval = totalsize / 99 + 1
		
		line1, line2 = self.read_record()
		while line1 or line2:
			if line1 == '0':
				if line2 == 'EOF':
					break
				elif not self.load_sections():
					warn_tb(INTERNAL, _('DXFLoader: error. Non find end of sections'))
			line1, line2 = self.read_record()


	def run(self,keyword, *args):
		if keyword is None:
			return
		return_code = False
		unknown_operator = (None, None)
		funclist = self.funclist
		if keyword is not None:
			method, argc = funclist.get(keyword, unknown_operator)
			if method is not None:
				try:
					##print '******', keyword
					if len(args):
						i = 0
						while i<len(args):
							return_code = apply(method, args[i:argc+i])
							i+=argc
					else:
						return_code = method()
						
				except:
					warn_tb(INTERNAL, 'DXFLoader: error')
			else:
				self.add_message(_('Not interpreted %s') % keyword)
		return return_code



	def Load(self):
		import time
		start_time = time.clock()
		#print '		************ "DXF_objects" **************'
		self.funclist = self.get_compiled()
		self.document()
		self.layer(name = _("DXF_objects"))
		self.interpret()
		self.end_all()
		for style in self.dynamic_style_dict.values():
			self.object.load_AddStyle(style)
		self.object.load_Completed()
		print 'times',time.clock() - start_time
		return self.object

