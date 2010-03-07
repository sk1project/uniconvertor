# Sketch - A Python-based interactive drawing program
# Copyright (C) 1996, 1997, 1998, 1999, 2000 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

#
# Classes:
#
# SketchDocument
# EditDocument(SketchDocument)
#
# The document class represents a complete Sketch drawing. Each drawing
# consists of one or more Layers, which in turn consist of zero of more
# graphics objects. Graphics objects can be primitives like rectangles
# or curves or composite objects like groups which consist of graphics
# objects themselves. Objects may be arbitrarily nested.
#
# The distinction between SketchDocument and EditDocument has only
# historical reasons...
#

from types import ListType, IntType, StringType, TupleType
from string import join

from app.events.warn import pdebug, warn, warn_tb, USER, INTERNAL
from app import SketchInternalError


from app import config, _
from app.events.connector import Issue, RemovePublisher, Connect, Disconnect, QueueingPublisher, Connector
from app.events.undodict import UndoDict

from app import Rect, Point, UnionRects, InfinityRect, Trafo, Rotation, Translation, Scale
from app import UndoRedo, Undo, CreateListUndo, NullUndo, UndoAfter
import app
import color, selinfo, pagelayout

from base import Protocols
from layer import Layer, GuideLayer, GridLayer
from group import Group
from bezier import CombineBeziers
from properties import EmptyProperties
from pattern import SolidPattern
import guide
from selection import SizeSelection, EditSelection, TrafoSelection, TrafoRectangle
from math import *
from app.conf.const import STYLE, SELECTION, EDITED, MODE, UNDO, REDRAW, LAYOUT, PAGE
from app.conf.const import LAYER, LAYER_ORDER, LAYER_ACTIVE, GUIDE_LINES, GRID
from app.conf.const import SelectSet, SelectAdd,SelectSubtract,SelectSubobjects,\
		SelectDrag, SelectGuide, Button1Mask
from app.conf.const import SCRIPT_OBJECT, SCRIPT_OBJECTLIST, SCRIPT_GET

#
from text import CanCreatePathText, CreatePathText


# SketchDocument is derived from Protocols for the benefit of the loader
# classes

class SketchDocument(Protocols):

	can_be_empty = 1

	script_access = {}

	def __init__(self, create_layer = 0):
		self.pages = []
		self.active_page=0
		self.snap_grid = GridLayer()
		self.snap_grid.SetDocument(self)
		self.guide_layer = GuideLayer(_("Guide Lines"))
		self.guide_layer.SetDocument(self)
		layer=Layer(_("MasterLayer 1"))
		layer.SetDocument(self)
		layer.is_MasterLayer=1
		self.master_layers=[layer]
		if create_layer:
			# a new empty document
			self.active_layer = Layer(_("Layer 1"))
			self.active_layer.SetDocument(self)
			self.layers = [self.snap_grid]+[self.active_layer] + self.master_layers + [self.guide_layer]
			self.pages.append([self.active_layer])
		else:
			# we're being created by the load module
			self.active_layer = None
			self.layers = []
			self.pages.append(self.layers)

	def __del__(self):
		if __debug__:
			pdebug('__del__', '__del__', self.meta.filename)

	def __getitem__(self, idx):
		if type(idx) == IntType:
			return self.layers[idx]
		elif type(idx) == TupleType:
			if len(idx) > 1:
				return self.layers[idx[0]][idx[1:]]
			elif len(idx) == 1:
				return self.layers[idx[0]]
		raise ValueError, 'invalid index %s' % `idx`

	def AppendLayer(self, layer_name = None, master=0, *args, **kw_args):
		try:
			old_layers = self.layers[:]
			if layer_name is None:
				layer_name = _("Layer %d") % (len(self.layers) + 1)
			else:
				layer_name = str(layer_name)
			layer = apply(Layer, (layer_name,) + args, kw_args)
			layer.SetDocument(self)
			if master:
				layer.is_MasterLayer=1
				mlayers=self.getMasterLayers()
				mlayers.append(layer)
				self.layers = [self.snap_grid] + self.getRegularLayers() + mlayers + [self.guide_layer]
			else:
				rlayers=self.getRegularLayers()
				rlayers.append(layer)
				self.layers = [self.snap_grid] + rlayers + self.getMasterLayers() + [self.guide_layer]
			if not self.active_layer:
				self.active_layer = layer			
			return layer
		except:
			self.layers[:] = old_layers
			raise
	script_access['AppendLayer'] = SCRIPT_OBJECT
	
	def RearrangeLayers(self):
		if not len(self.getMasterLayers()):
			layer=Layer(_("MasterLayer 1"))
			layer.SetDocument(self)
			layer.is_MasterLayer=1
			self.layers.append(layer)
		self.layers = [self.snap_grid] + self.getRegularLayers() + self.getMasterLayers() + [self.guide_layer]
	
	def getRegularLayers(self):
		result=[]
		for layer in self.layers:
			if not layer.is_SpecialLayer and not layer.is_MasterLayer:
				result.append(layer)
		return result
	
	def getMasterLayers(self):
		result=[]
		for layer in self.layers:
			if layer.is_MasterLayer:
				result.append(layer)
		return result
	
	def insert_pages(self, number=1, index=0, is_before=0):
		for item in range(number):
			if is_before:
				self.pages.insert(index, self.NewPage())
				self.active_page+=1
				self.setActivePage(index)
			else:
				self.pages.insert(index+item+1, self.NewPage())
				self.setActivePage(index+1)	
			
	def setActivePage(self, index):
		self.pages[self.active_page]=self.getRegularLayers()
		self.layers=[self.snap_grid] + self.pages[index] + self.getMasterLayers() + [self.guide_layer]
		self.active_page=index
		self.active_layer=(self.pages[index])[0]

	def updateActivePage(self):
		self.pages[self.active_page]=self.getRegularLayers()
		
	def NewPage(self):
		page=[]
		new_layer=Layer(_("Layer 1"))
		new_layer.SetDocument(self)
		page.append(new_layer)
		return page				
	
	def delete_page(self, index=0):
		if len(self.pages)==1:
			return
		if self.active_page and index == self.active_page:
			self.setActivePage(index-1)
		if not self.active_page and index == self.active_page:
			self.setActivePage(1)
			self.active_page=0	
		if self.active_page and self.active_page>index:
			self.active_page-=1					
		self.pages.remove(self.pages[index])
		
	def delete_pages(self, number=1, index=0,is_before=0):
		for item in range(number):
			self.delete_page(index+is_before)

	def move_page(self, index=0, backward=0):
		if index==0 or index==len(self.pages)-1:
			return
		else:
			page=self.pages[index]
			self.pages.remove(page)
			self.pages.insert(index+1-2*backward, page)
		if index==self.active_page:
			self.active_page=self.active_page+1-2*backward
			

	def BoundingRect(self, visible = 1, printable = 0):
		rects = []
		for layer in self.layers:
			if ((visible and layer.Visible())
				or (printable and layer.Printable())):
				rect = layer.bounding_rect
				if rect and rect != InfinityRect:
					rects.append(rect)
		if rects:
			return reduce(UnionRects, rects)
		return None
	script_access['BoundingRect'] = SCRIPT_GET

	def augment_sel_info(self, info, layeridx):
		if type(layeridx) != IntType:
			layeridx = self.layers.index(layeridx)
		return selinfo.prepend_idx(layeridx, info)

	def insert(self, object, at = None, layer = None):
		undo_info = None
		try:
			if layer is None:
				layer = self.active_layer
			elif type(layer) == IntType:
				layer = self.layers[layer]
			if layer is None or layer.Locked():
				raise SketchInternalError('Layer %s is locked' % layer)
			if type(object) == ListType:
				for obj in object:
					obj.SetDocument(self)
			else:
				object.SetDocument(self)
			sel_info, undo_info = layer.Insert(object, at)
			sel_info = self.augment_sel_info(sel_info, layer)
			return (sel_info, undo_info)
		except:
			if undo_info is not None:
				Undo(undo_info)
			raise

	def selection_from_point(self, p, hitrect, device, path = None):
		# iterate top down (i.e. backwards) through the list of layers
		if path:
			path_layer = path[0]
			path = path[1:]
		else:
			path_layer = -1
		for idx in range(len(self.layers) - 1, -1, -1):
			if idx == path_layer:
				info = self.layers[idx].SelectSubobject(p, hitrect, device, path)
			else:
				info = self.layers[idx].SelectSubobject(p, hitrect, device)
			if info:
				return self.augment_sel_info(info, idx)
		else:
			return None

	def selection_from_rect(self, rect):
		info = []
		for layer in self.layers:
			info = info + self.augment_sel_info(layer.SelectRect(rect), layer)
		return info

	def Draw(self, device, rect = None):
		for layer in self.layers:
			layer.Draw(device, rect)

	def Grid(self):
		return self.snap_grid

	def SnapToGrid(self, p):
		return self.snap_grid.Snap(p)

	def SnapToGuide(self, p, maxdist):
		return self.guide_layer.Snap(p) #, maxdist)

	def DocumentInfo(self):
		info = []
		info.append('%d layers' % len(self.layers))
		for idx in range(len(self.layers)):
			layer = self.layers[idx]
			info.append('%d: %s,\t%d objects' % (idx + 1, layer.name,
													len(layer.objects)))
		return join(info, '\n')

	def SaveToFile(self, file):
		self.updateActivePage()
		file.BeginDocument()
		self.page_layout.SaveToFile(file)
		self.write_styles(file)
		self.snap_grid.SaveToFile(file)
		
		pagesnum=len(self.pages)
		pagecount=0
		interval=100/pagesnum			
		for page in self.pages:
			file.Page()
			pagecount+=1
			app.updateInfo(inf2=_('Saving page %u of %u')%(pagecount,pagesnum),
						 inf3=interval*pagecount)			
			layercount=0
			layersnum=len(page)
			l_interval=interval/layersnum
			for layer in page:
				layercount+=1
				app.updateInfo(inf2=_('Saving page %u of %u, layer %u of %u')%
							(pagecount,pagesnum,layercount,layersnum),
							 inf3=interval*pagecount)
				layer.SaveToFile(file)			

		for layer in self.getMasterLayers():
			layer.SaveToFile(file)			
		self.guide_layer.SaveToFile(file)
		file.EndDocument()

	def load_AppendObject(self, layer):
		self.layers.append(layer)

	def load_Done(self):
		pass

	def load_Completed(self):
		if not self.layers:
			self.layers = [Layer(_("Layer 1"))]
		if self.active_layer is None:
			for layer in self.layers:
				if layer.CanSelect():
					self.active_layer = layer
					break
		add_guide_layer = add_grid_layer = 1
		for layer in self.layers:
			layer.SetDocument(self)
			if isinstance(layer, GuideLayer):
				self.guide_layer = layer
				add_guide_layer = 0
			if isinstance(layer, GridLayer):
				self.snap_grid = layer
				add_grid_layer = 0
		if add_guide_layer:
			self.layers.append(self.guide_layer)
		if add_grid_layer:
			self.layers.append(self.snap_grid)
		self.extract_pages()
		self.RearrangeLayers()
		
	def extract_pages(self):
		layers=self.getRegularLayers()
		if layers[0].is_Page:
			self.pages=[]
			for layer in layers:
				if layer.is_Page:
					page=[]
					self.pages.append(page)
				else:
					page.append(layer)
			pages=[]+self.pages
			for page in pages:
				if not len(page):		
					self.pages.remove(page)
		else:
			self.pages=[]
			self.pages.append(layers)
		self.active_page=0
		self.layers=[self.snap_grid] + self.pages[0] + self.getMasterLayers() + [self.guide_layer]
		self.active_layer=(self.pages[0])[0]

