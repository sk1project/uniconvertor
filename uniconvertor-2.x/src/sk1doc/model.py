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
	
	guide_layer = None
	grid_layer = None
	master_layers = []
	pages = []
	
	current_page = None
	active_layer = None
	selection = None 
	undo = None

class DocumentObject:
	"""
	Abstract parent class for all document 
	child objects. Provides common object properties.
	"""
	is_doc = False
	is_selectable = False

class StructuralObject(DocumentObject):
	"""
	Abstract parent class for structural objects. 
	Provides common structural object properties.
	"""	
	objects = []
	name = ''

class SelectableObject(DocumentObject):
	"""
	Abstract parent class for selectable objects. 
	Provides common selectable object properties.
	"""
	is_selectable = True
	bbox = []

#================Structural Objects==================

PORTRAIT = 0
LANDSCAPE = 1

class Page(StructuralObject):
	format = []
	orientaion = PORTRAIT

class Layer(StructuralObject):
	color = []

class GuideLayer(Layer):
	name = 'Guide Layer'
	color = []

class GridLayer(Layer):
	name = 'Grid Layer'
	color = []

#================Selectable Objects==================

class Rectangle(SelectableObject):
	pass
