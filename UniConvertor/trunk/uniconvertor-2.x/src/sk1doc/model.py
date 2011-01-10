# -*- coding: utf-8 -*-
#
# sK1 document object model classes
#
# Copyright (C) 2010 Igor E. Novikov
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA 



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

class Page(StructuralObject):
	format = []

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
