# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
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
#       Font management...
#

import os, re, operator, sys
from string import split, strip, atoi, atof, lower, translate, maketrans


import ft2

from app import _, config, Point, Scale, Subscribe, CreatePath, SKCache, ContAngle, ContSmooth

from app.conf import const

from sk1libs.utils.fs import find_in_path, find_files_in_path, get_files_tree, gethome, get_system_fontdirs


fontlist = []
fontmap = {}
svg_fontmap = {}
fontfamily_map = {}
ps_to_filename = {}
font_cache = SKCache()

def make_family_to_fonts():
	families = {}
	for item in fontlist:
		family = item[1]
		fontname = item[0]
		if families.has_key(family):
			families[family] = families[family] + (fontname,)
		else:
			families[family] = (fontname,)
	return families

#===============NEW FONT ENGINE IMPLEMENTATION===========================
# font types: PS1 - Postscript Type1; TTF - TrueType; OTF - OpenType
# Currently TTF support only

# Fontlist definition (list of tuples):
#-------------------
#PS name
#family name
#style
#xlfd name
#encoding
#filename
#bold -flag
#italic -flag

freetype_lib = ft2.Library()

def scan_fonts_dirs():
	fontfile_list=[]	

	paths=get_system_fontdirs()
	for path in get_system_fontdirs():
		for ext in ['ttf','otf','TTF','OTF']:
			fontfile_list+=get_files_tree(path,ext) 	
				
	if not len(fontfile_list):
		fallback_path = os.path.join(__path__[0],'fallback_fonts')
		for ext in ['ttf','otf','TTF','OTF']:
			fontfile_list+=get_files_tree(fallback_path,ext)	
	
	
	for fontfile in fontfile_list:
		try:
			f = open(fontfile, 'rb')
			face = ft2.Face(freetype_lib, f, 0)
		except:
			sys.stderr.write("error opening file %s\n" % (fontfile))
			continue
		#Check for Unicode support into font
		is_unicode=0
		for index in range(face.num_charmaps):
			cm = ft2.CharMap(face, index)
			if cm.encoding_as_string == "unic":
				is_unicode = 1
				break
		if is_unicode:			
			ps_name=face.getPostscriptName()
			info=(ps_name,
					face.family_name,
					face.style_name,
					'',
					'UTF8',
					fontfile,
					face.style_flags & ft2.FT_STYLE_FLAG_BOLD,
					face.style_flags & ft2.FT_STYLE_FLAG_ITALIC)
			fontlist.append(info)
			fontmap[ps_name] = (face.family_name,
					face.style_name,
					'',
					'UTF8',
					fontfile,
					face.style_flags & ft2.FT_STYLE_FLAG_BOLD,
					face.style_flags & ft2.FT_STYLE_FLAG_ITALIC)
	
			filename = (fontfile,)
			if ps_to_filename.has_key(ps_name):
				filename = ps_to_filename[ps_name] + filename
			ps_to_filename[ps_name] = filename
		
		f.close()
	for item in fontmap.keys():
		fontfamily_map[fontmap[item][0]]=item
		if fontmap[item][1] in ["Regular", "Normal", "Book"]:
			svg_fontmap[fontmap[item][0]]=item
		else:
			svg_fontmap[fontmap[item][0]+" "+fontmap[item][1]]=item
		
	
_warned_about_font = {}

def GetFont(fontname):
	if not len(fontlist):
		scan_fonts_dirs()
		
	if font_cache.has_key(fontname):
		return font_cache[fontname]
	if not fontmap.has_key(fontname):
		
		#Search in SVG style fontmap
		if svg_fontmap.has_key(fontname):
			return Font(svg_fontmap[fontname])
		
		#Search in font family map
		name=''
		for family in fontfamily_map.keys():
			if fontname.count(family):
				name=fontfamily_map[family]
				break
		if name:
			return Font(name)				
			
		if not _warned_about_font.get(fontname):
			_warned_about_font[fontname] = 1
		if fontname != config.preferences.fallback_font:
			return GetFont(config.preferences.fallback_font)
		else:
			names = fontmap.keys()
			names.sort()
			return GetFont(names[0])
		raise ValueError, 'Cannot find font %s.' % fontname
	return Font(fontname)

default_encoding = 'utf-8'
resolution=72  

