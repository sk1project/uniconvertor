# -*- coding: utf-8 -*-

# cms - small package which provides binding
# to LittleCMS library.

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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import _cms, os, types
from PIL import Image

INTENT_PERCEPTUAL = 0
INTENT_RELATIVE_COLORIMETRIC = 1
INTENT_SATURATION = 2
INTENT_ABSOLUTE_COLORIMETRIC = 3

TYPE_RGB_8 = "RGB"
TYPE_RGBA_8 = "RGBA"
TYPE_CMYK_8 = "CMYK"
TYPE_GRAY_8 = "L"
TYPE_YCbCr_8 = "YCCA"

cmsFLAGS_NOTPRECALC = 0x0100
cmsFLAGS_GAMUTCHECK = 0x1000
cmsFLAGS_SOFTPROOFING = 0x4000
cmsFLAGS_BLACKPOINTCOMPENSATION = 0x2000
cmsFLAGS_PRESERVEBLACK = 0x8000
cmsFLAGS_NULLTRANSFORM = 0x0200
cmsFLAGS_HIGHRESPRECALC = 0x0400
cmsFLAGS_LOWRESPRECALC = 0x0800


class cmsError(Exception):
	pass

def get_version():
	"""
	Retuns LCMS version.
	"""
	ver = str(_cms.getVersion())
	return ver[0] + '.' + ver[1:]

def COLORB():
	"""
	The function for python-lcms compatibility.
	Emulates COLORB object from python-lcms.
	Actually function returns regular 4-member list.
	"""
	return [0, 0, 0, 0]

def cmsSetAlarmCodes(r, g, b):
	"""
	Used to define gamut check marker.
	r,g,b are expected to be integers in range 0..255
	"""
	if r in range(0, 256) and g in range(0, 256) and b in range(0, 256):
		_cms.setAlarmCodes(r, g, b)
	else:
		raise cmsError, "r,g,b are expected to be integers in range 0..255"


def cmsOpenProfileFromFile(profileFilename, mode=None):
	"""	
	Returns a handle to lcms profile wrapped as a Python object. 
	The handle doesn't require to be closed after usage because
	on object delete operation Python calls native cmsCloseProfile()
	function automatically  

	profileFilename - a valid filename path to the ICC profile
	mode - stub parameter for python-lcms compatibility
	"""
	if not os.path.isfile(profileFilename):
		raise cmsError, "Invalid profile path provided: %s" % profileFilename

	result = _cms.openProfile(profileFilename)

	if result is None:
		raise cmsError, "It seems provided profile is invalid: %s" % profileFilename

	return result

def cmsCreateRGBProfile():
	"""	
	Returns a handle to lcms built-in sRGB profile wrapped as a Python object. 
	The handle doesn't require to be closed after usage because
	on object delete operation Python calls native cmsCloseProfile()
	function automatically
	"""
	result = _cms.createRGBProfile()

	if result is None:
		raise cmsError, "LCMS library misconfiguration"

	return result

def cmsCreateCMYKProfile():
	"""	
	Artificial functionality. The function emulates built-in CMYK
	profile reading real file attached to the package.
	Returns a handle to lcms built-in CMYK profile wrapped as a Python object. 
	The handle doesn't require to be closed after usage because
	on object delete operation Python calls native cmsCloseProfile()
	function automatically
	"""
	profile_path = os.path.join(__path__[0], 'profiles')
	profile = os.path.join(profile_path, 'GenericCMYK.icm')
	return cmsOpenProfileFromFile(profile)

def cmsCreateLabProfile():
	"""	
	Returns a handle to lcms built-in Lab profile wrapped as a Python object. 
	The handle doesn't require to be closed after usage because
	on object delete operation Python calls native cmsCloseProfile()
	function automatically
	"""
	result = _cms.createLabProfile()

	if result is None:
		raise cmsError, "LCMS library misconfiguration"

	return result


