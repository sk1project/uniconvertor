# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
#       Color Handling
#

from string import atoi

from app.events.warn import warn, INTERNAL, USER
from app._sketch import RGBColor
from app import config, _
import app, string

skvisual = None
CMYK = 'CMYK'
RGB = 'RGB'
colormanager=app.colormanager

def CreateRGBColor(r, g, b):
	return RGB_Color(round(r, 3), round(g, 3), round(b, 3))

def CreateRGBAColor(r, g, b, a):
	return RGB_Color(round(r, 3), round(g, 3), round(b, 3), round(a, 3))

def XRGBColor(s):
	# only understands the old x specification with two hex digits per
	# component. e.g. `#00FF00'
	if s[0] != '#':
		raise ValueError("Color %s doesn't start with a '#'" % s)
	r = atoi(s[1:3], 16) / 255.0
	g = atoi(s[3:5], 16) / 255.0
	b = atoi(s[5:7], 16) / 255.0
	return CreateRGBColor(r, g, b)

def CreateCMYKColor(c, m, y, k):
	return CMYK_Color(c, m, y, k)

def CreateCMYKAColor(c, m, y, k, a):
	return CMYK_Color(c, m, y, k, a)

def CreateSPOTColor(r,g,b,c,m,y,k,name,palette):
	return SPOT_Color(r,g,b,c,m,y,k, alpha=1, name=name, palette=palette)

def CreateSPOTAColor(r,g,b,c,m,y,k, alpha, name,palette):
	return SPOT_Color(r,g,b,c,m,y,k, alpha=alpha, name=name, palette=palette)

def CreateSPOT_RGBColor(r,g,b,name,palette):
	if app.config.preferences.use_cms:
		c,m,y,k = app.colormanager.convertRGB(r, g, b)
	else:
		c,m,y,k = rgb_to_cmyk(r, g, b)
	return SPOT_Color(r,g,b,c,m,y,k, alpha=1, name=name, palette=palette)

def CreateSPOT_CMYKColor(c,m,y,k,name,palette):
	if app.config.preferences.use_cms:
		r,g,b = app.colormanager.processCMYK(c,m,y,k)
	else:
		r,g,b = cmyk_to_rgb(c,m,y,k)
	return SPOT_Color(r,g,b,c,m,y,k, alpha=1, name=name, palette=palette)

def cmyk_to_rgb(c, m, y, k):
	r = round(1.0 - min(1.0, c + k), 3)
	g = round(1.0 - min(1.0, m + k), 3)
	b = round(1.0 - min(1.0, y + k), 3)
	return r, g, b
	
def rgb_to_tk((r, g, b)):
	return '#%04x%04x%04x' % (65535 * r, 65535 * g, 65535 * b)

def tk_to_rgb(tk):
	r=int(string.atoi(tk[1:3], 0x10))/ 255.0 
	g=int(string.atoi(tk[3:5], 0x10))/ 255.0 
	b=int(string.atoi(tk[5:], 0x10))/ 255.0	
	return r,g,b

def rgb_to_cmyk(r, g, b):
	c = 1.0 - r
	m = 1.0 - g
	y = 1.0 - b
	k = min(c, m, y)
	return c - k, m - k, y - k, k

def ParseSketchColor(v1, v2, v3):
	return RGB_Color(round(v1, 3), round(v2, 3), round(v3, 3))
	
def ParseSKColor(model, v1, v2, v3, v4=0, v5=0):
	if model=='CMYK':
		return CMYK_Color(v1, v2, v3, v4)
	if model=='CMYKA':
		return CMYK_Color(v1, v2, v3, v4, v5)
	if model=='RGB':
		return RGB_Color(round(v1, 3), round(v2, 3), round(v3, 3))
	if model=='RGBA':
		return RGB_Color(round(v1, 3), round(v2, 3), round(v3, 3), round(v4, 3))
	
