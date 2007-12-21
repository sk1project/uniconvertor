# Sketch - A Python-based interactive drawing program
# Copyright (C) 1996, 1997, 1998 by Bernhard Herzog
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


# Functions to manipulate selection info

#
# Representation
#
# The set of currently selected objects in Sketch is represented as a
# list of tuples. Each of the tuples has the form:
#
#	(PATH, OBJ)
#
# where OBJ is a selected object and PATH is a tuple of ints describing
# the path through the hierarchy of objects to OBJ, usually starting
# from the document at the top of the hierarchy. Each item in PATH is
# the index of the next object in the path. For example, the second
# object in the first layer has the PATH (0, 1) (indexes start from 0).
#
# This representation serves two purposes:
#
#	1. storing the path to the object allows fast access to the
#	parents of the selected object.
#
#	2. it allows sorting the list by path, which results in a list
#	with the objects lowest in the stack of objects at the front.
#
#	A sorted list is important when changing the stacking order of
#	objects, since the indices, i.e. the path elements, may change
#	during the operation.
#
#	Sorting the list also allows to make sure that each selected
#	object is listed exactly once in the list.
#
# This representation, if the list is sorted, is called the _standard
# representation_.
#
# Alternative Representations:
#
# There are several alternative representations that are mainly useful
# in the methods of compound objects that rearrange the children. In
# those methods, the path is usually taken relative to self. Where
# selection info has to be passed to children, to rearrange their
# children, the first component of the path is stripped, so that the
# path is relative to the child.
#
# All of the alternative representations are lists of tuples sorted at
# least by the first item of the tuples.
#
# Tree:
#
# An alternative representation of the selection info is a list of
# tuples of the form:
#
#	(INDEX, LIST)
#
# where INDEX is just the first part of the PATH of the standard
# representation and LIST is a list of selection info in standard
# representation but with each PATH stripped of its first component
# which is INDEX. That is, LIST is selection info in standard form
# relative to the compound object given by INDEX.
#
# Tree2:
#
# Just like Tree1, but if LIST would contain just one item with an empty
# PATH (an empty tuple), LIST is replaced by the object.
#
# Sliced Tree:
#
# A variant of Tree2, where consecutive items with an object (i.e.
# something that is no list) are replaced by a tuple `(start, end)'
# where start is the lowest INDEX and end the highest. Consecutive items
# are items where the INDEX parts are consecutive integers.
#
#
# Creating Selection Info:
#
# Selecting objects is done for instance by the GraphicsObject method
# SelectSubobject. In a compound object, when it has determined that a
# certain non compound child obj is to be selected, this method
# constructs a selection info tuple by calling build_info:
#
#	info1 = build_info(idx1, obj)
#
# idx is the index of obj in the compound object's list of children.
# info1 will then be just a tuple: ((idx1,) obj) This info is returned
# to the caller, its parent, which is often another compound object.
# This parent then extends the selection info with
#
#	info2 = prepend_idx(idx2, info)
#
# This results in a new tuple new_info: ((idx2, idx1), obj). idx2 is, of
# course, the index of the compound object in its parent's list of
# children.
#
# Finally, the document object receives such a selection info tuple from
# one of its layers, prepends that layer's index to the info and puts it
# into the list of selected objects.
#


from types import TupleType, ListType

def build_info(idx, obj):
	return ((idx,), obj)

def prepend_idx(idx, info):
	# prepend idx to the path of info.
	if type(info) == TupleType:
		return ((idx,) + info[0], info[1])

	if type(info) == ListType:
		idx = (idx,)
		for i in range(len(info)):
			tmp = info[i]
			info[i] = (idx + tmp[0], tmp[1])
		return info

	# assume info is an instance object
	return ((idx,), info)

def select_all(objects):
	return map(None, map(lambda *t: t, range(len(objects))), objects)

def select_range(min, objects):
	return map(None, map(lambda *t: t, range(min, min + len(objects))),
				objects)

def get_parent(info):
	path, obj = info
	if len(path) > 1:
		parent = obj.parent
		if parent is not None:
			return (path[:-1], parent)
	return None


def list_to_tree(infolist):
	# convert standard representation to Tree1 representation
	dict = {}
	for info in infolist:
		path, obj = info
		idx = path[0]
		info = (path[1:], obj)
		try:
			dict[idx].append(info)
		except KeyError:
			dict[idx] = [info]
	result = dict.items()
	result.sort()
	for idx, info in result:
		info.sort()
	return result

def list_to_tree2(infolist):
	# convert standard representation to Tree2 representation
	dict = {}
	for info in infolist:
		path, obj = info
		idx = path[0]
		path = path[1:]
		if path:
			info = (path, obj)
		else:
			info = obj
		try:
			dict[idx].append(info)
		except KeyError:
			dict[idx] = [info]
	result = dict.items()
	result.sort()
	for i in range(len(result)):
		idx, info = result[i]
		if len(info) == 1 and type(info[0]) != TupleType:
			result[i] = (idx, info[0])
		else:
			info.sort()
	return result

def list_to_tree_sliced(infolist):
	# convert standard representation to sliced tree representation
	result = []
	slice_start = slice_end = -1
	last_obj = None
	for idx, list in list_to_tree2(infolist):
		if type(list) != ListType:
			# list is a child
			if idx == slice_end:
				slice_end = idx + 1
			else:
				if slice_start > -1:
					if slice_end > slice_start + 1:
						result.append((slice_start, slice_end))
					else:
						result.append((slice_start, last_obj))
				slice_start = idx
				slice_end = idx + 1
				last_obj = list
		else:
			# list is a list of children of child
			if slice_start > -1:
				if slice_end > slice_start + 1:
					result.append((slice_start, slice_end))
				else:
					result.append((slice_start, last_obj))
			slice_start = -1
			slice_end = -1
			last_obj = None
			result.append((idx, list))
	else:
		if slice_start > -1:
			if slice_end > slice_start + 1:
				result.append((slice_start, slice_end))
			else:
				result.append((slice_start, last_obj))
	return result



def tree_to_list(tree):
	result = []
	for idx, info in tree:
		idx = (idx,)
		for path, obj in info:
			result.append((idx + path, obj))
	return result


def common_prefix(list):
	# Return the longest path that all items in LIST have in common.
	# LIST is in standard representation. Since that is a sorted list,
	# we just have to compare the first and last elements.
	if not list:
		return ()
	if len(list) == 1:
		return list[0][0]
	first = list[0][0]
	last = list[-1][0]
	if len(first) > len(last):
		length = len(last)
		first = first[:length]
	else:
		length = len(first)
		last = last[:length]
	for i in range(length):
		if first[i] != last[i]:
			return first[:i]
	return first