def cmsCreateGrayProfile():
	"""	
	Returns a handle to lcms built-in Gray profile wrapped as a Python object. 
	The handle doesn't require to be closed after usage because
	on object delete operation Python calls native cmsCloseProfile()
	function automatically
	"""
	result = _cms.createGrayProfile()

	if result is None:
		raise cmsError, "LCMS library misconfiguration"

	return result



def cmsCreateTransform(inputProfile, inMode,
					outputProfile, outMode,
					renderingIntent=INTENT_PERCEPTUAL,
					flags=cmsFLAGS_NOTPRECALC):
	"""
	Returns a handle to lcms transformation wrapped as a Python object.

	inputProfile - a valid lcms profile handle
	outputProfile - a valid lcms profile handle
	inMode - predefined string constant (i.e. TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8, etc.) or valid PIL mode		
	outMode - predefined string constant (i.e. TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8, etc.) or valid PIL mode		
	renderingIntent - integer constant (0-3) specifying rendering intent for the transform
	flags - a set of predefined lcms flags
	"""

	if renderingIntent not in (0, 1, 2, 3):
		raise cmsError, "renderingIntent must be an integer between 0 and 3"

	result = _cms.buildTransform(inputProfile, inMode, outputProfile, outMode, renderingIntent, flags)

	if result is None:
		raise cmsError, "Cannot create requested transform: %s %s" % (inMode, outMode)

	return result

def cmsCreateProofingTransform(inputProfile, inMode,
							outputProfile, outMode,
							proofingProfile,
							renderingIntent=INTENT_PERCEPTUAL,
							proofingIntent=INTENT_RELATIVE_COLORIMETRIC,
							flags=cmsFLAGS_SOFTPROOFING):
	"""
	Returns a handle to lcms transformation wrapped as a Python object.

	inputProfile - a valid lcms profile handle
	outputProfile - a valid lcms profile handle
	proofingProfile - a valid lcms profile handle 
	inMode - predefined string constant (i.e. TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8, etc.) or valid PIL mode		
	outMode - predefined string constant (i.e. TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8, etc.) or valid PIL mode		
	renderingIntent - integer constant (0-3) specifying rendering intent for the transform
	proofingIntent - integer constant (0-3) specifying proofing intent for the transform
	flags - a set of predefined lcms flags
	"""

	if renderingIntent not in (0, 1, 2, 3):
		raise cmsError, "renderingIntent must be an integer between 0 and 3"

	if proofingIntent not in (0, 1, 2, 3):
		raise cmsError, "proofingIntent must be an integer between 0 and 3"

	result = _cms.buildProofingTransform(inputProfile, inMode, outputProfile, outMode,
										proofingProfile, renderingIntent, proofingIntent, flags)

	if result is None:
		raise cmsError, "Cannot create requested proofing transform: %s %s" % (inMode, outMode)

	return result

def cmsDoTransform(hTransform, inputBuffer, outputBuffer, buffersSizeInPixels=None):
	"""
	Transform color values from inputBuffer to outputBuffer using provided lcms transform handle.
	
	hTransform - a valid lcms transformation handle
	inputBuffer - 4-member list object. The members must be an integer between 0 and 255
	outputBuffer - 4-member list object with any values for recording transformation results.
	             Can be [0,0,0,0].
	buffersSizeInPixels - parameter for python-lcms compatibility. Can be skipped.               
	"""

	if type(inputBuffer) is types.ListType and type(outputBuffer) is types.ListType:

		outputBuffer[0], outputBuffer[1], outputBuffer[2], outputBuffer[3] = _cms.transformPixel(hTransform,
																							inputBuffer[0],
																							inputBuffer[1],
																							inputBuffer[2],
																							inputBuffer[3])
		return

	else:
		raise cmsError, "inputBuffer and outputBuffer must be Python 4-member list objects"

def cmsDoTransform2(hTransform, channel1, channel2, channel3, channel4=0):
	"""
	Accelerated variant of cmsDoTransform. Adapted for sK1 color management.
	Not presented in python-lcms API.
	
	hTransform - a valid lcms transformation handle
	channel1, channel2, channel3, channel4 - color channel values. Must be float between 0 and 1.
	
	Returns 4-member tuple of converted color values (i.e. CMYK or RGBA) as a float between 0 and 1.
	"""
	return _cms.transformPixel2(hTransform, channel1, channel2, channel3, channel4)