class SK1_Color:	
	rgb=None
	rgba=None
	RGB_object=None
	
	def __init__(self):
		colormanager.add_to_pool(self)
		
	def __del__(self):
		if colormanager is not None:
			colormanager.remove_from_pool(self)
	
	def getScreenColor(self):
		pass
	
	def RGB(self):
		return self.RGB_object
	
	def cRGB(self):
		return self.rgb
	
	def cRGBA(self):
		return self.rgba
	
	def update(self):
		rgb=self.getScreenColor()
		self.RGB_object=rgb
		self.rgb=(rgb.red, rgb.green, rgb.blue)
		self.rgba=(rgb.red, rgb.green, rgb.blue, self.alpha)
		
	def Blend(self, color, frac1, frac2):
		if self.model==color.model==CMYK:
			return self.blend_cmyka(color, frac1, frac2)
		if self.model==color.model==RGB:
			return self.blend_rgba(color, frac1, frac2)		
		if app.config.preferences.color_blending_rule:		
			return self.blend_cmyka(color, frac1, frac2)
		else:
			return self.blend_rgba(color, frac1, frac2)
			
	def blend_cmyka(self, color, frac1, frac2):
		c1,m1,y1,k1=self.getCMYK()
		c2,m2,y2,k2=color.getCMYK()			
		return CMYK_Color(c1*frac1+c2*frac2,
						 m1*frac1+m2*frac2, 
						 y1*frac1+y2*frac2, 
						 k1*frac1+k2*frac2, 
						 self.alpha*frac1+color.alpha*frac2)
		
	def blend_rgba(self, color, frac1, frac2):
		r1,g1,b1 = self.getRGB()
		r2,g2,b2 = color.getRGB()
		return RGB_Color(r1*frac1+r2*frac2, 
						g1*frac1+g2*frac2, 
						b1*frac1+b2*frac2, 
						self.alpha*frac1+color.alpha*frac2)		
		
class RGB_Color(SK1_Color):
	
	def __init__(self, r, g, b, alpha=1, name='Not defined'):
		SK1_Color.__init__(self)		
		self.model = 'RGB'
		self.red=r
		self.green=g
		self.blue=b
		self.alpha=alpha
		self.name=name
		self.update()		
	
	def getCMYK(self):
		if app.config.preferences.use_cms:
			c,m,y,k = app.colormanager.convertRGB(self.red, self.green, self.blue)
		else:
			c,m,y,k = rgb_to_cmyk(self.red, self.green, self.blue)
		return c,m,y,k
	
	def getRGB(self):
		if app.config.preferences.use_cms:
			if app.config.preferences.simulate_printer:
				c,m,y,k = app.colormanager.convertRGB(self.red, self.green, self.blue)
				r,g,b = app.colormanager.processCMYK(c,m,y,k)                       
				return r, g, b
			else:
				r,g,b = app.colormanager.processRGB(self.red, self.green, self.blue)
				return r, g, b
		else:
			return self.red, self.green, self.blue
	
	def getScreenColor(self):
		if app.config.preferences.use_cms:
			if app.config.preferences.simulate_printer:
				c,m,y,k = app.colormanager.convertRGB(self.red, self.green, self.blue)
				r,g,b = app.colormanager.processCMYK(c,m,y,k)                       
				return RGBColor(r, g, b)
			else:
				r,g,b = app.colormanager.processRGB(self.red, self.green, self.blue)
				return RGBColor(r, g, b)
		else:
			return RGBColor(self.red, self.green, self.blue)
	
	def toString(self):
		R='R-'+str(int(round(self.red*255, 0)))
		G=' G-'+str(int(round(self.green*255, 0)))
		B=' B-'+str(int(round(self.blue*255, 0)))
		return R+G+B
			
	def toSave(self):
		R= str(round(self.red, 5))+','
		G= str(round(self.green, 5))+','
		B= str(round(self.blue, 5))
		result='"'+self.model+'",'+R+G+B
		if self.alpha<1: result += ','+ str(round(self.alpha, 5))
		return '('+result+')'

