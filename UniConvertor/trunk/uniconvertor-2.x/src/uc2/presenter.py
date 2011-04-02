# -*- coding: utf-8 -*-
#
#	Copyright (C) 2011 by Igor E. Novikov
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import uc2
import sk1doc

from uc2 import _
from uc2.sk1doc import model
from uc2 import utils
from uc2.utils import fs
from uc2 import formats
from uc2.methods import UCMethods

class UCDocPresenter:

	config = None
	doc_dir = ''

	model = None
	methods = None
	renderer = None
	doc_file = ''
	doc_id = ''

	active_page = None
	active_layer = None


	def __init__(self, config=uc2.config, appdata=uc2.appdata):
		self.config = config
		self.appdata = appdata
		self.doc_id = utils.generate_id()


	def new(self):
		self.model = sk1doc.create_new_doc(self.config)
		self.active_page = self.model.childs[0].childs[0]
		self.active_layer = self.active_page.childs[0]
		self.methods = UCMethods(self)
		self.create_cache_structure()

	def load(self, path):
		if path and os.path.lexists(path):
			try:
				loader = formats.get_loader(path)
				self.create_cache_structure()
				self.model = loader.load(self, path)
			except:
				self.close()
				raise IOError(_('Error while loading') + ' ' + path,
							sys.exc_info()[1], sys.exc_info()[2])

			self.doc_file = path
			self.active_page = self.model.childs[0].childs[0]
			self.active_layer = self.active_page.childs[0]
			self.methods = UCMethods(self)
		else:
			raise IOError(_('Error while loading:') + ' ', _('Empty file name'))

	def save(self, path):
		if path:
			try:
				saver = formats.get_saver(path)
				if saver is None:
					ext = os.path.splitext(path)[1]
					ext = ext.upper().replace('.', '')
					msg = _('Cannot find export filter for %s format') % (ext)
					raise IOError(msg)
				saver.save(self, path)
			except:
				raise IOError(_('Error while saving') + ' ' + path,
							sys.exc_info()[1], sys.exc_info()[2])
		else:
			raise IOError(_('Error while saving:') + ' ', _('Empty file name'))

	def merge(self):
		pass

	def close(self):
		self.doc_file = ''
		self.active_page = None
		self.active_layer = None
		self.model = None
		try:
			fs.xremove_dir(self.doc_dir)
		except IOError:
			print 'error', sys.exc_info()
			pass

	def get_page_size(self, page=None):
		if page is None:
			page_format = self.active_page.page_format
		else:
			page_format = page.page_format
		if page_format[2]:
			h, w = page_format[1]
		else:
			w, h = page_format[1]
		return w, h

	def create_cache_structure(self):
		doc_cache_dir = os.path.join(self.appdata.app_config_dir, 'docs_cache')
		self.doc_dir = os.path.join(doc_cache_dir, 'doc_' + self.doc_id)
		for dir in sk1doc.DOC_STRUCTURE:
			path = os.path.join(self.doc_dir, dir)
			os.makedirs(path)
		mime = open(os.path.join(self.doc_dir, 'mimetype') , 'wb')
		mime.write(sk1doc.DOC_MIME)
		mime.close()
