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


# Document object enumeration
DOCUMENT = 0

STRUCTURAL_CLASS = 50

SELECTABLE_CLASS = 100
COMPOUND_CLASS = 101

PRIMITIVE_CLASS = 200


class Document:
	"""
	Represents sK1 Document object.
	This is a root DOM instance.
	"""
	is_doc = True
	
	page_format = []
	guide_layer = None
	grid_layer = None
	master_layers = []
	pages = []
	
	active_page = None
	
	page_count = 0

class DocumentObject:
	"""
	Abstract parent class for all document 
	child objects. Provides common object properties.
	"""
	is_doc = False
	is_selectable = False
	parent = None

#----------------------------------------------------
class StructuralObject(DocumentObject):
	"""
	Abstract parent class for structural objects. 
	Provides common structural object properties.
	"""	
	is_printable = True
	is_editable = True
	is_visible = True
	objects = []
	name = ''

#================Structural Objects==================

class Page(StructuralObject):
	'''
	PAGE OBJECT
	All child layers are in objects list.
	Page format: [format name, (width, height), orientation]
	'''
	format = []
	active_layer = None
	layer_count = 0

class Layer(StructuralObject):
	color = []

class GuideLayer(Layer):
	name = 'Guide Layer'

class GridLayer(Layer):
	name = 'Grid Layer'
	grid = []


#----------------------------------------------------

class SelectableObject(DocumentObject):
	"""
	Abstract parent class for selectable objects. 
	Provides common selectable object properties.
	"""
	is_selectable = True
	bbox = []
#================Selectable Objects==================

class Rectangle(SelectableObject):
	pass
