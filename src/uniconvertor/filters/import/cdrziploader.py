# -*- coding: utf-8 -*-

# Copyright (C) 2008 by Igor E. Novikov
#
# This library is covered by GNU General Public License v2.0.
# For more info see COPYRIGHTS file in sK1 root directory.

###Sketch Config
#type = Import
#class_name = 'CDRZIPLoader'
#rx_magic = 'PK'
#tk_file_type = ('CorelDRAW X4 files', '.cdr')
#format_name = 'zipped-Meta'
#standard_messages = 1
###End

(''"zipped CDR files")

import os

from app import SketchLoadError
from app.io import load
from zipfile import ZipFile
from tempfile import NamedTemporaryFile

class CDRZIPLoader:

	def __init__(self, file, filename, match):
		self.file = file
		self.filename = filename
		self.match = match
		self.messages = ''
		self.doc_class = None

	def set_doc_class(self, doc_class):
		self.doc_class = doc_class

	def Load(self):
		doc = None
		basename, ext = os.path.splitext(self.filename)
		if ext == '.cdr':			
			file = ZipFile(self.filename)			
			target=None
			for name in file.namelist():
				if name[-3:]=='cdr':
					target=name
					break
			if target:
				cdrfile=NamedTemporaryFile()
				content = file.read(target)				
				cdrfile.write(content)
				cdrfile.file.seek(0)
				doc = load.load_drawing_from_file(cdrfile, cdrfile.name, doc_class = self.doc_class)
				cdrfile.close()
			file.close()
			
		return doc

	def Messages(self):
		return self.messages