class CMYK_Color(SK1_Color):
	
	def __init__(self, c, m, y, k, alpha=1, name='Not defined'):
		SK1_Color.__init__(self)		
		self.model = 'CMYK'
		self.c=c
		self.m=m
		self.y=y
		self.k=k
		self.alpha=alpha
		self.name=name
		self.update()	
		
	def getCMYK(self):
		return self.c, self.m, self.y, self.k
	
	def getRGB(self):
		if app.config.preferences.use_cms:
			r,g,b = app.colormanager.processCMYK(self.c,self.m,self.y,self.k)
		else:
			r,g,b = cmyk_to_rgb(self.c,self.m,self.y,self.k)				
		return r,g,b
	
	def getScreenColor(self):
		if app.config.preferences.use_cms:
			r,g,b = app.colormanager.processCMYK(self.c,self.m,self.y,self.k)
		else:
			r,g,b = cmyk_to_rgb(self.c,self.m,self.y,self.k)				
		return RGBColor(r, g, b)
	
	def toString(self):
		C='C-'+str(int(round(self.c, 2)*100))+'% '
		M='M-'+str(int(round(self.m, 2)*100))+'% '
		Y='Y-'+str(int(round(self.y, 2)*100))+'% '
		K='K-'+str(int(round(self.k, 2)*100))+'%'
		return C+M+Y+K
		
	def toSave(self):
		C= str(round(self.c, 5))+','
		M= str(round(self.m, 5))+','
		Y= str(round(self.y, 5))+','
		K= str(round(self.k, 5))
		result='"'+self.model+'",'+C+M+Y+K
		if self.alpha<1: result += ','+ str(round(self.alpha, 5))
		return '('+result+')'
	
class SPOT_Color(SK1_Color):
	
	def __init__(self, r, g, b, c, m, y, k, alpha=1, name='Not defined', palette='Unknown'):
		SK1_Color.__init__(self)		
		self.model = 'SPOT'
		self.r=r
		self.g=g
		self.b=b
		self.c=c
		self.m=m
		self.y=y
		self.k=k
		self.alpha=alpha
		self.name=name
		self.palette = palette
		self.update()
		
	def getCMYK(self):
		return self.c, self.m, self.y, self.k
	
	def getRGB(self):
		if app.config.preferences.use_cms:
			if app.config.preferences.simulate_printer:
				r,g,b = app.colormanager.processCMYK(c,m,y,k)                       
				return r, g, b
			else:
				return self.r, self.g, self.b
		else:
			return self.r, self.g, self.b
	
	def getScreenColor(self):
		if app.config.preferences.use_cms:
			if app.config.preferences.simulate_printer:
				r,g,b = app.colormanager.processCMYK(c,m,y,k)                       
				return RGBColor(r, g, b)
			else:
				return RGBColor(self.r, self.g, self.b)
		else:
			return RGBColor(self.r, self.g, self.b)
	
	def toString(self):
		return self.name
		
	def toSave(self):
		R= str(round(self.r, 5))+','
		G= str(round(self.g, 5))+','
		B= str(round(self.b, 5))+','
		C= str(round(self.c, 5))+','
		M= str(round(self.m, 5))+','
		Y= str(round(self.y, 5))+','
		K= str(round(self.k, 5))
		
		result='"'+self.model+'",'+self.palette+'","'+self.name+'",'+R+G+B+C+M+Y+K
		if self.alpha<1: result += ','+ str(round(self.alpha, 5))
		return '('+result+')'

	
class Registration_Black(SPOT_Color):
	
	def __init__(self, r=0, g=0, b=0, c=1, m=1, y=1, k=1, alpha=1, name='All', palette='Unknown'):
		SPOT_Color.__init__(self,r, g, b, c, m, y, k, alpha, name, palette)
		
	def toString(self):
		return _('Registration Black (')+self.name + ')'
		
