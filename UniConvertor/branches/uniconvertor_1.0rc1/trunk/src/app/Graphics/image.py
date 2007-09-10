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

import os
from types import StringType

import PIL.Image, PIL.ImageChops

from app import _, RegisterCommands
#from app.UI.command import AddCmd

from external import ExternalData, get_cached, ExternalGraphics

class ImageData(ExternalData):

	attributes = {'mode':0, 'size':0, 'im':0, 'info':0}

	def __init__(self, image, filename = '', cache = 1):
		# convert image to mode 'L' or 'RGB' if necessary
		if image.mode not in ('RGB', 'RGBA', 'L'):
			if image.mode == '1':
				mode = 'L'
			else:
				mode = 'RGB'
			image = image.convert(mode)
		else:
			image.load()
		self.image = image
		ExternalData.__init__(self, filename, cache)

	def __getattr__(self, attr):
		if self.attributes.has_key(attr):
			return getattr(self.image, attr)
		raise AttributeError, attr

	def AsEmbedded(self):
		if self.filename:
			return ImageData(self.image)
		else:
			return self

	def IsEmbedded(self):
		return not self.filename

	def Size(self):
		return self.size

	def Image(self):
		return self.image

	def Convert(self, mode):
		if mode != self.image.mode:
			return ImageData(self.image.convert(mode))
		else:
			return self

	def Invert(self):
		return ImageData(PIL.ImageChops.invert(self.image))



def load_image(filename, cache = 1):
	if type(filename) == StringType:
		image = get_cached(filename)
		if image:
			return image
	image = PIL.Image.open(filename)
	if type(filename) != StringType:
		filename = ''
	return ImageData(image, filename = filename, cache = cache)

class Image(ExternalGraphics):

	is_Image = 1
	is_clip = 1

	commands = ExternalGraphics.commands[:]

	def __init__(self, image = None, imagefile = '', trafo = None,
					duplicate = None):
		if duplicate is None:
			if not image:
				if not imagefile:
					raise ValueError, 'Image must be instantiated with'\
										' either image or imagefile'
				image = load_image(imagefile)
		ExternalGraphics.__init__(self, image, trafo,
									duplicate = duplicate)

	def DrawShape(self, device, rect = None, clip = 0):
		device.DrawImage(self.data, self.trafo, clip)

	def Info(self):
		width, height = self.data.Size()
		x, y = self.trafo.offset()
		if self.IsEmbedded():
			return _("Embedded Image %(width)d x %(height)d "
						"at (%(x)d, %(y)d)") % locals()
		else:
			filename = os.path.basename(self.data.Filename())
			return _("Linked Image `%(filename)s' %(width)d x %(height)d "
						"at (%(x)d, %(y)d)") % locals()

	def SaveToFile(self, file):
		file.Image(self.data, self.trafo)

	def IsEmbedded(self):
		return self.data.IsEmbedded()

	def CanEmbed(self):
		return not self.IsEmbedded()

	def Embed(self):
		return self.SetData(self.data.AsEmbedded())
	#AddCmd(commands, 'EmbedImage', _("Embed Image"), Embed,
			#sensitive_cb = 'CanEmbed')

	def CallImageFunction(self, function, args = ()):
		if type(args) != type(()):
			args = (args,)
		data = apply(getattr(self.data, function), args)
		return self.SetData(data)
	#AddCmd(commands, 'GrayscaleImage', _("Grayscale Image"),
			#CallImageFunction, args = ('Convert', 'L'))
	#AddCmd(commands, 'InvertImage', _("Invert Image"), CallImageFunction,
			#args = 'Invert')

	#context_commands = ('EmbedImage', 'GrayscaleImage', 'InvertImage')

RegisterCommands(Image)

