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
from app._sketch import RGBColor#, XVisual
from app import config, _
import app

skvisual = None
CMYK = 'CMYK'
RGB = 'RGB'

def CreateRGBColor(r, g, b):
	return RGB_Color(round(r, 3), round(g, 3), round(b, 3))

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
	#r,g,b = cmyk_to_rgb(c, m, y, k)
	return CMYK_Color(c, m, y, k)

def cmyk_to_rgb(c, m, y, k):
	r = round(1.0 - min(1.0, c + k), 3)
	g = round(1.0 - min(1.0, m + k), 3)
	b = round(1.0 - min(1.0, y + k), 3)
	return r, g, b
	
def rgb_to_tk((r, g, b)):
	return '#%04x%04x%04x' % (65535 * r, 65535 * g, 65535 * b)
	
# def rgb2cmyk(r,g,b):
#       r = 1.0 - min(1.0, c + k)
#       g = 1.0 - min(1.0, m + k)
#       b = 1.0 - min(1.0, y + k)
#       return c, m, y, k

def ParseSKColor(model, v1, v2, v3, v4=0, v5=0):
	if model=='CMYK':
		r,g,b = cmyk_to_rgb(v1, v2, v3, v4)
		return CMYK_Color(v1, v2, v3, v4)
	if model=='RGB':
		return RGB_Color(round(v1, 3), round(v2, 3), round(v3, 3))
	

class RGB_Color:
	
	def __init__(self, r, g, b, alpha=0, name='Not defined'):		
		self.model = 'RGB'
		self.red=r
		self.green=g
		self.blue=b
		self.alpha=alpha
		self.name=name
	
	def RGB(self):
		return self.getScreenColor()
	
	def cRGB(self):
		rgb=self.getScreenColor()
		return (rgb.red, rgb.green, rgb.blue)
	
	def cRGBA(self):
		rgb=self.getScreenColor()
		return (rgb.red, rgb.green, rgb.blue, self.alpha)
	
	def getCMYK(self):
		c,m,y,k = app.colormanager.convertRGB(self.red, self.green, self.blue)
		return c,m,y,k
	
	def getScreenColor(self):
		if app.config.preferences.use_cms:
			if app.config.preferences.simulate_printer:
				c,m,y,k = app.colormanager.convertRGB(self.red, self.green, self.blue)
				r,g,b = app.colormanager.processCMYK(c,m,y,k)                       
				return RGBColor(r, g, b)
			else:
				r,g,b = app.colormanager.processRGB(self.red, self.green, self.blue)
				return RGBColor(self.red, self.green, self.blue)
		else:
			return RGBColor(self.red, self.green, self.blue)
	
	def toString(self):
		R='R-'+str(int(round(self.red*255, 0)))
		G=' G-'+str(int(round(self.green*255, 0)))
		B=' B-'+str(int(round(self.blue*255, 0)))
		return R+G+B
			
	def toSave(self):
		R= str(round(self.red, 3))+','
		G= str(round(self.green, 3))+','
		B= str(round(self.blue, 3))
		return '("'+self.model+'",'+R+G+B+')'

class CMYK_Color:
	
	def __init__(self, c, m, y, k, alpha=0, name='Not defined'):		
		self.model = 'CMYK'
		self.c=c
		self.m=m
		self.y=y
		self.k=k
		self.alpha=alpha
		self.name=name
		
	def getCMYK(self):
		return self.c, self.m, self.y, self.k
	
	def RGB(self):
		return self.getScreenColor()
	
	def cRGB(self):
		rgb=self.getScreenColor()
		return (rgb.red, rgb.green, rgb.blue)
	
	def cRGBA(self):
		rgb=self.getScreenColor()
		return (rgb.red, rgb.green, rgb.blue, self.alpha)
	
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
		C= str(round(self.c, 3))+','
		M= str(round(self.m, 3))+','
		Y= str(round(self.y, 3))+','
		K= str(round(self.k, 3))
		return '("'+self.model+'",'+C+M+Y+K+')'

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
	global _init_from_widget_done, skvisual
	if _init_from_widget_done:
		return
	if root:
		visual = root.winfo_visual()
		if visual == 'truecolor':
			skvisual = XVisual(tkwin.c_display(), tkwin.c_visual())
			#skvisual.set_gamma(config.preferences.screen_gamma)
			alloc_function = skvisual.get_pixel
		if visual == 'pseudocolor' and root.winfo_depth() == 8:
			global global_colormap
			cmap = tkwin.colormap()
			newcmap, idxs = fill_colormap(cmap)
			if newcmap != cmap:
				cmap = newcmap
				tkwin.SetColormap(cmap)
			shades_r, shades_g, shades_b, shades_gray \
						= config.preferences.color_cube
			skvisual = XVisual(tkwin.c_display(), tkwin.c_visual(),
								(shades_r, shades_g, shades_b, shades_gray, idxs))
			global_colormap = cmap
	_init_from_widget_done = 1
