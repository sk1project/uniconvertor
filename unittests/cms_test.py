#!/usr/bin/python

# -*- coding: utf-8 -*-

# cms - small package which provides binding to LittleCMS library.

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
from PIL import Image
from uniconvertor import cms

class TestCmsFunctions(unittest.TestCase):

	def setUp(self):
		self.inProfile = cms.cmsOpenProfileFromFile('cms_data/sRGB.icm')
		self.outProfile = cms.cmsOpenProfileFromFile('cms_data/GenericCMYK.icm')
		self.transform = cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGBA_8,
											 self.outProfile, cms.TYPE_CMYK_8,
											 cms.INTENT_PERCEPTUAL,
											 cms.cmsFLAGS_NOTPRECALC)
		self.transform2 = cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGBA_8,
											 self.outProfile, cms.TYPE_CMYK_8,
											 cms.INTENT_PERCEPTUAL, 0)

	def test00_GetVersion(self):
		self.assertNotEqual(None, cms.get_version())

	def test01_OpenProfile(self):
		self.assertNotEqual(None, self.inProfile)
		self.assertNotEqual(None, self.outProfile)
		self.assertNotEqual(None, cms.cmsCreateRGBProfile())
		self.assertNotEqual(None, cms.cmsCreateCMYKProfile())
		self.assertNotEqual(None, cms.cmsCreateLabProfile())
		self.assertNotEqual(None, cms.cmsCreateGrayProfile())

	def test02_OpenInvalidProfile(self):
		try:
			cms.cmsOpenProfileFromFile('cms_data/empty.icm')
		except cms.cmsError:
			return
		self.fail()

	def test03_OpenAbsentProfile(self):
		try:
			cms.cmsOpenProfileFromFile('cms_data/xxx.icm')
		except cms.cmsError:
			return
		self.fail()

	def test04_CreateTransform(self):
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.TYPE_CMYK_8))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGBA_8,
														self.outProfile, cms.TYPE_CMYK_8))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.outProfile, cms.TYPE_CMYK_8,
														self.inProfile, cms.TYPE_RGBA_8))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.outProfile, cms.TYPE_CMYK_8,
														self.inProfile, cms.TYPE_RGB_8))

	def test05_CreateTransformWithCustomIntent(self):
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_PERCEPTUAL))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_RELATIVE_COLORIMETRIC))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_SATURATION))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_ABSOLUTE_COLORIMETRIC))

	def test06_CreateTransformWithCustomFlags(self):
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_PERCEPTUAL,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_GAMUTCHECK))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_PERCEPTUAL,
														cms.cmsFLAGS_PRESERVEBLACK | cms.cmsFLAGS_BLACKPOINTCOMPENSATION))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_PERCEPTUAL,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_HIGHRESPRECALC))
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8, self.outProfile,
														cms.TYPE_CMYK_8, cms.INTENT_PERCEPTUAL,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_LOWRESPRECALC))

	def test07_CreateTransformWithInvalidIntent(self):
		self.assertNotEqual(None, cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.TYPE_CMYK_8, 3))
		try:
			cms.cmsCreateTransform(self.inProfile, cms.TYPE_RGB_8,
									self.outProfile, cms.TYPE_CMYK_8, 4)
		except cms.cmsError:
			return
		self.fail()

	def test08_CreateProofingTransform(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGBA_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGBA_8,
														self.outProfile))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGBA_8,
														self.inProfile, cms.TYPE_RGBA_8,
														self.outProfile))
	def test09_CreateProofingTransformWithCustomIntent(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_RELATIVE_COLORIMETRIC))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_SATURATION))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_ABSOLUTE_COLORIMETRIC))

	def test10_CreateProofingTransformWithCustomProofingIntent(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_PERCEPTUAL))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_RELATIVE_COLORIMETRIC))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_SATURATION))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_ABSOLUTE_COLORIMETRIC))

	def test11_CreateProofingTransformWithCustomFlags(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_RELATIVE_COLORIMETRIC,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_GAMUTCHECK))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_RELATIVE_COLORIMETRIC,
														cms.cmsFLAGS_PRESERVEBLACK | cms.cmsFLAGS_BLACKPOINTCOMPENSATION))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_RELATIVE_COLORIMETRIC,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_HIGHRESPRECALC))
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, cms.INTENT_PERCEPTUAL, cms.INTENT_RELATIVE_COLORIMETRIC,
														cms.cmsFLAGS_NOTPRECALC | cms.cmsFLAGS_LOWRESPRECALC))

	def test12_CreateProofingTransformWithInvalidIntent(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, 3))
		try:
			cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, 4)
		except cms.cmsError:
			return
		self.fail()

	def test13_CreateProofingTransformWithInvalidProofingIntent(self):
		self.assertNotEqual(None, cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, 1, 2))
		try:
			cms.cmsCreateProofingTransform(self.inProfile, cms.TYPE_RGB_8,
														self.inProfile, cms.TYPE_RGB_8,
														self.outProfile, 1, 4)
		except cms.cmsError:
			return
		self.fail()

	def test14_SetAlarmCodesWithNullValues(self):
		try:
			cms.cmsSetAlarmCodes(0, 1, 1)
			cms.cmsSetAlarmCodes(1, 0, 1)
			cms.cmsSetAlarmCodes(1, 1, 0)
		except cms.cmsError:
			self.fail()

	def test15_SetAlarmCodesWithLagestValues(self):
		try:
			cms.cmsSetAlarmCodes(0, 255, 255)
			cms.cmsSetAlarmCodes(255, 0, 255)
			cms.cmsSetAlarmCodes(255, 255, 0)
		except cms.cmsError:
			self.fail()

	def test16_SetAlarmCodesWithIncorrectValues(self):
		counter = 0
		try:
			cms.cmsSetAlarmCodes(256, 255, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(0, 256, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(0, 255, 256)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(-1, 255, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(255, -1, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(255, 255, -1)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(255, 255, .1)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(255, .1, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes(.1, 255, 255)
		except cms.cmsError:
			counter += 1

		try:
			cms.cmsSetAlarmCodes("#fff", "#fff", "#fff")
		except cms.cmsError:
			counter += 1

		self.assertEqual(counter, 10)

	def test17_DoTransformWithNullInput(self):
		rgb = cms.COLORB()
		cmyk = cms.COLORB()
		cms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertNotEqual(0, cmyk[0])
		self.assertNotEqual(0, cmyk[1])
		self.assertNotEqual(0, cmyk[2])
		self.assertNotEqual(0, cmyk[3])

	def test18_DoTransformWithMaximumAllowedInput(self):
		rgb = cms.COLORB()
		cmyk = cms.COLORB()
		rgb[0] = 255
		rgb[1] = 255
		rgb[2] = 255
		cms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertEqual(0, cmyk[0])
		self.assertEqual(0, cmyk[1])
		self.assertEqual(0, cmyk[2])
		self.assertEqual(0, cmyk[3])

	def test19_DoTransformWithIntermediateInput(self):
		rgb = cms.COLORB()
		cmyk = cms.COLORB()
		rgb[0] = 100
		rgb[1] = 190
		rgb[2] = 150
		cms.cmsDoTransform(self.transform, rgb, cmyk)
		self.assertNotEqual(0, cmyk[0])
		self.assertNotEqual(0, cmyk[1])
		self.assertNotEqual(0, cmyk[2])
		self.assertNotEqual(0, cmyk[3])

	def test20_DoTransformWithIncorrectColorValues(self):
		rgb = cms.COLORB()
		cmyk = cms.COLORB()
		rgb[0] = 455
		rgb[1] = 255
		rgb[2] = 255
		try:
			cms.cmsDoTransform(self.transform, rgb, cmyk)
		except:
			self.fail()


	def test21_DoTransformWithIncorrectInputBuffer(self):
		cmyk = cms.COLORB()
		rgb = 255
		try:
			cms.cmsDoTransform(self.transform, rgb, cmyk)
		except cms.cmsError:
			return
		self.fail()

	def test22_DoTransformWithIncorrectOutputBuffer(self):
		rgb = cms.COLORB()
		rgb[0] = 255
		rgb[1] = 255
		rgb[2] = 255
		cmyk = 255
		try:
			cms.cmsDoTransform(self.transform, rgb, cmyk)
		except cms.cmsError:
			return
		self.fail()


	def test23_DoTransform2WithNullInput(self):
		cmyk = cms.cmsDoTransform2(self.transform, 0, 0, 0)
		self.assertNotEqual(0, cmyk[0])
		self.assertNotEqual(0, cmyk[1])
		self.assertNotEqual(0, cmyk[2])
		self.assertNotEqual(0, cmyk[3])

	def test24_DoTransform2WithMaximalAllowedInput(self):
		cmyk = cms.cmsDoTransform2(self.transform, 1, 1, 1)
		self.assertEqual(0, cmyk[0])
		self.assertEqual(0, cmyk[1])
		self.assertEqual(0, cmyk[2])
		self.assertEqual(0, cmyk[3])

	def test25_DoTransform2WithIntermediateInput(self):
		cmyk = cms.cmsDoTransform2(self.transform, .392, .745, .588)
		self.assertNotEqual(0, cmyk[0])
		self.assertNotEqual(0, cmyk[1])
		self.assertNotEqual(0, cmyk[2])
		self.assertNotEqual(0, cmyk[3])

	def test26_DoBitmapTransform(self):
		inImage = Image.open("cms_data/black100x100.png")
		pixel = inImage.getpixel((1, 1))
		self.assertEqual(3, len(pixel))
		outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, cms.TYPE_RGB_8, cms.TYPE_CMYK_8)
		pixel = outImage.getpixel((1, 1))
		self.assertEqual(4, len(pixel))

		inImage = Image.open("cms_data/white100x100.png")
		pixel = inImage.getpixel((1, 1))
		self.assertEqual(3, len(pixel))
		outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, cms.TYPE_RGB_8, cms.TYPE_CMYK_8)
		pixel = outImage.getpixel((1, 1))
		self.assertEqual(4, len(pixel))

		inImage = Image.open("cms_data/color100x100.png")
		pixel = inImage.getpixel((1, 1))
		self.assertEqual(3, len(pixel))
		outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, cms.TYPE_RGB_8, cms.TYPE_CMYK_8)
		pixel = outImage.getpixel((1, 1))
		self.assertEqual(4, len(pixel))

	def test27_DoBitmapTransformWithUnsupportedImage(self):
		inImage = Image.open("cms_data/black100x100.png")
		inImage.load()
		inImage = inImage.convert("YCbCr")
		try:
			outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, cms.TYPE_RGB_8, cms.TYPE_CMYK_8)
		except cms.cmsError:
			return
		self.fail()

	def test28_DoBitmapTransformWithUnsupportedInMode(self):
		inImage = Image.open("cms_data/black100x100.png")
		try:
			outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, "YCbCr", cms.TYPE_CMYK_8)
		except cms.cmsError:
			return
		self.fail()

	def test29_DoBitmapTransformWithUnsupportedOutMode(self):
		inImage = Image.open("cms_data/black100x100.png")
		try:
			outImage = cms.cmsDoBitmapTransform(self.transform2, inImage, cms.TYPE_RGB_8, "YCbCr")
		except cms.cmsError:
			return
		self.fail()

	def test30_GetProfileName(self):
		result = cms.cmsGetProfileName(self.outProfile)
		self.assertEqual(type("string"), type(result))
		self.assertNotEqual(0, len(result))

	def test31_GetProfileInfo(self):
		result = cms.cmsGetProfileInfo(self.outProfile)
		self.assertEqual(type("string"), type(result))
		self.assertNotEqual(0, len(result))

	def test32_GetPixelsFromImage(self):
		image = Image.open("cms_data/black100x100.png")
		self.assertNotEqual(None, cms.getPixelsFromImage(image))

	def test33_GetImageFromPixels(self):
		image = Image.open("cms_data/black100x100.png")
		pixels = cms.getPixelsFromImage(image)
		width, height = image.size
		self.assertNotEqual(None, cms.getImageFromPixels(pixels, image.mode, width, height))

	def test34_DoPixelsTransform(self):
		image = Image.open("cms_data/black100x100.png")
		pixels = cms.getPixelsFromImage(image)
		width, height = image.size
		self.assertNotEqual(None, cms.cmsDoPixelsTransform(self.transform2, pixels, width * height))

	def tearDown(self):
		pass

def get_suite():
	suite = unittest.TestSuite()
	suite.addTest(unittest.makeSuite(TestCmsFunctions))
	return suite

def run_tests():
	print "CMS module test suite\n" + "-"*60
	unittest.TextTestRunner(verbosity=2).run(get_suite())

if __name__ == '__main__':
	run_tests()
