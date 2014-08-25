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

###Sketch Config
#type = Import
#class_name = 'GZIPLoader'
#rx_magic = '\037\213'
#tk_file_type = ('Gzipped Files', '.gz')
#format_name = 'Gzipped-Meta'
#standard_messages = 1
###End

(''"Gzipped Files")

import os

from app import SketchLoadError
from app.io import load
from sk1libs.utils import sh_quote

class GZIPLoader:

	def __init__(self, file, filename, match):
		self.file = file
		self.filename = filename
		self.match = match
		self.messages = ''
		self.doc_class = None

	def set_doc_class(self, doc_class):
		self.doc_class = doc_class

	def Load(self):
		if self.filename:
			basename, ext = os.path.splitext(self.filename)
			if ext != '.gz':
				basename = self.filename
			stream = os.popen('gzip -d -c ' + sh_quote(self.filename))
			doc = load.load_drawing_from_file(stream, basename,
												doc_class = self.doc_class)
			if doc:
				doc.meta.compressed = "gzip"
				doc.meta.compressed_file = self.filename
				self.messages = doc.meta.load_messages
			return doc
		raise SketchLoadError('gziploader must be instantiated with filename')

	def Messages(self):
		return self.messages