#
#	Class MetaInfo
#
#	Each document has an instance of this class as the variable
#	meta. The application object uses this variable to store various
#	data about the document, such as the name of the file it was
#	read from, the file type, etc. See skapp.py
#
class MetaInfo:
	pass

class AbortTransactionError(SketchInternalError):
	pass

SelectionMode = 0
EditMode = 1

class EditDocument(SketchDocument, QueueingPublisher):

	drag_mask = Button1Mask # canvas sometimes has the doc as current
							# object
	script_access = SketchDocument.script_access.copy()

	def __init__(self, create_layer = 0):
		SketchDocument.__init__(self, create_layer)
		QueueingPublisher.__init__(self)
		self.selection = SizeSelection()
		self.__init_undo()
		self.was_dragged = 0
		self.meta = MetaInfo()
		self.hit_cache = None
		self.connector = Connector()
		self.init_transaction()
		self.init_clear()
		self.init_styles()
		self.init_after_handler()
		self.init_layout()

	def Destroy(self):
		self.undo = None
		self.destroy_styles()
		RemovePublisher(self)
		for layer in self.layers:
			layer.Destroy()
		self.layers = []
		self.active_layer = None
		self.guide_layer = None
		self.snap_grid = None
		# make self.connector empty connector to remove circular refs
		# and to allow object to call document.connector.RemovePublisher
		# in their __del__ methods
		self.connector = Connector()
		self.selection = None
		self.transaction_undo = []
		self.transaction_sel = []

	def queue_layer(self, *args):
		if self.transaction:
			apply(self.queue_message, (LAYER,) + args)
			return (self.queue_layer, args)
		else:
			apply(self.issue, (LAYER,) + args)

	def queue_selection(self):
		self.queue_message(SELECTION)

	def queue_edited(self):
		# An EDITED message should probably indicate the type of edit,
		# i.e. whether properties changed, the geometry of objects
		# changed, etc.; hence the additional string argument which may
		# hold this information in the future
		self.queue_message(EDITED, '')
		return (self.queue_edited,)

	def Subscribe(self, channel, func, *args):
		Connect(self, channel, func, args)

	def Unsubscribe(self, channel, func, *args):
		Disconnect(self, channel, func, args)

	def init_after_handler(self):
		self.after_handlers = []

	def AddAfterHandler(self, handler, args = (), depth = 0):
		handler = (depth, handler, args)
		try:
			self.after_handlers.remove(handler)
		except ValueError:
			pass
		self.after_handlers.append(handler)

	def call_after_handlers(self):
		if not self.after_handlers:
			return 0

		while self.after_handlers:
			handlers = self.after_handlers

			handlers.sort()
			handlers.reverse()
			depth = handlers[0][0]

			count = 0
			for d, handler, args in handlers:
				if d == depth:
					count = count + 1
				else:
					break
			self.after_handlers = handlers[count:]
			handlers = handlers[:count]

			for d, handler, args in handlers:
				try:
					apply(handler, args)
				except:
					warn_tb(INTERNAL, "In after handler `%s'%s", handler, args)

		return 1

	def init_clear(self):
		self.clear_rects = []
		self.clear_all = 0

	reset_clear = init_clear

	def AddClearRect(self, rect):
		self.clear_rects.append(rect)
		return (self.AddClearRect, rect)

	def view_redraw_all(self):
		self.clear_all = 1
		return (self.view_redraw_all,)

	def issue_redraw(self):
		try:
			if self.clear_all:
				Issue(self, REDRAW, 1)
			else:
				Issue(self, REDRAW, 0, self.clear_rects)
		finally:
			self.clear_rects = []
			self.clear_all = 0

	def init_transaction(self):
		self.reset_transaction()

	def reset_transaction(self):
		self.transaction = 0
		self.transaction_name = ''
		self.transaction_sel = []
		self.transaction_undo = []
		self.transaction_sel_ignore = 0
		self.transaction_clear = None
		self.transaction_aborted = 0
		self.transaction_cleanup = []

	def cleanup_transaction(self):
		for handler, args in self.transaction_cleanup:
			try:
				apply(handler, args)
			except:
				warn_tb(INTERNAL, "in cleanup handler %s%s", handler, `args`)
		self.transaction_cleanup = []

	def add_cleanup_handler(self, handler, *args):
		handler = (handler, args)
		try:
			self.transaction_cleanup.remove(handler)
		except ValueError:
			pass
		self.transaction_cleanup.append(handler)

	def begin_transaction(self, name = '', no_selection = 0,
							clear_selection_rect = 1):
		if self.transaction_aborted:
			raise AbortTransactionError
		if self.transaction == 0:
			if not no_selection:
				selinfo = self.selection.GetInfo()[:]
				if selinfo != self.transaction_sel:
					self.transaction_sel = selinfo
				self.transaction_sel_mode = self.selection.__class__
			self.transaction_sel_ignore = no_selection
			self.transaction_name = name
			self.transaction_undo = []
			if clear_selection_rect:
				if self.selection:
					self.transaction_clear = self.selection.bounding_rect
			else:
				self.transaction_clear = None
		elif not self.transaction_name:
			self.transaction_name = name
		self.transaction = self.transaction + 1

	def end_transaction(self, issue = (), queue_edited = 0):
		self.transaction = self.transaction - 1
		if self.transaction_aborted:
			# end an aborted transaction
			if self.transaction == 0:
				# undo the changes already done...
				undo = self.transaction_undo
				undo.reverse()
				map(Undo, undo)
				self.cleanup_transaction()
				self.reset_transaction()
				self.reset_clear()
		else:
			# a normal transaction
			if type(issue) == StringType:
				self.queue_message(issue)
			else:
				for channel in issue:
					self.queue_message(channel)
			if self.transaction == 0:
				# the outermost end_transaction
				# increase transaction flag temporarily because some
				# after handlers might call public methods that are
				# themselves transactions...
				self.transaction = 1
				if self.call_after_handlers():
					self.selection.ResetRectangle()
				self.transaction = 0
				undo = CreateListUndo(self.transaction_undo)
				if undo is not NullUndo:
					undo = [undo]
					if self.transaction_clear is not None:
						undo.append(self.AddClearRect(self.transaction_clear))
						if self.selection:
							self.selection.ResetRectangle()
							rect = self.selection.bounding_rect
							undo.append(self.AddClearRect(rect))
					if queue_edited:
						undo.append(self.queue_edited())
					undo = CreateListUndo(undo)
					if self.transaction_sel_ignore:
						self.__real_add_undo(self.transaction_name, undo)
					else:
						self.__real_add_undo(self.transaction_name, undo,
												self.transaction_sel,
												self.transaction_sel_mode)
				self.flush_message_queue()
				self.issue_redraw()
				self.cleanup_transaction()
				self.reset_transaction()
				self.reset_clear()
			elif self.transaction < 0:
				raise SketchInternalError('transaction < 0')

	def abort_transaction(self):
		self.transaction_aborted = 1
		warn_tb(INTERNAL, "in transaction `%s'" % self.transaction_name)
		raise AbortTransactionError

	# public versions of the transaction methods
	BeginTransaction = begin_transaction
	AbortTransaction = abort_transaction

	def EndTransaction(self):
		self.end_transaction(queue_edited = 1)

	def Insert(self, object, undo_text = _("Create Object")):
		group_flag = 0
		if isinstance(object, guide.GuideLine):
			self.add_guide_line(object)
		else:
			self.begin_transaction(undo_text, clear_selection_rect = 0)
			try:
				try:
					if type(object) == ListType:
						gobject = Group(object)
					else:
						gobject = object
					selected, undo = self.insert(object)
					self.add_undo(undo)
					self.add_undo(self.AddClearRect(gobject.bounding_rect))
					self.__set_selection(selected, SelectSet)
					self.add_undo(self.remove_selected())
					
					extracted_select=[]
					for info, object in self.selection.GetInfo():
						objects=[]
						if type(object) == ListType:
							objects = object
						else:
							objects.append(object)												
						select, undo_insert = self.insert(objects, at = info[1:], layer = info[0])
						extracted_select+=select
						self.add_undo(undo_insert)
					self.__set_selection(extracted_select, SelectSet)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def SelectPoint(self, p, device, type = SelectSet):
		# find object at point, and modify the current selection
		# according to type
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if type == SelectSubobjects:
					path = self.selection.GetPath()
				else:
					path = ()
				rect = device.HitRectAroundPoint(p)
				if self.hit_cache:
					cp, cdevice, hit = self.hit_cache
					self.hit_cache = None
					if p is cp and device is cdevice:
						selected = hit
					else:
						selected = self.selection_from_point(p, rect, device, path)
				else:
					selected = self.selection_from_point(p, rect, device, path)
				if type == SelectGuide:
					if selected and selected[-1].is_GuideLine:
						return selected[-1]
					return None
				elif selected:
					path, object = selected
					if self.layers[path[0]] is self.guide_layer:
						if object.is_GuideLine:
							# guide lines cannot be selected in the
							# ordinary way, but other objects on the
							# guide layer can.
