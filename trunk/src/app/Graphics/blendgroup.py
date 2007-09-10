# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


#
#	The Blend Group
#


from types import IntType, ListType
import operator

#from app.UI import command

from app.conf.const import SelectAdd
from app import SketchInternalError, _
from app import NullUndo, CreateListUndo, CreateMultiUndo, Undo, UndoAfter

import selinfo
from compound import Compound
from blend import Blend
from group import Group

SelectStart = 0
SelectEnd = 1


class BlendInterpolation(Compound):

	can_be_empty = 1
	is_BlendInterpolation = 1

	def __init__(self, steps = 2, start = None, end = None,
					duplicate = None):
		if duplicate is not None:
			self.steps = duplicate.steps
			Compound.__init__(self, duplicate = duplicate)
		else:
			self.steps = steps
			if start is not None:
				Compound.__init__(self, self.compute_blend(start, end))
			else:
				Compound.__init__(self)

	def SetParameters(self, steps):
		if steps < 2:
			raise ValueError, 'steps must be >= 2'
		if self.steps != steps:
			undo = (self.SetParameters, self.steps)
			self.steps = steps
			self.parent.RecomputeChild(self)
		else:
			undo = NullUndo
		return undo

	def Steps(self):
		return self.steps

	def Recompute(self, start, end):
		self.set_objects(self.compute_blend(start, end))

	def compute_blend(self, start, end):
		steps = self.steps
		blended = []
		for step in range(1, steps):
			fraction = float(step) / steps
			blend = Blend(start, end, fraction)
			blend.SetDocument(self.document)
			blend.SetParent(None)
			blended.append(blend)
		blended.reverse()
		return blended

	def set_objects(self, new_objs):
		# called by __init__ and recompute
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)
		for obj in self.objects:
			obj.Destroy()
		self.objects = new_objs
		self.del_lazy_attrs()
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)
		self.issue_changed()

	def SaveToFile(self, file):
		if file.options.full_blend:
			file.BeginBlendInterpolation(self.steps)
			for obj in self.objects:
				obj.SaveToFile(file)
			file.EndBlendInterpolation()
		else:
			file.BlendInterpolation(self.steps)

	def AsGroup(self):
		return Group(self.objects[:])

	def Transform(self, trafo):
		if self.parent.changing_children:
			return Compound.Transform(self, trafo)
		else:
			return NullUndo

	def Translate(self, offset):
		if self.parent.changing_children:
			Compound.Translate(self, offset)
		return NullUndo

	def Info(self):
		return _("Interpolation with %d steps") % self.steps


