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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307	USA

from app.conf import const
CHANGED = const.CHANGED
from app.events.connector import Publisher
from app import CreateListUndo, UndoAfter, NullUndo, SketchInternalError, _
from app.events.warn import pdebug, INTERNAL

from pattern import SolidPattern, EmptyPattern
from color import StandardColors, StandardCMYKColors
from blend import Blend


class Style(Publisher):

	is_dynamic = 0
	name = ''

	def __init__(self, name = '', duplicate = None, **kw):
		if duplicate is not None:
			self.__dict__ = duplicate.__dict__.copy()
			if hasattr(self, 'fill_pattern'):
				self.fill_pattern = self.fill_pattern.Copy()
			if hasattr(self, 'line_pattern'):
				self.line_pattern = self.line_pattern.Copy()
		else:
			if name:
				self.name = name
			for key, value in kw.items():
				setattr(self, key, value)

	def SetProperty(self, prop, value):
		dict = self.__dict__
		if dict.has_key(prop):
			undo = (self.SetProperty, prop, dict[prop])
		else:
			undo = (self.DelProperty, prop)
		if prop == 'fill_pattern' or prop == 'line_pattern':
			value = value.Copy()
		dict[prop] = value
		self.issue(CHANGED, self)
		return undo

	def DelProperty(self, prop):
		undo = (self.SetProperty, prop, getattr(self, prop))
		delattr(self, prop)
		self.issue(CHANGED, self)
		return undo

	def Duplicate(self):
		if self.is_dynamic:
			return self
		return self.__class__(duplicate = self)

	def Copy(self):
		return self.__class__(duplicate = self)

	def Name(self):
		return self.name

	def SetName(self, name):
		undo = self.SetName, self.name
		self.name = name
		return undo

	def AsDynamicStyle(self):
		result = self.Copy()
		result.is_dynamic = 1
		return result

	def AsUndynamicStyle(self):
		result = self.Copy()
		if self.is_dynamic:
			del result.is_dynamic
			del result.name
		return result

	def SaveToFile(self, file):
		if self.is_dynamic:
			file.DynamicStyle(self)

	def IsEmpty(self):
		return not self.__dict__

def FillStyle(pattern):
	return Style(fill_pattern = pattern)

EmptyFillStyle = Style(fill_pattern = EmptyPattern)

def LineStyle(color = None, width = 1, cap  = const.CapButt,
				join  = const.JoinMiter, dashes = None,
				arrow1 = None, arrow2 = None):
	return Style(line_pattern = SolidPattern(color), line_width = width,
					line_cap = cap, line_join = join, line_dashes = dashes,
					line_arrow1 = arrow1, line_arrow2 = arrow2)

SolidLine = LineStyle
EmptyLineStyle = Style(line_pattern = EmptyPattern)

