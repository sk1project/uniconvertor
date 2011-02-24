# -*- coding: utf-8 -*-


# Copyright (C) 2010-2011 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.



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
