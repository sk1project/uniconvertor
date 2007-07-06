# Sketch - A Python-based interactive drawing program
# Copyright (C) 1998, 1999, 2001 by Bernhard Herzog
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


from types import TupleType
from app import _, SketchError, CreateListUndo, Undo, \
		Trafo, Translation, Scale, Identity, TrafoType

from compound import Compound


class PluginCompound(Compound):

	class_name = ''	 # has to be provided by derived classes
	is_Plugin = 1

	def SetParameters(self, kw = None):
		# XXX could be extended to handle keyword arguments.
		undo = {}
		for key, value in kw.items():
			undo[key] = getattr(self, key)
			setattr(self, key, value)
		return self.SetParameters, undo

	def SaveToFile(self, file, *args, **kw):
		if self.class_name:
			apply(file.BeginPluginCompound, (self.class_name,) + args, kw)
			for obj in self.objects:
				obj.SaveToFile(file)
			file.EndPluginCompound()
		else:
			raise SketchError("Plugin %s doesn't define a class name"
								% self.__class__)

class TrafoPlugin(PluginCompound):

	def __init__(self, trafo = None, duplicate = None, loading = 0):
		PluginCompound.__init__(self, duplicate = duplicate)
		if duplicate is not None:
			self.trafo = duplicate.trafo
		else:
			if trafo is None:
				trafo = Identity
			elif type(trafo) == TupleType:
				trafo = apply(Trafo, trafo)
			elif isinstance(trafo, TrafoType):
				# trafo is already a trafo object
				pass
			else:
				# assume a number and interpret it as a scaling transformation
				trafo = Scale(trafo)
			self.trafo = trafo

	def recompute(self):
		# Implement this in the derived class to update the children.
		pass

	def SetParameters(self, kw):
		undo = PluginCompound.SetParameters(self, kw)
		try:
			self.recompute()
		except:
			Undo(undo)
			raise
		return undo

	def set_transformation(self, trafo):
		undo = (self.set_transformation, self.trafo)
		self.trafo = trafo
		self.recompute()
		return undo

	def Transform(self, trafo):
		undo = [self.begin_change_children()]
		try:
			undo.append(PluginCompound.Transform(self, trafo))
			undo.append(self.set_transformation(trafo(self.trafo)))
			undo.append(self.end_change_children())
		except:
			undo.reverse()
			map(Undo, undo)
			raise
		return CreateListUndo(undo)

	def Translate(self, offset):
		return self.Transform(Translation(offset))

	def RemoveTransformation(self):
		return self.set_transformation(Translation(self.trafo.offset()))

	def LayoutPoint(self):
		return self.trafo.offset()

	def Trafo(self):
		return self.trafo


class UnknownPlugin(PluginCompound):

	is_Group = 1
	changed = 0

	def __init__(self, class_name = '', *args, **kw):
		if kw.has_key('loading'):
			del kw['loading']
		duplicate = kw.get('duplicate')
		if duplicate is not None:
			self.class_name = duplicate.class_name
			self.args = duplicate.args
			self.kw = duplicate.kw
		else:
			self.class_name = class_name
			self.args = args
			self.kw = kw
		PluginCompound.__init__(self, duplicate = duplicate)
		self.disguise()

	def disguise(self):
		# If self has only one child, try to behave like it:
		if len(self.objects) == 1:
			object = self.objects[0]
			if object.is_curve:
				self.is_curve = object.is_curve
				self.AsBezier = object.AsBezier
				self.Paths = object.Paths

	def _changed(self):
		PluginCompound._changed(self)
		self.changed = 1

	def load_Done(self):
		PluginCompound.load_Done(self)
		self.disguise()

	def SaveToFile(self, file):
		if not self.changed:
			apply(PluginCompound.SaveToFile, (self, file) + self.args, self.kw)
		else:
			# XXX an alternative approach for a changed UnknownPlugin
			# might be to store explicitly as an 'UnknownPlugin' so that
			# always is represented by this class.
			if len(self.objects) == 1:
				self.objects[0].SaveToFile(file)
			else:
				# Save as ordinary group. This might not be a good idea,
				# since the UnknownPlugin may (in the future) have some
				# special behaviour, that the group doesn't have.
				file.BeginGroup()
				for obj in self.objects:
					obj.SaveToFile(file)
				file.EndGroup()


	def Info(self):
		return _("Unknown Plugin Object `%s'") % self.class_name

	Ungroup = PluginCompound.GetObjects


# XXX this implementation of the UnknownPlugin my fail in some
# situations.
#
# The following example is now fixed, but similar situations are
# conceivable:
#
# If the plugin defines is_curve and AsBezier(), for instance, it can be
# used as a control object in a BlendGroup with, say, a PolyBezier
# object as the other control object. The UnknownPlugin does not provide
# that interface, so that loading a document containing such a
# BlendGroup would fail, because the UnknownPlugin instance cannot be
# converted to a PolyBezier object when the interpolation is recomputed.
#
# A solution would be to make the UnknownPlugin behave different if it
# only has one child. Or to have it examine its children and try to
# support the interfaces they have in common. I.e. if all children have
# is_curve == 1, it could also set its instance variable is_curve to 1,
# and implement the AsBezier meghod by returning a PolyBezier object
# that is the combination (`Combine Beziers') of its converted children.
# This would not always be appropriate, however.
#
# Are there other cases where UnknownPlugin has shortcomings?

