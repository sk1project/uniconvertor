# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor Novikov
#
# This library is covered by GNU General Public License v2.0.
# For more info see COPYRIGHTS file in sK1 root directory.

###Sketch Config
#type = Import
#class_name = 'CDRLoader'
#rx_magic = '(?s)RIFF....CDR[789ABCDE]'
#tk_file_type = ('CorelDRAW Graphics', '.cdr')
#format_name = 'CDR'
#unload = 1
#standard_messages = 1
###End




import sys, types, struct, zlib, math, StringIO
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
		
from app.Graphics import pagelayout

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
	is_layer=False
	is_page=False
	
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
				self.is_page=True
				self.infocollector.obj_chunks.append(self)
			if self.listtype == 'layr':
				self.infocollector.layers+=1
				self.is_layer=True
				self.infocollector.obj_chunks.append(self)
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
					
			if self.listtype == 'grp ':
				self.infocollector.obj_chunks.append(None)
			if self.listtype == 'layr':
				self.infocollector.obj_chunks.append(2)
			if self.listtype == 'page':
				self.infocollector.obj_chunks.append(1)
	
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
	
class CDRCurve:
	is_Rectangle=0
	is_Curve=1
	is_Ellipse=0
	outlineIndex=''
	colorIndex=''
	paths = []
	scale=1
	
	def __init__(self, outlineIndex, colorIndex, paths, scale):
		self.colorIndex=colorIndex
		self.outlineIndex=outlineIndex
		self.paths=paths
		self.scale=scale
		
class CDRRectangle:
	is_Rectangle=1
	is_Curve=0
	is_Ellipse=0
	outlineIndex=''
	colorIndex=''
	trafo = []
	scale=1
	radiuses=[]
	
	def __init__(self, outlineIndex, colorIndex, trafo, scale, radiuses=[]):
		self.colorIndex=colorIndex
		self.outlineIndex=outlineIndex
		self.trafo=trafo
		self.scale=scale
		self.radiuses=radiuses
		
class CDREllipse:
	is_Rectangle=0
	is_Curve=0
	is_Ellipse=1
	outlineIndex=''
	colorIndex=''
	trafo = []
	scale=1
	angles=[]
	ellipse_type=False
	
	def __init__(self, outlineIndex, colorIndex, trafo, scale, angles=[],ellipse_type=False):
		self.colorIndex=colorIndex
		self.outlineIndex=outlineIndex
		self.trafo=trafo
		self.scale=scale
		self.angles=angles
		self.ellipse_type=ellipse_type
	
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
	scale =.000283464566929
	loader=None
	trafo_list=[]
	extracted_image = None
	image_dpi_trafo = None
	rectangle=None
	ellipse=None
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
			if chunk==1:
				self.paths_heap.append(1)
			elif chunk==2:
				self.paths_heap.append(2)
			elif chunk:
				if chunk.is_group:
					self.paths_heap.append(-1)
				elif chunk.is_page:
					self.paths_heap.append(-2)
				elif chunk.is_layer:
					self.paths_heap.append(-3)
				else:
					self.process_paths(chunk)
			else:
				self.paths_heap.append(0)
				
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
		
		obj_trafo=Trafo( var0, var3, var1, var4, (var2+x_shift/2)*scale, (var5+y_shift/2)*scale)
		
		if self.image_dpi_trafo is None:
#			return Trafo( var0, var3, var1, var4, (var2+x_shift/2)*scale, (var5+y_shift/2)*scale)
			return obj_trafo
		else:
			[w,h]=self.image_dpi_trafo
			image_scale=Scale(w,h)
			return obj_trafo(image_scale)
