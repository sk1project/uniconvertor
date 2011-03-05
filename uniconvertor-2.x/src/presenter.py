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

class UCDocPresenter:	
	
	config = None
	
	model = None
	renderer = None
	doc_file = ''
	doc_name = ''
	
	def __init__(self, config=uc2.config):
		self.config = config
		
	def new(self):
		pass
	
	def load(self):
		pass
	
	def save(self):
		pass
	
	def merge(self):
		pass
	
	def close(self):
		pass