class Font:
	def __init__(self, name):
		self.name = name
		info = fontmap[name]
		family, font_attrs, xlfd_start, encoding_name, fontfile, bold, italic = info
		self.bold=bold
		self.italic=italic
		self.fontfile=fontfile
		self.family = family
		self.font_attrs = font_attrs
		self.xlfd_start = lower(xlfd_start)
		self.encoding_name = encoding_name
		self.metric = None
		self.encoding = self.encoding_name
		self.outlines = None
		self.face = None
		self.enc_vector=None
		self.ref_count = 0
		font_cache[self.name] = self
		self.fontstream=None
		self.fontsize=10
		self.use_unicode = 0
		
		self.init_face()
		self.face.setCharSize(10240, 10240, resolution, resolution)

	def __del__(self):
		if font_cache.has_key(self.name):
			del font_cache[self.name]

	def __repr__(self):
		return "<Font %s>" % self.name

	def PostScriptName(self):
		return self.name
	
	def init_face(self):
		if not self.face:
			if not self.fontstream:
				f = open(self.fontfile, 'rb')
				import StringIO
				s = f.read()
				f.close()
				self.fontstream= StringIO.StringIO(s)
						
			self.face=ft2.Face(freetype_lib, self.fontstream, 0)			
			
			for index in range(self.face.num_charmaps):
				cm = ft2.CharMap(self.face, index)
				if cm.encoding_as_string == "unic":
					self.use_unicode = 1
					self.face.setCharMap(cm)
					break
			
			if not self.use_unicode:
				self.face.setCharMap(ft2.CharMap(self.face, 0, 0))
			self.enc_vector = self.face.encodingVector()

################
	def TextBoundingBox(self, text, size, prop):
		# Return the bounding rectangle of TEXT when set in this font
		# with a size of SIZE. The coordinates of the rectangle are
		# relative to the origin of the first character.

		posx = posy = posx_max = posy_max= 0
		lastIndex = 0
		text_xmin = text_ymin = 0
		text_xmax = text_ymax = 0		
		
		fheight=self.getFontHeight(prop)*5
		lines=split(text, '\n')
		adv=0
		tab=1
		align_offset=0
		for line in lines:
			posx = 0
			for c in line:
				if c=='\t':
					c=' ';tab=3
				else:
					tab=1
				try:
					thisIndex = self.enc_vector[ord(c)]
				except:
					thisIndex = self.enc_vector[ord('?')]
				glyph = ft2.Glyph(self.face, thisIndex, 0)
				kerning = self.face.getKerning(lastIndex, thisIndex, 0)
				posx += kerning[0] << 10
				posy += kerning[1] << 10
				if c==' ':
					adv= glyph.advance[0]*prop.chargap*prop.wordgap*tab
				else:
					adv= glyph.advance[0]*prop.chargap
				posx+=adv
				posy += glyph.advance[1]
				lastIndex = thisIndex
				(gl_xmin, gl_ymin, gl_xmax, gl_ymax) = glyph.getCBox(ft2.ft_glyph_bbox_subpixels)
				gl_xmin += int(posx) >> 10
				gl_ymin += int(posy) >> 10 
				gl_xmax += int(posx) >> 10
				gl_ymax += int(posy) >> 10
				text_xmin = min(text_xmin, gl_xmin)
				text_ymin = min(text_ymin, gl_ymin)
				text_xmax = max(text_xmax, gl_xmax)
				text_ymax = max(text_ymax, gl_ymax)
			align_offset=min(self.getAlignOffset(line,prop),align_offset)
			posx_max = max(posx_max,posx)
			posy_max -= fheight
		posy_max =posy_max + fheight + text_ymin
		x1=text_xmin*size/10240.0
		y1=text_ymax*size/10240.0
		x2=posx_max*size/10240000.0
		y2=posy_max*size/10240.0
		if prop.align:
			if prop.align==const.ALIGN_RIGHT:
				return (-x2, y1, x1, y2)
			if prop.align==const.ALIGN_CENTER:
				return (x1-x2/2, y1, x2/2, y2)
		else:
			return (x1, y1, x2, y2)


	def TextCoordBox(self, text, size, prop):
		# Return the coord rectangle of TEXT when set in this font with
		# a size of SIZE. The coordinates of the rectangle are relative
		# to the origin of the first character.
		return self.TextBoundingBox(text, size, prop)

################
	def TextCaretData(self, text, pos, size, prop):
		fheight=self.getFontHeight(prop)*5*size/10240.0
		vofset=-(len(split(text[0:pos], '\n'))-1)*fheight
		lly=vofset-fheight*1/4*.75
		ury=vofset+fheight*3/4
		
		line=split(text, '\n')[len(split(text[0:pos], '\n'))-1]
		x1,y1,x2,y2=self.TextBoundingBox(line,size, prop)
		align_offset=x1-x2
		
		fragment=split(text[0:pos], '\n')[-1]
		x1,y1,x2,y2=self.TextBoundingBox(fragment,size, prop)
		if prop.align:
			if prop.align==const.ALIGN_RIGHT:
				x=align_offset-x1
			if prop.align==const.ALIGN_CENTER:
				x=x2*2+align_offset/2
		else:
			x=x2	
		up = ury - lly
		return Point(x, lly), Point(0, up)

################
	def TypesetText(self, text, prop):					
		return self.cacl_typeset(text, prop)[0:-1]

	def IsPrintable(self, char):
		return 1

