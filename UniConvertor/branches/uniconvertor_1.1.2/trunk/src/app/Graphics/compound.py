# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2002 by Bernhard Herzog
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
# Class Compound
#
# a baseclass for objects that contain other graphics objects
# (primitives or other compounds)
#

from types import ListType, TupleType, IntType, InstanceType
import operator

from app import _, SketchError, UnionRects, EmptyRect, _sketch
from app import NullUndo, CreateListUndo, Undo

from base import GraphicsObject, Bounded, CHANGED
from blend import Blend, MismatchError
from properties import EmptyProperties

from selinfo import prepend_idx, select_range, build_info, list_to_tree2, \
		list_to_tree_sliced



class Compound(GraphicsObject):

	has_edit_mode = 0
	is_Group	  = 0
	is_Compound	  = 1
	can_be_empty  = 0

	allow_traversal = 0

	def __init__(self, objects = None, duplicate = None):
		GraphicsObject.__init__(self, duplicate = duplicate)
		if duplicate is not None:
			objects = []
			for obj in duplicate.objects:
				objects.append(obj.Duplicate())
			self.objects = objects
		elif objects:
			self.objects = objects
		else:
			self.objects = []
		self.changing_children = 0
		self.set_parent()

	def Destroy(self):
		self.destroy_objects()
		GraphicsObject.Destroy(self)

	def destroy_objects(self):
		for obj in self.objects:
			obj.Destroy()
		self.objects = []

	def SetParent(self, parent):
		if parent is self.parent:
			return
		GraphicsObject.SetParent(self, parent)
		if parent is not None:
			self.set_parent()
		else:
			self.unset_parent()

	def set_parent(self):
		for child in self.objects:
			child.SetParent(self)

	def unset_parent(self):
		for child in self.objects:
			child.SetParent(None)

	def SelectionInfo(self, child = None):
		info = GraphicsObject.SelectionInfo(self)
		if info and child is not None:
			path = info[0]
			return (path + (_sketch.IdIndex(self.objects, child),),
					child)
		return info

	def ChildChanged(self, child):
		self.del_lazy_attrs()
		if self.changing_children:
			return
		self.issue_changed()

	def SetDocument(self, doc):
		for obj in self.objects:
			obj.SetDocument(doc)
		GraphicsObject.SetDocument(self, doc)
		self.set_parent()

	def disconnect_objects(self):
		for obj in self.objects:
			obj.Disconnect()

	def Disconnect(self):
		self.disconnect_objects()
		self.unset_parent()

	def connect_objects(self):
		for obj in self.objects:
			obj.Connect()

	def Connect(self):
		self.set_parent()
		self.connect_objects()

	def set_objects(self, new_objs):
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)
		self.disconnect_objects()
		self.destroy_objects()
		self.objects = new_objs
		for obj in self.objects:
			if self.document is not None:
				obj.SetDocument(self.document)
			obj.SetParent(self)
		# XXX no connect here ?
		self.del_lazy_attrs()
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)

	def UntieFromDocument(self):
		for obj in self.objects:
			obj.UntieFromDocument()

	def TieToDocument(self):
		for obj in self.objects:
			obj.TieToDocument()

	def load_AppendObject(self, object):
		self.objects.append(object)

	def load_Done(self):
		pass

	def __getitem__(self, idx):
		if type(idx) == IntType:
			return self.objects[idx]
		elif type(idx) == TupleType:
			if len(idx) > 1:
				return self.objects[idx[0]][idx[1:]]
			elif len(idx) == 1:
				return self.objects[idx[0]]
		raise ValueError, 'invalid index %s' % `idx`

	def GetObjects(self):
		# XXX should this return a copy of self.objects?
		return self.objects

	def del_lazy_attrs(self):
		Bounded.del_lazy_attrs(self)
		return (self.del_lazy_attrs,)

	def update_rects(self):
		# XXX: should we raise an exception here if self.objects is empty?
		boxes = map(lambda o: o.coord_rect, self.objects)
		if boxes:
			self.coord_rect = reduce(UnionRects, boxes, boxes[0])
		else:
			self.coord_rect = EmptyRect

		boxes = map(lambda o: o.bounding_rect, self.objects)
		if boxes:
			self.bounding_rect = reduce(UnionRects, boxes, boxes[0])
		else:
			self.bounding_rect = EmptyRect

	def SelectSubobject(self, p, rect, device, path = None, *rest):
		return self

	def Insert(self, obj, at):
		raise SketchError('Cannot insert in compound')

	def Remove(self, *args, **kw):
		raise SketchError('Cannot remove from compound')

	RemoveSlice = Remove
	RemoveObjects = Remove

	ReplaceChild = Remove

	def MoveObjectsToTop(self, infolist):
		raise SketchError('Cannot rearrange objects in compound')

	MoveObjectsToBottom = MoveObjectsToTop
	MoveObjectsDown = MoveObjectsToTop
	MoveObjectsUp = MoveObjectsToTop
	def move_objects_to_top(self, infolist, to_bottom = 0):
		return infolist, NullUndo

	def DuplicateObjects(self, infolist, offset):
		raise SketchError('Cannot duplicate objects in compound')

	def ForAll(self, func):
		self.changing_children = 1
		try:
			return map(func, self.objects)
		finally:
			self.changing_children = 0

	def WalkHierarchy(self, func):
		for obj in self.objects:
			if obj.is_Compound:
				obj.WalkHierarchy(func)
			else:
				func(obj)

	def begin_change_children(self):
		self.changing_children = self.changing_children + 1
		return (self.end_change_children,)

	def end_change_children(self):
		self.changing_children = self.changing_children - 1
		if not self.changing_children:
			self._changed()
		return (self.begin_change_children,)

	def ForAllUndo(self, func):
		if self.objects:
			undo = [self.begin_change_children()]
			undo = undo + map(func, self.objects)
			undo.append(self.end_change_children())
			return CreateListUndo(undo)
		else:
			return NullUndo

	def FilterAll(self, func):
		return filter(func, self.GetObjects())

	def NumObjects(self):
		return len(self.objects)

	def Info(self):
		return _("Compound with %d objects") % len(self.objects)

	def AddStyle(self, style):
		undo = self.ForAllUndo(lambda o, style = style: o.AddStyle(style))
		return undo

	def Properties(self):
		return EmptyProperties

	def SetProperties(self, **kw):
		self.del_lazy_attrs()
		func = lambda o, kw = kw: apply(o.SetProperties, (), kw)
		undo = self.ForAllUndo(func)
		return undo

	def Hit(self, p, rect, device):
		test = rect.overlaps
		objects = self.objects
		for obj_idx in range(len(objects) - 1, -1, -1):
			obj = objects[obj_idx]
			if test(obj.bounding_rect):
				if obj.Hit(p, rect, device):
					return obj_idx + 1
		return 0

	def Transform(self, trafo):
		self.del_lazy_attrs()
		undo = self.ForAllUndo(lambda o, t = trafo: o.Transform(t))
		return undo

	def Translate(self, offset):
		undo = self.ForAllUndo(lambda o, p = offset: o.Translate(p))
		return undo

	def DrawShape(self, device, rect = None):
		if rect:
			test = rect.overlaps
			for o in self.objects:
				if test(o.bounding_rect):
					o.DrawShape(device, rect)
		else:
			for obj in self.objects:
				obj.DrawShape(device)

	def PickObject(self, point, rect, device):
		objects = self.objects[:]
		objects.reverse()
		test = rect.overlaps
		for obj in objects:
			if test(obj.bounding_rect):
				if obj.is_Compound:
					result = obj.PickObject(point, rect, device)
					if result:
						break
				elif obj.Hit(point, rect, device):
					result =  obj
					break
		else:
			result = None

		return result

	def Blend(self, other, frac1, frac2):
		try:
			objs = self.objects
			oobjs = other.objects
			blended = []
			for i in range(min(len(objs), len(oobjs))):
				blended.append(Blend(objs[i], oobjs[i], frac1, frac2))
			return Compound(blended)
		except:
			raise MismatchError

	def GetObjectHandle(self, multiple):
		return self.ForAll(lambda o: o.GetObjectHandle(1))


	def SelectFirstChild(self):
		if self.allow_traversal and self.objects:
			return self.objects[0]

	def SelectLastChild(self):
		if self.allow_traversal and self.objects:
			return self.objects[-1]

	def SelectNextChild(self, child, idx):
		if self.allow_traversal and len(self.objects) > idx + 1:
			return self.objects[idx + 1]

	def SelectPreviousChild(self, child, idx):
		if self.allow_traversal and len(self.objects) > idx - 1 and idx > 0:
			return self.objects[idx - 1]


