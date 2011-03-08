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

from abstract import AbstractLoader, AbstractSaver

class SKX_Loader(AbstractLoader):
	name = 'SKX_Loader'
	options = {}
	
	def __init__(self):
		AbstractLoader.__init__(self)
		
	def load(self, presenter, path):
		self.presenter = presenter
		self.path = path

class SKX_Saver(AbstractSaver):
	name = 'SKX_Saver'
	options = {}
	
	def __init__(self):
		AbstractSaver.__init__(self)
		
	def save(self, presenter, path):
		self.presenter = presenter
		self.path = path
		