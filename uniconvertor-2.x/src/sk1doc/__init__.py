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
import model
from uc2 import _, uc_conf

                                               

def create_new_document(config=uc2.config):
	
	doc = model.Document()
	set_page_format(doc, None, config.page_format, config.page_orientation)
	
	doc.guide_layer = model.GuideLayer()
	doc.guide_layer.objects = []
	# FIXME: layer should have default color 
	
	doc.grid_layer = model.GridLayer()
	doc.grid_layer.objects = []
	# FIXME: layer should have default color and grid value
	
	doc.master_layers = []
	doc.pages = []
	
	add_new_page(doc)	
	return doc
	
	
def set_page_format(doc=None, page=None, format=None, orientation=None, config=uc2.config):
	data = []
	
	if not format or not uc_conf.PAGE_FORMATS.has_key(format):
		format = config.page_format
	data.append(format)
	data.append(uc_conf.PAGE_FORMATS[format])
	
	if orientation is None:
		orientation = config.page_orientation
	data.append(orientation)
	
	if page is None:
		doc.page_format = data
	else:
		page.format = data
	return data

def get_page_size(doc):
	if doc.active_page.format[2]:
		h, w = doc.active_page.format[1]
	else:
		w, h = doc.active_page.format[1]
	return w, h
		
def add_new_page(doc, position=None):
	page = model.Page()
	page.format = [] + doc.page_format
	page.name = _('Page') + ' %s' % (doc.page_count + 1)
	
	#FIXME: add page inserting
	doc.pages.append(page)
	
	page.parent = doc
	doc.active_page = page
	doc.page_count += 1
	page.objects = []
	add_new_layer(page)
	return page
	
def add_new_layer(page, position=None):
	layer = model.Layer()
	layer.name = _('Layer') + ' %s' % (page.layer_count + 1)
	# FIXME: layer should have default color
	
	#FIXME: add layer inserting
	page.objects.append(layer)
	
	layer.parent = page
	layer.objects = []
	page.active_layer = layer
	page.layer_count += 1
	return layer
	
	
		
	
	
