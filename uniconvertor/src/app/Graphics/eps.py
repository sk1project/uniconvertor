# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000, 2002 by Bernhard Herzog
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
#	A GraphicsObject for Encapsulated Postscript Pictures
#

import os, math

from sk1libs.imaging import Image

from app.Lib import dscparser
from sk1libs import utils
IsEpsFileStart = dscparser.IsEpsFileStart
from app import _, Point, config

from base import GraphicsObject
from external import ExternalData, get_cached, ExternalGraphics


gs_command = ('gs -sDEVICE=ppmraw -r%(resolution)d -dNOPAUSE -dSAFER -q'
				' -sOutputFile=%(temp)s -g%(width)dx%(height)d'
				' -c %(offx)f %(offy)f translate'
				' /oldshowpage /showpage load def /showpage \'{}\' def '
				' -f %(filename)s -c oldshowpage quit')

def render_preview(filename, startx, starty, width, height, resolution = None):
	import tempfile
	temp = tempfile.mktemp()

	try:
		# quote the filename so that it can have spaces and to avoid a
		# security hole
		filename = utils.sh_quote(filename)
		if resolution is None:
			resolution = config.preferences.eps_preview_resolution
		factor = resolution / 72.0
		width = int(math.ceil(width * factor))
		height = int(math.ceil(height * factor))
		offx = -startx
		offy = -starty
		os.system(gs_command % locals())

		image = Image.open(temp)
		image.load()
		return image
	finally:
		try:
			os.unlink(temp)
		except:
			pass



class EpsData(ExternalData):

	def __init__(self, filename):
		self.info = info = dscparser.parse_eps_file(filename)
		self.filename = filename
		if info.BoundingBox:
			llx, lly, urx, ury = info.BoundingBox
			self.width = Point(urx - llx, 0)
			self.height = Point(0, ury - lly)
			self.start = (llx, lly)
			self.size = (urx - llx, ury - lly)
			self.image = None
			try:
				self.image = render_preview(filename, llx, lly,
											urx - llx, ury - lly)
			except IOError:
				pass
		else:
			raise TypeError, '%s has no BoundingBox' % filename

		ExternalData.__init__(self, filename)

	def Start(self):
		return self.start

	def Size(self):
		return self.size

	def WriteLines(self, file):
		write = file.write

		try:
			infile = open(self.filename, 'r')
		except IOError, val:
			raise IOError, (filename, val)
		try:
			readline = infile.readline

			line = readline()
			while line:
				if line[:15] == '%%BeginPreview:':
					while line[:12] != '%%EndPreview':
						line = readline()
					continue
				write(line)
				line = readline()
		finally:
			infile.close()


def load_eps(filename):
	eps = get_cached(filename)
	if eps:
		return eps
	return EpsData(filename)


class EpsImage(ExternalGraphics):

	has_edit_mode = 0
	is_Eps = 1

	def __init__(self, filename = '', trafo = None, duplicate = None):
		if duplicate is None:
			if not filename:
				raise ValueError, 'filename must be provided'
			data = load_eps(filename)
		else:
			data = None
		ExternalGraphics.__init__(self, data, trafo,
									duplicate = duplicate)

	def DrawShape(self, device, rect = None):
		device.DrawEps(self.data, self.trafo)

	def Info(self):
		filename = os.path.basename(self.data.Filename())
		width, height = self.data.Size()
		x, y = self.trafo.offset()
		return _("EpsFile `%(filename)s' %(width)d x %(height)d "
					"at (%(x)d, %(y)d)") % locals()

	def SaveToFile(self, file):
		file.EpsFile(self.data, self.trafo)

	def PSNeededResources(self):
		return self.data.info.DocumentNeededResources



