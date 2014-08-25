# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor Novikov
#
# This library is covered by GNU General Public License v2.0.
# For more info see COPYRIGHTS file in sK1 root directory.

###Sketch Config
#type = Parsing
#class_name = 'CDRLoader'
#rx_magic = '(?s)RIFF....CDR[3456789ABCDE]'
#tk_file_type = ('CorelDRAW Graphics', '.cdr')
#format_name = 'CDR'
#unload = 1
#standard_messages = 1
###End




import sys, types, struct, zlib, math, StringIO, os
from PIL import Image

from struct import unpack, calcsize

from types import TupleType

from streamfilter import BinaryInput

from app import _, CreatePath, Point, ContSmooth, ContAngle, ContSymmetrical, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient, \
		ConicalGradient, PolyBezier, MultiGradient,\
		CreateRGBColor, CreateCMYKColor, Trafo, Point, Polar, Translation, \
		Scale, StandardColors, ImageTilePattern, ImageData, MaskGroup, \
		Arrow

from app.events.warn import INTERNAL, warn_tb, warn, USER
from app.io.load import GenericLoader, SketchLoadError, EmptyCompositeError
from app.Lib import units
import app

def load_file(file):
	f = open(file, 'rb')
	buf = f.read()
	f.close()
	cdr = RiffChunk()
	cdr.load(buf)
	return cdr 
	
class RiffChunk:
	fourcc = '????'
	hdroffset = 0
	rawsize = 0
	data = ''
	contents = []
	fullname= ''
	chunkname= ''
	chunksize= ''
	compression = False
	infocollector=None
	number=0
	listtype=''
	is_group=False
	
	def __init__(self, infocollector=None):
		if infocollector:
			self.infocollector=infocollector
		else:
			self.infocollector=InfoCollector()
			self.infocollector.image=None
			self.infocollector.bitmap=None
	
	def loadcompressed(self):
		if self.data[0:4] != 'cmpr':
			raise Exception("can't happen")
		self.compression=True
		self.infocollector.compression=True
		[compressedsize] = struct.unpack('<I', self.data[4:8])
		[uncompressedsize] = struct.unpack('<I', self.data[8:12])
		[blocksizessize] = struct.unpack('<I', self.data[12:16])
		assert(self.data[20:24] == 'CPng')
		assert(struct.unpack('<H', self.data[24:26])[0] == 1)
		assert(struct.unpack('<H', self.data[26:28])[0] == 4)
		if (20 + compressedsize + blocksizessize + 1) & ~1 != self.rawsize:
			raise Exception('mismatched blocksizessize value (20 + %u + %u != %u)' % (compressedsize, blocksizessize, self.rawsize))
		decomp = zlib.decompressobj()
		self.uncompresseddata = decomp.decompress(self.data[28:])
		if len(decomp.unconsumed_tail):
			raise Exception('unconsumed tail in compressed data (%u bytes)' % len(decomp.unconsumed_tail))
		if len(decomp.unused_data) != blocksizessize:
			raise Exception('mismatch in unused data after compressed data (%u != %u)' % (len(decomp.unused_data), blocksizessize))
		if len(self.uncompresseddata) != uncompressedsize:
			raise Exception('mismatched compressed data size: expected %u got %u' % (uncompressedsize, len(self.uncompresseddata)))
		chunk = RiffChunk(infocollector=self.infocollector)
		blocksizesdata = zlib.decompress(self.data[28+compressedsize:])
		blocksizes = []
		for i in range(0, len(blocksizesdata), 4):
			blocksizes.append(struct.unpack('<I', blocksizesdata[i:i+4])[0])
		offset = 0
		self.contents = []
		while offset < len(self.uncompresseddata):
			chunk = RiffChunk(infocollector=self.infocollector)
			chunk.parent = self
			chunk.load(self.uncompresseddata, offset, blocksizes)
			self.contents.append(chunk)
			offset += 8 + chunk.rawsize

	def load(self, buf, offset=0, blocksizes=()):
		self.hdroffset = offset
		self.fourcc = buf[offset:offset+4]
		self.chunksize = buf[offset+4:offset+8]
		[self.rawsize] = struct.unpack('<I', buf[offset+4:offset+8])
		if len(blocksizes):
			self.rawsize = blocksizes[self.rawsize]
		self.data = buf[offset+8:offset+8+self.rawsize]
		if self.rawsize & 1:
			self.rawsize += 1
		self.number=self.infocollector.numcount
		self.infocollector.numcount+=1
		if self.fourcc == 'vrsn':
			[version] = struct.unpack('<H', self.data)
			self.infocollector.cdr_version=version/100
		if self.fourcc == 'fild':
			self.infocollector.fill_chunks.append(self)
		if self.fourcc == 'outl':
			self.infocollector.outl_chunks.append(self)
		if self.fourcc == 'bmp ':
			self.infocollector.bmp_chunks.append(self)
		if self.fourcc == 'mcfg':
			self.infocollector.page_chunk=self
		self.contents = []
		self.fullname = self.full_name()
		self.chunkname = self.chunk_name()
		if self.fourcc == 'RIFF' or self.fourcc == 'LIST':
			self.listtype = buf[offset+8:offset+12]
			self.fullname = self.full_name()
			self.chunkname = self.chunk_name()
			
			if self.listtype == 'page':
				self.infocollector.pages+=1
				self.is_group=True
				self.infocollector.obj_chunks.append(self)
			if self.listtype == 'layr':
				self.infocollector.layers+=1
			if self.listtype == 'obj ':
				self.infocollector.objects+=1
				self.infocollector.obj_chunks.append(self)
			if self.listtype == 'bmpt':
				self.infocollector.bitmaps+=1
			if self.listtype == 'grp ':
				self.infocollector.groups+=1
				self.is_group=True
				self.infocollector.obj_chunks.append(self)
				
			if self.listtype == 'stlt':
				self.chunkname = '<stlt>'
			elif self.listtype == 'cmpr':
				self.loadcompressed()
			else:
				offset += 12
				while offset < self.hdroffset + 8 + self.rawsize:
					chunk = RiffChunk(infocollector=self.infocollector)
					chunk.parent = self
					chunk.load(buf, offset, blocksizes)
					self.contents.append(chunk)
					offset += 8 + chunk.rawsize
					
			if self.listtype == 'grp ' or self.listtype == 'page':
				self.infocollector.obj_chunks.append(None)
	
	def full_name(self):
		if hasattr(self, 'parent'):
			name = self.parent.fullname + '.'
			if hasattr(self, 'listtype'):
				return name + self.listtype
			return name + self.fourcc
		else:
			return self.fourcc
		
	def chunk_name(self):
		if self.fourcc == 'RIFF':
			return '<'+self.fourcc+'>'
		if hasattr(self, 'listtype'):
			return '<'+self.listtype+'>'
		return '<'+self.fourcc+'>'
	
