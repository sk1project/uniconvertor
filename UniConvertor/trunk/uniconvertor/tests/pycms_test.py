#!/usr/bin/python

# -*- coding: utf-8 -*-

# pycms - small package which provides binding to LittleCMS library.

# Copyright (c) 2009 by Igor E.Novikov
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU Library General Public
#License as published by the Free Software Foundation; either
#version 2 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#Library General Public License for more details.
#
#You should have received a copy of the GNU Library General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA


import unittest
from sk1libs.imaging import Image
from sk1libs import pycms

class TestPycmsFunctions(unittest.TestCase):

	def setUp(self):
		self.inProfile=pycms.cmsOpenProfileFromFile('pycms_data/sRGB.icm')	
		self.outProfile=pycms.cmsOpenProfileFromFile('pycms_data/GenericCMYK.icm')
		self.transform = pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGBA_8,
											 self.outProfile, pycms.TYPE_CMYK_8,
											 pycms.INTENT_PERCEPTUAL,
											 pycms.cmsFLAGS_NOTPRECALC)
		self.transform2 = pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGBA_8,
											 self.outProfile, pycms.TYPE_CMYK_8,
											 pycms.INTENT_PERCEPTUAL, 0)

	def test01_OpenProfile(self):
		self.assertNotEqual(None, self.inProfile)
		self.assertNotEqual(None, self.outProfile)
		self.assertNotEqual(None, pycms.cmsCreateRGBProfile())
		self.assertNotEqual(None, pycms.cmsCreateCMYKProfile())
		self.assertNotEqual(None, pycms.cmsCreateLabProfile())
		self.assertNotEqual(None, pycms.cmsCreateGrayProfile())

	def test02_OpenInvalidProfile(self):
		try:
			pycms.cmsOpenProfileFromFile('pycms_data/empty.icm')
		except pycms.pycmsError:
			return
		self.fail()

	def test03_OpenAbsentProfile(self):
		try:
			pycms.cmsOpenProfileFromFile('pycms_data/xxx.icm')
		except pycms.pycmsError:
			return
		self.fail()
		
	def test04_CreateTransform(self):	
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.outProfile, pycms.TYPE_CMYK_8))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGBA_8, 
														self.outProfile, pycms.TYPE_CMYK_8))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.outProfile, pycms.TYPE_CMYK_8, 
														self.inProfile, pycms.TYPE_RGBA_8))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.outProfile, pycms.TYPE_CMYK_8, 
														self.inProfile, pycms.TYPE_RGB_8))
		
	def test05_CreateTransformWithCustomIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_PERCEPTUAL))		
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_RELATIVE_COLORIMETRIC))		
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_SATURATION))		
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_ABSOLUTE_COLORIMETRIC))
		
	def test06_CreateTransformWithCustomFlags(self):
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_PERCEPTUAL,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_GAMUTCHECK))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_PERCEPTUAL,
														pycms.cmsFLAGS_PRESERVEBLACK |pycms.cmsFLAGS_BLACKPOINTCOMPENSATION))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_PERCEPTUAL,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_HIGHRESPRECALC))
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, self.outProfile, 
														pycms.TYPE_CMYK_8, pycms.INTENT_PERCEPTUAL,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_LOWRESPRECALC))
		
	def test07_CreateTransformWithInvalidIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.outProfile, pycms.TYPE_CMYK_8, 3))
		try:
			pycms.cmsCreateTransform(self.inProfile, pycms.TYPE_RGB_8, 
									self.outProfile, pycms.TYPE_CMYK_8, 4)
		except pycms.pycmsError:
			return
		self.fail()	
		
	def test08_CreateProofingTransform(self):	
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGBA_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGBA_8,		
														self.outProfile))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGBA_8, 
														self.inProfile, pycms.TYPE_RGBA_8,		
														self.outProfile))
	def test09_CreateProofingTransformWithCustomIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_RELATIVE_COLORIMETRIC))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_SATURATION))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_ABSOLUTE_COLORIMETRIC))			

	def test10_CreateProofingTransformWithCustomProofingIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_PERCEPTUAL))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_RELATIVE_COLORIMETRIC))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_SATURATION))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_ABSOLUTE_COLORIMETRIC))

	def test11_CreateProofingTransformWithCustomFlags(self):
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_RELATIVE_COLORIMETRIC,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_GAMUTCHECK))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_RELATIVE_COLORIMETRIC,
														pycms.cmsFLAGS_PRESERVEBLACK |pycms.cmsFLAGS_BLACKPOINTCOMPENSATION))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_RELATIVE_COLORIMETRIC,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_HIGHRESPRECALC))
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile,pycms.INTENT_PERCEPTUAL,pycms.INTENT_RELATIVE_COLORIMETRIC,
														pycms.cmsFLAGS_NOTPRECALC |pycms.cmsFLAGS_LOWRESPRECALC))

	def test12_CreateProofingTransformWithInvalidIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile, 3))
		try:
			pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile, 4)
		except pycms.pycmsError:
			return
		self.fail()	
		
	def test13_CreateProofingTransformWithInvalidProofingIntent(self):
		self.assertNotEqual(None, pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile, 1,2))
		try:
			pycms.cmsCreateProofingTransform(self.inProfile, pycms.TYPE_RGB_8, 
														self.inProfile, pycms.TYPE_RGB_8,		
														self.outProfile, 1,4)
		except pycms.pycmsError:
			return
		self.fail()	
		
	def test14_SetAlarmCodesWithNullValues(self):
		try:
			pycms.cmsSetAlarmCodes(0,1,1)
			pycms.cmsSetAlarmCodes(1,0,1)
			pycms.cmsSetAlarmCodes(1,1,0)
		except pycms.pycmsError:
			self.fail()	
			
	def test15_SetAlarmCodesWithLagestValues(self):
		try:
			pycms.cmsSetAlarmCodes(0,255,255)
			pycms.cmsSetAlarmCodes(255,0,255)
			pycms.cmsSetAlarmCodes(255,255,0)
		except pycms.pycmsError:
			self.fail()	
			
	def test16_SetAlarmCodesWithIncorrectValues(self):
		counter=0
		try:
			pycms.cmsSetAlarmCodes(256,255,255)
		except pycms.pycmsError:
			counter+=1	
			
		try:
			pycms.cmsSetAlarmCodes(0,256,255)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(0,255,256)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(-1,255,255)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(255,-1,255)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(255,255,-1)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(255,255,.1)
		except pycms.pycmsError:
			counter+=1			
			
		try:
			pycms.cmsSetAlarmCodes(255,.1,255)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes(.1,255,255)
		except pycms.pycmsError:
			counter+=1
			
		try:
			pycms.cmsSetAlarmCodes("#fff","#fff","#fff")
		except pycms.pycmsError:
			counter+=1
			
		self.assertEqual(counter,10)
		
	def test17_DoTransformWithNullInput(self):
		rgb=pycms.COLORB()
		cmyk=pycms.COLORB()
		pycms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertNotEqual(0,cmyk[0])
		self.assertNotEqual(0,cmyk[1])
		self.assertNotEqual(0,cmyk[2])
		self.assertNotEqual(0,cmyk[3])	
		
	def test18_DoTransformWithMaximumAllowedInput(self):
		rgb=pycms.COLORB()
		cmyk=pycms.COLORB()
		rgb[0]=255
		rgb[1]=255
		rgb[2]=255		
		pycms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertEqual(0,cmyk[0])
		self.assertEqual(0,cmyk[1])
		self.assertEqual(0,cmyk[2])
		self.assertEqual(0,cmyk[3])
		
	def test19_DoTransformWithIntermediateInput(self):
		rgb=pycms.COLORB()
		cmyk=pycms.COLORB()
		rgb[0]=100
		rgb[1]=190
		rgb[2]=150		
		pycms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertNotEqual(0,cmyk[0])
		self.assertNotEqual(0,cmyk[1])
		self.assertNotEqual(0,cmyk[2])
		self.assertNotEqual(0,cmyk[3])
		
	def test20_DoTransformWithIncorrectColorValues(self):			
		rgb=pycms.COLORB()
		cmyk=pycms.COLORB()
		rgb[0]=455
		rgb[1]=255
		rgb[2]=255	
		try:
			pycms.cmsDoTransform(self.transform, rgb, cmyk)			
		except:
			self.fail()
		
		
	def test21_DoTransformWithIncorrectInputBuffer(self):
		cmyk=pycms.COLORB()
		rgb=255
		try:
			pycms.cmsDoTransform(self.transform, rgb, cmyk)			
		except pycms.pycmsError:
			return
		self.fail()	
		
	def test22_DoTransformWithIncorrectOutputBuffer(self):			
		rgb=pycms.COLORB()
		rgb[0]=255
		rgb[1]=255
		rgb[2]=255
		cmyk=255	
		try:
			pycms.cmsDoTransform(self.transform, rgb, cmyk)			
		except pycms.pycmsError:
			return
		self.fail()	
		

	def test23_DoTransform2WithNullInput(self):						
		cmyk=pycms.cmsDoTransform2(self.transform, 0,0,0)
		self.assertNotEqual(0,cmyk[0])
		self.assertNotEqual(0,cmyk[1])
		self.assertNotEqual(0,cmyk[2])
		self.assertNotEqual(0,cmyk[3])	
		
	def test24_DoTransform2WithMaximalAllowedInput(self):
		cmyk=pycms.cmsDoTransform2(self.transform, 1,1,1)				
		self.assertEqual(0,cmyk[0])
		self.assertEqual(0,cmyk[1])
		self.assertEqual(0,cmyk[2])
		self.assertEqual(0,cmyk[3])

	def test25_DoTransform2WithIntermediateInput(self):			
		cmyk=pycms.cmsDoTransform2(self.transform, .392, .745, .588)	
		self.assertNotEqual(0,cmyk[0])
		self.assertNotEqual(0,cmyk[1])
		self.assertNotEqual(0,cmyk[2])
		self.assertNotEqual(0,cmyk[3])
		
	def test26_DoBitmapTransform(self):			
		inImage=Image.open("pycms_data/black100x100.png")
		pixel=inImage.getpixel((1,1))
		self.assertEqual(3,len(pixel))
		outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,pycms.TYPE_RGB_8, pycms.TYPE_CMYK_8)
		pixel=outImage.getpixel((1,1))
		self.assertEqual(4,len(pixel))
		
		inImage=Image.open("pycms_data/white100x100.png")
		pixel=inImage.getpixel((1,1))
		self.assertEqual(3,len(pixel))
		outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,pycms.TYPE_RGB_8, pycms.TYPE_CMYK_8)
		pixel=outImage.getpixel((1,1))
		self.assertEqual(4,len(pixel))
		
		inImage=Image.open("pycms_data/color100x100.png")
		pixel=inImage.getpixel((1,1))
		self.assertEqual(3,len(pixel))
		outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,pycms.TYPE_RGB_8, pycms.TYPE_CMYK_8)
		pixel=outImage.getpixel((1,1))
		self.assertEqual(4,len(pixel))
		
	def test27_DoBitmapTransformWithUnsupportedImage(self):			
		inImage=Image.open("pycms_data/black100x100.png")
		inImage.load()
		inImage=inImage.convert("YCbCr")
		try:
			outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,pycms.TYPE_RGB_8, pycms.TYPE_CMYK_8)			
		except pycms.pycmsError:
			return
		self.fail()
		
	def test28_DoBitmapTransformWithUnsupportedInMode(self):			
		inImage=Image.open("pycms_data/black100x100.png")
		try:
			outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,"YCbCr", pycms.TYPE_CMYK_8)			
		except pycms.pycmsError:
			return
		self.fail()
		
	def test29_DoBitmapTransformWithUnsupportedOutMode(self):			
		inImage=Image.open("pycms_data/black100x100.png")
		try:
			outImage=pycms.cmsDoBitmapTransform(self.transform2,inImage,pycms.TYPE_RGB_8, "YCbCr")			
		except pycms.pycmsError:
			return
		self.fail()
		
	def test30_GetProfileName(self):
		result=pycms.cmsGetProfileName(self.outProfile)
		self.assertEqual(type("string"),type(result))
		self.assertNotEqual(0,len(result))
		
	def test31_GetProfileInfo(self):
		result=pycms.cmsGetProfileInfo(self.outProfile)
		self.assertEqual(type("string"),type(result))
		self.assertNotEqual(0,len(result))
	
	def test32_GetPixelsFromImage(self):
		image=Image.open("pycms_data/black100x100.png")
		self.assertNotEqual(None,pycms.getPixelsFromImage(image))
		
	def test33_GetImageFromPixels(self):
		image=Image.open("pycms_data/black100x100.png")
		pixels=pycms.getPixelsFromImage(image)
		width, height=image.size
		self.assertNotEqual(None,pycms.getImageFromPixels(pixels, image.mode, width, height))

	def test34_DoPixelsTransform(self):	
		image=Image.open("pycms_data/black100x100.png")		
		pixels=pycms.getPixelsFromImage(image)
		width, height=image.size			
		self.assertNotEqual(None,pycms.cmsDoPixelsTransform(self.transform2, pixels, width*height))
		
	def tearDown(self):
		pass


if __name__ == '__main__':
	unittest.main()