class PropertyStack:

	update_cache = 1

	def __init__(self, base = None, duplicate = None):
		if duplicate is not None:
			self.stack = []
			for layer in duplicate.stack:
				self.stack.append(layer.Duplicate())
		else:
			if base is None:
				base = factory_defaults.Duplicate()
			self.stack = [base]

	def __getattr__(self, attr):
		if self.update_cache:
			cache = self.__dict__
			stack = self.stack[:]
			stack.reverse()
			for layer in stack:
				cache.update(layer.__dict__)
			self.update_cache = 0
		try:
			return self.__dict__[attr]
		except KeyError:
			raise AttributeError, attr

	def _clear_cache(self):
		self.__dict__ = {'stack' : self.stack}
		return (self._clear_cache,)

	def prop_layer(self, prop):
		# return property layer containing PROP
		for item in self.stack:
			if hasattr(item, prop):
				return item
		# we should never reach this...
		raise SketchInternalError('unknown graphics property "%s"' % prop)

	def set_property(self, prop, value):
		layer = self.prop_layer(prop)
		if layer.is_dynamic:
			if self.stack[0].is_dynamic:
				layer = Style()
				setattr(layer, prop, value)
				return self.add_layer(layer)
			else:
				layer = self.stack[0]
		return layer.SetProperty(prop, value)

	def SetProperty(self, **kw):
		stack = self.stack
		undo = []
		append = undo.append
		if len(stack) == 1 and not stack[0].is_dynamic:
			set = stack[0].SetProperty
			for prop, value in kw.items():
				append(set(prop, value))
		else:
			set = self.set_property
			for prop, value in kw.items():
				append(set(prop, value))

		if len(self.stack) > 1:
			undo_stack = (self.set_stack, self.stack[:])
			if self.delete_shadowed_layers():
				undo.append(undo_stack)
		undo = CreateListUndo(undo)
		undo = (UndoAfter, undo, self._clear_cache())
		return undo

	def set_stack(self, stack):
		undo = (self.set_stack, self.stack)
		self.stack = stack
		self._clear_cache()
		return undo

	def delete_shadowed_layers(self):
		# check if some styles are completely hidden now
		stack = self.stack
		layers = []
		dict = {'name':1, 'is_dynamic':0}
		dict.update(stack[0].__dict__)
		length = len(dict)
		for layer in stack[1:]:
			dict.update(layer.__dict__)
			if length != len(dict):
				layers.append(layer)
			length = len(dict)
		length = len(stack)
		stack[1:] = layers
		return length != len(stack)

	def add_layer(self, layer):
		undo = (self.set_stack, self.stack[:])
		self.stack.insert(0, layer)
		return undo
	load_AddStyle = add_layer

	def AddStyle(self, style):
		if style.is_dynamic:
			undo = self.add_layer(style)
			self.delete_shadowed_layers()
			self._clear_cache()
			return undo
		else:
			return apply(self.SetProperty, (), style.__dict__)


	def HasFill(self):
		return self.fill_pattern is not EmptyPattern

	def IsAlgorithmicFill(self):
		return self.fill_pattern.is_procedural

	def ExecuteFill(self, device, rect = None):
		self.fill_pattern.Execute(device, rect)

	def HasLine(self):
		return self.line_pattern is not EmptyPattern

	def IsAlgorithmicLine(self):
		return self.line_pattern.is_procedural

	def ExecuteLine(self, device, rect = None):
		line_pattern = self.line_pattern
		if line_pattern is not EmptyPattern:
			line_pattern.Execute(device, rect)
			device.SetLineAttributes(self.line_width, self.line_cap,
										self.line_join, self.line_dashes)

	def HasFont(self):
		return self.font is not None

	def ObjectChanged(self, object):
		if object in self.stack:
			self._clear_cache()
			return 1
		return 0

	def ObjectRemoved(self, object):
		if object in self.stack:
			idx = self.stack.index(object)
			undo = (self.set_stack, self.stack[:])
			self.stack[idx] = self.stack[idx].AsUndynamicStyle()
			pdebug('properties', 'made style undynamic')
			return undo
		return NullUndo

	def Untie(self):
		info = []
		for i in range(len(self.stack)):
			style = self.stack[i]
			if style.is_dynamic:
				self.stack[i] = style.AsUndynamicStyle()
				info.append((i, style))
		self._clear_cache()
		return info

	def Tie(self, document, info):
		for i, style in info:
			s = document.GetDynamicStyle(style.Name())
			if s == style:
				self.stack[i] = s
		self._clear_cache()

	def Duplicate(self):
		return self.__class__(duplicate = self)


	grow_join = [5.240843064, 0.5, 0.5]
	grow_cap = [None, 0.5, 0.5, 0.70710678]

	def GrowAmount(self):
		return self.line_width * max(self.grow_cap[self.line_cap],
										self.grow_join[self.line_join])

	def Blend(self, other, frac1, frac2):
		result = {}
		for prop, func in blend_functions:
			if func:
				result[prop] = func(getattr(self, prop), getattr(other, prop),
									frac1, frac2)
			else:
				result[prop] = getattr(self, prop)
		return PropertyStack(apply(Style, (), result))

	def Transform(self, trafo, rects):
		# XXX hardcoding which properties may need to be transformed is
		# not really a good idea, but it's significantly faster.
		undo = NullUndo
		if len(self.stack) == 1 and not self.stack[0].is_dynamic:
			if self.fill_transform:
				pattern = self.fill_pattern
				if pattern.is_procedural:
					undo = pattern.Transform(trafo, rects)
		elif self.fill_transform:
			pattern = self.fill_pattern
			if pattern.is_procedural:
				pattern = pattern.Duplicate()
				if pattern.Transform(trafo, rects) is not NullUndo:
					undo = self.set_property('fill_pattern', pattern)
		if undo is not NullUndo:
			undo = (UndoAfter, undo, self._clear_cache())
		return undo

	def CreateStyle(self, which_properties):
		properties = {}
		for prop in which_properties:
			if property_types[prop] == FontProperty and not self.HasFont():
				continue
			properties[prop] = getattr(self, prop)
		return apply(Style, (), properties)

	def DynamicStyleNames(self):
		names = []
		for style in self.stack:
			if style.is_dynamic:
				names.append(style.Name())
		return names

	def condense(self):
		stack = self.stack
		last = stack[0]
		for style in stack[1:]:
			if not last.is_dynamic and not style.is_dynamic:
				dict = style.__dict__.copy()
				dict.update(last.__dict__)
				last.__dict__ = dict
			last = style
		length = len(stack)
		self.delete_shadowed_layers()

	def SaveToFile(self, file):
		file.Properties(self)


