# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998 by Bernhard Herzog
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


#
# Class PageLayout
#
# This class represents the layout of one page. This includes the
# papersize, margins, etc. The papersize can be a standard paper size
# like `A4' or `legal' or some user specific format like `10cm x 10cm'.
#
# XXX: margins are not yet implemented

from papersize import Papersize
from app import config

Portrait = 0
Landscape = 1

class PageLayout:

	def __init__(self, paperformat = None, width = None, height = None,
					orientation = None):
		if width and height:
			self.width = width
			self.height = height
			self.paperformat = ''
		else:
			if paperformat is None:
				self.paperformat = config.preferences.default_paper_format
			else:
				self.paperformat = paperformat
			self.width, self.height = Papersize[self.paperformat]
		if orientation is None:
			self.orientation = config.preferences.default_page_orientation
		else:
			self.orientation = orientation
		if self.orientation not in (Portrait, Landscape):
			self.orientation = Portrait

	def Width(self):
		if self.orientation == Portrait:
			return self.width
		else:
			return self.height

	def Height(self):
		if self.orientation == Portrait:
			return self.height
		else:
			return self.width

	def Size(self):
		if self.orientation == Portrait:
			return (self.width, self.height)
		else:
			return (self.height, self.width)

	def FormatName(self):
		return self.paperformat

	def Orientation(self):
		return self.orientation


	def SaveToFile(self, file):
		file.PageLayout(self.paperformat, self.width, self.height,
						self.orientation)