class Outline:
	outlineIndex=''
	color = None
	width = 0
	caps=0
	corner=0
	spec=0
	dashes = []
	
class BezierNode:
	point1=None
	point2=None
	point3=None
	
class BezierCurve:
	outlineIndex=''
	colorIndex=''
	paths = []
	scale=1
	
	def __init__(self, outlineIndex, colorIndex, paths, scale):
		self.colorIndex=colorIndex
		self.outlineIndex=outlineIndex
		self.paths=paths
		self.scale=scale
	
class InfoCollector:
	image=None
	cdr_version=0
	objects=0
	pages=0
	layers=0
	groups=0
	bitmaps=0
	compression=False
	numcount=0
	bmp_chunks=[]
	bmp_dict={}
	obj_chunks=[]
	fill_chunks=[]
	outl_chunks=[]
	fill_data={}
	outl_data={}
	paths_heap=[]
	current_paths=[]
	outlineIndex=None
	default_outl_data=None
	colorIndex=None
	loda_type_func = None
	scale =.0002835
	loader=None
	trafo_list=[]
	extracted_image = None
	page_chunk=None
	doc_page=()
	scale_with=1
	
	def process_properties(self):
		self.loda_type_func = {0xa:self.loda_outl,0x14:self.loda_fild,0x1e:self.loda_coords}
		for chunk in self.fill_chunks:
			self.process_fill(chunk)
		outl_index=0
		for chunk in self.outl_chunks:
			self.process_outline(chunk,outl_index)
			outl_index+=1
		self.obj_chunks.reverse()
		for bmp in self.bmp_chunks:
			self.bmp_dict[ord(bmp.data[0])]=bmp
		self.get_page_size()
		for chunk in self.obj_chunks:
			if chunk:
				if chunk.is_group:
					self.paths_heap.append(0)
				else:
					self.process_paths(chunk)
			else:
				self.paths_heap.append(1)
		self.validate_heap()
	
	def validate_heap(self):
		paths_heap=self.paths_heap
		result=[]
		for obj in paths_heap:
			if obj==0:
				if result[-1]==1:
					result=result[:-1]
				elif result==[]:
					pass
				else:
					result.append(obj)
			else:
				result.append(obj)
		self.paths_heap=result
	
	def get_page_size(self):
		if self.page_chunk is None:
			return
		offset=0x4
		if self.cdr_version >= 13:
			offset=0xc
		if self.cdr_version in [7,8]:
			offset=0x0
		[width] = struct.unpack('<L', self.page_chunk.data[offset:offset+0x4])
		[height] = struct.unpack('<L', self.page_chunk.data[offset+0x4:offset+0x8])
		self.doc_page = (width, height)	   
	
	def check_trafo(self, chunk):
		pass
		
	def get_trafo(self, trfd, scale=1):
		cdr_version=self.cdr_version
		
		ieeestart = 32
		if cdr_version >= 13:
			ieeestart = 40
		if cdr_version == 5:
			ieeestart = 18
		
		(x_shift,y_shift)=self.doc_page
		
		[var0] = struct.unpack('<d', trfd.data[ieeestart:ieeestart+8])
		[var1] = struct.unpack('<d', trfd.data[ieeestart+8:ieeestart+8+8])
		[var2] = struct.unpack('<d', trfd.data[ieeestart+2*8:ieeestart+8+2*8])
		[var3] = struct.unpack('<d', trfd.data[ieeestart+3*8:ieeestart+8+3*8])
		[var4] = struct.unpack('<d', trfd.data[ieeestart+4*8:ieeestart+8+4*8])
		[var5] = struct.unpack('<d', trfd.data[ieeestart+5*8:ieeestart+8+5*8])
		self.scale_with=min(var0*cmp(var0,0), var4*cmp(var4,0))
		return Trafo( var0, var3, var1, var4, (var2+x_shift/2)*scale, (var5+y_shift/2)*scale)
		
	def process_paths(self, list):
		cdr_version=self.cdr_version
		chunk=None
		trfd=None
		for child in list.contents:
			if child.listtype=='lgob':
				for subchild in child.contents:
					if subchild.fourcc=='loda':
						chunk=subchild
					if subchild.listtype=='trfl': 
						trfd=subchild.contents[0]
		if not chunk:
			return
		
		trafo=self.get_trafo(trfd)
		
		[numofparms] = struct.unpack('<L', chunk.data[0x4:0x8])
		[startofparms] = struct.unpack('<L',chunk.data[0x8:0xC])
		[startoftypes] = struct.unpack('<L',chunk.data[0xC:0x10])
		
		type = ord(chunk.data[0x10])

		for i in range(numofparms):
			[offset] = struct.unpack('<L',chunk.data[startofparms+i*4:startofparms+i*4+4])
			[argtype] = struct.unpack('<L',chunk.data[startoftypes + (numofparms-1-i)*4:startoftypes + (numofparms-1-i)*4+4])
			
			if self.loda_type_func.has_key(argtype) == 1:
				self.loda_type_func[argtype](chunk,type,offset,cdr_version,trafo)
		
		if not self.current_paths.count==[]:
			self.paths_heap.append(BezierCurve(self.outlineIndex, self.colorIndex, self.current_paths, self.scale_with))
			
		if self.extracted_image is not None:
			trafo=self.get_trafo(trfd, self.scale)
			self.paths_heap.append(('BMP',self.extracted_image, trafo))
		
		self.current_paths=[]
		self.extracted_image = None
		self.outlineIndex=None
		self.colorIndex=None
		self.scale_with=1
		
	def extract_bmp(self, numbmp,width,height):
		if not self.bmp_dict.has_key(numbmp):
			return
		chunk=self.bmp_dict[numbmp]
		palflag = ord(chunk.data[0x36])
		[bmpsize] = struct.unpack('<L',chunk.data[42:46])
		[bmpstart] = struct.unpack('<L',chunk.data[50:54])
		
		numcol = (bmpstart - 82)/3
		if palflag == 5:
			numcol = 256
		bmpstart2 = numcol*4 + 54
		bmpstart2 = struct.pack('<L',bmpstart2)
		
		if palflag == 3:#CMYK image
			self.bmpbuf=chunk.data[bmpstart+40:]
			self.extracted_image = Image.fromstring('CMYK', (width, height), self.bmpbuf, 'raw', 'CMYK', 0, -1)
		elif palflag == 5:#Grayscale image
			self.bmpbuf=chunk.data[bmpstart+40:]
			bytes=math.ceil(width/2.0)*2
			self.extracted_image = Image.fromstring('L', (width, height), self.bmpbuf, 'raw', 'L', bytes, -1)
		elif palflag == 6: #Mono image
			bmpstart2 = numcol*4 + 66
			bmpstart2 = struct.pack('<L',bmpstart2)		
			self.bmpbuf = 'BM'+chunk.data[42:50]+bmpstart2[0:4]+'\x28\x00\x00\x00'
			self.bmpbuf += chunk.data[62:72]+chunk.data[74:78]
			self.bmpbuf += '\x00\x00'+chunk.data[82:90]+'\x00\x00\x00\x00'
			self.bmpbuf += '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
			self.bmpbuf += chunk.data[bmpstart+40:]			
			self.extracted_image = Image.open(StringIO.StringIO(self.bmpbuf ))
			self.extracted_image.load()
			