#
#       some standard colors.
#

class StandardColors:
	black   = CreateRGBColor(0.0, 0.0, 0.0)
	darkgray        = CreateRGBColor(0.25, 0.25, 0.25)
	gray    = CreateRGBColor(0.5, 0.5, 0.5)
	lightgray       = CreateRGBColor(0.75, 0.75, 0.75)
	white   = CreateRGBColor(1.0, 1.0, 1.0)
	red             = CreateRGBColor(1.0, 0.0, 0.0)
	green   = CreateRGBColor(0.0, 1.0, 0.0)
	blue    = CreateRGBColor(0.0, 0.0, 1.0)
	cyan    = CreateRGBColor(0.0, 1.0, 1.0)
	magenta = CreateRGBColor(1.0, 0.0, 1.0)
	yellow  = CreateRGBColor(1.0, 1.0, 0.0)

class StandardCMYKColors:
	black   = CreateCMYKColor(0.0, 0.0, 0.0, 1.0)
	darkgray        = CreateCMYKColor(0.0, 0.0, 0.0, 0.75)
	gray    = CreateCMYKColor(0.0, 0.0, 0.0, 0.5)
	lightgray       = CreateCMYKColor(0.0, 0.0, 0.0, 0.25)
	white   = CreateCMYKColor(0.0, 0.0, 0.0, 0.0)
	red             = CreateCMYKColor(0.0, 1.0, 1.0, 0.0)
	green   = CreateCMYKColor(1.0, 0.0, 1.0, 0.0)
	blue    = CreateCMYKColor(1.0, 1.0, 0.0, 0.0)
	cyan    = CreateCMYKColor(1.0, 0.0, 0.0, 0.0)
	magenta = CreateCMYKColor(0.0, 1.0, 0.0, 0.0)
	yellow  = CreateCMYKColor(0.0, 0.0, 1.0, 0.0)

#
#       For 8-bit displays:
#

def float_to_x(float):
	return int(int(float * 63) / 63.0 * 65535)

def fill_colormap(cmap):
	max = 65535
	colors = []
	color_idx = []
	failed = 0
	
	shades_r, shades_g, shades_b, shades_gray = config.preferences.color_cube
	max_r = shades_r - 1
	max_g = shades_g - 1
	max_b = shades_b - 1

	for red in range(shades_r):
		red = float_to_x(red / float(max_r))
		for green in range(shades_g):
			green = float_to_x(green / float(max_g))
			for blue in range(shades_b):
				blue = float_to_x(blue / float(max_b))
				colors.append((red, green, blue))
	for i in range(shades_gray):
		value = int((i / float(shades_gray - 1)) * max)
		colors.append((value, value, value))

	for red, green, blue in colors:
		try:
			ret = cmap.AllocColor(red, green, blue)
			color_idx.append(ret[0])
		except:
			color_idx.append(None)
			failed = 1

	if failed:
		warn(USER,
				_("I can't alloc all needed colors. I'll use a private colormap"))
		warn(INTERNAL, "allocated colors without private colormap: %d",
				len(filter(lambda i: i is None, color_idx)))
		if config.preferences.reduce_color_flashing:
			#print 'reduce color flashing'
			cmap = cmap.CopyColormapAndFree()
			for idx in range(len(color_idx)):
				if color_idx[idx] is None:
					color_idx[idx] = apply(cmap.AllocColor, colors[idx])[0]
		else:
			#print "don't reduce color flashing"
			cmap = cmap.CopyColormapAndFree()
			cmap.FreeColors(filter(lambda i: i is not None, color_idx), 0)
			color_idx = []
			for red, green, blue in colors:
				color_idx.append(cmap.AllocColor(red, green, blue)[0])
				
	return cmap, color_idx

_init_from_widget_done = 0
global_colormap = None
def InitFromWidget(tkwin, root = None):
	_init_from_widget_done = 1
