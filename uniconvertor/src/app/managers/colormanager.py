# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.
import os, app

from sk1libs.pycms import cmsOpenProfileFromFile,cmsCreateTransform,cmsDoTransform, \
	cmsCreateRGBProfile, cmsCreateCMYKProfile, cmsCreateLabProfile, cmsCreateGrayProfile, \
	cmsDoBitmapTransform, cmsDeleteTransform,cmsCloseProfile,TYPE_RGB_8,TYPE_CMYK_8, \
	INTENT_PERCEPTUAL,cmsFLAGS_NOTPRECALC,COLORB, INTENT_RELATIVE_COLORIMETRIC
			
class ColorManager:
	rgb_monitor=None
	cmyk_rgb=None
	rgb_cmyk=None
	cmyk_monitor=None
	
	hRGB=None
	hCMYK=None
	hMONITOR=None
	colors_pool=[]
	image_pool=[]
	
	def __init__(self):
		self.refresh_profiles()
		
	def add_to_pool(self,color):
		self.colors_pool.append(color)
		
	def add_to_image_pool(self,image):
		self.image_pool.append(image)
		
	def remove_from_pool(self,color):
		if color in self.colors_pool:
			self.colors_pool.remove(color)
		
	def remove_from_image_pool(self,image):
		if image in self.image_pool:
			self.image_pool.remove(image)
		
	def update(self):
		for color in self.colors_pool:
			color.update()
			
		for image in self.image_pool:
			image.update()
		
		
	def refresh_profiles(self):
		if app.config.preferences.user_rgb_profile and os.path.isfile(app.config.preferences.user_rgb_profile):
			rgb_file=app.config.user_rgb_profile
			self.hRGB   = cmsOpenProfileFromFile(rgb_file, "r")
		else:
			self.hRGB   = cmsCreateRGBProfile()
			
		if app.config.preferences.user_cmyk_profile and os.path.isfile(app.config.preferences.user_cmyk_profile):
			cmyk_file=app.config.preferences.user_cmyk_profile
			self.hCMYK  = cmsOpenProfileFromFile(cmyk_file, "r")
		else:
			self.hCMYK  = cmsCreateCMYKProfile()
			
		if app.config.preferences.user_monitor_profile and os.path.isfile(app.config.preferences.user_monitor_profile):
			monitor_file=app.config.preferences.user_monitor_profile
			self.hMONITOR  = cmsOpenProfileFromFile(cmyk_file, "r")
		else:
			self.hMONITOR  = cmsCreateRGBProfile()
	
		self.cmyk_rgb = cmsCreateTransform(self.hCMYK, 
								   TYPE_CMYK_8, 
								   self.hRGB, 
								   TYPE_RGB_8, 
								   INTENT_RELATIVE_COLORIMETRIC,
								   #INTENT_PERCEPTUAL, 
								   cmsFLAGS_NOTPRECALC)		
		
		self.rgb_cmyk = cmsCreateTransform(self.hRGB, 
								   TYPE_RGB_8,
								   self.hCMYK, 
								   TYPE_CMYK_8,  
								   INTENT_PERCEPTUAL, 
								   cmsFLAGS_NOTPRECALC)			
		
		self.rgb_monitor = cmsCreateTransform(self.hRGB, 
								   TYPE_RGB_8,
								   self.hRGB, 
								   TYPE_RGB_8,  
								   INTENT_PERCEPTUAL, 0)			
		
		self.cmyk_monitor = cmsCreateTransform(self.hCMYK, 
								   TYPE_CMYK_8,
								   self.hRGB, 
								   TYPE_RGB_8,  
								   INTENT_PERCEPTUAL, 
								   cmsFLAGS_NOTPRECALC)
		
	def processCMYK(self,c,m,y,k):
		CMYK = COLORB()
		CMYK[0] = int(round(c, 3)*255)
		CMYK[1] = int(round(m, 3)*255)
		CMYK[2] = int(round(y, 3)*255)
		CMYK[3] = int(round(k, 3)*255)
		
		outRGB = COLORB()
		outRGB[0] = 0
		outRGB[1] = 0
		outRGB[2] = 0	
		cmsDoTransform(self.cmyk_rgb, CMYK, outRGB, 1)
		
		return round(outRGB[0]/255.0, 3), round(outRGB[1]/255.0, 3), round(outRGB[2]/255.0, 3)
	
	def processRGB(self,r,g,b):
		RGB = COLORB()
		RGB[0] = int(round(r, 3)*255)
		RGB[1] = int(round(g, 3)*255)
		RGB[2] = int(round(b, 3)*255)
		
		outRGB = COLORB()
		outRGB[0] = 0
		outRGB[1] = 0
		outRGB[2] = 0		
		cmsDoTransform(self.rgb_monitor, RGB, outRGB, 1)
		
		return round(outRGB[0]/255.0, 3), round(outRGB[1]/255.0, 3), round(outRGB[2]/255.0, 3)

	def convertRGB(self,r,g,b):
		RGB = COLORB()
		RGB[0] = int(round(r, 3)*255)
		RGB[1] = int(round(g, 3)*255)
		RGB[2] = int(round(b, 3)*255)
		
		CMYK = COLORB()
		CMYK[0] = 0
		CMYK[1] = 0
		CMYK[2] = 0
		CMYK[3] = 0
		cmsDoTransform(self.rgb_cmyk, RGB, CMYK, 1)
		
		return round(CMYK[0]/255.0, 3), round(CMYK[1]/255.0, 3), round(CMYK[2]/255.0, 3), round(CMYK[3]/255.0, 3)

	def convertCMYK(self,c,m,y,k):
		CMYK = COLORB()
		CMYK[0] = int(round(c, 3)*255)
		CMYK[1] = int(round(m, 3)*255)
		CMYK[2] = int(round(y, 3)*255)
		CMYK[3] = int(round(k, 3)*255)
		
		outRGB = COLORB()
		outRGB[0] = 0
		outRGB[1] = 0
		outRGB[2] = 0		
		cmsDoTransform(self.cmyk_rgb, CMYK, outRGB, 1)
		
		return round(outRGB[0]/255.0, 3), round(outRGB[1]/255.0, 3), round(outRGB[2]/255.0, 3)
	
	def terminate(self):
		cmsDeleteTransform(self.cmyk_rgb)
		cmsDeleteTransform(self.rgb_cmyk)
		cmsDeleteTransform(self.rgb_monitor)
		cmsDeleteTransform(self.cmyk_monitor)
		cmsCloseProfile(self.hCMYK)
		cmsCloseProfile(self.hRGB)	
		cmsCloseProfile(self.hMONITOR)	
		
	def ImageRGBtoCMYK(self, image):
		return cmsDoBitmapTransform(self.rgb_cmyk, image, image.mode, TYPE_CMYK_8)
		
	def ImageCMYKtoRGB(self, image):
		return cmsDoBitmapTransform(self.cmyk_rgb, image, TYPE_CMYK_8, TYPE_RGB_8)		
		
		
		
		
		
		
		
		
		