################	
	# face.getMetrics() returns tuple:	
	#(x_ppem, y_ppem, x_scale, y_scale, 
	# ascender, descender, height, max_advance)
	def getFontHeight(self,prop):
		return (abs(self.face.getMetrics()[5])+abs(self.face.getMetrics()[6]))*prop.linegap/5.583
#		return abs(self.face.getMetrics()[7]/5.35)*prop.linegap
	
	def getAlignOffset(self,line,prop):
		if prop.align:
			typeset=self.cacl_typeset(line, prop,1)
			x1,y1=typeset[0]
			x2,y2=typeset[-1]
			if prop.align==const.ALIGN_RIGHT:
				return x1-x2
			if prop.align==const.ALIGN_CENTER:
				return (x1-x2)/2	
		else:
			return 0
		
	def cacl_typeset(self, text, prop, noalign=0): 
		posx = 0
		posy = 0
		lastIndex = 0
		result=[]
		tab=1
		
		fheight=self.getFontHeight(prop)*5
		voffset=0
		lines=split(text, '\n')
		for line in lines:
			if noalign:
				align_offset=0
			else:
				align_offset=self.getAlignOffset(line,prop)
			result.append(Point(align_offset,voffset/10240.0))
			for c in line:
				if c=='\t':
					c=' ';tab=3
				else:
					tab=1
				try:
					thisIndex = self.enc_vector[ord(c)]
				except:
					thisIndex = self.enc_vector[ord('?')]
				glyph = ft2.Glyph(self.face, thisIndex, 0)
				kerning = self.face.getKerning(lastIndex, thisIndex, 0)
				posx += kerning[0]
				posy += kerning[1]
				if c==' ':
					posx += glyph.advance[0]*prop.chargap*prop.wordgap*tab/1000
				else:
					posx += glyph.advance[0]*prop.chargap/1000
				posy += glyph.advance[1]/1000
				lastIndex = thisIndex
				result.append(Point(posx/10240.0+align_offset,voffset/10240.0))				
			voffset-=fheight
			posx = 0
		return result
					
################		
	def GetPaths(self, text, prop):
		# convert glyph data into bezier polygons	
		paths = []
		fheight=self.getFontHeight(prop)
		voffset=0
		tab=1
		lastIndex=0
		lines=split(text, '\n')
		for line in lines:
			offset = c = 0
			align_offset=self.getAlignOffset(line,prop)
			for c in line:
				if c=='\t':
					c=' ';tab=3
				else:
					tab=1		
				try:
					thisIndex = self.enc_vector[ord(c)]
				except:
					thisIndex = self.enc_vector[ord('?')]
				glyph = ft2.Glyph(self.face, thisIndex, 1)
				kerning = self.face.getKerning(lastIndex, thisIndex, 0)
				lastIndex = thisIndex
				offset += kerning[0]  / 4.0
				voffset += kerning[1] / 4.0
				for contour in glyph.outline:
					# rotate contour so that it begins with an onpoint
					x, y, onpoint = contour[0]
					if onpoint:
						for j in range(1, len(contour)):
							x, y, onpoint = contour[j]
							if onpoint:
								contour = contour[j:] + contour[:j]
								break
					else:
						print "unsupported type of contour (no onpoint)"
					# create a sK1 path object
					path = CreatePath()
					j = 0
					npoints = len(contour)
					x, y, onpoint = contour[0]
					last_point = Point(x, y)
					while j <= npoints:
						if j == npoints:
							x, y, onpoint = contour[0]
						else:
							x, y, onpoint = contour[j]
						point = Point(x, y)
						j = j + 1
						if onpoint:
							path.AppendLine(point)
							last_point = point
						else:
							c1 = last_point + (point - last_point) * 2.0 / 3.0
							x, y, onpoint = contour[j % npoints]
							if onpoint:
								j = j + 1
								cont = ContAngle
							else:
								x = point.x + (x - point.x) * 0.5
								y = point.y + (y - point.y) * 0.5
								cont = ContSmooth
							last_point = Point(x, y)
							c2 = last_point + (point - last_point) * 2.0 / 3.0
							path.AppendBezier(c1, c2, last_point, cont)
					path.ClosePath()
					path.Translate(offset, voffset)
					path.Transform(Scale(0.5/1024.0))
					path.Translate(align_offset, 0)
					paths.append(path)
				if c==' ':
					offset = offset + glyph.advance[0]*prop.chargap*prop.wordgap*tab/1000
				else:
					offset = offset + glyph.advance[0]*prop.chargap/1000
			voffset-=fheight
		return tuple(paths)

	def GetOutline(self, char):		
		return self.GetPaths(char)

	def FontFileName(self):
		return font_file_name(self.PostScriptName())

#
#       Initialization on import
#

Subscribe(const.INITIALIZE, scan_fonts_dirs)
