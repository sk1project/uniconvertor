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

DOC_MIME = 'application/vnd.sk1project.skx-graphics'

DOC_EXTENSION = '.skx'

DOC_STRUCTURE = [
'Fonts', 
'Images', 
'META-INF', 
'Palettes', 
'Previews', 
'Profiles', 
'Thumbnails', 
]

DOC_ORIGIN_CENTER = 0
DOC_ORIGIN_LL = 1
DOC_ORIGIN_LU = 2
ORIGINS = [DOC_ORIGIN_CENTER, DOC_ORIGIN_LL, DOC_ORIGIN_LU]
	
def create_new_doc(config=uc2.config):
	doc = model.Document(config)
	
	layer = model.Layer(config)
	page = model.Page(config)
	add_child(page, layer)
	page.layer_counter += 1
	
	pages = model.Pages(config)
	add_child(pages, page)
	pages.page_counter += 1
	
	ml = model.MasterLayers(config)
	gl = model.GridLayer(config)
	guide = model.GuideLayer(config)
	add_childs(doc, [pages, ml, gl, guide])
	
	return doc
	
	
def add_childs(parent, childs=[]):
	if childs:
		for child in childs:
			parent.childs.append(child)
			child.parent = parent
			
def add_child(parent, child):
	add_childs(parent, [child,])
	
	
