# -*- coding: utf-8 -*-


# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

from pagelayout import PageLayout
from compound import EditableCompound

class Page(EditableCompound):
	
	name=""	
	page_layout=None
	objects=[]
	is_Page=1
	is_Bezier=0
	is_Plugin=0
	
	def __init__(self, name="", page_layout=PageLayout(), *args, **kw):
		self.name=name
		self.page_layout=page_layout
		EditableCompound.__init__(self, *args, **kw)
	
	def CanSelect(self):
		return 0
	
	def SaveToFile(self, file):	
		file.Page(self.name, self.page_layout.paperformat, self.page_layout.width, 
				self.page_layout.height, self.page_layout.orientation)
		for layer in self.objects:
		    layer.SaveToFile(file)
	
	