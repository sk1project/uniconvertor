# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

#
#	Class MaskGroup
#
#	A special group where one object defines a clip mask for the
#	entire group
#

from app.events.warn import warn_tb, INTERNAL

#from app.UI.command import AddCmd

from app import _, IntersectRects, RegisterCommands
from compound import EditableCompound
from properties import EmptyFillStyle, EmptyLineStyle

class MaskGroup(EditableCompound):

	is_Group = 1
	is_MaskGroup = 1

	_lazy_attrs = EditableCompound._lazy_attrs.copy()
	_lazy_attrs['mask_fill'] = 'update_mask_attrs'
	_lazy_attrs['mask_line'] = 'update_mask_attrs'

	commands = EditableCompound.commands[:]

	def __init__(self, objects = None, duplicate = None):
		EditableCompound.__init__(self, objects,
									duplicate = duplicate)

	def update_mask_attrs(self):
		if self.objects:
			mask = self.objects[0]
			if mask.has_properties:
				self.mask_fill = mask.Properties().Duplicate()
				self.mask_fill.AddStyle(EmptyLineStyle)
				if mask.has_line and mask.Properties().HasLine():
					self.mask_line = mask.Properties().Duplicate()
					self.mask_line.AddStyle(EmptyFillStyle)
				else:
					self.mask_line = None
			else:
				self.mask_line = self.mask_fill = None

	def update_rects(self):
		if self.objects:
			self.bounding_rect = self.objects[0].bounding_rect
			self.coord_rect = self.objects[0].coord_rect

	def ChildChanged(self, child):
		if child is self.objects[0]:
			if self.document is not None:
				self.document.AddClearRect(child.bounding_rect)
		EditableCompound.ChildChanged(self, child)

	def Info(self):
		return _("MaskGroup with %d objects") % len(self.objects)

	def Hit(self, p, rect, device):
		if self.objects[0].Hit(p, rect, device, clip = 1):
			return EditableCompound.Hit(self, p, rect, device)

	def Blend(self, other, frac1, frac2):
		try:
			objs = self.objects
			oobjs = other.objects
			blended = []
			for i in range(min(len(objs), len(oobjs))):
				blended.append(Blend(objs[i], oobjs[i], frac1, frac2))
			return MaskGroup(blended)
		except:
			warn_tb(INTERNAL)
			raise MismatchError

	def Ungroup(self):
		objects = EditableCompound.GetObjects(self)
		# Move the mask, which is in objects[0] to the end of the
		# objects list, because it was on top of all other objects
		# before the group was created.
		#
		# Use a copy of the objects list or we're modifying the list
		# used by the mask group itself with unpredictable consequences
		# for undo.
		# XXX perhaps it would be better to have GetObjects return a
		# copy of the list.
		objects = objects[:]
		objects.append(objects[0])
		del objects[0]
		return objects

	def SaveToFile(self, file):
		file.BeginMaskGroup()
		for obj in self.objects:
			obj.SaveToFile(file)
		file.EndMaskGroup()

	def DrawShape(self, device, rect = None):
		if not self.objects:
			return
		mask = self.objects[0]
		if mask.has_properties:
			attr = mask.properties
			mask.properties = self.mask_fill
		device.PushClip()
		clipped = 1
		try:
			mask.DrawShape(device, rect, clip = 1)
			if rect:
				rect = IntersectRects(rect, mask.bounding_rect)
				test = rect.overlaps
				for o in self.objects[1:]:
					if test(o.bounding_rect):
						o.DrawShape(device, rect)
			else:
				for obj in self.objects[1:]:
					obj.DrawShape(device)
			if self.mask_line is not None:
				device.PopClip()
				clipped = 0
				mask.properties = self.mask_line
				mask.DrawShape(device, rect)
		finally:
			if clipped:
				device.PopClip()
			if mask.has_properties:
				mask.properties = attr

	def permute_objects(self, permutation):
		# make sure the mask stays at index 0
		if permutation[0] != 0:
			permutation = list(permutation)
			permutation.remove(0)
			permutation.insert(0, 0)
		return EditableCompound.permute_objects(self, permutation)

	def Mask(self):
		return self.objects[0]

	def MaskedObjects(self):
		return self.objects[1:]

	def SelectMask(self):
		if self.document is not None:
			self.document.SelectObject(self.objects[0])
	#AddCmd(commands, SelectMask, _("Select Mask"), key_stroke = 'm')

	context_commands = ('SelectMask',)

RegisterCommands(MaskGroup)
