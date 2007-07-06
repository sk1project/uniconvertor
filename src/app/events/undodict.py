# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

#
# A dictionary with undo capability. This is used for the styles, so
# this dictionary assumes, that objects stored in it have SetName() and
# Name() methods.
#

from app.events.undo import NullUndo

class UndoDict:

	def __init__(self):
		self.dict = {}

	def __getitem__(self, key):
		return self.dict[key]

	def __len__(self):
		return len(self.dict)
	
	def keys(self):
		return self.dict.keys()

	def items(self):
		return self.dict.items()

	def values(self):
		return self.dict.values()
	
	def has_key(self, key):
		return self.dict.has_key(key)

	def SetItem(self, key, item):
		# Add ITEM to self using KEY.
		#      
		# Two cases:
		#
		#	1. ITEM is stored in self under item.Name(): Store it under
		#	KEY, rename ITEM and remove the old entry.
		#
		#	2. ITEM is not stored in self: Store it under KEY and rename
		#	ITEM.
		if self.dict.has_key(key):
			if self.dict[key] is item:
				return NullUndo
			# name conflict
			raise ValueError, '%s already used' % key
		oldname = item.Name()
		if self.dict.has_key(oldname):
			del self.dict[oldname]
			undo = (self.SetItem, oldname, item)
		else:
			undo = (self.DelItem, key)
		item.SetName(key)
		self.dict[key] = item
		return undo

	def DelItem(self, key):
		item = self.dict[key]
		del self.dict[key]
		return (self.SetItem, key, item)

			
			
