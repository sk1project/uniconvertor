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

import uc2
import sk1doc

from uc2.sk1doc import model

class UCDocPresenter:	
	
	config = None
	
	model = None
	renderer = None
	doc_file = ''
	
	active_page = None
	active_layer = None
	
	def __init__(self, config=uc2.config):
		self.config = config
		
	def new(self):
		self.model = model.Document(self.config)
		self.active_page = self.model.childs[0].childs[0]
		self.active_layer = self.active_page.childs[0]
	
	def load(self, filename):
		self.doc_file = filename
		#FIXME: Here should be file loading
		self.model = model.Document(self.config)
		self.active_page = self.model.childs[0].childs[0]
		self.active_layer = self.active_page.childs[0]
	
	def save(self):
		pass
	
	def merge(self):
		pass
	
	def close(self):
		self.doc_file = ''
		self.active_page = None
		self.active_layer = None
		self.model = None
		
	def get_page_size(self):
		if self.active_page.format[2]:
			h, w = self.active_page.format[1]
		else:
			w, h = self.active_page.format[1]
		return w, h
		