class EditableCompound(Compound):

	allow_traversal = 1

	def SelectSubobject(self, p, rect, device, path = None, *rest):
		test = rect.overlaps
		if path is None:
			return self
		if path:
			path_idx = path[0]
			path = path[1:]
		else:
			path_idx = -1
			path = None
		objects = self.objects
		for obj_idx in range(len(objects) - 1, -1, -1):
			obj = objects[obj_idx]
			if test(obj.bounding_rect) and obj.Hit(p, rect, device):
				if obj_idx == path_idx:
					result = obj.SelectSubobject(p, rect, device, path)
				else:
					result = obj.SelectSubobject(p, rect, device)
				return prepend_idx(obj_idx, result)
		return None

	def Insert(self, obj, at):
		# Insert OBJ into the object hierarchy at the position described
		# by AT. AT should be either an integer or a tuple of integers.
		# OBJ can be a graphics object of a list of such objects.
		#
		# If AT is a tuple of 2 or more ints, self's child at AT[0] has
		# to be a compound object and its Insert method is called with
		# OBJ and AT[1:] as arguments.
		#
		# If AT is an int or a singleton of one int, insert OBJ at that
		# position in self's children. If OBJ is a graphics object, this
		# works just like a list objects insert method (insert(AT,
		# OBJ)). If its a list of graphics objects this method
		# effectively assigns that list to the slice AT:AT.
		#
		# As a side effect, this method calls the following methods of
		# the inserted objects:
		#
		#	    obj.SetDocument(self.document)
		#	    obj.SetParent(self)
		#	    obj.Connect()
		#
		# Return a tuple (SELINFO, UNDO), where SELINFO is selection
		# info for the inserted objects at their new positions, and UNDO
		# is the appropriate undo info.
		#
		# If self is modified directly, issue a CHANGED message.
		undo_info = None
		try:
			if type(at) == TupleType and at:
				if len(at) == 1:
					at = at[0]
				else:
					child = at[0]
					at = at[1:]
					sel_info, undo_info = self.objects[child].Insert(obj, at)
					sel_info = prepend_idx(child, sel_info)
					return (sel_info, undo_info)
			if type(at) != IntType or at > len(self.objects):
				at = len(self.objects)
			if type(obj) == InstanceType:
				self.objects.insert(at, obj)
				obj.SetDocument(self.document)
				obj.SetParent(self)
				obj.Connect()
				sel_info = build_info(at, obj)
				undo_info = (self.Remove, obj, at)
			else:
				self.objects[at:at] = obj
				for o in obj:
					# XXX: should we have undo info for these:
					o.SetDocument(self.document)
					o.SetParent(self)
					o.Connect()
				sel_info = select_range(at, obj)
				undo_info = (self.RemoveSlice, at, at + len(obj))
			self._changed()
			return (sel_info, undo_info)
		except:
			if undo_info is not None:
				Undo(undo_info)
			raise

	def _insert_with_undo(self, obj, at):
		# The same as the Insert method but return only the undo info.
		return self.Insert(obj, at)[1]

	def do_remove_child(self, idx):
		obj = self.objects[idx]
		del self.objects[idx]
		obj.Disconnect()
		obj.SetParent(None)
		self._changed()
		return (self._insert_with_undo, obj, idx)

	def Remove(self, obj, idx = None):
		if type(idx) == TupleType:
			if len(idx) == 1:
				idx = idx[0]
			else:
				return self.objects[idx[0]].Remove(obj, idx[1:])
		if idx is None:
			idx = self.objects.index(obj)
		elif self.objects[idx] is not obj:
			raise ValueError, 'Compound.Remove(): invalid index'
		return self.do_remove_child(idx)

	def RemoveSlice(self, min, max):
		objs = self.objects[min:max]
		self.objects[min:max] = []
		for obj in objs:
			obj.Disconnect()
			obj.SetParent(None)
		self._changed()
		return (self._insert_with_undo, objs, min)

	def RemoveObjects(self, infolist):
		if not infolist:
			return NullUndo
		sliced = list_to_tree_sliced(infolist)
		sliced.reverse() # important!
		undo = [self.begin_change_children()]
		try:
			for start, end in sliced:
				if type(end) == IntType:
					undo.append(self.RemoveSlice(start, end))
				elif type(end) == ListType:
					undo.append(self.objects[start].RemoveObjects(end))
				else:
					undo.append(self.Remove(end, start))
			undo.append(self.end_change_children())
			return CreateListUndo(undo)
		except:
			Undo(CreateListUndo(undo))
			raise

	def ReplaceChild(self, child, object):
		# replace self's child child with object. Return undo info
		idx = self.objects.index(child)
		self.objects[idx] = object
		object.SetParent(self)
		object.SetDocument(self.document)
		child.SetParent(None)
		self._changed()
		return (self.ReplaceChild, object, child)

	def permute_objects(self, permutation):
		# permutation must be a list of ints and len(permutation) must be
		# equal to len(self.objects). permutation[i] is the index of the
		# object that is moved to index i in the result.
		objects = self.objects
		length = len(objects)
		identity = range(length)
		if permutation == identity:
			return NullUndo
		if len(objects) != len(permutation):
			raise ValueError, 'len(permutation) != len(self.objects)'

		result = map(operator.getitem, [objects] * length, permutation)
		inverse = [0] * length
		map(operator.setitem, [inverse] * length, permutation, identity)
		self.objects = result
		self._changed()
		return (self.permute_objects, inverse)

	def move_objects_to_top(self, infolist, to_bottom = 0):
		# Implement the public methods MoveToTop (if to_bottom is false)
		# and MoveToBottom (if to_bottom is true).
		sliced = list_to_tree_sliced(infolist)
		sliced.reverse()

		undo = [self.begin_change_children()]
		selection = []
		idxs = []
		permutation = range(len(self.objects))
		try:
			for start, end in sliced:
				if type(end) == IntType:
					# a contiguous range of self's children (start:end)
					idxs[:0] = permutation[start:end]
					del permutation[start:end]
				elif type(end) == ListType:
					# children of self.objects[start]
					child = self.objects[start]
					sel, undo_info = child.move_objects_to_top(end, to_bottom)
					if undo_info is not NullUndo:
						undo.append(undo_info)
					selection = selection + prepend_idx(start, sel)
				else:
					# a single object (self.object[start])
					idxs.insert(0, start)
					del permutation[start]

			if idxs:
				# direct children of self are involved: apply the
				# permutation
				if to_bottom:
					permutation = idxs + permutation
				else:
					permutation = permutation + idxs
				undo_info = self.permute_objects(permutation)
				if undo_info is not NullUndo:
					undo.append(undo_info)
			# finished:
			undo.append(self.end_change_children())
			if len(undo) <= 2:
				# We haven't really done anything (undo has length 2),
				# so we just pass the selection info back unchanged
				selection = infolist
				undo = NullUndo
			else:
				# We have done something, so figure out the new
				# selection info
				undo = CreateListUndo(undo)

				if to_bottom:
					selection = selection \
								+ select_range(0, self.objects[:len(idxs)])
				else:
					min = len(self.objects) - len(idxs)
					selection = selection \
								+ select_range(min, self.objects[min:])
			return (selection, undo)
		except:
			# Ooops, something's gone wrong. Undo everything we've done
			# so far... (hmm, this currently fails to undo everything if
			# undo.append(undo_info) fails... (the undo_info involved
			# would be lost))
			Undo(CreateListUndo(undo))
			raise

	def MoveObjectsToTop(self, infolist):
		return self.move_objects_to_top(infolist)

	def MoveObjectsToBottom(self, infolist):
		return self.move_objects_to_top(infolist, to_bottom = 1)

	def MoveObjectsDown(self, infolist):
		sliced = list_to_tree_sliced(infolist)
		undo = [self.begin_change_children()]
		selection = []
		permutation = range(len(self.objects))
		objects = self.objects
		try:
			for start, end in sliced:
				if type(end) == IntType:
					if start > 0:
						temp = permutation[start:end]
						del permutation[start:end]
						permutation[start - 1:start - 1] = temp
						selection = selection +select_range(start - 1,
															objects[start:end])
					else:
						selection = selection +select_range(start,
															objects[start:end])

				elif type(end) == ListType:
					sel, undo_info = objects[start].MoveObjectsDown(end)
					if undo_info is not NullUndo:
						undo.append(undo_info)
					selection = selection + prepend_idx(start, sel)
				else:
					if start > 0:
						del permutation[start]
						permutation.insert(start - 1, start)
						selection.append(build_info(start - 1, objects[start]))
					else:
						selection.append(build_info(start, objects[start]))

			undo_info = self.permute_objects(permutation)
			if undo_info is not NullUndo:
				undo.append(undo_info)
			undo.append(self.end_change_children())
			if len(undo) <= 2:
				undo = NullUndo
				selection = infolist
			else:
				undo = CreateListUndo(undo)
			return (selection, undo)
		except:
			Undo(CreateListUndo(undo))
			raise

	def MoveObjectsUp(self, infolist):
		sliced = list_to_tree_sliced(infolist)
		sliced.reverse()
		undo = [self.begin_change_children()]
		selection = []
		permutation = range(len(self.objects))
		objects = self.objects
		max = len(objects)
		try:
			for start, end in sliced:
				if type(end) == IntType:
					if end < max:
						temp = permutation[start:end]
						del permutation[start:end]
						permutation[start + 1:start + 1] = temp
						selection = selection + select_range(start + 1,
															objects[start:end])
					else:
						selection = selection + select_range(start,
															objects[start:end])

				elif type(end) == ListType:
					sel, undo_info = objects[start].MoveObjectsUp(end)
					if undo_info is not NullUndo:
						undo.append(undo_info)
					selection = selection + prepend_idx(start, sel)
				else:
					if start < max - 1:
						del permutation[start]
						permutation.insert(start + 1, start)
						selection.append(build_info(start + 1, objects[start]))
					else:
						selection.append(build_info(start, objects[start]))

			undo_info = self.permute_objects(permutation)
			if undo_info is not NullUndo:
				undo.append(undo_info)
			undo.append(self.end_change_children())
			if len(undo) <= 2:
				undo = NullUndo
				selection = infolist
			else:
				undo = CreateListUndo(undo)
			return (selection, undo)
		except:
			Undo(CreateListUndo(undo))
			raise

	def DuplicateObjects(self, infolist, offset):
		infolist = list_to_tree2(infolist)

		objects = self.objects
		undo = [self.begin_change_children()]
		selection = []
		added = 0
		try:
			for idx, obj in infolist:
				idx = idx + added
				if type(obj) == ListType:
					# duplicate in subobj
					sel, undoinfo = objects[idx].DuplicateObjects(obj, offset)
					undo.append(undoinfo)
					selection = selection + prepend_idx(idx, sel)
				else:
					obj = obj.Duplicate()
					obj.Translate(offset)
					sel, undoinfo = self.Insert(obj, idx + 1)
					undo.append(undoinfo)
					selection.append(sel)
					added = added + 1
			undo.append(self.end_change_children())
			return (selection, CreateListUndo(undo))
		except:
			Undo(CreateListUndo(undo))
			raise
