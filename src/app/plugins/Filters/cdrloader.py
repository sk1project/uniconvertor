# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor E. Novikov, Valek Fillipov
#
# This library is covered by GNU General Public License v2.0.
# For more info see COPYRIGHTS file in sK1 root directory.

###Sketch Config
#type = Import
#class_name = 'CDRLoader'
#rx_magic = '(?s)RIFF....CDR[789ABCD]'
#tk_file_type = ('CorelDRAW Graphics', '.cdr')
#format_name = 'CDR'
#unload = 1
#standard_messages = 1
###End




import sys, types, struct, zlib, math

from struct import unpack, calcsize

from streamfilter import BinaryInput

from app import CreatePath, Point, ContSmooth, ContAngle, ContSymmetrical, \
		SolidPattern, EmptyPattern, LinearGradient, RadialGradient, \
		ConicalGradient, MultiGradient,\
		CreateRGBColor, CreateCMYKColor, Trafo, Point, Polar, Translation, \
		Scale, StandardColors, ImageTilePattern, ImageData, MaskGroup, \
		Arrow

from app.events.warn import INTERNAL, warn_tb, warn, USER
from app.io.load import GenericLoader, SketchLoadError, EmptyCompositeError
from app.Lib import units

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
			raise Exception('mismatch in unused data after compressed data (%u != %u)' % (len(decomp.unused_data), bytesatend))
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
		#if self.fourcc == 'DISP':
			#[bitmapoffset] = struct.unpack('<I',buf[offset+32:offset+36])
			#bitmapoffset = self.rawsize + 8 - bitmapoffset
			#bitmapoffset = struct.pack('>I', bitmapoffset)
			#self.image_buf = 'BM'+buf[offset+4:offset+7]+'\x00\x00\x00\x00'+bitmapoffset[2:3]+'\x00\x00'+buf[offset+10:offset+8+self.rawsize]
			#import PIL.Image,PIL.ImageTk, StringIO
			#self.image = PIL.Image.open(StringIO.StringIO(self.image_buf ))
			#self.image.load()
			#self.infocollector.image= PIL.ImageTk.PhotoImage(self.image)
		if self.fourcc == 'vrsn':
			[version] = struct.unpack('<H', self.data)
			self.infocollector.cdr_version=version/100
		if self.fourcc == 'fild':
			self.infocollector.fill_chunks.append(self)
		if self.fourcc == 'outl':
			self.infocollector.outl_chunks.append(self)
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
	
class BezierNode:	
	point1=None
	point2=None
	point3=None
	