#							pass
########################################################################
########################################################################
							selected = None
				self.__set_selection(selected, type)

				if self.IsEditMode():
					object = self.CurrentObject()
					if object is not None and object.is_Text:
						self.SelectPointPart(p, device, SelectSet)

			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
		return selected

	def SelectRect(self, rect, mode = SelectSet):
		# Find all objects contained in rect and modify the current
		# selection according to mode
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.hit_cache = None
				selected = self.selection_from_rect(rect)
				self.__set_selection(selected, mode)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
		return selected

	def SelectRectPart(self, rect, mode = SelectSet):
		# Select the part of the CSO that lies in rect. Currently this
		# works only in edit mode. For a PolyBezier this means that all
		# nodes within rect are selected.
		if not self.IsEditMode():
			raise SketchInternalError('SelectRectPart requires edit mode')
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.hit_cache = None
				self.selection.SelectRect(rect, mode)
				self.queue_selection()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SelectPointPart(self, p, device, mode = SelectSet):
		# Select the part of the current object under the point p.
		# Like SelectRectPart this only works in edit mode.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.hit_cache = None
				rect = device.HitRectAroundPoint(p)
				self.selection.SelectPoint(p, rect, device, mode)
				if mode != SelectDrag:
					self.queue_selection()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SelectHandle(self, handle, mode = SelectSet):
		# Select the handle indicated by handle. This only works in edit
		# mode.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.hit_cache = None
				self.selection.SelectHandle(handle, mode)
				if mode != SelectDrag:
					self.queue_selection()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SelectAll(self):
		# Select all objects that can currently be selected.
		# XXX should the objects in the guide layer also be selected by
		# this method? (currently they are)
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				sel_info = []
				for layer_idx in range(len(self.layers)):
					sel = self.layers[layer_idx].SelectAll()
					if sel:
						sel = self.augment_sel_info(sel, layer_idx)
						sel_info = sel_info + sel
				self.__set_selection(sel_info, SelectSet)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectAll'] = SCRIPT_GET

	def SelectNone(self):
		# Deselect all objects.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.__set_selection(None, SelectSet)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectNone'] = SCRIPT_GET

	def SelectObject(self, objects, mode = SelectSet):
		# Select the objects defined by OBJECTS. OBJECTS may be a single
		# GraphicsObject or a list of such objects. Modify the current
		# selection according to MODE.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if type(objects) != ListType:
					objects = [objects]
				selinfo = []
				for object in objects:
					selinfo.append(object.SelectionInfo())
				if selinfo:
					self.__set_selection(selinfo, mode)
				else:
					self.__set_selection(None, SelectSet)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	#script_access['SelectObject'] = SCRIPT_GET


	def select_first_in_layer(self, idx = 0):
		for layer in self.layers[idx:]:
			if layer.CanSelect() and not layer.is_SpecialLayer:
				object = layer.SelectFirstChild()
				if object is not None:
					return object

	def SelectNextObject(self):
		# If exactly one object is selected select its next higher
		# sibling. If there is no next sibling and its parent is a
		# layer, select the first object in the next higher layer that
		# allows selections.
		#
		# If more than one object is currently selected, deselect all
		# but the the highest of them.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				info = self.selection.GetInfo()
				if len(info) > 1:
					self.__set_selection(info[-1], SelectSet)
				elif info:
					path, object = info[0]
					parent = object.parent
					object = parent.SelectNextChild(object, path[-1])
					if object is None and parent.is_Layer:
						idx = self.layers.index(parent)
						object = self.select_first_in_layer(idx + 1)
					if object is not None:
						self.SelectObject(object)
				else:
					object = self.select_first_in_layer()
					if object is not None:
						self.SelectObject(object)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectNextObject'] = SCRIPT_GET

	def select_last_in_layer(self, idx):
		if idx < 0:
			return
		layers = self.layers[:idx + 1]
		layers.reverse()
		for layer in layers:
			if layer.CanSelect() and not layer.is_SpecialLayer:
				object = layer.SelectLastChild()
				if object is not None:
					return object

	def SelectPreviousObject(self):
		# If exactly one object is selected select its next lower
		# sibling. If there is no lower sibling and its parent is a
		# layer, select the last object in the next lower layer that
		# allows selections.
		#
		# If more than one object is currently selected, deselect all
		# but the the lowest of them.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				info = self.selection.GetInfo()
				if len(info) > 1:
					self.__set_selection(info[0], SelectSet)
				elif info:
					path, object = info[0]
					parent = object.parent
					object = parent.SelectPreviousChild(object, path[-1])
					if object is None and parent.is_Layer:
						idx = self.layers.index(parent)
						object = self.select_last_in_layer(idx - 1)
					if object is not None:
						self.SelectObject(object)
				else:
					object = self.select_last_in_layer(len(self.layers))
					if object is not None:
						self.SelectObject(object)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectPreviousObject'] = SCRIPT_GET

	def SelectFirstChild(self):
		# If exactly one object is selected and this object is a
		# compound object, select its first (lowest) child. The first
		# child is the object returned by the compound object's method
		# SelectFirstChild. If that method returns none, do nothing.
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				objects = self.selection.GetObjects()
				if len(objects) == 1:
					object = objects[0]
					if object.is_Compound:
						object = object.SelectFirstChild()
						if object is not None:
							self.SelectObject(object)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectFirstChild'] = SCRIPT_GET

	def SelectParent(self):
		# Select the parent of the currently selected object(s).
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if len(self.selection) > 1:
					path = selinfo.common_prefix(self.selection.GetInfo())
					if len(path) > 1:
						object = self[path]
						self.SelectObject(object)
				elif len(self.selection) == 1:
					object = self.selection.GetObjects()[0].parent
					if not object.is_Layer:
						self.SelectObject(object)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
	script_access['SelectParent'] = SCRIPT_GET

	def DeselectObject(self, object):
		# Deselect the object OBJECT.
		# XXX: for large selections this can be very slow.
		selected = self.selection.GetObjects()
		try:
			index = selected.index(object)
		except ValueError:
			return
		info = self.selection.GetInfo()
		del info[index]
		self.__set_selection(info, SelectSet)

	def __set_selection(self, selected, type):
		# Modify the current selection. SELECTED is a list of selection
		# info describing the new selection, TYPE indicates how the
		# current selection is modified:
		#
		# type			Meaning
		# SelectSet		Replace the old selection by the new one
		# SelectSubtract	Subtract the new selection from the old one
		# SelectAdd		Add the new selection to the old one.
		# SelectSubobjects	like SelectSet here
		changed = 0
		if type == SelectAdd:
			if selected:
				changed = self.selection.Add(selected)
		elif type == SelectSubtract:
			if selected:
				changed = self.selection.Subtract(selected)
		elif type == SelectGuide:
			if selected:
				pass
		else:
			# type is SelectSet or SelectSubobjects
			# set the selection. make a size selection if necessary
			if self.selection.__class__ == TrafoSelection:
				self.selection = SizeSelection()
				changed = 1
			changed = self.selection.SetSelection(selected) or changed
		if changed:
			self.queue_selection()

	def SetMode(self, mode):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if mode == SelectionMode:
					self.selection = SizeSelection(self.selection)
				else:
					self.selection = EditSelection(self.selection)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction(issue = (SELECTION, MODE))

	def Mode(self):
		if self.selection.__class__ == EditSelection:
			return EditMode
		return SelectionMode
	script_access['Mode'] = SCRIPT_GET

	def IsSelectionMode(self):
		return self.Mode() == SelectionMode
	script_access['IsSelectionMode'] = SCRIPT_GET

	def IsEditMode(self):
		return self.Mode() == EditMode
	script_access['IsEditMode'] = SCRIPT_GET


	def SelectionHit(self, p, device, test_all = 1):
		# Return true, if the point P hits the currently selected
		# objects.
		#
		# If test_all is true (the default), find the object that would
		# be selected by SelectPoint and return true if it or one of its
		# ancestors is contained in the current selection and false
		# otherwise.
		#
		# If test_all is false, just test the currently selected objects.
		rect = device.HitRectAroundPoint(p)
		if len(self.selection) < 10 or not test_all:
			selection_hit = self.selection.Hit(p, rect, device)
			if not test_all or not selection_hit:
				return selection_hit
		if test_all:
			path = self.selection.GetPath()
			if len(path) > 2:
				path = path[:-1]
			else:
				path = ()
			hit = self.selection_from_point(p, rect, device, path)
			self.hit_cache = (p, device, hit)
			while hit:
				if hit in self.selection.GetInfo():
					return 1
				hit = selinfo.get_parent(hit)
			#self.hit_cache = None
			return 0

	def GetSelectionHandles(self):
		if self.selection:
			return self.selection.GetHandles()
		else:
			return []

	#
	#	Get information about the selected objects
	#

	def HasSelection(self):
		# Return true, if one or more objects are selected
		return len(self.selection)
	script_access['HasSelection'] = SCRIPT_GET

	def CountSelected(self):
		# Return the number of currently selected objects
		return len(self.selection)
	script_access['CountSelected'] = SCRIPT_GET

	def SelectionInfoText(self):
		# Return a string describing the selected object(s)
		return self.selection.InfoText()
	script_access['SelectionInfoText'] = SCRIPT_GET

	def CurrentInfoText(self):
		return self.selection.CurrentInfoText()

	def SelectionBoundingRect(self):
		# Return the bounding rect of the current selection
		return self.selection.bounding_rect
	script_access['SelectionBoundingRect'] = SCRIPT_GET

	def CurrentObject(self):
		# If exactly one object is selected return that, None instead.
		if len(self.selection) == 1:
			return self.selection.GetObjects()[0]
		return None
	script_access['CurrentObject'] = SCRIPT_OBJECT

	def SelectedObjects(self):
		# Return the selected objects as a list. They are listed in the
		# order in which they are drawn.
		return self.selection.GetObjects()
	script_access['SelectedObjects'] = SCRIPT_OBJECTLIST

	def CurrentProperties(self):
		# Return the properties of the current object if exactly one
		# object is selected. Return EmptyProperties otherwise.
		if self.selection:
			if len(self.selection) > 1:
				return EmptyProperties
			return self.selection.GetInfo()[0][-1].Properties()
		return EmptyProperties
	script_access['CurrentProperties'] = SCRIPT_OBJECT


	def CurrentFillColor(self):
		# Return the fill color of the current object if exactly one
		# object is selected and that object has a solid fill. Return
		# None otherwise.
		if len(self.selection) == 1:
			properties = self.selection.GetInfo()[0][-1].Properties()
			try:
				return	properties.fill_pattern.Color()
			except AttributeError:
				pass
		return None
	script_access['CurrentFillColor'] = SCRIPT_GET


	def PickObject(self, device, point, selectable = 0):
		# Return the object that is hit by a click at POINT. The object
		# is not selected and should not be modified by the caller.
		#
		# If selectable is false, this function descends into compound
		# objects that are normally selected as a whole when one of
		# their children is hit. If selectable is true, the search is
		# done as for a normal selection.
		#
		# This method is intended to be used to
		# let the user click on the drawing and extract properties from
		# the indicated object. The fill and line dialogs use this
		# indirectly (through the canvas object's PickObject) for their
		# 'Update From...' button.
		#
		# XXX should this be implemented by calling WalkHierarchy
		# instead of requiring a special PickObject method in each
		# compound? Unlike the normal hit-test, this method is not that
		# time critical and WalkHierarchy is sufficiently fast for most
		# purposes (see extract_snap_points in the canvas).
		# WalkHierarchy would have to be able to traverse the hierarchy
		# top down and not just bottom up.
		object = None
		rect = device.HitRectAroundPoint(point)
		if not selectable:
			layers = self.layers[:]
			layers.reverse()
			for layer in layers:
				object = layer.PickObject(point, rect, device)
				if object is not None:
					break
		else:
			selected = self.selection_from_point(point, rect, device)
			if selected:
				object = selected[-1]
		return object

	def PickActiveObject(self, device, p):
		# return the object under point if it's selected or a guide
		# line. None otherwise.
		rect = device.HitRectAroundPoint(p)
		path = self.selection.GetPath()
		if len(path) > 2:
			path = path[:-1]
		else:
			path = ()
		hit = self.selection_from_point(p, rect, device, path)
		#self.hit_cache = (p, device, hit)
		if hit:
			if not hit[-1].is_GuideLine:
				while hit:
					if hit in self.selection.GetInfo():
						hit = hit[-1]
						break
					hit = selinfo.get_parent(hit)
			else:
				hit = hit[-1]
		return hit
	
	#
	#
	#

	def WalkHierarchy(self, func, printable = 1, visible = 1, all = 0):
		# XXX make the selection of layers more versatile
		for layer in self.layers:
			if (all
				or printable and layer.Printable()
				or visible and layer.Visible()):
				layer.WalkHierarchy(func)

	#
	#
	#
	def ButtonDown(self, p, button, state):
		self.was_dragged = 0
		self.old_change_rect = self.selection.ChangeRect()
		result = self.selection.ButtonDown(p, button, state)
		return result

	def MouseMove(self, p, state):
		self.was_dragged = 1
		self.selection.MouseMove(p, state)

	def ButtonUp(self, p, button, state):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if self.was_dragged:
					undo_text, undo_edit \
								= self.selection.ButtonUp(p, button, state)
					if undo_edit is not None and undo_edit != NullUndo:
						self.add_undo(undo_text, undo_edit)
						uc1 = self.AddClearRect(self.old_change_rect)
						uc2 = self.AddClearRect(self.selection.ChangeRect())
						self.add_undo(uc1, uc2)
						self.add_undo(self.queue_edited())
					else:
						# the user probably just moved the rotation
						# center point. The canvas has to update the
						# handles
						self.queue_selection()
				else:
					self.selection.ButtonUp(p, button, state, forget_trafo = 1)
					self.ToggleSelectionBehaviour()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def ToggleSelectionBehaviour(self):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				if self.selection.__class__ == SizeSelection:
					self.selection = TrafoSelection(self.selection)
				elif self.selection.__class__ == TrafoSelection:
					self.selection = SizeSelection(self.selection)
				self.queue_selection()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def DrawDragged(self, device, partially = 0):
		self.selection.DrawDragged(device, partially)

	def Hide(self, device, partially = 0):
		self.selection.Hide(device, partially)

	def Show(self, device, partially = 0):
		self.selection.Show(device, partially)

	def ChangeRect(self):
		return self.selection.ChangeRect()

	#
	#	The undo mechanism
	#

	def __init_undo(self):
		self.undo = UndoRedo()

	def CanUndo(self):
		return self.undo.CanUndo()
	script_access['CanUndo'] = SCRIPT_GET

	def CanRedo(self):
		return self.undo.CanRedo()
	script_access['CanRedo'] = SCRIPT_GET

	def Undo(self):
		if self.undo.CanUndo():
			self.begin_transaction(clear_selection_rect = 0)
			try:
				try:
					self.undo.Undo()
				except:
					self.abort_transaction()
			finally:
				self.end_transaction(issue = UNDO)
	script_access['Undo'] = SCRIPT_GET

	def add_undo(self, *infos):
		# Add undoinfo for the current transaction. should not be called
		# when not in a transaction.
		if infos:
			if type(infos[0]) == StringType:
				if not self.transaction_name:
					self.transaction_name = infos[0]
				infos = infos[1:]
				if not infos:
					return
			for info in infos:
				if type(info) == ListType:
					info = CreateListUndo(info)
				else:
					if type(info[0]) == StringType:
						if __debug__:
							pdebug(None, 'add_undo: info contains text')
						info = info[1:]
				self.transaction_undo.append(info)

	# public version of add_undo. to be called between calls to
	# BeginTransaction and EndTransaction/AbortTransaction
	AddUndo = add_undo

	def __undo_set_sel(self, selclass, selinfo, redo_class, redo_info):
		old_class = self.selection.__class__
		if old_class != selclass:
			self.selection = selclass(selinfo)
			self.queue_message(MODE)
		else:
			# keep the same selection object to avoid creating a new
			# editor object in EditMode
			self.selection.SetSelection(selinfo)
		self.queue_selection()
		return (self.__undo_set_sel, redo_class, redo_info, selclass, selinfo)

	def __real_add_undo(self, text, undo, selinfo = None, selclass = None):
		if undo is not NullUndo:
			if selinfo is not None:
				new_class = self.selection.__class__
				new_info = self.selection.GetInfo()[:]
				if new_info == selinfo:
					# make both lists identical
					new_info = selinfo
				undo_sel = (self.__undo_set_sel, selclass, selinfo,
							new_class, new_info)
				info = (text, UndoAfter, undo_sel, undo)
			else:
				info = (text, undo)
			self.undo.AddUndo(info)
			self.queue_message(UNDO)


	def Redo(self):
		if self.undo.CanRedo():
			self.begin_transaction(clear_selection_rect = 0)
			try:
				try:
					self.undo.Redo()
				except:
					self.abort_transaction()
			finally:
				self.end_transaction(issue = UNDO)
	script_access['Redo'] = SCRIPT_GET

	def ResetUndo(self):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.undo.Reset()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction(issue = UNDO)
	script_access['ResetUndo'] = SCRIPT_GET

	def UndoMenuText(self):
		return self.undo.UndoText()
	script_access['UndoMenuText'] = SCRIPT_GET

	def RedoMenuText(self):
		return self.undo.RedoText()
	script_access['RedoMenuText'] = SCRIPT_GET

	def SetUndoLimit(self, limit):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				self.undo.SetUndoLimit(limit)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction(issue = UNDO)
	script_access['SetUndoLimit'] = SCRIPT_GET

	def WasEdited(self):
		# return true if document has changed since last save
		if self.undo.UndoCount():
		  return 1
		return 0
	script_access['WasEdited'] = SCRIPT_GET

	def ClearEdited(self):
		self.undo.ResetUndoCount()
		self.issue(UNDO)

	#
	#

	def apply_to_selected(self, undo_text, func):
		if self.selection:
			self.begin_transaction(undo_text)
			try:
				try:
					self.add_undo(self.selection.ForAllUndo(func))
					self.queue_selection()
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def AddStyle(self, style):
		if type(style) == StringType:
			style = self.GetDynamicStyle(style)
		self.apply_to_selected(_("Add Style"),
								lambda o, style = style: o.AddStyle(style))

	def SetLineColor(self, color):
		# Set the line color of the currently selected objects.
		# XXX this method should be removed in favour of the more
		# generic SetProperties.
		self.SetProperties(line_pattern = SolidPattern(color),
							if_type_present = 0)

	def SetProperties(self, **kw):
		self.apply_to_selected(_("Set Properties"),
								lambda o, kw=kw: apply(o.SetProperties, (), kw))

	def SetStyle(self, style):
		if type(style) == StringType:
			style = self.get_dynamic_style(style)
			self.AddStyle(style)

	#
	#	Deleting and rearranging objects...
	#

	def remove_objects(self, infolist):
		split = selinfo.list_to_tree(infolist)
		undo = []
		try:
			for layer, infolist in split:
				undo.append(self.layers[layer].RemoveObjects(infolist))
			return CreateListUndo(undo)
		except:
			Undo(CreateListUndo(undo))
			raise

	def remove_selected(self):
		return self.remove_objects(self.selection.GetInfo())

	def RemoveSelected(self):
		# Remove all selected objects. After successful completion, the
		# selection will be empty.
		if self.selection:
			self.begin_transaction(_("Delete"))
			try:
				try:
					self.add_undo(self.remove_selected())
					self.__set_selection(None, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def __call_layer_method_sel(self, undotext, methodname, *args):
		if not self.selection:
			return
		self.begin_transaction(undotext)
		try:
			try:
				split = selinfo.list_to_tree(self.selection.GetInfo())
				edited = 0
				selection = []
				for layer, infolist in split:
					method = getattr(self.layers[layer], methodname)
					sel, undo = apply(method, (infolist,) + args)
					if undo is not NullUndo:
						self.add_undo(undo)
						edited = 1
					selection = selection + self.augment_sel_info(sel, layer)
				self.__set_selection(selection, SelectSet)
				if edited:
					self.add_undo(self.queue_edited())
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def MoveSelectedToTop(self):
		self.__call_layer_method_sel(_("Move To Top"), 'MoveObjectsToTop')

	def MoveSelectedToBottom(self):
		self.__call_layer_method_sel(_("Move To Bottom"),'MoveObjectsToBottom')

	def MoveSelectionDown(self):
		self.__call_layer_method_sel(_("Lower"), 'MoveObjectsDown')

	def MoveSelectionUp(self):
		self.__call_layer_method_sel(_("Raise"), 'MoveObjectsUp')

	def MoveSelectionToLayer(self, layer):
		if self.selection:
			self.begin_transaction(_("Move Selection to `%s'")
									% self.layers[layer].Name())
			try:
				try:
					# remove the objects from the document...
					self.add_undo(self.remove_selected())
					# ... and insert them a the end of the layer
					objects = self.selection.GetObjects()
					select, undo_insert = self.insert(objects, layer = layer)

					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	#
	#	Cut/Copy
	#

	def copy_objects(self, objects):
		copies = []
		for obj in objects:
			copies.append(obj.Duplicate())

		if len(copies) > 1:
			for copy in copies:
				copy.UntieFromDocument()
				copy.SetDocument(None)
		else:
			copy = copies[0]
			# This is ugly: Special case for internal path text objects.
			# If the internal path text object is the only selected
			# object, turn the copy into a normal simple text object.
			# Thsi avoids some of the problems when you "Copy" an
			# internal path text.
			import text
			if copy.is_PathTextText:
				properties = copy.Properties().Duplicate()
				copy = text.SimpleText(text = copy.Text(),
											properties = properties)

			copy.UntieFromDocument()
			copy.SetDocument(None)
			copies[0]=copy
			
		return copies

	def CopyForClipboard(self):
		if self.selection:
			return self.copy_objects(self.selection.GetObjects())

	def CutForClipboard(self):
		result = None
		if self.selection:
			self.begin_transaction(_("Cut"))
			try:
				try:
					objects = self.selection.GetObjects()
					result = self.copy_objects(objects)
					self.add_undo(self.remove_selected())
					self.__set_selection(None, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					result = None
					self.abort_transaction()
			finally:
				self.end_transaction()
		return result

	#
	#	Duplicate
	#
	def ApplyToDuplicate(self):
		offset = Point(0,0)
		self.__call_layer_method_sel(_("Duplicate"), 'DuplicateObjects', offset)

	def DuplicateSelected(self, offset = None):
		if offset is None:
			offset = Point(config.preferences.duplicate_offset)
		self.__call_layer_method_sel(_("Duplicate"), 'DuplicateObjects', offset)

	#
	#	Group
	#

	def group_selected(self, title, creator):
		self.begin_transaction(title)
		try:
			try:
				self.add_undo(self.remove_selected())
				objects = self.selection.GetObjects()
				group = creator(objects)
				parent = selinfo.common_prefix(self.selection.GetInfo())
				if parent:
					layer = parent[0]
					at = parent[1:]
				else:
					layer = None
					at = None
				select, undo_insert = self.insert(group, at = at, layer =layer)
				self.add_undo(undo_insert)
				self.__set_selection(select, SelectSet)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def CanGroup(self):
		return len(self.selection) > 1

	def GroupSelected(self):
		if self.CanGroup():
			self.group_selected(_("Create Group"), Group)

	def CanUngroup(self):
		infos = self.selection.GetInfo()
		return len(infos) == 1 and infos[0][-1].is_Group

	def CanUngroupAll(self):
		infos = self.selection.GetInfo()
		isGroup=0
		if len(infos) > 0:
			for i in range(len(infos)):
				isGroup+=infos[i][-1].is_Group
		#if len(infos) > 0:
					#isGroup=infos[0][-1].is_Group
					#for i in range(len(infos)):
							#if infos[i][-1].is_Group:
									#isGroup=infos[i][-1].is_Group
		return len(infos) > 0 and isGroup

	def UngroupSelected(self):
		if self.CanUngroup():
			self.begin_transaction(_("Ungroup"))
			try:
				try:
					self.add_undo(self.remove_selected())
					info, group = self.selection.GetInfo()[0]
					objects = group.Ungroup()
					select, undo_insert = self.insert(objects, at = info[1:],
														layer = info[0])
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()
				
	def ExtractNonGroup(self, object):
		objects=[]
		if object.is_Blend:
			objs=object.Ungroup()
			for item in objs:
				objects+=self.ExtractNonGroup(item)
		elif object.is_Group:
			for item in object.objects:
				objects+=self.ExtractNonGroup(item)
		else:
			objects.append(object)
		return objects				

	def UngroupAllSelected(self):
		if self.CanUngroupAll():
			self.begin_transaction(_("Ungroup All"))
			try:
				try:
					self.add_undo(self.remove_selected())
					extracted_select=[]
					for info, object in self.selection.GetInfo():
						objects = self.ExtractNonGroup(object)
						select, undo_insert = self.insert(objects, at = info[1:], layer = info[0])
						extracted_select+=select
						self.add_undo(undo_insert)
					self.__set_selection(extracted_select, SelectSet)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()
				
	def ModifyAndCopy(self):
		if self.selection:
			copies=self.copy_objects(self.selection.GetObjects())
			self.Undo()
			self.Insert(copies, undo_text=_("Modify&Copy"))	

	def CanCreateMaskGroup(self):
		infos = self.selection.GetInfo()
		return len(infos) > 1 and infos[-1][-1].is_clip

	def CreateMaskGroup(self):
		if self.CanCreateMaskGroup():
			self.begin_transaction(_("Create Mask Group"))
			try:
				try:
					import maskgroup
					self.add_undo(self.remove_selected())
					objects = self.selection.GetObjects()
					if config.preferences.topmost_is_mask:
						mask = objects[-1]
						del objects[-1]
						objects.insert(0, mask)
					group = maskgroup.MaskGroup(objects)
					parent = selinfo.common_prefix(self.selection.GetInfo())
					if parent:
						layer = parent[0]
						at = parent[1:]
					else:
						layer = None
						at = None
					select, undo_insert = self.insert(group, at = at,
														layer = layer)
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()


	#
	#	Transform, Translate, ...
	#

	def TransformSelected(self, trafo, undo_text = _("Transform")):
		self.apply_to_selected(undo_text, lambda o, t = trafo: o.Transform(t))

	def TranslateSelected(self, offset, undo_text = _("Translate")):
		self.apply_to_selected(undo_text, lambda o, v = offset: o.Translate(v))

	def RemoveTransformation(self):
		self.apply_to_selected(_("Remove Transformation"),
								lambda o: o.RemoveTransformation())

	#
	#	Align, Flip, ...
	#
	# XXX These functions could be implemented outside of the document.
	# (Maybe by command plugins or scripts?)
	#

	def AlignSelection(self, x, y, reference = 'selection'):
		if self.selection and (x or y):
			self.begin_transaction(_("Align Objects"))
			try:
				try:
					add_undo = self.add_undo
					objects = self.selection.GetObjects()
					if reference == 'page':
						br = self.PageRect()
					elif reference == 'lowermost':
						br = objects[0].coord_rect
					else:
						br = self.selection.coord_rect
					for obj in objects:
						r = obj.coord_rect
						xoff = yoff = 0
						if x == 1:
							xoff = br.left - r.left
						elif x == 3:
							xoff = br.right - r.right
						elif x == 2:
							xoff = (br.left + br.right - r.left - r.right) / 2

						if y == 1:
							yoff = br.top - r.top
						elif y == 3:
							yoff = br.bottom - r.bottom
						elif y == 2:
							yoff = (br.top + br.bottom - r.top - r.bottom) / 2

						add_undo(obj.Translate(Point(xoff, yoff)))

					add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def AbutHorizontal(self):
		if len(self.selection) > 1:
			self.begin_transaction(_("Abut Horizontal"))
			try:
				try:
					pos = []
					for obj in self.selection.GetObjects():
						rect = obj.coord_rect
						pos.append((rect.left, rect.top,
									rect.right - rect.left, obj))
					pos.sort()
					undo = []
					start, top, width, ob = pos[0]
					next = start + width
					for left, top, width, obj in pos[1:]:
						off = Point(next - left, 0)
						self.add_undo(obj.Translate(off))
						next = next + width

					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def AbutVertical(self):
		if len(self.selection) > 1:
			self.begin_transaction(_("Abut Vertical"))
			try:
				try:
					pos = []
					for obj in self.selection.GetObjects():
						rect = obj.coord_rect
						pos.append((rect.top, -rect.left,
									rect.top - rect.bottom, obj))
					pos.sort()
					pos.reverse()
					undo = []
					start, left, height, ob = pos[0]
					next = start - height
					for top, left, height, obj in pos[1:]:
						off = Point(0, next - top)
						self.add_undo(obj.Translate(off))
						next = next - height

					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def FlipSelected(self, horizontal = 0, vertical = 0):
		if self.selection and (horizontal or vertical):
			self.begin_transaction()
			try:
				try:
					rect = self.selection.coord_rect
					if horizontal:
						xoff = rect.left + rect.right
						factx = -1
						text = _("Flip Horizontal")
					else:
						xoff = 0
						factx = 1
					if vertical:
						yoff = rect.top + rect.bottom
						facty = -1
						text = _("Flip Vertical")
					else:
						yoff = 0
						facty = 1
					if horizontal and vertical:
						text = _("Flip Both")
					trafo = Trafo(factx, 0, 0, facty, xoff, yoff)
					self.TransformSelected(trafo, text)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def RotateSelected(self, angle):
		if self.selection:
			self.begin_transaction()
			try:
				try:
					cnt = self.selection.coord_rect.center()
					text = _("Rotation")
					angle=angle*pi/180
					trafo = Rotation(angle, cnt)
					self.TransformSelected(trafo, text)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()
				
	def HandleMoveSelected(self, h, v):
		val=config.preferences.handle_jump
		self.MoveSelected(h*val, v*val)

	def MoveSelected(self, h, v):
		if self.selection:
			self.begin_transaction()
			try:
				try:
					#cnt = self.selection.coord_rect.center()
					text = _("Move")
					#angle=angle*pi/180
					trafo = Translation(h, v)
					self.TransformSelected(trafo, text)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()
				
	def MoveAndCopy(self, h, v, *args):
		if self.selection:
			self.begin_transaction()
			try:
				try:
					text = _("Move&Copy")
					methodname='DuplicateObjects'
					split = selinfo.list_to_tree(self.selection.GetInfo())
					edited = 0
					selection = []
					for layer, infolist in split:
						method = getattr(self.layers[layer], methodname)
						sel, undo = apply(method, (infolist,) + args)
						if undo is not NullUndo:
							self.add_undo(undo)
							edited = 1
						selection = selection + self.augment_sel_info(sel, layer)
					self.__set_selection(selection, SelectSet)
					if edited:
						self.add_undo(self.queue_edited())					
					
					trafo = Translation(h, v)
					self.TransformSelected(trafo, text)
					
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def ScaleSelected(self, h, v):
		if self.selection:
			self.begin_transaction()
			try:
				try:
					br=self.selection.coord_rect
					hor_sel=br.right - br.left
					ver_sel=br.top - br.bottom
					cnt_x=hor_sel/2+br.left
					cnt_y=ver_sel/2+br.bottom
					text = _("Scale")
					trafo = Trafo(h, 0, 0, v, cnt_x-cnt_x*h, cnt_y-cnt_y*v)
					self.TransformSelected(trafo, text)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def CallObjectMethod(self, aclass, description, methodname, *args):
		self.begin_transaction(description)
		try:
			try:
				undo = self.selection.CallObjectMethod(aclass, methodname,
														args)
				if undo != NullUndo:
					self.add_undo(undo)
					self.add_undo(self.queue_edited())
					# force recomputation of selections rects:
					self.selection.ResetRectangle()
				else:
					# in case the handles have to be updated
					self.queue_selection()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def GetObjectMethod(self, aclass, method):
		return self.selection.GetObjectMethod(aclass, method)

	def CurrentObjectCompatible(self, aclass):
		obj = self.CurrentObject()			
		if obj is not None:
			if aclass.is_Editor:
				return obj.__class__.__name__== aclass.EditedClass.__name__
			else:
				return obj.__class__.__name__== aclass.__name__
		return 0

	# XXX the following methods for blend groups, path text, clones and
	# bezier objects should perhaps be implemented in their respective
	# modules (and then somehow grafted onto the document class?)

		
	def CanBlend(self):
		info = self.selection.GetInfo()
		if len(info) == 2:
			path1, obj1 = info[0]
			path2, obj2 = info[1]
			if len(path1) == len(path2) + 1:
				return obj1.parent.is_Blend and 2
			if len(path1) + 1 == len(path2):
				return obj2.parent.is_Blend and 2
			return len(path1) == len(path2)
		return 0

	def Blend(self, steps):
		info = self.selection.GetInfo()
		path1, obj1 = info[0]
		path2, obj2 = info[1]
		if len(path1) == len(path2) + 1:
			if obj1.parent.is_Blend:
				del info[0]
			else:
				return
		elif len(path1) + 1 == len(path2):
			if obj2.parent.is_Blend:
				del info[1]
			else:
				return
		elif len(path1) != len(path2):
			return
		if steps >= 2:
			import blendgroup, blend
			self.begin_transaction(_("Blend"))
			try:
				try:
					self.add_undo(self.remove_objects(info))
					try:
						blendgrp, undo = blendgroup.CreateBlendGroup(obj1,obj2,
																		steps)
						self.add_undo(undo)
					except blend.MismatchError:
						warn(USER, _("I can't blend the selected objects"))
						# XXX: is there some other solution?:
						raise

					if len(info) == 2:
						select, undo_insert = self.insert(blendgrp,
															at = path1[1:],
															layer = path1[0])
						self.add_undo(undo_insert)
						self.__set_selection(select, SelectSet)
					else:
						self.SelectObject(blendgrp)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def CanCancelBlend(self):
		info = self.selection.GetInfo()
		return len(info) == 1 and info[0][-1].is_Blend

	def CancelBlend(self):
		if self.CanCancelBlend():
			self.begin_transaction(_("Cancel Blend"))
			try:
				try:
					info = self.selection.GetInfo()[0]
					self.add_undo(self.remove_selected())
					group = info[-1]
					objs = group.CancelEffect()
					info = info[0]
					layer = info[0]
					at = info[1:]
					select, undo_insert = self.insert(objs, at = at,
														layer = layer)
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	#
	#

	def CanCreatePathText(self):
		return CanCreatePathText(self.selection.GetObjects())

	def CreatePathText(self):
		if self.CanCreatePathText():
			self.begin_transaction(_("Create Path Text"))
			try:
				try:
					self.add_undo(self.remove_selected())
					object = CreatePathText(self.selection.GetObjects())

					select, undo_insert = self.insert(object)
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	#
	#	Clone (under construction...)
	#

	def CanCreateClone(self):
		if len(self.selection) == 1:
			obj = self.selection.GetObjects()[0]
			return not obj.is_Compound
		return 0

	def CreateClone(self):
		if self.CanCreateClone():
			self.begin_transaction(_("Create Clone"))
			try:
				try:
					from clone import CreateClone
					object = self.selection.GetObjects()[0]
					clone, undo_clone = CreateClone(object)
					self.add_undo(undo_clone)
					select, undo_insert = self.insert(clone)
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()


	#
	#	Bezier Curves
	#

	def CanCombineBeziers(self):
		if len(self.selection) > 1:
			can = 1
			for obj in self.selection.GetObjects():
				can = can and obj.is_Bezier
			return can
		return 0

	def CombineBeziers(self):
		if self.CanCombineBeziers():
			self.begin_transaction(_("Combine Beziers"))
			try:
				try:
					self.add_undo(self.remove_selected())
					objects = self.selection.GetObjects()
					combined = CombineBeziers(objects)
					select, undo_insert = self.insert(combined)
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def CanSplitBeziers(self):
		return len(self.selection) == 1 \
				and self.selection.GetObjects()[0].is_Bezier

	def SplitBeziers(self):
		if self.CanSplitBeziers():
			self.begin_transaction(_("Split Beziers"))
			try:
				try:
					self.add_undo(self.remove_selected())
					info, bezier = self.selection.GetInfo()[0]
					objects = bezier.PathsAsObjects()
					select, undo_insert = self.insert(objects, at = info[1:],
														layer =info[0])
					self.add_undo(undo_insert)
					self.__set_selection(select, SelectSet)
					self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def CanConvertToCurve(self):
		check_crv = 0
		if len(self.selection) >0:
				check_crv = 1
#		for a  in range(len(self.selection)):
#			if self.selection.GetObjects()[a].is_curve:
#				pass
#			else:
#				check_crv = 0
		return check_crv
		# return len(self.selection) == 1 \
				#and self.selection.GetObjects()[0].is_curve

	def ConvertToCurve(self):
		if self.CanConvertToCurve():
			self.begin_transaction(_("Convert To Curve"))
			try:
				try:
					selection = []
					edited = 0
					for info, object in self.selection.GetInfo():
						if object.is_curve:
								if object.is_Bezier:
									selection.append((info, object))
								else:
									bezier = object.AsBezier()
									parent = object.parent
									self.add_undo(parent.ReplaceChild(object, bezier))
									selection.append((info, bezier))
									edited = 1
						else:
								pass
					self.__set_selection(selection, SelectSet)
					if edited:
						self.add_undo(self.queue_edited())
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()
	#
	#  IMAGES MANAGMENT
	#
	
############
	def CanBeRGB(self):
		from image import RGB_IMAGE, RGBA_IMAGE
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image:
				if obj.data.image_mode==RGB_IMAGE or obj.data.image_mode==RGBA_IMAGE:
					return 0
				else:
					return 1
		return 0

	def CanBeCMYK(self):
		from image import CMYK_IMAGE
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image and not obj.data.image_mode==CMYK_IMAGE:
					return 1
		return 0

	def CanBeGrayscale(self):
		from image import GRAYSCALE_IMAGE
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image and not obj.data.image_mode==GRAYSCALE_IMAGE:
					return 1
		return 0

	def CanBeBW(self):
		from image import BW_IMAGE
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image and not obj.data.image_mode==BW_IMAGE:
					return 1
		return 0
	
	def ConvertImage(self, mode):
		obj = self.CurrentObject()
		self.CallObjectMethod(obj.__class__, _("Convert Image"), 'Convert', mode)
#		obj.Convert(mode)
		self.SelectNone()
		self.SelectObject(obj)
				
	def CanEmbed(self):
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image and obj.CanEmbed():
				return obj.CanEmbed()
		return 0
	
	def Embed(self):
		obj = self.CurrentObject()
		obj.Embed()
		self.SelectNone()
		self.SelectObject(obj)

	def CanInvert(self):
		obj = self.CurrentObject()
		if obj:
			if obj.is_Image and obj.IsEmbedded():
				return 1
		return 0

	def Invert(self):
		obj = self.CurrentObject()
		self.CallObjectMethod(obj.__class__, _("Invert Image"), 'InvertImage')
		app.mw.canvas.ForceRedraw()


	#
	#  PAGES MANAGMENT
	#
	
############
	def CanGoToPage(self):
		return len(self.pages)>1
	
	def GoToPage(self, index=0):
		self.begin_transaction(_("Go to page"),clear_selection_rect = 0)
		try:
			try:
				current_page=self.active_page
				if self.CanUndo():
					self.add_undo((self._return_to_page, current_page))
				self.setActivePage(index)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
			self.issue(PAGE)			
	
	def _return_to_page(self, index):
		current_page=self.active_page
		self.setActivePage(index)
		self.issue(PAGE)
		return (self._return_to_page, current_page)
	
############	
	def InsertPages(self, number=1, index=0, is_before=0):
		if number>1:
			self.begin_transaction(_("Insert Pages"), clear_selection_rect = 0)
		else:
			self.begin_transaction(_("Insert Page"), clear_selection_rect = 0)
		try:
			try:
				for_del=abs(is_before-1)
				self.add_undo((self._delete_pages,number,index,for_del))
				self.insert_pages(number,index,is_before)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()			
			self.issue(PAGE)
	
	def _insert_pages(self,number,index,is_before):
		self.insert_pages(number,index,is_before)
		self.issue(PAGE)
		return (self._delete_pages,number,index,is_before)
		
	def _delete_pages(self, number=1, index=0,is_before=0):
		self.delete_pages(number,index,is_before)
		self.issue(PAGE)
		return (self._insert_pages,number,index,is_before)
	
############
	def CanDeletePage(self,index):
		return 0 <= index < len(self.pages) and len(self.pages) > 1
	
	def CanBePageDeleting(self):
		return len(self.pages) > 1
		
	def DeletePage(self, index=0):
		if self.CanDeletePage(index):
			self.begin_transaction(_("Delete Page"), clear_selection_rect = 0)
			try:
				try:
					self.add_undo((self._insert_page,index,self.pages[index]))
					self.delete_page(index)					
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()				
				self.issue(PAGE)
	
	def _insert_page(self,index,page):
		current_page = self.pages[self.active_page]
		self.pages.insert(index,page)		
		self.active_page = self.pages.index(current_page)
		self.SelectNone()
		self.issue(PAGE)
		return (self._delete_page,index,page)

	def _delete_page(self,index,page):
		current_page = self.pages[self.active_page]
		self.pages.remove(page)
		self.active_page = self.pages.index(current_page)
		self.SelectNone()
		self.issue(PAGE)
		return (self._insert_page,index,page)		
		

	#
	#  LAYERS METHODS
	#

	def Layers(self):
		return self.layers[:]

	def NumLayers(self):
		return len(self.layers)

	def ActiveLayer(self):
		return self.active_layer

	def ActiveLayerIdx(self):
		if self.active_layer is None:
			return None
		return self.layers.index(self.active_layer)

	def SetActiveLayer(self, idx):
		if type(idx) == IntType:
			layer = self.layers[idx]
		else:
			layer = idx
		if not layer.Locked():
			self.active_layer = layer
		self.queue_layer(LAYER_ACTIVE)

	def LayerIndex(self, layer):
		return self.layers.index(layer)

	def update_active_layer(self):
		if self.active_layer is not None and self.active_layer.CanSelect():
			return
		self.find_active_layer()

	def find_active_layer(self, idx = None):
		if idx is not None:
			layer = self.layers[idx]
			if layer.CanSelect():
				self.SetActiveLayer(idx)
				return
		for layer in self.layers:
			if layer.CanSelect():
				self.SetActiveLayer(layer)
				return
		self.active_layer = None
		self.queue_layer(LAYER_ACTIVE)

	def deselect_layer(self, layer_idx):
		# Deselect all objects in layer given by layer_idx
		# Called when a layer is deleted or becomes locked
		sel = selinfo.list_to_tree(self.selection.GetInfo())
		for idx, info in sel:
			if idx == layer_idx:
				self.__set_selection(selinfo.tree_to_list([(idx, info)]),
										SelectSubtract)

	def SelectLayer(self, layer_idx, mode = SelectSet):
		# Select all children of the layer given by layer_idx
		self.begin_transaction(_("Select Layer"), clear_selection_rect = 0)
		try:
			try:
				layer = self.layers[layer_idx]
				info = self.augment_sel_info(layer.SelectAll(), layer_idx)
				self.__set_selection(info, mode)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SetLayerState(self, layer_idx, visible, printable, locked, outlined):
		self.begin_transaction(_("Change Layer State"),
								clear_selection_rect = 0)
		try:
			try:
				layer = self.layers[layer_idx]
				self.add_undo(layer.SetState(visible, printable, locked,
												outlined))
				if not layer.CanSelect():
					# XXX: this depends on whether we're drawing visible or
					# printable layers
					self.deselect_layer(layer_idx)
					self.update_active_layer()
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SetLayerColor(self, layer_idx, color):
		self.begin_transaction(_("Set Layer Outline Color"),
								clear_selection_rect = 0)
		try:
			try:
				layer = self.layers[layer_idx]
				self.add_undo(layer.SetOutlineColor(color))
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def SetLayerName(self, idx, name):
		self.begin_transaction(_("Rename Layer"), clear_selection_rect = 0)
		try:
			try:
				layer = self.layers[idx]
				self.add_undo(layer.SetName(name))
				self.add_undo(self.queue_layer())
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def AppendLayer(self, *args, **kw_args):
		self.begin_transaction(_("Append Layer"),clear_selection_rect = 0)
		try:
			try:
				layer = apply(SketchDocument.AppendLayer, (self,) + args,
								kw_args)
				self.add_undo((self._remove_layer, len(self.layers) - 1))
				self.queue_layer(LAYER_ORDER, layer)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()
		return layer

	def NewLayer(self):
		self.begin_transaction(_("New Layer"), clear_selection_rect = 0)
		try:
			try:
				self.AppendLayer()
				self.active_layer = self.layers[-1]
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def _move_layer_up(self, idx):
		# XXX: exception handling
		if idx < len(self.layers) - 1:
			# move the layer...
			layer = self.layers[idx]
			del self.layers[idx]
			self.layers.insert(idx + 1, layer)
			other = self.layers[idx]
			# ... and adjust the selection
			sel = self.selection.GetInfoTree()
			newsel = []
			for i, info in sel:
				if i == idx:
					i = idx + 1
				elif i == idx + 1:
					i = idx
				newsel.append((i, info))
			self.__set_selection(selinfo.tree_to_list(newsel), SelectSet)
			self.queue_layer(LAYER_ORDER, layer, other)
			return (self._move_layer_down, idx + 1)
		return None

	def _move_layer_down(self, idx):
		# XXX: exception handling
		if idx > 0:
			# move the layer...
			layer = self.layers[idx]
			del self.layers[idx]
			self.layers.insert(idx - 1, layer)
			other = self.layers[idx]
			# ...and adjust the selection
			sel = self.selection.GetInfoTree()
			newsel = []
			for i, info in sel:
				if i == idx:
					i = idx - 1
				elif i == idx - 1:
					i = idx
				newsel.append((i, info))
			self.__set_selection(selinfo.tree_to_list(newsel), SelectSet)
			self.queue_layer(LAYER_ORDER, layer, other)
			return (self._move_layer_up, idx - 1)
		return NullUndo

	def MoveLayerUp(self, idx):
		if idx < len(self.layers) - 1:
			self.begin_transaction(_("Move Layer Up"), clear_selection_rect=0)
			try:
				try:
					self.add_undo(self._move_layer_up(idx))
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def MoveLayerDown(self, idx):
		if idx > 0:
			self.begin_transaction(_("Move Layer Down"),clear_selection_rect=0)
			try:
				try:
					self.add_undo(self._move_layer_down(idx))
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def _remove_layer(self, idx):
		layer = self.layers[idx]
		del self.layers[idx]
		if layer is self.active_layer:
			if idx < len(self.layers):
				self.find_active_layer(idx)
			else:
				self.find_active_layer()
		sel = self.selection.GetInfoTree()
		newsel = []
		for i, info in sel:
			if i == idx:
				continue
			elif i > idx:
				i = i - 1
			newsel.append((i, info))
		self.__set_selection(selinfo.tree_to_list(newsel), SelectSet)

		self.queue_layer(LAYER_ORDER, layer)
		return (self._insert_layer, idx, layer)

	def _insert_layer(self, idx, layer):
		self.layers.insert(idx, layer)
		layer.SetDocument(self)
		self.queue_layer(LAYER_ORDER, layer)
		return (self._remove_layer, idx)

	def CanDeleteLayer(self, idx):
		return (len(self.layers) > 3 and not self.layers[idx].is_SpecialLayer)

	def DeleteLayer(self, idx):
		if self.CanDeleteLayer(idx):
			self.begin_transaction(_("Delete Layer"), clear_selection_rect = 0)
			try:
				try:
					self.add_undo(self._remove_layer(idx))
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()



	#
	#	Style management
	#

	def queue_style(self):
		self.queue_message(STYLE)
		return (self.queue_style,)

	def init_styles(self):
		self.styles = UndoDict()
		self.auto_assign_styles = 1
		self.asked_about = {}

	def destroy_styles(self):
		for style in self.styles.values():
			style.Destroy()
		self.styles = None

	def get_dynamic_style(self, name):
		return self.styles[name]

	def GetDynamicStyle(self, name):
		try:
			return self.styles[name]
		except KeyError:
			return None

	def Styles(self):
		return self.styles.values()

	def write_styles(self, file):
		for style in self.styles.values():
			style.SaveToFile(file)

	def load_AddStyle(self, style):
		self.styles.SetItem(style.Name(), style)

	def add_dynamic_style(self, name, style):
		if style:
			style = style.AsDynamicStyle()
			self.add_undo(self.styles.SetItem(name, style))
			self.add_undo(self.queue_style())
			return style

	def update_style_dependencies(self, style):
		def update(obj, style = style):
			obj.ObjectChanged(style)
		self.WalkHierarchy(update)
		return (self.update_style_dependencies, style)

	def UpdateDynamicStyleSel(self):
		if len(self.selection) == 1:
			self.begin_transaction(_("Update Style"), clear_selection_rect = 0)
			try:
				try:
					properties = self.CurrentProperties()
					# XXX hack
					for style in properties.stack:
						if style.is_dynamic:
							break
					else:
						return
					undo = []
					# we used to use dir(style) to get at the list of
					# instance variables of style. In Python 2.2 dir
					# returns class attributes as well. So we use
					# __dict__.keys() now.
					for attr in style.__dict__.keys():
						if attr not in ('name', 'is_dynamic'):
							undo.append(style.SetProperty(attr,
															getattr(properties,
																	attr)))
					undo.append(properties.AddStyle(style))
					undo = (UndoAfter, CreateListUndo(undo),
							self.update_style_dependencies(style))
					self.add_undo(undo)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def CanCreateStyle(self):
		if len(self.selection) == 1:
			obj = self.selection.GetObjects()[0]
			return obj.has_fill or obj.has_line
		return 0

	def CreateStyleFromSelection(self, name, which_properties):
		if self.CanCreateStyle():
			properties = self.CurrentProperties()
			style = properties.CreateStyle(which_properties)
			self.begin_transaction(_("Create Style %s") % name,
									clear_selection_rect = 0)
			try:
				try:
					style = self.add_dynamic_style(name, style)
					self.AddStyle(style)
				except:
					self.abort_transaction()
			finally:
				self.end_transaction()

	def RemoveDynamicStyle(self, name):
		style = self.GetDynamicStyle(name)
		if not style:
			# style does not exist. XXX: raise an exception ?
			return
		self.begin_transaction(_("Remove Style %s") % name,
								clear_selection_rect = 0)
		try:
			try:
				def remove(obj, style = style, add_undo = self.add_undo):
					add_undo(obj.ObjectRemoved(style))
				self.WalkHierarchy(remove)
				self.add_undo(self.styles.DelItem(name))
				self.add_undo(self.queue_style())
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def GetStyleNames(self):
		names = self.styles.keys()
		names.sort()
		return names

	#
	#	Layout
	#

	def queue_layout(self):
		self.queue_message(LAYOUT)
		return (self.queue_layout,)

	def init_layout(self):
		self.page_layout = pagelayout.PageLayout()

	def Layout(self):
		return self.page_layout

	def PageSize(self):
		return (self.page_layout.Width(), self.page_layout.Height())

	def PageRect(self):
		w, h = self.page_layout.Size()
		return Rect(0, 0, w, h)

	def load_SetLayout(self, layout):
		self.page_layout = layout

	def __set_page_layout(self, layout):
		undo = (self.__set_page_layout, self.page_layout)
		self.page_layout = layout
		self.queue_layout()
		return undo

	def SetLayout(self, layout):
		self.begin_transaction(clear_selection_rect = 0)
		try:
			try:
				undo = self.__set_page_layout(layout)
				self.add_undo(_("Change Page Layout"), undo)
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	#
	#	Grid Settings
	#

	def queue_grid(self):
		self.queue_message(GRID)
		return (self.queue_grid,)

	def SetGridGeometry(self, geometry):
		self.begin_transaction(_("Set Grid Geometry"))
		try:
			try:
				self.add_undo(self.snap_grid.SetGeometry(geometry))
				self.add_undo(self.queue_grid())
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def GridGeometry(self):
		return self.snap_grid.Geometry()

	def GridLayerChanged(self):
		return self.queue_grid()


	#
	#	Guide Lines
	#

	def add_guide_line(self, line):
		self.begin_transaction(_("Add Guide Line"), clear_selection_rect = 0)
		try:
			try:
				sel, undo = self.guide_layer.Insert(line, 0)
				self.add_undo(undo)
				self.add_undo(self.AddClearRect(line.get_clear_rect()))
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def AddGuideLine(self, point, horizontal):
		self.add_guide_line(guide.GuideLine(point, horizontal))

	def RemoveGuideLine(self, line):
		if not line.parent is self.guide_layer or not line.is_GuideLine:
			return
		self.begin_transaction(_("Delete Guide Line"),
								clear_selection_rect = 0)
		try:
			try:
				self.add_undo(self.remove_objects([line.SelectionInfo()]))
				self.add_undo(self.AddClearRect(line.get_clear_rect()))
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def MoveGuideLine(self, line, point):
		if not line.parent is self.guide_layer or not line.is_GuideLine:
			return
		self.begin_transaction(_("Move Guide Line"), clear_selection_rect = 0)
		try:
			try:
				self.add_undo(self.AddClearRect(line.get_clear_rect()))
				self.add_undo(line.SetPoint(point))
				self.add_undo(self.AddClearRect(line.get_clear_rect()))
				self.add_undo(self.GuideLayerChanged(line.parent))
			except:
				self.abort_transaction()
		finally:
			self.end_transaction()

	def GuideLayerChanged(self, layer):
		self.queue_message(GUIDE_LINES, layer)
		return (self.GuideLayerChanged, layer)

	def GuideLines(self):
		return self.guide_layer.GuideLines()


	#
	#
	def as_group(self):
		for name in self.GetStyleNames():
			self.RemoveDynamicStyle(name)
		layers = self.layers
		self.layers = []
		groups = []
		for layer in layers:
			if not layer.is_SpecialLayer:
				layer.UntieFromDocument()
				objects = layer.GetObjects()
				layer.objects = []
				if objects:
					groups.append(Group(objects))
			else:
				layer.Destroy()
		if groups:
			return Group(groups)
		else:
			return None
		
