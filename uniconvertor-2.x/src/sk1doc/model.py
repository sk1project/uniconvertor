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

from copy import deepcopy

import uc2
from uc2 import uc_conf
from uc2 import _ 


# Document object enumeration
DOCUMENT = 0

METAINFO = 10
STYLES = 11
STYLE = 12
PROFILES = 13
FONTS = 14
IMAGES = 15

STRUCTURAL_CLASS = 50
PAGES = 51
PAGE = 52
LAYER_GROUP = 53
MASTER_LAYERS = 54
LAYER = 55
MASTER_LAYER = 56
GRID_LAYER = 57
GUIDE_LAYER = 58

SELECTABLE_CLASS = 100
COMPOUND_CLASS = 101
GROUP = 102
CLIP_GROUP = 103
TEXT_BLOCK = 104
TEXT_COLUMN = 105

PRIMITIVE_CLASS = 200
RECTANGLE = 201
CIRCLE = 202
POLYGON = 203
CURVE = 204
CHAR = 205
IMAGE = 206


class DocumentObject:
	"""
	Abstract parent class for all document 
	objects. Provides common object properties.
	"""	
	cid = 0
	parent = None
	config = None
	childs = []


class Document(DocumentObject):
	"""
	Represents sK1 Document object.
	This is a root DOM instance.
	"""	
	cid = DOCUMENT
	metainfo = None
	styles = []
	profiles = []
	
	
	def __init__(self, config):
		self.config = config
		self.childs = [Pages(self.config, self),
					MasterLayers(self.config, self),
					GridLayer(self.config, self),
					GuideLayer(self.config, self)]
		

class Pages(DocumentObject):
	"""
	Container for pages.
	Page format: [format name, (width, height), orientation]
	"""
	cid = PAGES
	page_format = []
	page_counter = 0
	
	def __init__(self, config, parent=None):
		self.parent = parent
		self.config = config		 
		format = '' + self.config.page_format
		size = uc_conf.PAGE_FORMATS[format]
		orient = config.page_orientation
		self.page_format = [format, size, orient]
		name = _('Page') + ' %s' % (self.page_counter + 1)
		self.childs = [Page(self.config, self, name)]
		self.page_counter += 1


#================Structural Objects==================

class StructuralObject(DocumentObject):
	"""
	Abstract parent for structural objects.
	"""
	cid = STRUCTURAL_CLASS
	name = ''

class Page(StructuralObject):
	"""
	PAGE OBJECT
	All child layers are in childs list.
	Page format: [format name, (width, height), orientation]
	"""
	cid = PAGE
	format = []
	name = ''
	
	layer_counter = 0
	
	def __init__(self, config, parent=None , name=_('Page')):
		self.parent = parent
		self.config = config
		self.name = name
		if parent is None:
			format = '' + self.config.page_format
			size = uc_conf.PAGE_FORMATS[format]
			orient = config.page_orientation
			self.format = [format, size, orient]
		else:
			self.format = deepcopy(parent.page_format)
		name = _('Layer') + ' %s' % (self.layer_counter + 1)
		self.childs = [Layer(self.config, self, name)]
		self.layer_counter += 1

class Layer(StructuralObject):
	cid = LAYER
	color = ''
	name = ''
	
	def __init__(self, config, parent=None, name=_('Layer')):
		self.parent = parent
		self.config = config
		self.name = name
		self.color = '' + self.config.layer_color
		self.childs = []
		
class GuideLayer(Layer):
	cid = GUIDE_LAYER
	
	def __init__(self, config, parent=None, name=_('GuideLayer')):
		Layer.__init__(self, config, parent, name)
		self.color = '' + self.config.guide_color

class GridLayer(Layer):
	cid = GRID_LAYER
	grid = []
	
	def __init__(self, config, parent=None, name=_('GridLayer')):
		Layer.__init__(self, config, parent, name)
		self.color = '' + self.config.grid_color
		self.grid = [] + self.config.grid_geometry
		
class LayerGroup(StructuralObject):
	cid = LAYER_GROUP
	layer_counter = 0
	
	def __init__(self, config, parent=None):
		self.parent = parent
		self.config = config
		self.childs = []	

class MasterLayers(LayerGroup):
	cid = MASTER_LAYERS
	
	def __init__(self, config, parent=None):
		LayerGroup.__init__(self, config, parent)
	


#================Selectable Objects==================
class SelectableObject(DocumentObject):
	"""
	Abstract parent class for selectable objects. 
	Provides common selectable object properties.
	"""
	cid = SELECTABLE_CLASS
	trafo = []
	bbox = []
	style = None
	

#---------------Compound objects---------------------
class Group(SelectableObject):pass
class ClipGroup(SelectableObject):pass
class TextBlock(SelectableObject):pass
class ColumnText(SelectableObject):pass

#---------------Primitives---------------------------
class Rectangle(SelectableObject):pass
class Circle(SelectableObject):pass
class Polygon(SelectableObject):pass
class Curve(SelectableObject):pass
class Char(SelectableObject):pass
class Image(SelectableObject):pass