class _EmptyProperties:
	def HasFill(self):
		return 0
	HasLine = HasFill
	HasFont = HasFill

	def DynamicStyleNames(self):
		return []

EmptyProperties = _EmptyProperties()

#
#
#

factory_defaults = Style()
default_graphics_style = None # set below
default_text_style = None # set below
blend_functions = []
property_names = []
property_titles = {}
property_types = {}
transform_properties = []

def blend_number(n1, n2, frac1, frac2):
	return n1 * frac1 + n2 * frac2

LineProperty = 1
FillProperty = 2
FontProperty = 3
OtherProperty = -1

def _set_defaults(prop, title, short_title, type, value,
					blend = None, transform = 0):
	factory_defaults.SetProperty(prop, value)
	property_names.append(prop)
	property_titles[prop] = (title, short_title)
	property_types[prop] = type
	blend_functions.append((prop, blend))
	if transform:
		transform_properties.append(prop)

black = StandardCMYKColors.black

# XXX the default properties should be defined by the user.
_set_defaults('fill_pattern', _("Fill Pattern"), _("Pattern"), FillProperty,
				EmptyPattern, blend = Blend, transform = 1)
_set_defaults('fill_transform', _("Fill Transform Pattern"),
				_("Transform pattern"), FillProperty, 1)
_set_defaults('line_pattern', _("Line Pattern"), _("Pattern"), LineProperty,
				SolidPattern(black), blend = Blend, transform = 1)
_set_defaults('line_width', _("Line Width"), _("Width"), LineProperty, .283286 ,
				blend = blend_number)
_set_defaults('line_cap', _("Line Cap"), _("Cap"), LineProperty,
				const.CapButt)
_set_defaults('line_join', _("Line Join"), _("Join"), LineProperty,
				const.JoinMiter)
_set_defaults('line_dashes', _("Line Dashes"), _("Dashes"), LineProperty, ())
_set_defaults('line_arrow1', _("Line Arrow 1"), _("Arrow 1"), LineProperty,
				None)
_set_defaults('line_arrow2', _("Line Arrow 2"), _("Arrow 2"), LineProperty,
				None)
_set_defaults('font', _("Font"), _("Font"), FontProperty, None)
_set_defaults('font_size', _("Font Size"), _("Size"), FontProperty, 12, blend = blend_number)
_set_defaults('linegap', _("Linegap"), _("Linegap"), FontProperty, 1.0)
_set_defaults('wordgap', _("Wordgap"), _("Wordgap"), FontProperty, 1.0)
_set_defaults('chargap', _("Chargap"), _("Chargap"), FontProperty, 1.0)
_set_defaults('align', _("Text Alignment"), _("Alignment"), FontProperty, const.ALIGN_LEFT)
_set_defaults('valign', _("Text Vertical Alignment"), _("VAlignment"), FontProperty, const.ALIGN_BASE)


factory_text_style = factory_defaults.Copy()
factory_text_style.fill_pattern = SolidPattern(black)
factory_text_style.line_pattern = EmptyPattern
factory_text_style.font = None
default_graphics_style = factory_defaults.Copy()
default_text_style = factory_defaults.Copy()
default_text_style.fill_pattern = SolidPattern(black)
default_text_style.line_pattern = EmptyPattern
default_text_style.font = None


def FactoryTextStyle():
	import app
	style = factory_text_style.Copy()
	if style.font is None:
		fontname = app.config.preferences.default_font
		style.font = app.GetFont(fontname)
	return style

def DefaultTextProperties():
	import app
	if default_text_style.font is None:
		fontname = app.config.preferences.default_font
		default_text_style.font = app.GetFont(fontname)
	return PropertyStack(base = default_text_style.Copy())

def DefaultGraphicsProperties():
	return PropertyStack(base = default_graphics_style.Copy())

def set_graphics_defaults(kw):
	for key, value in kw.items():
		if not property_types[key] == FontProperty:
			if key in ('fill_pattern', 'line_pattern'):
				value = value.Copy()
			default_graphics_style.SetProperty(key, value)

def set_text_defaults(kw):
	for key, value in kw.items():
		if not property_types[key] == LineProperty:
			if key == 'fill_pattern':
				value = value.Copy()
			default_text_style.SetProperty(key, value)
	
