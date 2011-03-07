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
from uc2 import config
from uc2 import uc_conf
from uc2 import _ 


# Document object enumeration
DOCUMENT = 0

METAINFO = 10
STYLES = 11
STYLE = 12
PROFILES = 13
PROFILE = 14
FONTS = 15
FONT = 16
IMAGES = 17
IMAGE = 18

STRUCTURAL_CLASS = 50
PAGES = 51
PAGE = 52
LAYER_GROUP = 53
MASTER_LAYERS = 54
LAYER = 55
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
PIXMAP = 206

CID_TO_NAME = {
	DOCUMENT: _('Document'),
	
	METAINFO: _('Metainfo'), STYLES: _('Styles'), STYLE: _('Style'), 
	PROFILES: _('Profiles'), PROFILE: _('Profile'), FONTS: _('Fonts'), 
	FONT: _('Font'),IMAGES: _('Images'), IMAGE: _('Image'),
	
	PAGES: _('Pages'), PAGE: _('Page'), LAYER_GROUP: _('Layer group'), 
	MASTER_LAYERS: _('Master layers'), LAYER: _('Layer'), 
	GRID_LAYER: _('Grid layer'), GUIDE_LAYER: _('Guide layer'),
	
	GROUP: _('Group'), CLIP_GROUP: _('Clip group'), 
	TEXT_BLOCK: _('Text block'), TEXT_COLUMN: _('Text column'),
	
	RECTANGLE: _('Rectangle'), CIRCLE: _('Ellipse'), 
	POLYGON: _('Polygon'), CURVE: _('Curve'),
	CHAR: _('Char'), PIXMAP: _('Pixmap'),
	}


CID_TO_TAGNAME = {
	DOCUMENT: 'Document',
	
	METAINFO: 'Metainfo', STYLES: 'Styles', STYLE: 'Style', 
	PROFILES: 'Profiles', PROFILE: 'Profile', FONTS: 'Fonts', 
	FONT: 'Font',IMAGES: 'Images', IMAGE: 'Image',
	
	PAGES: 'Pages', PAGE: 'Page', LAYER_GROUP: 'LayerGroup', 
	MASTER_LAYERS: 'MasterLayers', LAYER: 'Layer', 
	GRID_LAYER: 'GridLayer', GUIDE_LAYER: 'GuideLayer',
	
	GROUP: 'Group', CLIP_GROUP: 'ClipGroup', 
	TEXT_BLOCK: 'TextBlock', TEXT_COLUMN: 'TextColumn',
	
	RECTANGLE: 'Rectangle', CIRCLE: 'Ellipse', 
	POLYGON: 'Polygon', CURVE: 'Curve',
	CHAR: 'Char', PIXMAP: 'Pixmap',
	}

class DocumentObject:
	"""
	Abstract parent class for all document 
	objects. Provides common object properties.
	"""	
	cid = 0
	parent = None
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
	doc_origin = 1
	
	def __init__(self):
		self.doc_origin = config.doc_origin
		self.childs = [Pages(self),
					MasterLayers(self),
					GridLayer(self),
					GuideLayer(self)]
		

class Pages(DocumentObject):
	"""
	Container for pages.
	Page format: [format name, (width, height), orientation]
	"""
	cid = PAGES
	page_format = []
	page_counter = 0
	
	def __init__(self, parent=None):
		self.parent = parent		 
		format = '' + config.page_format
		size = uc_conf.PAGE_FORMATS[format]
		orient = config.page_orientation
		self.page_format = [format, size, orient]
		name = _('Page') + ' %s' % (self.page_counter + 1)
		self.childs = [Page(self, name)]
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
	
	def __init__(self, parent=None , name=_('Page')):
		self.parent = parent
		self.name = name
		if parent is None:
			format = '' + config.page_format
			size = uc_conf.PAGE_FORMATS[format]
			orient = config.page_orientation
			self.format = [format, size, orient]
		else:
			self.format = deepcopy(parent.page_format)
		name = _('Layer') + ' %s' % (self.layer_counter + 1)
		self.childs = [Layer(self, name)]
		self.layer_counter += 1

class Layer(StructuralObject):
	cid = LAYER
	color = ''
	name = ''
	
	def __init__(self, parent=None, name=_('Layer')):
		self.parent = parent
		self.name = name
		self.color = '' + config.layer_color
		self.childs = []
		
class GuideLayer(Layer):
	cid = GUIDE_LAYER
	
	def __init__(self, parent=None, name=_('GuideLayer')):
		Layer.__init__(self, parent, name)
		self.color = '' + config.guide_color

class GridLayer(Layer):
	cid = GRID_LAYER
	grid = []
	
	def __init__(self, parent=None, name=_('GridLayer')):
		Layer.__init__(self, parent, name)
		self.color = '' + config.grid_color
		self.grid = [] + config.grid_geometry
		
class LayerGroup(StructuralObject):
	cid = LAYER_GROUP
	layer_counter = 0
	
	def __init__(self, parent=None):
		self.parent = parent
		self.childs = []	

class MasterLayers(LayerGroup):
	cid = MASTER_LAYERS
	
	def __init__(self, parent=None):
		LayerGroup.__init__(self, parent)
	


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
class TextColumn(SelectableObject):pass

#---------------Primitives---------------------------
class Rectangle(SelectableObject):pass
class Circle(SelectableObject):pass
class Polygon(SelectableObject):pass
class Curve(SelectableObject):pass
class Char(SelectableObject):pass
class Pixmap(SelectableObject):pass



CID_TO_CLASS = {
	DOCUMENT: Document,
	
	METAINFO: None, STYLES: None, STYLE: None, 
	PROFILES: None, PROFILE: None, FONTS: None, 
	FONT: None,IMAGES: None, IMAGE: None,
	
	PAGES: Pages, PAGE: Page, LAYER_GROUP: LayerGroup, 
	MASTER_LAYERS: MasterLayers, LAYER: Layer, 
	GRID_LAYER: GridLayer, GUIDE_LAYER: GuideLayer,
	
	GROUP: Group, CLIP_GROUP: ClipGroup, 
	TEXT_BLOCK: TextBlock, TEXT_COLUMN: TextColumn,
	
	RECTANGLE: Rectangle, CIRCLE: Circle, 
	POLYGON: Polygon, CURVE: Curve,
	CHAR: Char, PIXMAP: Pixmap,
	}