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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

# A simple graphics object that represents a pixel image. It uses the
# Python Image Library for file I/O. The ExternalData baseclass
# maintains a cache of images to avoid having multiple copies of data in
# memory.
#

import os, app
from types import StringType

from sk1libs.imaging import ImageChops
from sk1libs import imaging

from app import _, RegisterCommands, colormanager
#from app.UI.command import AddCmd

from external import ExternalData, get_cached, ExternalGraphics

RGB_IMAGE=_('RGB')
RGBA_IMAGE=_('RGBA')
GRAYSCALE_IMAGE=_('Grayscale')
CMYK_IMAGE=_('CMYK')
BW_IMAGE=_('Monochrome')
UNSUPPORTED=_('UNSUPPORTED')

class ImageData(ExternalData):

	attributes = {'mode':0, 'size':0, 'im':0, 'info':0}
	cached =0
	
	def __init__(self, image, filename = '', cache = 1):
		self.orig_image=image.copy()

		if image.mode=='1':
			self.image_mode=BW_IMAGE
		elif image.mode=='L':
			self.image_mode=GRAYSCALE_IMAGE
		elif image.mode=='RGB':
			self.image_mode=RGB_IMAGE
		elif image.mode=='RGBA':
			self.image_mode=RGBA_IMAGE
		elif image.mode=='CMYK':
			self.image_mode=CMYK_IMAGE
			colormanager.add_to_image_pool(self)
			self.cached=1
		else:
			self.image_mode=UNSUPPORTED
													
		if image.mode not in ('RGB', 'RGBA'):
			image.load()
			if image.mode=='CMYK':
				if app.config.preferences.use_cms_for_bitmap:
					self.image=colormanager.ImageCMYKtoRGB(image)
				else:
					self.image = image.convert('RGB')
			else:				
				self.image = image.convert('RGB')
		else:
			image.load()
			self.image = image
			
		if self.image_mode==UNSUPPORTED:
			self.orig_image=self.image.copy()
			self.image_mode=RGB_IMAGE
			
		ExternalData.__init__(self, filename, cache)
		
	def __del__(self):
		if self.cached and colormanager is not None:
			colormanager.remove_from_image_pool(self)

	def __getattr__(self, attr):
		if self.attributes.has_key(attr):
			return getattr(self.image, attr)
		raise AttributeError, attr
	
	def update(self):
		if app.config.preferences.use_cms_for_bitmap:
			if self.image_mode==CMYK_IMAGE:
				self.image=colormanager.ImageCMYKtoRGB(self.orig_image)
			else:
				self.image = self.orig_image.convert('RGB')
		else:
			self.image = self.orig_image.convert('RGB')

	def AsEmbedded(self):
		if self.filename:
			return ImageData(self.orig_image)
		else:
			return self

	def IsEmbedded(self):
		return not self.filename

	def Size(self):
		return self.size

	def Image(self):
		return self.orig_image

	def Convert(self, mode):
		if mode != self.orig_image.mode:
			if app.config.preferences.use_cms_for_bitmap:
				if mode=='RGB'and self.orig_image.mode=='CMYK':
					return ImageData(colormanager.ImageCMYKtoRGB(self.orig_image))
				if mode=='CMYK'and self.orig_image.mode=='RGB':
					return ImageData(colormanager.ImageRGBtoCMYK(self.orig_image))
				return ImageData(self.orig_image.convert(mode))
			else:				
				return ImageData(self.orig_image.convert(mode))
		else:
			return self

	def Invert(self):
		return ImageData(ImageChops.invert(self.orig_image))



def load_image(filename, cache = 0):
	image = imaging.Image.open(filename)
	if type(filename) != StringType:
		filename = ''
	return ImageData(image, filename = filename, cache = cache)

class Image(ExternalGraphics):

	is_Image = 1
	is_clip = 1

	commands = ExternalGraphics.commands[:]

	def __init__(self, image = None, imagefile = '', trafo = None, duplicate = None):
		if duplicate is None:
			if not image:
				if not imagefile:
					raise ValueError, 'Image must be instantiated with'\
										' either image or imagefile'
				image = load_image(imagefile)
		ExternalGraphics.__init__(self, image, trafo, duplicate = duplicate)
		self.Embed()

	def DrawShape(self, device, rect = None, clip = 0):
		device.DrawImage(self.data, self.trafo, clip)

	def Info(self):
		mode=self.data.image_mode
		width, height = self.data.Size()
		x, y = self.trafo.offset()
		return _("Embedded %(mode)s image %(width)d x %(height)d "
					"at (%(x)d, %(y)d)") % locals()

	def SaveToFile(self, file):
		file.Image(self.data, self.trafo)

	def IsEmbedded(self):
		return self.data.IsEmbedded()

	def CanEmbed(self):
		return not self.IsEmbedded()

	def Embed(self):
		return self.SetData(self.data.AsEmbedded())
	
	def InvertImage(self):
		return self.SetData(self.data.Invert())
	
	def Convert(self, image_mode):
		undo = (self.SetData, self.data)
		if image_mode==RGB_IMAGE:
			self.SetData(self.data.Convert('RGB'))
		if image_mode==RGBA_IMAGE:
			self.SetData(self.data.Convert('RGB'))
		if image_mode==GRAYSCALE_IMAGE:
			self.SetData(self.data.Convert('L'))
		if image_mode==CMYK_IMAGE:
			self.SetData(self.data.Convert('CMYK'))
		if image_mode==BW_IMAGE:
			self.SetData(self.data.Convert('1'))
		return undo

	def CallImageFunction(self, function, args = ()):
		if type(args) != type(()):
			args = (args,)
		data = apply(getattr(self.data, function), args)
		return self.SetData(data)