#			return Trafo( var0, var3, var1, var4, (var2+x_shift/2)*scale, (var5+y_shift/2)*scale)image_scale()
		
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
			self.paths_heap.append(CDRCurve(self.outlineIndex, self.colorIndex, self.current_paths, self.scale_with))
			
		if not self.rectangle is None:
			rect=self.rectangle[0]
			trafo=[rect.m11,rect.m21,rect.m12,rect.m22,rect.v1*self.scale,rect.v2*self.scale]
			self.paths_heap.append(CDRRectangle(self.outlineIndex, self.colorIndex, trafo, self.scale_with, self.rectangle[1]))

		if not self.ellipse is None:
			rect=self.ellipse[0]
			trafo=[rect.m11,rect.m21,rect.m12,rect.m22,rect.v1*self.scale,rect.v2*self.scale]
			self.paths_heap.append(CDREllipse(self.outlineIndex, self.colorIndex, 
											trafo, self.scale_with, self.ellipse[1], self.ellipse[2]))

			
		if not self.extracted_image is None:
			trafo=self.get_trafo(trfd, self.scale)
			self.paths_heap.append(('BMP',self.extracted_image, trafo))
		
		self.current_paths=[]
		self.extracted_image = None
		self.image_dpi_trafo = None
		self.outlineIndex=None
		self.rectangle=None
		self.ellipse=None
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
			[CoordX2] = struct.unpack('<L', chunk.data[offset:offset+4])                            
			[CoordY2] = struct.unpack('<L', chunk.data[offset+4:offset+8])
			if CoordX2 > 0x7FFFFFFF:
				CoordX2 = CoordX2 - 0x100000000
			if CoordY2 > 0x7FFFFFFF:
				CoordY2 = CoordY2 - 0x100000000
				
			[R1] = struct.unpack('<L', chunk.data[offset+8:offset+12])

			CoordX2=CoordX2*self.scale
			CoordY2=CoordY2*self.scale
			radiuses=[]
			R1=R1*self.scale
			if R1:
				radiuses=[abs(R1/CoordX2),abs(R1/CoordY2)]
					
			rect_trafo=Trafo(CoordX2,0,0,CoordY2,0,0)
			
			self.rectangle=[trafo(rect_trafo),radiuses]
			
		if type == 2:  # ellipse
			[CoordX2] = struct.unpack('<L', chunk.data[offset:offset+4])                            
			[CoordY2] = struct.unpack('<L', chunk.data[offset+4:offset+8])
			
			[startangle] = struct.unpack('<L', chunk.data[offset+8:offset+12])                              
			[endangle] = struct.unpack('<L', chunk.data[offset+12:offset+16])
			[rotangle] = struct.unpack('<L', chunk.data[offset+16:offset+20])
			
			ellipse_type=False
			
			if not startangle==endangle and rotangle == 0:
				ellipse_type=True
			
			startangle /=1000000.0
			endangle /=1000000.0
			
			startangle=math.radians(startangle)
			endangle=math.radians(endangle)
			angles=[startangle,endangle]
			
			if CoordX2 > 0x7FFFFFFF:
				CoordX2 = CoordX2 - 0x100000000
			if CoordY2 > 0x7FFFFFFF:
				CoordY2 = CoordY2 - 0x100000000	
				
			v1=CoordX2/2
			v2=CoordY2/2		
						
			CoordX2=CoordX2*self.scale/2
			CoordY2=CoordY2*self.scale/2

			ellipse_trafo=Trafo(CoordX2,0,0,CoordY2,v1,v2)
			
			self.ellipse=[trafo(ellipse_trafo),angles,ellipse_type]
			
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
			
			if version == 7:
				shift = 0x3c
			if version == 8:
				shift = 0x40
			if version > 8:
				shift = 0x48    
			offset = offset + shift
			points=[]
			#For bitmaps always should be 4 points
			[pointnum] = struct.unpack('<L', chunk.data[offset:offset+4])
			for i in range (pointnum):
				[CoordX] = struct.unpack('<L', chunk.data[offset+4+i*8:offset+8+i*8])                           
				[CoordY] = struct.unpack('<L', chunk.data[offset+8+i*8:offset+12+i*8])
				
				if CoordX > 0x7FFFFFFF:
					CoordX -= 0x100000000
				if CoordY > 0x7FFFFFFF:
					CoordY -= 0x100000000
				
				points.append([round(CoordX/10000.0,2),round(CoordY/10000.0,2)])
			
			w=abs(points[2][0]-points[0][0])
			h=abs(points[2][1]-points[0][1])
			
			#Calc dpi trafo
			width_mm=width*25.4/72
			height_mm=height*25.4/72
			
			self.image_dpi_trafo=[w/width_mm, h/height_mm]
			
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
			
			self.document()
			
			
			if self.verbosity:
				text=''
				if cdr.infocollector.cdr_version>0:
					text+='CorelDRAW ver.%u'%cdr.infocollector.cdr_version+'          \n'
					text+='   Pages: %u'%(cdr.infocollector.pages-1)+'\n'
					text+='   Layers: %u'%(cdr.infocollector.layers/cdr.infocollector.pages)+'\n'
					text+='   Groups: %u'%cdr.infocollector.groups+'\n'
					text+='   Objects: %u'%cdr.infocollector.objects+'\n'
					text+='   Bitmaps: %u'%cdr.infocollector.bitmaps+'\n'
					if cdr.infocollector.compression:
						text+='   COMPRESSED'
				sys.stderr.write(text)
			
			if cdr.infocollector.cdr_version>6:
				self.info=cdr.infocollector
				self.info.loader=self
				self.info.process_properties()
				
				self.import_curves()
				
			else:
				warn(USER, 'File <'+self.filename+
										'> contains usupported CorelDRAW ver.%u'%cdr.infocollector.cdr_version+'.0 drawing')
			self.end_all()
			self.object.load_Completed()
			self.object.pages.remove(self.object.pages[-1])
			self.object.pages.reverse()
			self.object.active_page=len(self.object.pages)-1
			self.object.setActivePage(0)
			
			return self.object
		
		except RiffEOF:
			raise SketchLoadError(_("Unexpected problems in file parsing"))
		except:
			import traceback
			traceback.print_exc()
			raise
		
	def import_curves(self):
		objcount=0
		objnum=len(self.info.paths_heap)
		jump=87.0/objnum
		interval=int((objnum/20)/10)+1
		interval_count=0
		layer_count=1
		for obj in self.info.paths_heap:
			objcount+=1
			interval_count+=1
			if interval_count>interval:
				interval_count=0
				app.updateInfo(inf2=_("Interpreting object %u of %u")%(objcount,objnum),inf3=10+int(jump*objcount))
				
			if obj==0:
				self.begin_group()
			elif obj==-1:
				self.end_group()
			elif obj==1:#page
				layout=pagelayout.PageLayout(width = self.info.doc_page[0]*self.info.scale, 
											height = self.info.doc_page[1]*self.info.scale, 
											orientation = 0)
				self.begin_page("",layout)
			elif obj==-2:#page
				self.end_composite()
			elif obj==2:#layer
				self.layer('cdr_layer%g'%(layer_count), 1, 1, 0, 0, ('RGB',0,0,0))
				layer_count+=1
			elif obj==-3:#layer
				self.end_layer()
				
			elif type(obj)==TupleType and obj[0]=='BMP':
				self.image(obj[1],obj[2])
			elif obj.is_Rectangle:
				self.set_style(obj)
				[m11,m21,m12,m22,v1,v2]=obj.trafo
				if len(obj.radiuses):
					self.rectangle(m11, m21, m12, m22, v1, v2, obj.radiuses[0], obj.radiuses[1])
				else:
					self.rectangle(m11, m21, m12, m22, v1, v2)
			elif obj.is_Ellipse:
				ellipse_type=app.conf.const.ArcPieSlice
				if obj.ellipse_type:
					ellipse_type=app.conf.const.ArcArc
					obj.colorIndex=False
				self.set_style(obj)
				[m11,m21,m12,m22,v1,v2]=obj.trafo
				self.ellipse(m11, m21, m12, m22, v1, v2, obj.angles[0], obj.angles[1],ellipse_type)
					
			else:
				self.set_style(obj)
						
				object = PolyBezier(paths = tuple(obj.paths), properties = self.get_prop_stack())
				self.append_object(object)
				
				if obj.outlineIndex:
					if self.info.outl_data[obj.outlineIndex].spec & 0x10:
						copy = object.Duplicate()
						copy.properties.SetProperty(line_width=0)
						self.append_object(copy)
				else:
					if self.info.default_outl_data.spec & 0x10:
						copy = object.Duplicate()
						copy.properties.SetProperty(line_width=0)
						self.append_object(copy)
				

	def set_style(self, obj):
		style = self.style
		if obj.colorIndex:
			if self.info.fill_data.has_key(obj.colorIndex):
				style.fill_pattern = SolidPattern(self.info.fill_data[obj.colorIndex])
			else:
				style.fill_pattern = EmptyPattern
		else:
			style.fill_pattern = EmptyPattern
			
		if obj.outlineIndex:
			if self.info.outl_data.has_key(obj.outlineIndex):
				if self.info.outl_data[obj.outlineIndex].spec & 0x01:
					style.line_pattern = EmptyPattern
				else:
					style.line_pattern = SolidPattern(self.info.outl_data[obj.outlineIndex].color)
				
				if self.info.outl_data[obj.outlineIndex].spec & 0x04:
					style.line_dashes = self.info.outl_data[obj.outlineIndex].dashes
				
				if self.info.outl_data[obj.outlineIndex].spec & 0x20:
					style.line_width = self.info.outl_data[obj.outlineIndex].width*obj.scale
				else:
					style.line_width = self.info.outl_data[obj.outlineIndex].width
					
				style.line_cap = self.info.outl_data[obj.outlineIndex].caps + 1
				style.line_join = self.info.outl_data[obj.outlineIndex].corner
			else:
				style.line_pattern = EmptyPattern
		else:
			if self.info.default_outl_data:
				if self.info.default_outl_data.spec & 0x01:
					style.line_pattern = EmptyPattern
				else:
					style.line_pattern = SolidPattern(self.info.default_outl_data.color)
					
				if self.info.default_outl_data.spec & 0x04:
					style.line_dashes = self.info.default_outl_data.dashes

				if self.info.default_outl_data.spec & 0x20:
					style.line_width = self.info.default_outl_data.width*obj.scale
				else:
					style.line_width = self.info.default_outl_data.width
				style.line_cap = self.info.default_outl_data.caps + 1
				style.line_join = self.info.default_outl_data.corner
			else:
				style.line_pattern = EmptyPattern
					
				