class BlendGroup(Compound):

	is_Blend = 1
	is_Group = 1

	allow_traversal = 1 # allow selection of subobjects via M-Down etc.

	def __init__(self, steps = 0, start = None, end = None, duplicate = None):
		# Three different ways to instantiate this class:
		#
		# 1. Duplicating a BlendGroup: duplicate is not None.
		#
		# 2. Creating a BlendGroup from two normal graphics objects:
		#    start and end are not None.
		#
		# 3. Creating a BlendGroup from an sk file: steps is 0.

		if duplicate is not None:
			# case 1
			Compound.__init__(self, duplicate = duplicate)
			#self.Connect()
		elif start is not None:
			# case 2
			inter = BlendInterpolation(steps, start, end)
			Compound.__init__(self, [start, inter, end])
			#self.Connect()
		else:
			# case 3
			Compound.__init__(self)

	def load_AppendObject(self, object):
		Compound.load_AppendObject(self, object)
		length = len(self.objects)
		if length > 2 and length & 1:
			# last object was a control object
			if len(self.objects[-2].objects) == 0:
				self.objects[-2].Recompute(self.objects[-3], self.objects[-1])

	def insert(self, obj, at):
		undo_info = None
		try:
			if type(at) != IntType or at > len(self.objects):
				at = len(self.objects)
			self.objects.insert(at, obj)
			obj.SetDocument(self.document)
			obj.SetParent(self)
			obj.Connect()
			undo_info = (self.remove, at)
			self._changed()
			return undo_info
		except:
			if undo_info is not None:
				Undo(undo_info)
			raise

	def remove(self, idx):
		obj = self.objects[idx]
		del self.objects[idx]
		obj.Disconnect()
		obj.SetParent(None)
		self._changed()
		return (self.insert, obj, idx)

	def do_remove_child(self, idx):
		undo = []
		try:
			if idx % 2 == 0:
				# a control object
				if self.document is not None:
					undo.append(self.document.AddClearRect(self.bounding_rect))
				if len(self.objects) > 3:
					if idx == 0:
						undo.append(self.remove(1))
						undo.append(self.remove(0))
					elif idx == len(self.objects) - 1:
						undo.append(self.remove(idx))
						undo.append(self.remove(idx - 1))
					else:
						steps = self.objects[idx + 1].Steps() \
								+ self.objects[idx - 1].Steps()
						u = (UndoAfter, CreateMultiUndo(self.remove(idx + 1), self.remove(idx)),
								self.objects[idx - 1].SetParameters(steps))
						undo.append(u)
				else:
					# remove one of only two control objects -> Remove self
					undo.append(self.parent.Remove(self))
				return CreateListUndo(undo)
			else:
				# XXX implement this case
				raise ValueError, 'BlendGroup: cannot remove non control child'
		except:
			Undo(CreateListUndo(undo))
			raise

	def RemoveSlice(self, min, max):
		raise SketchInternalError('RemoveSlice not allowed for BlendGroup')

	def RemoveObjects(self, infolist):
		if not infolist:
			return NullUndo
		sliced = selinfo.list_to_tree_sliced(infolist)
		sliced.reverse()
		undo = [self.begin_change_children()]
		try:
			for start, end in sliced:
				if type(end) == IntType:
					# > 1 adjacent children of self. XXX implement this
					raise SketchInternalError('Deletion of multiple objects'
												' of BlendGroups not yet'
												' implemented')
				elif type(end) == ListType:
					# remove grandchildren (children of child of self)
					if start % 2 == 0:
						# control object changes. This should result in
						# a recompute() automatically.
						undo.append(self.objects[start].RemoveObjects(end))
					else:
						pass
				else:
					# a single child. If it's one of our control
					# objects, remove self
					undo.append(self.do_remove_child(start))
			undo.append(self.end_change_children())
			return CreateListUndo(undo)
		except:
			Undo(CreateListUndo(undo))
			raise

	def permute_objects(self, permutation):
		# for now, silently ignore this
		return NullUndo

	def DuplicateObjects(self, infolist, offset):
		# XXX: should allow duplication of the control objects by inserting
		# them into the parent.
		return [], NullUndo

	def ReplaceChild(self, child, object):
		idx = self.objects.index(child)
		if idx % 2 == 0:
			# the object is a control object
			undo = self.ReplaceChild, object, child
			self.objects[idx] = object
			object.SetParent(self)
			object.SetDocument(self.document)
			child.SetParent(None)
			self.ChildChanged(object)
			return undo
		else:
			raise SketchError('Cannot replace child')

	def SelectSubobject(self, p, rect, device, path = None, *rest):
		idx = self.Hit(p, rect, device) - 1
		obj = self.objects[idx]
		if idx % 2 == 0:
			# a control object
			if path:
				path_idx = path[0]
				path = path[1:]
				obj = obj.SelectSubobject(p, rect, device, path)
			elif path == ():
				obj = obj.SelectSubobject(p, rect, device)
			info = selinfo.prepend_idx(idx, obj)
		else:
			# an interpolation object
			if path is None:
				info = self
			else:
				info = selinfo.prepend_idx(idx, obj)
		return info

	def ForAllUndo(self, func):
		# XXX: should we just change start and end and recompute?
		self.begin_change_children()
		undo = map(func, self.objects)
		self.end_change_children(ignore_child_changes = 1)
		idx = range(0, len(self.objects), 2)
		undo = map(operator.getitem, [undo] * len(idx), idx)
		return CreateListUndo(undo)

	def begin_change_children(self):
		self.child_has_changed = 0
		return Compound.begin_change_children(self)

	def end_change_children(self, ignore_child_changes = 0):
		if self.child_has_changed and not ignore_child_changes:
			self.document.AddAfterHandler(self.recompute, (), self.depth())
		self.child_has_changed = 0
		return Compound.end_change_children(self)

	def ChildChanged(self, child):
		idx = self.objects.index(child)
		if idx % 2 == 0:
			if self.changing_children:
				self.child_has_changed = 1
			else:
				depth = self.depth(); recompute = self.recompute
				if idx > 0:
					self.document.AddAfterHandler(recompute, (idx - 1,), depth)
				if idx < len(self.objects) - 1:
					self.document.AddAfterHandler(recompute, (idx + 1,), depth)
		else:
			Compound.ChildChanged(self, child)
		self.del_lazy_attrs()

	def recompute(self, idx):
		self.objects[idx].Recompute(self.objects[idx - 1], self.objects[idx+1])

	def RecomputeChild(self, child):
		self.recompute(self.objects.index(child))

	def SaveToFile(self, file):
		file.BeginBlendGroup()
		for obj in self.objects:
			obj.SaveToFile(file)
		file.EndBlendGroup()

	def Info(self):
		return _("BlendGroup with %d control objects") \
				% (len(self.objects) / 2 + 1)

	def CancelEffect(self):
		self.unset_parent()
		idx = range(0, len(self.objects), 2)
		return map(operator.getitem, [self.objects] * len(idx), idx)

	def SelectControl(self, relative, which):
		idx = self.objects.index(relative)
		if idx % 2 == 1:
			# an interpolation
			if which == SelectStart:
				idx = idx - 1
			else:
				idx = idx + 1
		else:
			# a control
			if which == SelectStart:
				if idx > 0:
					idx = idx - 2
			else:
				if idx < len(self.objects) - 1:
					idx = idx + 2
		self.document.SelectObject(self.objects[idx])

	def ExtendBlend(self, start, end, steps):
		idx = self.objects.index(start)
		if idx == 0:
			inter = BlendInterpolation(steps, end, start)
			return CreateMultiUndo(self.insert(inter, 0), self.insert(end, 0))
		elif idx == len(self.objects) - 1:
			inter = BlendInterpolation(steps, start, end)
			return CreateMultiUndo(self.insert(inter, None), self.insert(end, None))

	def Ungroup(self):
		objects = []
		for obj in self.objects:
			if obj.__class__ is BlendInterpolation:
				objects.append(obj.AsGroup())
			else:
				objects.append(obj)
		return objects


def CreateBlendGroup(start, end, steps):
	if isinstance(start.parent, BlendGroup):
		undo = start.parent.ExtendBlend(start, end, steps)
		result = start.parent
	elif isinstance(end.parent, BlendGroup):
		undo = end.parent.ExtendBlend(end, start, steps)
		result = end.parent
	else:
		result = BlendGroup(steps, start, end)
		undo = NullUndo
	return result, undo