def cmsDoBitmapTransform(hTransform, inImage, inMode, outMode):
	"""
	The method provides PIL images support for color management.
	
	hTransform - a valid lcms transformation handle
	inImage - a valid PIL image object
	inMode, outMode -  - predefined string constant (i.e. TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8) or valid PIL mode
	Currently supports RGB, RGBA and CMYK modes only.
	Returns new PIL image object in outMode colorspace.
	"""
	if not inImage.mode == inMode:
		raise cmsError, "incorrect inMode"

	if not inImage.mode in [TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8]:
		raise cmsError, "unsupported image type: %s" % inImage.mode

	if not inMode in [TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8]:
		raise cmsError, "unsupported inMode type: %s" % inMode

	if not outMode in [TYPE_RGB_8, TYPE_RGBA_8, TYPE_CMYK_8]:
		raise cmsError, "unsupported outMode type: %s" % outMode

	w, h = inImage.size
	inImage.load()
	outImage = Image.new(outMode, (w, h))

	_cms.transformBitmap(hTransform, inImage.im, outImage.im, w, h)

	return outImage

def cmsGetProfileName(profile):
	"""
	This function is given mainly for building user interfaces.
	
	profile - a valid lcms profile handle
	Returns profile name as a string value.	
	"""
	return _cms.getProfileName(profile)

def cmsGetProfileInfo(profile):
	"""
	This function is given mainly for building user interfaces.
	
	profile - a valid lcms profile handle
	Returns profile description info as a string value.	
	"""
	return _cms.getProfileInfo(profile)

def cmsDeleteTransform(transform):
	"""
	This is a function stub for python-lcms compatibility.
	Transform handle will be released automatically.
	"""
	pass

def cmsCloseProfile(profile):
	"""
	This is a function stub for python-lcms compatibility.
	Profile handle will be released automatically.
	"""
	pass

##############################################################
#              Pixels API
##############################################################
#  Best color management performance can be achieved for plane
#  pixel arrays (i.e. for unsigned char* on native side)
#  Also pixel arrays can be used for Cairo and ImageMagick
#  integration.
##############################################################

def getPixelsFromImage(image):
	"""
	Creates pixel array using provided image. Accepts any valid PIL image.
	
	image - any valid PIL image.
	Returns pixel array handle wrapped as a python object.
	"""
	image.load()
	width, height = image.size
	pixel = image.getpixel((0, 0))
	bytes_per_pixel = 1
	if type(pixel) is types.TupleType:
		bytes_per_pixel = len(pixel)
	if image.mode == TYPE_RGB_8:
		bytes_per_pixel = 4
	return _cms.getPixelsFromImage(image.im, width, height, bytes_per_pixel)

def getImageFromPixels(pixels, mode, width, height):
	"""
	Creates new image using provided pixel array.
	
	pixels - pixel array wrapped as a python object.
	mode - pixel array appropriate PIL mode.
	width, height - pixel array appropriate image size.
	Returns new PIL image object.
	"""
	image = Image.new(mode, (width, height))
	pixel = image.getpixel((0, 0))
	bytes_per_pixel = 1
	if type(pixel) is types.TupleType:
		bytes_per_pixel = len(pixel)
	if image.mode == TYPE_RGB_8:
		bytes_per_pixel = 4
	_cms.setImagePixels(pixels, image.im, width, height, bytes_per_pixel)
	return image

def cmsDoPixelsTransform(hTransform, pixels, width):
	"""
	Transforms pixel array using provided lcms transform handle.
	Supports TYPE_RGB_8, TYPE_RGBA_8, and TYPE_CMYK_8 transforms only.
	
	hTransform - valid lcms transform handle
	pixels - pixel array wrapped as a python object.
	width - pixel array width.
	Returns handle to new pixel array.
	"""
	return _cms.transformPixels(hTransform, pixels, width)