class BezierCurve:	
	outlineIndex=''
	colorIndex=''
	paths = []
	
	def __init__(self, outlineIndex, colorIndex, paths):
		self.colorIndex=colorIndex
		self.outlineIndex=outlineIndex
		self.paths=paths
		
	
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
	obj_chunks=[]
	fill_chunks=[]
	outl_chunks=[]
	fill_data={}
	outl_data={}
	paths_heap=[]
	current_paths=[]
	outlineIndex=None
	colorIndex=None
	loda_type_func = None
	scale =.0002835
	loader=None
	trafo_list=[]
	
	def process_properties(self):
		self.loda_type_func = {0xa:self.loda_outl,0x14:self.loda_fild,0x1e:self.loda_coords}	
		for chunk in self.fill_chunks:
			self.process_fill(chunk)
		for chunk in self.outl_chunks:
			self.process_outline(chunk)		
		self.obj_chunks.reverse()	
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
				
	def check_trafo(self, chunk):
		pass
			
	def get_trafo(self, trfd):
		cdr_version=self.cdr_version
		
		ieeestart = 32
		if cdr_version == 13:
			ieeestart = 40
		if cdr_version == 5:
			ieeestart = 18

		[var0] = struct.unpack('<d', trfd.data[ieeestart:ieeestart+8]) 
		[var1] = struct.unpack('<d', trfd.data[ieeestart+8:ieeestart+8+8]) 
		[var2] = struct.unpack('<d', trfd.data[ieeestart+2*8:ieeestart+8+2*8]) 		
		[var3] = struct.unpack('<d', trfd.data[ieeestart+3*8:ieeestart+8+3*8]) 
		[var4] = struct.unpack('<d', trfd.data[ieeestart+4*8:ieeestart+8+4*8]) 
		[var5] = struct.unpack('<d', trfd.data[ieeestart+5*8:ieeestart+8+5*8]) 
		#print 'chunk no.:',trfd.number
		#print 'trafo: ', var4, var3,  var1, var0, var2, var5		
		return Trafo( var0, var3, var1, var4, var2, var5)
			
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
			else:
				pass
		
		if not self.current_paths.count==[]:
			self.paths_heap.append(BezierCurve(self.outlineIndex, self.colorIndex, self.current_paths))	
		self.current_paths=[]
		self.outlineIndex=None
		self.colorIndex=None
		
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

		
	def loda_fild(self,chunk,type,offset,version,trafo):
		self.colorIndex='%02X'%ord(chunk.data[offset])+'%02X'%ord(chunk.data[offset+1])+\
					'%02X'%ord(chunk.data[offset+2])+'%02X'%ord(chunk.data[offset+3])
		
	def loda_outl(self,chunk,type,offset,version,trafo):
		self.outlineIndex='%02X'%ord(chunk.data[offset])+'%02X'%ord(chunk.data[offset+1])+\
				'%02X'%ord(chunk.data[offset+2])+'%02X'%ord(chunk.data[offset+3])

			
	def process_outline(self, chunk):
		cdr_version=self.cdr_version
		outl = Outline()
		outl.outlineIndex='%02X'%ord(chunk.data[0]) + '%02X'%ord(chunk.data[1]) + '%02X'%ord(chunk.data[2]) + '%02X'%ord(chunk.data[3])

		ct_offset = 0x8
		lw_offset = 0xc
		lc_offset = 0x6
		offset = 0x1c	
			
		if cdr_version == 13:
			ct_offset = 0x1c
			lw_offset = 0x1e
			lc_offset = 0x1a
			offset = 0x28
		
		outl.caps=ord(chunk.data[lc_offset])
		outl.corner=ord(chunk.data[ct_offset])
		[line_width] = struct.unpack('<L',chunk.data[lw_offset:lw_offset+4])
		outl.width=line_width*self.scale
		
		clrmode = ord(chunk.data[offset+0x30])
		
		if clrmode == 9:
			outl.color=CreateCMYKColor(0, 0, 0, ord(chunk.data[offset+0x38]) /255.0)
		elif clrmode == 5:
			outl.color=CreateRGBColor(ord(chunk.data[offset+0x3a]) / 255.0, 
						   ord(chunk.data[offset+0x39])/ 255.0,
						   ord(chunk.data[offset+0x38]) / 255.0)
		elif clrmode == 4:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/100.0,
							ord(chunk.data[offset+0x39])/100.0,
							ord(chunk.data[offset+0x3a])/100.0, 0/100.0)
		elif clrmode == 2:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/100.0,
							ord(chunk.data[offset+0x39])/100.0,
							ord(chunk.data[offset+0x3a])/100.0,
							ord(chunk.data[offset+0x3b])/100.0)
		elif clrmode == 17:
			outl.color=CreateCMYKColor(ord(chunk.data[offset+0x38])/255.0,
							ord(chunk.data[offset+0x39])/255.0,
							ord(chunk.data[offset+0x3a])/255.0,
							ord(chunk.data[offset+0x3b])/255.0)
		elif clrmode == 20:
			outl.color=CreateCMYKColor(1.0,1.0,1.0,1.0)
		else:
			outl.color=None
			
		if outl.width==0.0002835:
			outl.color=None
		self.outl_data[outl.outlineIndex]=outl

	
	def process_fill(self, chunk):
		cdr_version=self.cdr_version
		fill_data=self.fill_data
		fild_pal_type = ('Transparent', 'Solid', 'Gradient')
		colorIndex='%02X'%ord(chunk.data[0]) + '%02X'%ord(chunk.data[1]) + '%02X'%ord(chunk.data[2]) + '%02X'%ord(chunk.data[3])
		pal = ord(chunk.data[4])
		if cdr_version == 13:
			pal = ord(chunk.data[0xc])		
		if	pal < 3:
			fild_type = fild_pal_type[pal]
		else:
			fild_type = 'Unknown (%X)'%pal					
		clr_offset = 0x8
		if cdr_version == 13:
			clr_offset = 0x1b
			
		if clr_offset < chunk.rawsize:			
			clrmode = ord(chunk.data[clr_offset])
			if fild_type == 'Solid':
				offset = 0x10
				if cdr_version == 13:
					offset =0x23
				if clrmode == 9:
					fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, ord(chunk.data[offset]) /255.0)
				elif clrmode == 5:
					fill_data[colorIndex]=CreateRGBColor(ord(chunk.data[offset+2]) / 255.0, 
								   ord(chunk.data[offset+1])/ 255.0,
								   ord(chunk.data[offset]) / 255.0)
				elif clrmode == 4:
					fill_data[colorIndex]=CreateCMYKColor(ord(chunk.data[offset])/100.0,
									ord(chunk.data[offset+1])/100.0,
									ord(chunk.data[offset+2])/100.0, 0/100.0)
				elif clrmode == 2:
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
				elif clrmode == 0x14:
					fill_data[colorIndex]=CreateCMYKColor(1,1,1,1)
				else:
					fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, .20)
			if fild_type == 'Transparent':
				fill_data[colorIndex]=None
			if fild_type == 'Gradient':
				fill_data[colorIndex]=CreateCMYKColor(0, 0, 0, .3)
	

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
		
	def Load(self):
		try:
			cdr = load_file(self.filename)
			
			self.document()
			self.layer('cdr_object', 1, 1, 0, 0, ('RGB',0,0,0))

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
			return self.object
		
		except RiffEOF:
			raise SketchLoadError(_("Unexpected problems in file parsing"))
		except:
			import traceback
			traceback.print_exc()
			raise
		
	def import_curves(self):
		for obj in self.info.paths_heap:
			if obj==1:
				self.begin_group()
			elif obj==0:
				self.end_group()
			else:
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
						if self.info.outl_data[obj.outlineIndex].color and self.info.outl_data[obj.outlineIndex].width>0.2268:
							style.line_pattern = SolidPattern(self.info.outl_data[obj.outlineIndex].color)
						else:
							style.line_pattern = EmptyPattern
						style.line_width = self.info.outl_data[obj.outlineIndex].width
						style.line_cap = self.info.outl_data[obj.outlineIndex].caps + 1
						style.line_join = self.info.outl_data[obj.outlineIndex].corner
					else:
						style.line_pattern = EmptyPattern
				else:
					style.line_pattern = EmptyPattern
					
				self.bezier(tuple(obj.paths))



			