#		elif palflag == 1: #RGB
#			print 'width, height', (width, height)
#			self.bmpbuf=chunk.data[bmpstart+40:]
#			self.extracted_image = Image.fromstring('RGB', (width, height), self.bmpbuf, 'raw', 'BGR', 0, -1)
		
		else:
			self.bmpbuf = 'BM'+chunk.data[42:50]+bmpstart2[0:4]+'\x28\x00\x00\x00'
			self.bmpbuf += chunk.data[62:72]+chunk.data[74:78]
			self.bmpbuf += '\x00\x00'+chunk.data[82:90]+'\x00\x00\x00\x00'
			if numcol > 1:
				self.bmpbuf = self.bmpbuf+'\x00\x01\x00\x00\x00\x00\x00\x00'
				for i in range (numcol):
					self.bmpbuf = self.bmpbuf+chunk.data[122+i*3:125+i*3]+'\x00'
			self.bmpbuf += chunk.data[bmpstart+40:]
			self.extracted_image = Image.open(StringIO.StringIO(self.bmpbuf ))
			self.extracted_image.load()
			
	def loda_coords(self,chunk,type,offset,version,trafo):
		if type == 1:  # rectangle
			CoordX1 = 0 
			CoordY1 = 0
			[CoordX2] = struct.unpack('<L', chunk.data[offset:offset+4])                            
			[CoordY2] = struct.unpack('<L', chunk.data[offset+4:offset+8])
			if CoordX2 > 0x7FFFFFFF:
				CoordX2 = CoordX2 - 0x100000000
			if CoordY2 > 0x7FFFFFFF:
				CoordY2 = CoordY2 - 0x100000000
			
			CoordX1, CoordY1=trafo(CoordX1, CoordY1)
			CoordX2, CoordY2=trafo(CoordX2, CoordY2)
			
			path = CreatePath()
			path.AppendLine(Point(CoordX1*self.scale, CoordY1*self.scale))
			path.AppendLine(Point(CoordX2*self.scale, CoordY1*self.scale))
			path.AppendLine(Point(CoordX2*self.scale, CoordY2*self.scale))
			path.AppendLine(Point(CoordX1*self.scale, CoordY2*self.scale))
			path.AppendLine(Point(CoordX1*self.scale, CoordY1*self.scale))
			path.AppendLine(path.Node(0))
			path.ClosePath()
			self.current_paths.append(path)

		if type == 3: # line and curve
			[pointnum] = struct.unpack('<L', chunk.data[offset:offset+4])
			
			path=None
			point1=None
			point2=None
			cont=ContSymmetrical
			for i in range (pointnum):
				[CoordX] = struct.unpack('<L', chunk.data[offset+4+i*8:offset+8+i*8])
				[CoordY] = struct.unpack('<L', chunk.data[offset+8+i*8:offset+12+i*8])
				
				if CoordX > 0x7FFFFFFF:
					CoordX = CoordX - 0x100000000
				if CoordY > 0x7FFFFFFF:
					CoordY = CoordY - 0x100000000
				CoordX, CoordY=trafo(CoordX, CoordY)
				
				Type = ord(chunk.data[offset+4+pointnum*8+i])
				
				if Type&2 == 2:
					pass
				if Type&4 == 4:
					pass
				if Type&0x10 == 0 and Type&0x20 == 0:
					cont=ContAngle
				if Type&0x10 == 0x10:
					cont=ContSmooth
				if Type&0x20 == 0x20:
					cont=ContSymmetrical
				if Type&0x40 == 0 and Type&0x80 == 0:
					if path:
						self.current_paths.append(path)
					path = CreatePath()
					path.AppendLine(Point(CoordX*self.scale, CoordY*self.scale))
					point1=None
					point2=None
				if Type&0x40 == 0x40 and Type&0x80 == 0:
					if path:
						path.AppendLine(Point(CoordX*self.scale, CoordY*self.scale))
						point1=None
						point2=None
				if Type&0x40 == 0 and Type&0x80 == 0x80:
					path.AppendBezier(point1,point2,Point(CoordX*self.scale, CoordY*self.scale),cont)
					point1=None
					point2=None
				if Type&0x40 == 0x40 and Type&0x80 == 0x80:
					if point1:
						point2=Point(CoordX*self.scale, CoordY*self.scale)
					else:
						point1=Point(CoordX*self.scale, CoordY*self.scale)
				if Type&8 == 8:
					if path:
						path.ClosePath()
			if path:
				self.current_paths.append(path)
		if type == 5: # bitmap
			bmp_color_models = ('Invalid','Pal1','CMYK255','RGB','Gray','Mono','Pal6','Pal7','Pal8')
			bmp_clrmode = ord(chunk.data[offset+0x30])
			clrdepth = ord(chunk.data[offset+0x22])
			[width] = struct.unpack('<L', chunk.data[offset+0x24:offset+0x28])
			[height] = struct.unpack('<L', chunk.data[offset+0x28:offset+0x2c])
			[idx1] = struct.unpack('<L', chunk.data[offset+0x2c:offset+0x30])
			numbmp = ord(chunk.data[offset+0x30])
			[idx2] = struct.unpack('<L', chunk.data[offset+0x34:offset+0x38])
			[idx3] = struct.unpack('<L', chunk.data[offset+0x38:offset+0x3c])
			self.extract_bmp(numbmp,width,height)

	def loda_fild(self,chunk,type,offset,version,trafo):
		self.colorIndex='%02X'%ord(chunk.data[offset])+'%02X'%ord(chunk.data[offset+1])+\
					'%02X'%ord(chunk.data[offset+2])+'%02X'%ord(chunk.data[offset+3])

	def loda_outl(self,chunk,type,offset,version,trafo):
		self.outlineIndex='%02X'%ord(chunk.data[offset])+'%02X'%ord(chunk.data[offset+1])+\
				'%02X'%ord(chunk.data[offset+2])+'%02X'%ord(chunk.data[offset+3])


	def process_outline(self, chunk, usual):
		cdr_version=self.cdr_version
		outl = Outline()
		outl.outlineIndex='%02X'%ord(chunk.data[0]) + '%02X'%ord(chunk.data[1]) + '%02X'%ord(chunk.data[2]) + '%02X'%ord(chunk.data[3])

		ls_offset = 0x4
		lc_offset = 0x6
		ct_offset = 0x8
		lw_offset = 0xc
		offset = 0x1c
		dash_offset = 0x68
			
		if cdr_version >= 13:
			ls_offset = 0x18
			lc_offset = 0x1a
			ct_offset = 0x1c
			lw_offset = 0x1e
			offset = 0x28
			dash_offset = 0x74
			
		outl.spec=ord(chunk.data[ls_offset])
		
		outl.caps=ord(chunk.data[lc_offset])
		outl.corner=ord(chunk.data[ct_offset])
		[line_width] = struct.unpack('<L',chunk.data[lw_offset:lw_offset+4])
		outl.width=line_width*self.scale

		## dashes
		[dashnum]= struct.unpack('<h', chunk.data[dash_offset:dash_offset+2])
		if dashnum > 0:
			outl.dashes = range(dashnum)
			for i in outl.dashes:
				[dash] = struct.unpack('<h', chunk.data[dash_offset+2+i*2:dash_offset+4+i*2])
				outl.dashes[i] = dash

		clrmode = ord(chunk.data[offset+0x30])
		
		if clrmode == 9:
			outl.color=CreateCMYKColor(0, 0, 0, 1.0 - ord(chunk.data[offset+0x38]) /255.0)
		elif clrmode == 5:
			outl.color=CreateRGBColor(ord(chunk.data[offset+0x3a]) / 255.0, 
						   ord(chunk.data[offset+0x39])/ 255.0,
						   ord(chunk.data[offset+0x38]) / 255.0)
		elif clrmode == 4:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/255.0,
							ord(chunk.data[offset+0x39])/255.0,
							ord(chunk.data[offset+0x3a])/255.0, 0.0)
		elif clrmode == 2:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/100.0,
							ord(chunk.data[offset+0x39])/100.0,
							ord(chunk.data[offset+0x3a])/100.0,
							ord(chunk.data[offset+0x3b])/100.0)
		elif clrmode == 3 or clrmode == 0x11:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/255.0,
							ord(chunk.data[offset+0x39])/255.0,
							ord(chunk.data[offset+0x3a])/255.0,
							ord(chunk.data[offset+0x3b])/255.0)
		elif clrmode == 17:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/255.0,
							ord(chunk.data[offset+0x39])/255.0,
							ord(chunk.data[offset+0x3a])/255.0,
							ord(chunk.data[offset+0x3b])/255.0)
		elif clrmode == 20:
			outl.color=CreateCMYKColor(1.0,1.0,1.0,1.0)
		else:
			outl.color=CreateCMYKColor(0, 0, 0, 1)
			
		self.outl_data[outl.outlineIndex]=outl
		if not usual:
			self.default_outl_data=outl

	
	def process_fill(self, chunk):
		cdr_version=self.cdr_version
		fill_data=self.fill_data
		fild_pal_type = ('Transparent', 'Solid', 'Gradient')
		colorIndex='%02X'%ord(chunk.data[0]) + '%02X'%ord(chunk.data[1]) + '%02X'%ord(chunk.data[2]) + '%02X'%ord(chunk.data[3])
		pal = ord(chunk.data[4])
		if cdr_version >= 13:
			pal = ord(chunk.data[0xc])		
		if	pal < 3:
			fild_type = fild_pal_type[pal]
		else:
			fild_type = 'Unknown (%X)'%pal
		clr_offset = 0x8
		if cdr_version >= 13:
			clr_offset = 0x1b
			
		if clr_offset < chunk.rawsize:
			clrmode = ord(chunk.data[clr_offset])
			if fild_type == 'Solid':
				offset = 0x10
				if cdr_version >= 13:
					offset =0x23
				if clrmode == 9: #Grayscale
					fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, 1.0 - ord(chunk.data[offset]) /255.0)
				elif clrmode == 5: #RGB
					fill_data[colorIndex]=CreateRGBColor(ord(chunk.data[offset+2]) / 255.0, 
									ord(chunk.data[offset+1])/ 255.0,
									ord(chunk.data[offset]) / 255.0)
				elif clrmode == 4: #CMY
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/255.0,
									ord(chunk.data[offset+1])/255.0,
									ord(chunk.data[offset+2])/255.0, 0.0)
				elif clrmode == 3:#CMYK255
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/255.0,
									ord(chunk.data[offset+1])/255.0,
									ord(chunk.data[offset+2])/255.0,
									ord(chunk.data[offset+3])/255.0)
				elif clrmode == 2: #CMYK
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/100.0,
									ord(chunk.data[offset+1])/100.0,
									ord(chunk.data[offset+2])/100.0,
									ord(chunk.data[offset+3])/100.0)
				elif clrmode == 1:
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/255.0,
									ord(chunk.data[offset+1])/255.0,
									ord(chunk.data[offset+2])/255.0,
									ord(chunk.data[offset+3])/255.0)
				elif clrmode == 0x11:
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/255.0,
									ord(chunk.data[offset+1])/255.0,
									ord(chunk.data[offset+2])/255.0,
									ord(chunk.data[offset+3])/255.0)
				elif clrmode == 0x14: #Registration Color
					fill_data[colorIndex]=CreateCMYKColor(1,1,1,1)
				else:
					fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, .20)
			if fild_type == 'Transparent':
				fill_data[colorIndex]=None
			if fild_type == 'Gradient':
				fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, .3)
