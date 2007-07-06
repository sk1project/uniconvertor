# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2000, 2002 by Bernhard Herzog
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
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

from types import ListType

from app import _
from app.conf.const import SCRIPT_UNDO, SCRIPT_GET, SCRIPT_OBJECT, \
		SCRIPT_OBJECTLIST, SelectSet
from app.events.warn import warn, USER

class UndoMethodWrapper:

	def __init__(self, method, document):
		self.method = method
		self.document = document

	def __call__(self, *args, **kw):
		self.document.AddUndo(apply(self.method, args, kw))

class ObjectMethodWrapper:

	def __init__(self, method, document):
		self.method = method
		self.document = document

	def __call__(self, *args, **kw):
		return ObjectWrapper(apply(self.method, args, kw), self.document)

class ObjectListMethodWrapper:

	def __init__(self, method, document):
		self.method = method
		self.document = document

	def __call__(self, *args, **kw):
		objects = apply(self.method, args, kw)
		return map(ObjectWrapper, objects, (self.document,) * len(objects))


# special methods (__*__) which can be called safely
safe_special_methods = {
	"__eq__": 1,
	"__lt__": 1,
	"__gt__": 1,
	"__cmp__": 1,
	"__repr__": 1,
	"__str__": 1,
	"__coerce__": 1,
	}
	
class Wrapper:

	def __init__(self, object, document):
		self._object = object
		self._document = document

	def __getattr__(self, attr):
		try:
			access = self._object.script_access[attr]
		except KeyError:
			if not safe_special_methods.get(attr):
				warn(USER,'Cant access attribute %s of %s in safe user script', attr, self._object)
			raise AttributeError, attr
		if access == SCRIPT_UNDO:
			return UndoMethodWrapper(getattr(self._object, attr), self._document)
		elif access == SCRIPT_GET:
			return getattr(self._object, attr)
		elif access == SCRIPT_OBJECT:
			return ObjectMethodWrapper(getattr(self._object, attr), self._document)
		elif access == SCRIPT_OBJECTLIST:
			return ObjectListMethodWrapper(getattr(self._object, attr), self._document)
		else:
			raise AttributeError, attr

	def __cmp__(self, other):
		return cmp(self._object, strip_wrapper(other))

def strip_wrapper(wrapped):
	if isinstance(wrapped, Wrapper):
		return wrapped._object
	else:
		return object


class DocumentWrapper(Wrapper):

	def __init__(self, document):
		Wrapper.__init__(self, document, document)

	def SelectObject(self, objects, mode = SelectSet):
		if type(objects) == ListType:
			objects = map(strip_wrapper, objects)
		else:
			objects = strip_wrapper(objects)
		self._document.SelectObject(objects, mode)

	def DeselectObject(self, object):
		self._document.DeselectObject(strip_wrapper(object))

	def Insert(self, object, undo_text = _("Create Object")):
		self._document(strip_wrapper(object), undo_text)

				


#

ObjectWrapper = Wrapper

