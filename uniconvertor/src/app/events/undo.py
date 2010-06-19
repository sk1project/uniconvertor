# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998 by Bernhard Herzogg 
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


#
#	Sketch's undo handler
#
# For a description of the representation and generation of undo
# information, see the Developer's Guide in the Doc directory.
#


from types import StringType, TupleType
from app import config 
preferences = config.preferences
from sys import maxint

from app.events.warn import warn, INTERNAL, warn_tb

from app import _

def Undo(info):
	# execute a single undoinfo
	func = info[0]
	if type(func) == StringType:
		text = func
		func = info[1]
		args = info[2:]
	else:
		args = info[1:]
		text = None
	try:
		redo = apply(func, args)
		if text is not None and callable(redo[0]):
			return (text,) + redo
		else:
			return redo
	except:
		warn(INTERNAL, 'Exception in undo:\ninfo: %s\nfunc: %s\nargs: %s',
				info, func, args)
		warn_tb(INTERNAL)
		

def UndoList(infos):
	undoinfo = map(Undo, infos)
	undoinfo.reverse()
	return (UndoList, undoinfo)

def _get_callable(info):
	if type(info[0]) == StringType:
		return info[1]
	return info[0]

def CreateListUndo(infos):
	infos.reverse()
	undolist = []
	for info in infos:
		if info is NullUndo:
			continue
		if info[0] is UndoList:
			undolist[len(undolist):] = list(info[-1])
		else:
			undolist.append(info)
	if undolist:
		if len(undolist) == 1:
			return undolist[0]
		return (UndoList, undolist)
	return NullUndo

def CreateMultiUndo(*infos):
	if len(infos) > 1:
		return CreateListUndo(list(infos))
	return infos[0]


def UndoAfter(undo_info, after_info):
	return (UndoAfter, Undo(undo_info), Undo(after_info))


# NullUndo: undoinfo that does nothing. Useful when undoinfo has to be
# returned but nothing has really changed.
def _NullUndo(*ignore):
	return NullUndo
NullUndo = (_NullUndo,)

class UndoTypeError(Exception):
	pass

def check_info(info):
	# Check whether INFO has the correct format for undoinfo. Raise
	# UndoTypeError if the format is invalid.
	if type(info) != TupleType:
		raise UndoTypeError("undo info is not a tuple (%s, type %s)"
							% (info, type(info)))
	if len(info) < 1:
		raise UndoTypeError("undo info is empty tuple")
	f = info[0]
	if type(f) == StringType:
		if len(info) > 1:
			f = info[1]
	if not callable(f):
		raise UndoTypeError("undo info has no callable item")

def check_info_silently(info):
	# Return true if INFO is valid undo information, false otherwise.
	try:
		check_info(info)
		return 1
	except UndoTypeError:
		return 0

class UndoRedo:

	# A Class that manages lists of of undo and redo information
	# 
	# It also manages the undo count. This is the number of operations
	# performed on the document since the last save operation. It
	# increased by adding undo info, that is, by editing the document or
	# by Redo, and is decreased by undoing something. The undo count can
	# be used to determine whether the document was changed since the
	# last save or not.

	undo_count = 0
	
	def __init__(self):
		self.undoinfo = []
		self.redoinfo = []
		self.SetUndoLimit(preferences.undo_limit)
		if not self.undo_count:
			self.undo_count = 0

	def SetUndoLimit(self, undo_limit):
		if undo_limit is None:
			# unlimited undo. approximate by choosing a very large number
			undo_limit = maxint
		if undo_limit >= 1:
			self.max_undo = undo_limit
		else:
			self.max_undo = 1

	def CanUndo(self):
		# Return true, iff an undo operation can be performed.
		return len(self.undoinfo) > 0

	def CanRedo(self):
		# Return true, iff a redo operation can be performed.
		return len(self.redoinfo) > 0

	def Undo(self):
		# If undo info is available, perform a single undo and add the
		# redo info to the redo list. Also, decrement the undo count.
		if len(self.undoinfo) > 0:
			self.add_redo(Undo(self.undoinfo[0]))
			del self.undoinfo[0]
			self.undo_count = self.undo_count - 1

	def AddUndo(self, info, clear_redo = 1):
		# Add the undo info INFO to the undo list. If the undo list is
		# longer than self.max_undo, discard the excessive undo info.
		# Also increment the undo count and discard all redo info.
		#
		# The flag CLEAR_REDO is used for internal purposes and inhibits
		# clearing the redo info if it is false. This flag is only used
		# by the Redo method. Code outside of this class should not use
		# this parameter.
		check_info(info)
		if info:
			self.undoinfo.insert(0, info)
			self.undo_count = self.undo_count + 1
			if len(self.undoinfo) > self.max_undo:
				del self.undoinfo[self.max_undo:]
			if clear_redo:
				self.redoinfo = []

	def Redo(self):
		# If redo info is available, perform a single redo and add the
		# undo info to the undo list. The undo count is taken care of by
		# the AddUndo method.
		if len(self.redoinfo) > 0:
			self.AddUndo(Undo(self.redoinfo[0]), 0)
			del self.redoinfo[0]

	def add_redo(self, info):
		# Internal method: add a single redo info
		check_info(info)
		self.redoinfo.insert(0, info)

	def UndoText(self):
		# Return a string to describe the operation that would be undone
		# next, in a format suitable for a menu entry.
		if self.undoinfo:
			undolabel = self.undoinfo[0][0]
			if type(undolabel) == StringType:
				return _("Undo %s") % undolabel
		return _("Undo")

	def RedoText(self):
		# Return a string to describe the operation that would be redone
		# next, in a format suitable for a menu entry.
		if self.redoinfo:
			redolabel = self.redoinfo[0][0]
			if type(redolabel) == StringType:
				return _("Redo %s") % redolabel
		return _("Redo")

	def Reset(self):
		# Forget all undo/redo information
		self.__init__()

	def ResetUndoCount(self):
		self.undo_count = 0

	def UndoCount(self):
		return self.undo_count