#			else:
#				fill_data[colorIndex]=CreateCMYKColor(0, 1, 0, 0)

class RiffEOF(Exception):
	pass

class CDRLoader(GenericLoader):

	def __init__(self, file, filename, match):
		GenericLoader.__init__(self, file, filename, match)
		self.fix_tile = None
		self.fix_clip = 0
		self.fix_lens = ()
		self.object = None
		self.filename =filename
		self.verbosity=False
		self.info = None
		self.file=file

	def Load(self):
		try:			
			self.file.seek(0)
			cdr = RiffChunk()
			cdr.load(self.file.read())
			app.updateInfo(inf2=_("Parsing is finished"),inf3=10)

			summary=[
			('CDR version', cdr.infocollector.cdr_version),
			('pages', cdr.infocollector.pages-1),
			('layers', cdr.infocollector.layers/cdr.infocollector.pages),
			('groups', cdr.infocollector.groups),
			('objects', cdr.infocollector.objects),
			('bitmaps', cdr.infocollector.bitmaps),
			]
			if cdr.infocollector.compression:
				summary.append(('compression','yes'))
			else:
				summary.append(('compression','no'))


			if self.filename == None:
				return
			from xml.sax.saxutils import XMLGenerator
	
			try:
				file = open(self.filename, 'w')
			except (IOError, os.error), value:
				import sys
				sys.stderr('cannot write parsing result into %s: %s'% (`filename`, value[1]))
				return
		
			writer = XMLGenerator(out=file,encoding='utf-8')
			writer.startDocument()	
	
			writer.startElement('riffDocument',{})
			writer.characters('\n')
			
			writer.startElement('docSummary',{})
			writer.characters('\n')
			
			for key, value in summary:
				writer.characters('\t')
				writer.startElement('%s' % key,{})
				writer.characters('%s' % `value`)
				writer.endElement('%s' % key)
				writer.characters('\n')
				
			writer.endElement('docSummary')
			writer.characters('\n')
			
			writer.startElement('docStructure',{})
			writer.characters('\n')
			
			if cdr.infocollector.cdr_version>6:
				self.info=cdr.infocollector
				self.info.loader=self
				self.info.process_properties()				
				self.import_curves(writer)
				
			else:
				writer.characters('\t')
				writer.startElement('info',{})
				value='Parsed file contains usupported CorelDRAW ver.%u'%cdr.infocollector.cdr_version+'.0 drawing'
				writer.characters('%s' % `value`)
				writer.endElement('info')
				writer.characters('\n')
		
		except RiffEOF:
			writer.characters('\t')
			writer.startElement('info',{})	
			writer.characters('Unexpected problems in file parsing')
			writer.endElement('info')
			writer.characters('\n')					
			raise SketchLoadError(_("Unexpected problems in file parsing"))
		
		except:
			import traceback
			traceback.print_exc()
			raise
		
		finally:
			writer.endElement('docStructure')
			writer.characters('\n')
			
			writer.endElement('riffDocument')
			writer.endDocument()
			file.close	
			return
		
	def import_curves(self,writer):
		ident='\t'
		for obj in self.info.paths_heap:
			
			if obj==1:	
				writer.characters(ident)
				writer.startElement('group',{})		
				writer.characters('\n')
				ident+='\t'
				
			elif obj==0:
				ident=ident[1:]	
				writer.characters(ident)				
				writer.endElement('group')
				writer.characters('\n')
				
			elif type(obj)==TupleType and obj[0]=='BMP':					
				writer.characters(ident)
				writer.startElement('image',{})
				writer.endElement('image')
				writer.characters('\n')
				
			else:
				writer.characters(ident)
				writer.startElement('curve',{})
				writer.endElement('curve')
				writer.characters('\n')
				

				

					
				
