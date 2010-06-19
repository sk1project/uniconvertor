# -*- coding: utf-8 -*-
# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
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
# SimpleText: A graphics object representing a single line of text
#
#
# Model:
#
# An instance of SimpleText is a single line of text in one particular
# font. The position and orientation of the text is described by an
# anchor point and an arbitrary linear transformation (a 2x2-matrix).
# The transformation allows rotated, sheared, reflected and nonuniformly
# scaled text.
#
# In addition, there are two flags that control which of several special
# points of the text is located at the anchor point: horizontal and
# vertical alignment. The special point chosen is the reference point.
#
# Horizontal alignment can be one of `left', `right' and `center',
# meaning the left, right and horizontal center of the text. Vertical
# alignment can be `top', `bottom', `center' and `baseline', referring
# to the top, bottom, vertical center and the baseline of the text.
#
# The default alignment is left and baseline.
#
# The anchor point is also the layout point. If some form of snapping is
# active, this point will be `magnetic'.
#
#
# Representation:
#
# The position and orientation of a SimpleText-instance is stored in a
# single affine transformation in the instance variable `trafo' (An
# instance of the Trafo type (see the developer's guide)). The
# translation part of the transformation (trafo.v1 and trafo.v2) is the
# position of the anchor point. The matrix part (trafo.m11, ...,
# trafo.m22) is the linear transformation.
#
# The alignment is stored in the instance variables `halign' and
# `valign' and in a special internal transformation `atrafo'.
#
# atrafo is set up in such a way, that trafo(atrafo) (the concatenation
# of both transformations) maps text coordinates to document
# coordinates. Text coordinates are the natural coordinates for the text
# and the given font and size. The origin is the leftmost point of the
# first character projected on the baseline. X extends to the right, y
# upwards. The unit is the point.
#
# While halign and valign are independent of font, size and the text
# itself, atrafo needs to be recomputed every time some of these change.
#
# The definition of trafo and atrafo leads to these rules:
#
# 1. trafo(0, 0) is the anchor point.
#
# 2. If (rx, ry) is the reference point in text coordinates, then
#		atrafo(rx, ry) == (0, 0)
#
# 3. For the default alignment, atrafo is the identity transformation.
#
#

from string import split
from math import sin, cos, atan2, hypot, pi, fmod, floor
		
from app import _, Rect, UnionRects, EmptyRect, NullPoint, Polar, \
		IdentityMatrix, SingularMatrix, Identity, Trafo, Scale, Translation, \
		Rotation, NullUndo, CreateMultiUndo, RegisterCommands
#from app.UI.command import AddCmd
from app import config
from app.conf import const

import handle
import selinfo, codecs
from base import Primitive, RectangularPrimitive, Creator, Editor
from compound import Compound
from group import Group
from bezier import PolyBezier, CombineBeziers
from blend import Blend, MismatchError, BlendTrafo
from properties import PropertyStack, FactoryTextStyle, DefaultTextProperties
import color, pattern, app

from app.Lib import encoding; iso_latin_1 = encoding.iso_latin_1


(encoder,decoder, sr,sw)=codecs.lookup('utf-8')


printable = ''
for n in range(len(iso_latin_1)):
	if iso_latin_1[n] != encoding.notdef:
		printable = printable + chr(n)

# Alignment. Defaults are 0
ALIGN_BASE = 0
ALIGN_CENTER = 1
ALIGN_TOP = 2
ALIGN_BOTTOM = 3
ALIGN_LEFT = 0
ALIGN_CENTER = 1
ALIGN_RIGHT = 2

class CommonText:

	commands = []

	def __init__(self, text = '', duplicate = None):
		if duplicate is not None:
			self.text = duplicate.text
		else:
			self.text = text

	def SetText(self, text, caret = None):
		if self.editor is not None:
			oldcaret = self.editor.Caret()
		else:
			oldcaret = 0
		undo = (self.SetText, self.text, oldcaret)
		self.text = text
		if caret is not None and self.editor is not None:
			self.editor.SetCaret(caret)
		self._changed()
		return undo

	def Text(self):
		return self.text

	editor = None
	def set_editor(self, editor):
		self.editor = editor

	def unset_editor(self, editor):
		if self.editor is editor:
			self.editor = None

	def SetFont(self, font, size = None):
		if size is not None:
			undo = self.properties.SetProperty(font = font, font_size = size)
		else:
			undo = self.properties.SetProperty(font = font)
		return self.properties_changed(undo)
	
	def SetGap(self, char, word, line):		
		undo = self.properties.SetProperty(chargap = char,
								wordgap = word,
								linegap = line)
		return self.properties_changed(undo)
	
	def SetAlign(self, align, valign):	
		if align == const.ALIGN_CENTER:
			valign=const.ALIGN_CENTER
		else:
			valign=const.ALIGN_BASE	
		undo = self.properties.SetProperty(align = align, valign = valign)		
		return self.properties_changed(undo)

	def SetFontSize(self, size):
		undo = self.properties.SetProperty(font_size = size)
		return self.properties_changed(undo)

	def Font(self):
		return self.properties.font

	def FontSize(self):
		return self.properties.font_size


class CommonTextEditor(Editor):

	EditedClass = CommonText
	commands = []

	def __init__(self, object):
		Editor.__init__(self, object)
		self.caret = 0
		object.set_editor(self)

	def Destroy(self):
		self.object.unset_editor(self)

	def ButtonDown(self, p, button, state):
		Editor.DragStart(self, p)

	def ButtonUp(self, p, button, state):
		Editor.DragStop(self, p)

	def update_selection(self):
		# a bit ugly...
		if self.document is not None:
			self.document.queue_selection()

	def SetCaret(self, caret):
		if caret > len(self.text):
			caret = len(self.text)
		self.caret = caret

	def Caret(self):
		return self.caret

	def InsertCharacter(self, event):
#		if len(char) == 1 and self.properties.font.IsPrintable(char):
		try:			
			char = event.char
			char=char.decode('utf-8')			
			text = self.text;	caret = self.caret
			text = text[:caret] + char + text[caret:]
			return self.SetText(text, caret + 1)
		except:
			return NullUndo
	#AddCmd(commands, InsertCharacter, '', key_stroke = tuple(printable), invoke_with_event = 1)
	
	def InsertEOL(self):
		try:	
			text = self.text;	caret = self.caret
			text = text[:caret] + '\n' + text[caret:]
			return self.SetText(text, caret + 1)
		except:
			return NullUndo
	#AddCmd(commands, InsertEOL, '', key_stroke = ('Return','KP_Enter'))

	def InsertTAB(self):
		try:	
			text = self.text;	caret = self.caret
			text = text[:caret] + '\t' + text[caret:]
			return self.SetText(text, caret + 1)
		except:
			return NullUndo
	#AddCmd(commands, InsertTAB, '', key_stroke = 'Tab')	
	
	def InsertTextFromClipboard(self):
		try:			
			insertion = app.root.tk.call('::tk::GetSelection','.','CLIPBOARD')
			insertion=insertion.decode('utf-8')		
			text = self.text;	caret = self.caret
			text = text[:caret] + insertion + text[caret:]
			return self.SetText(text, caret + len(insertion))
		except:
			return NullUndo
	#AddCmd(commands, InsertTextFromClipboard, '', key_stroke = ('Ctrl+v', 'Shift+Insert'))

	def DeleteCharBackward(self):
		if self.text and self.caret > 0:
			text = self.text; caret = self.caret
			text = text[:caret - 1] + text[caret:]
			return self.SetText(text, caret - 1)
		return NullUndo
	#AddCmd(commands, DeleteCharBackward, '', key_stroke = 'BackSpace')

	def DeleteCharForward(self):
		if self.text and self.caret < len(self.text):
			text = self.text; caret = self.caret
			text = text[:caret] + text[caret + 1:]
			return self.SetText(text, caret)
		return NullUndo
	#AddCmd(commands, DeleteCharForward, '', key_stroke = ('Delete', 'KP_Delete'))

	def MoveForwardChar(self):
		if self.caret < len(self.text):
			self.SetCaret(self.caret + 1)
			self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveForwardChar, '', key_stroke = ('Right', 'KP_Right'))

	def MoveBackwardChar(self):
		if self.caret > 0:
			self.SetCaret(self.caret - 1)
			self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveBackwardChar, '', key_stroke = ('Left', 'KP_Left'))

	def MoveToNextLine(self):
		lines=split(self.text, '\n')
		index, line_index = self.get_position()
		if line_index < len(lines)-1:
			if index>len(lines[line_index+1]):
				self.SetCaret(self.caret + len(lines[line_index+1])+len(lines[line_index])-index+2)
			else:
				self.SetCaret(self.caret + len(lines[line_index])+1)
			self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToNextLine, '', key_stroke = ('Down', 'KP_Down'))
	
	def MoveToPreviousLine(self):
		lines=split(self.text, '\n')
		index, line_index = self.get_position()
		if line_index > 0:
			if index>len(lines[line_index-1]):
				self.SetCaret(self.caret - index)
			else:
				self.SetCaret(self.caret - len(lines[line_index-1])-1)
			self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToPreviousLine, '', key_stroke = ('Up', 'KP_Up'))

	def MoveToBeginningOfLine(self):
		index, line_index = self.get_position()
		self.SetCaret(self.caret-index+1)
		self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToBeginningOfLine, '', key_stroke = ('Home', 'KP_Home'))
	
	def MoveToBeginningOfText(self):
		self.SetCaret(0)
		self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToBeginningOfText, '', key_stroke = ('Ctrl-Home', 'Ctrl-KP_Home'))

	def MoveToEndOfLine(self):
		lines=split(self.text, '\n')
		index, line_index = self.get_position()
		self.SetCaret(self.caret+len(lines[line_index])-index+1)
		self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToEndOfLine, '', key_stroke = ('End', 'KP_End'))
	
	def MoveToEndOfText(self):
		self.SetCaret(len(self.text))
		self.update_selection()
		return NullUndo
	#AddCmd(commands, MoveToEndOfText, '', key_stroke = ('Ctrl-End', 'Ctrl-KP_End'))
	
	def get_position(self):
		lines=split(self.text, '\n')
		caret=self.caret+1
		index=0
		line_index=0
		for line in lines:
			line+='\n'
			caret-=len(line)
			if caret<=0:
				index=len(line)+caret
				break
			line_index+=1
		return (index,line_index)
				
		


RegisterCommands(CommonTextEditor)


class SimpleText(CommonText, RectangularPrimitive):

	has_edit_mode	= 1
	is_Text		= 1
	is_SimpleText	= 1
	is_curve		= 1
	is_clip		= 1
	has_font		= 1
	has_fill		= 1
	has_line		= 0

	commands = CommonText.commands + RectangularPrimitive.commands

	_lazy_attrs = RectangularPrimitive._lazy_attrs.copy()
	_lazy_attrs['atrafo'] = 'update_atrafo'

	def __init__(self, trafo = None, text = '', halign = const.ALIGN_LEFT,
					valign = const.ALIGN_BASE, properties = None, duplicate = None):
		CommonText.__init__(self, text, duplicate)
		RectangularPrimitive.__init__(self, trafo, properties = properties,
										duplicate = duplicate)
		if duplicate != None:
			self.halign = duplicate.halign
			self.valign = duplicate.valign
			self.atrafo = duplicate.atrafo
		else:
			self.halign = halign
			self.valign = valign
			if properties is None:
				self.properties = PropertyStack(base=FactoryTextStyle())
			self.properties.align = self.halign
			self.properties.valign = self.valign
		self.cache = {}

	def Disconnect(self):
		self.cache = {}
		RectangularPrimitive.Disconnect(self)

	def Hit(self, p, rect, device, clip = 0):
		a = self.properties
		llx, lly, urx, ury = a.font.TextBoundingBox(self.text, a.font_size, a)
		trafo = self.trafo(self.atrafo)
		trafo = trafo(Trafo(urx - llx, 0, 0, ury - lly, llx, lly))
		return device.ParallelogramHit(p, trafo, 1, 1, 1,
										ignore_outline_mode = 1)

	def GetObjectHandle(self, multiple):
		trafo = self.trafo(self.atrafo(Scale(self.properties.font_size)))
		if multiple:
			return trafo(NullPoint)
		else:
			pts = self.properties.font.TypesetText(self.text,self.properties)
			return map(trafo, pts)

	def SetAlignment(self, horizontal, vertical):
		undo = (self.SetAlignment, self.halign, self.valign)
		if horizontal is not None:
			self.halign = horizontal
			self.properties.align = horizontal
		if vertical is not None:
			self.valign = vertical
			self.properties.valign = vertical
		self._changed()
		return undo
	
	#AddCmd(commands, 'AlignLeft', _("Align Left"), SetAlignment, args = (const.ALIGN_LEFT, None))
	#AddCmd(commands, 'AlignRight', _("Align Right"), SetAlignment, args =(const.ALIGN_RIGHT,None))
	#AddCmd(commands, 'AlignHCenter', _("Align H. Center"), SetAlignment, args = (const.ALIGN_CENTER, None))
	#AddCmd(commands, 'AlignTop', _("Align Top"), SetAlignment, args = (None, const.ALIGN_TOP))
	#AddCmd(commands, 'AlignVCenter', _("Align V. Center"), SetAlignment, args =(None, const.ALIGN_CENTER))
	#AddCmd(commands, 'AlignBase', _("Align Baseline"), SetAlignment, args = (None, const.ALIGN_BASE))
	#AddCmd(commands, 'AlignBottom', _("Align Bottom"), SetAlignment, args = (None, const.ALIGN_BOTTOM))

	def Alignment(self):
		return self.properties.align, self.properties.valign

	def RemoveTransformation(self):
		if self.trafo.matrix() != IdentityMatrix:
			a = self.properties
			trafo = self.trafo
			llx, lly, urx, ury = a.font.TextCoordBox(self.text, a.font_size, a)
			try:
				undostyle = Primitive.Transform(self, trafo.inverse())
			except SingularMatrix:
				undostyle = None
			undotrafo = self.set_transformation(Translation(trafo.offset()))
			return CreateMultiUndo(undostyle, undotrafo)
		return NullUndo

	def DrawShape(self, device, rect = None, clip = 0):
		RectangularPrimitive.DrawShape(self, device)
		base_trafo = self.trafo(self.atrafo)
		base_trafo = base_trafo(Scale(self.properties.font_size))
		paths = self.properties.font.GetPaths(self.text, self.properties)
		obj = PolyBezier(paths, self.properties.Duplicate())
		obj.Transform(base_trafo)
		device.MultiBezier(obj.paths, rect, clip)

	def update_atrafo(self):
#		a = self.properties
#		llx, lly, urx, ury = a.font.TextCoordBox(self.text, a.font_size, a)
#		hj = self.halign
#		if hj == ALIGN_RIGHT:
#			xoff = llx - urx
#		elif hj == ALIGN_CENTER:
#			xoff = (llx - urx) / 2
#		else:
#			xoff = 0
		xoff = 0
		yoff=0
#		vj = self.valign
#		if vj == ALIGN_TOP:
#			yoff = -ury
#		elif vj == ALIGN_CENTER:
#			yoff = (lly - ury) / 2 - lly
#		elif vj == ALIGN_BOTTOM:
#			yoff = -lly
#		else:
#			yoff = 0
		self.atrafo = Translation(xoff, yoff)

	def update_rects(self):
		trafo = self.trafo(self.atrafo)
		a = self.properties
		rect = apply(Rect, a.font.TextBoundingBox(self.text, a.font_size, a))
		self.bounding_rect = trafo(rect).grown(2)
		rect = apply(Rect, a.font.TextCoordBox(self.text, a.font_size, a))
		self.coord_rect = trafo(rect)

	def Info(self):
		text=self.text.replace('\n','')
		text=text.replace('\r','')
		text=text.replace('\t','')
		text=text.strip()
		if len(text)>25:
			text=text[:25]+'...'
		text=text.encode('utf-8')
		return (_("Text `%(text)s' at %(position)[position]"),
				{'text':text, 'position':self.trafo.offset()} )

	def FullTrafo(self):
		# XXX perhaps the Trafo method should return
		# self.trafo(self.atrafo) for a SimpleText object as well.
		return self.trafo(self.atrafo)

	def SaveToFile(self, file):
		RectangularPrimitive.SaveToFile(self, file)
		file.SimpleText(self.text, self.trafo, 
					self.properties.align, 
					self.properties.valign,
					self.properties.chargap,
					self.properties.wordgap,
					self.properties.linegap)

	def Blend(self, other, p, q):
		if self.__class__ != other.__class__ \
			or self.properties.font != other.properties.font \
			or self.text != other.text:
			raise MismatchError
		blended = self.__class__(BlendTrafo(self.trafo, other.trafo, p, q),
									self.text)
		self.set_blended_properties(blended, other, p, q)
		return blended

	def AsBezier(self):
		if self.text:
			text = split(self.text, '\n')[0]
			base_trafo = self.trafo(self.atrafo)
			base_trafo = base_trafo(Scale(self.properties.font_size))
			paths = self.properties.font.GetPaths(self.text, self.properties)
			obj = PolyBezier(paths, self.properties.Duplicate())
			obj.Transform(base_trafo)
			return obj

	def Paths(self):
#		paths = []
		if self.text:
			text = split(self.text, '\n')[0]
			base_trafo = self.trafo(self.atrafo)
			base_trafo = base_trafo(Scale(self.properties.font_size))
			paths = self.properties.font.GetPaths(self.text, self.properties)
			obj = PolyBezier(paths, self.properties.Duplicate())
			obj.Transform(base_trafo)
		return obj.paths 
							
#			base_trafo = self.trafo(self.atrafo)
#			base_trafo = base_trafo(Scale(self.properties.font_size))
#			pos = self.properties.font.TypesetText(self.text)
#			for i in range(len(self.text)):
#				outline = self.properties.font.GetOutline(self.text[i])
#				trafo = base_trafo(Translation(pos[i]))
#				for path in outline:
#					path.Transform(trafo)
#					paths.append(path)
#		return tuple(paths)            

	def Editor(self):
		return SimpleTextEditor(self)

	context_commands = ('AlignLeft', 'AlignRight', 'AlignHCenter', None,
						'AlignTop', 'AlignVCenter', 'AlignBase', 'AlignBottom')

RegisterCommands(SimpleText)


class SimpleTextCreator(Creator):

	is_Text = 1 # XXX: ugly
	creation_text = _("Create Text")

	def __init__(self, start):
		Creator.__init__(self, start)

	def ButtonDown(self, p, button, state):
		Creator.DragStart(self, p)

	def MouseMove(self, p, state):
		p = self.apply_constraint(p, state)
		Creator.MouseMove(self, p, state)
		
	def ButtonUp(self, p, button, state):
		p = self.apply_constraint(p, state)
		Creator.DragStop(self, p)

	def DrawDragged(self, device, partially):
		device.DrawLine(self.start, self.drag_cur)

	def apply_constraint(self, p, state):
		if state & const.ConstraintMask:
			r, phi = (p - self.start).polar()
			pi12 = pi / 12
			phi = pi12 * floor(phi / pi12 + 0.5)
			p = self.start + Polar(r, phi)
		return p

	def CreatedObject(self):
		trafo = Translation(self.start)
		r, phi = (self.drag_cur - self.start).polar()
		if r:
			trafo = trafo(Rotation(phi))
		return SimpleText(trafo = trafo, properties = DefaultTextProperties())

class SimpleTextEditor(CommonTextEditor):

	EditedClass = SimpleText
	commands = CommonTextEditor.commands[:]

	def GetHandles(self):
		a = self.properties
		pos, up = a.font.TextCaretData(self.text, self.caret, a.font_size, a)
		pos = self.trafo(self.atrafo(pos))
		up = self.trafo.DTransform(up)
		return [handle.MakeCaretHandle(pos, up)]

	def SelectPoint(self, p, rect, device, mode):
		trafo = self.trafo(self.atrafo(Scale(self.properties.font_size)))
		trafo = trafo.inverse()
		p2 = trafo(p)
		pts = self.properties.font.TypesetText(self.text + ' ',self.properties)
		dists = []
		for i in range(len(pts)):
			dists.append((abs(pts[i].x - p2.x), i))
		caret = min(dists)[-1]
		self.SetCaret(caret)
#		print "CATCHED!"
		return 1

	def Destroy(self):
		CommonTextEditor.Destroy(self)
		self.document.AddAfterHandler(maybe_remove_text, (self.object,))

RegisterCommands(SimpleTextEditor)


def maybe_remove_text(text):
	if text.parent is not None and not text.text:
		doc = text.document
		doc.DeselectObject(text)
		doc.AddUndo(text.parent.Remove(text))
		doc.selection.update_selinfo()
#
#
#

PATHTEXT_ROTATE = 1
PATHTEXT_SKEW = 2


def coord_sys_at(lengths, pos, type):
	if len(lengths) < 2:
		return None
	for idx in range(len(lengths)):
		if lengths[idx][0] > pos:
			d2, p2 = lengths[idx]
			d1, p1 = lengths[idx - 1]
			if d2 != d1 and p1 != p2:
				break
	else:
		return None
	t = (pos - d1) / (d2 - d1)
	p = (1 - t) * p1 + t * p2
	diff = (p2 - p1).normalized()
	del lengths[:idx - 1]
	if type == PATHTEXT_SKEW:
		return Trafo(diff.x, diff.y, 0, 1, p.x, p.y)
	else:
		return Trafo(diff.x, diff.y, -diff.y, diff.x, p.x, p.y)


def pathtext(path, start_pos, text, font, size, type, properties):
	metric = font.metric
	lengths = path.arc_lengths(start_pos)
	scale = Scale(size); factor = size / 2000.0
	pos = font.TypesetText(text, properties)
	pos = map(scale, pos)
	trafos = []
	for idx in range(len(text)):
		char = text[idx]
		width2 = metric.char_width(ord(char)) * factor
		x = pos[idx].x + width2
		trafo = coord_sys_at(lengths, x, type)
		if trafo is not None:
			trafos.append(trafo(Translation(-width2, 0)))
		else:
			# we've reached the end of the path. Ignore all following
			# characters
			break
	return trafos



class InternalPathText(CommonText, Primitive):

	has_edit_mode	= 1
	is_Text		= 1
	is_PathTextText	= 1
	is_curve		= 0
	is_clip		= 1
	has_font		= 1
	has_fill		= 1
	has_line		= 0


	_lazy_attrs = Primitive._lazy_attrs.copy()
	_lazy_attrs['trafos'] = 'update_trafos'
	_lazy_attrs['paths'] = 'update_paths'
	commands = CommonText.commands + Primitive.commands

	def __init__(self, text = '', trafo = None, model = PATHTEXT_ROTATE,
					start_pos = 0.0, properties = None, duplicate = None):
		CommonText.__init__(self, text, duplicate = duplicate)
		Primitive.__init__(self, properties = properties,
							duplicate = duplicate)
		if duplicate is not None and isinstance(duplicate, self.__class__):
			# dont copy paths, update it from parent
			self.trafo = duplicate.trafo
			self.model = duplicate.model
			self.start_pos = duplicate.start_pos
		else:
			if trafo is None:
				self.trafo = Identity
			else:
				self.trafo = trafo
			self.model = model
			self.start_pos = start_pos
		self.cache = {}


	def update_rects(self):
		a = self.properties
		length = len(self.trafos)
		sizes = [a.font_size] * length

		boxes = map(a.font.TextBoundingBox, self.text[:length], sizes, a)
		rects = map(lambda *a:a, map(apply, [Rect] * length, boxes))
		self.bounding_rect = reduce(UnionRects, map(apply, self.trafos, rects),
									EmptyRect)

		boxes = map(a.font.TextCoordBox, self.text[:length], sizes, a)
		rects = map(lambda *a:a, map(apply, [Rect] * length, boxes))
		self.coord_rect = reduce(UnionRects, map(apply, self.trafos, rects),
									EmptyRect)

	def update_trafos(self):
		self.trafos = map(self.trafo, pathtext(self.paths[0], self.start_pos,
												self.text, self.properties.font,
												self.properties.font_size,
												self.model,self.properties))
	def update_paths(self):
		paths = self.parent.get_paths()
		try:
			itrafo = self.trafo.inverse()
			transformed = []
			for path in paths:
				path = path.Duplicate()
				path.Transform(itrafo)
				transformed.append(path)
			paths = tuple(transformed)
		except SingularMatrix:
			# XXX what do we do?
			pass
		self.paths = paths

	def SetText(self, text, caret = None):
		self.cache = {}
		return CommonText.SetText(self, text, caret)

	def PathChanged(self):
		self.del_lazy_attrs()

	def SetModel(self, model):
		undo = (self.SetModel, self.model)
		self.model = model
		self._changed()
		return undo

	def Model(self):
		return self.model

	def SetStartPos(self, start_pos):
		undo = (self.SetStartPos, self.start_pos)
		self.start_pos = start_pos
		self._changed()
		return undo

	def StartPos(self):
		return self.start_pos

	def CharacterTransformations(self):
		return self.trafos

	def DrawShape(self, device, rect = None, clip = 0):
		text = self.text; trafos = self.trafos
		font = self.properties.font; font_size = self.properties.font_size

		Primitive.DrawShape(self, device)
		device.BeginComplexText(clip, self.cache)
		for idx in range(len(trafos)):
			char = text[idx]
			if char not in '\r\n': # avoid control chars
				device.DrawComplexText(text[idx], trafos[idx], font, font_size)
		device.EndComplexText()

	def Disconnect(self):
		self.cache = {}
		Primitive.Disconnect(self)

	def Hit(self, p, rect, device, clip = 0):
		bbox = self.properties.font.TextBoundingBox
		font_size = self.properties.font_size
		text = self.text; trafos = self.trafos

		for idx in range(len(trafos)):
			llx, lly, urx, ury = bbox(text[idx], font_size, self.properties)
			trafo = trafos[idx](Trafo(urx - llx, 0, 0, ury - lly, llx, lly))
			if device.ParallelogramHit(p, trafo, 1, 1, 1,
										ignore_outline_mode = 1):
				return 1
		return 0

	def Translate(self, offset):
		return NullUndo

	def Transform(self, trafo):
		return self.set_transformation(trafo(self.trafo))

	def set_transformation(self, trafo):
		undo = (self.set_transformation, self.trafo)
		self.trafo = trafo
		self._changed()
		return undo

	def RemoveTransformation(self):
		return self.set_transformation(Identity)

	def Blend(self, other, p, q):
		if self.__class__ != other.__class__ \
			or self.properties.font != other.properties.font \
			or self.text != other.text:
			raise MismatchError
		trafo = BlendTrafo(self.trafo, other.trafo, p, q)
		start_pos = p * self.start_pos + q * other.start_pos
		blended = self.__class__(self.text, trafo = trafo,
									start_pos = start_pos, model = self.model)
		self.set_blended_properties(blended, other, p, q)
		return blended

	def SaveToFile(self, file):
		Primitive.SaveToFile(self, file)
		file.InternalPathText(self.text, self.trafo, self.model,
								self.start_pos)

	def Info(self):
		return _("Text on Path: `%(text)s'") % {'text':self.text[:10]}

	def Editor(self):
		return InternalPathTextEditor(self)

class InternalPathTextEditor(CommonTextEditor):

	EditedClass = InternalPathText
	commands = CommonTextEditor.commands

	def GetHandles(self):
		a = self.properties
		if self.caret > 0 and self.trafos:
			# special case to deal with here: the characters that fall
			# off the end of the path are not visible. If the caret is
			# in this invisible area, display the caret after the last
			# visible character
			caret = 1
			index = min(self.caret, len(self.text), len(self.trafos)) - 1
			text = self.text[index]
			trafo = self.trafos[index]
		else:
			caret = 0
			if self.text and self.trafos:
				text = self.text[0]
				trafo = self.trafos[0]
			else:
				# XXX fix this
				self.start_point = self.paths[0].point_at(self.start_pos)
				return [handle.MakeNodeHandle(self.start_point, 1)]
		pos, up = a.font.TextCaretData(text, caret, a.font_size, a)
		pos = trafo(pos)
		up = trafo.DTransform(up)
		self.start_point = self.trafos[0].offset()
		return [handle.MakeCaretHandle(pos, up),
				handle.MakeNodeHandle(self.start_point, 1)]

	selection = None
	def SelectHandle(self, handle, mode = const.SelectSet):
		self.selection = handle

	def SelectPoint(self, p, rect, device, mode):
		if self.trafos:
			dists = []
			for i in range(len(self.trafos)):
				dists.append((abs(p - self.trafos[i].offset()), i))
				
			char = self.text[len(self.trafos) - 1]
			width = self.properties.font.metric.char_width(ord(char)) / 1000.0
			pos = self.trafos[-1](width * self.properties.font_size, 0)
			dists.append((abs(p - pos), len(self.trafos)))
			caret = min(dists)[-1]
			self.SetCaret(caret)

	def ButtonDown(self, p, button, state):
		self.cache = {}
		return p - self.start_point

	def nearest_start_pos(self, p):
		try:
			x, y = self.trafo.inverse()(p)
			t = self.paths[0].nearest_point(x, y)
		except SingularMatrix:
			# XXX
			t = 0.0
		return t

	def DrawDragged(self, device, partially):
		text = self.text; trafos = self.trafos
		font = self.properties.font; font_size = self.properties.font_size
		t = self.nearest_start_pos(self.drag_cur)
		trafos = map(self.trafo, pathtext(self.paths[0], t, text, font,
											font_size, self.model, self.properties))

		device.BeginComplexText(0, self.cache)
		for idx in range(len(trafos)):
			char = text[idx]
			if char not in '\n\r':
				device.DrawComplexText(char, trafos[idx], font, font_size)
		device.EndComplexText()
		device.ResetFontCache()

	def ButtonUp(self, p, button, state):
		CommonTextEditor.ButtonUp(self, p, button, state)
		return self.SetStartPos(self.nearest_start_pos(self.drag_cur))


RegisterCommands(InternalPathTextEditor)

class PathText(Compound):

	is_PathTextGroup = 1
	allow_traversal = 1

	commands = Compound.commands[:]

	def __init__(self, text = None, path = None, model = PATHTEXT_ROTATE,
					start_pos = 0.0, duplicate = None, _blended_text = None):
		if duplicate is not None:
			Compound.__init__(self, duplicate = duplicate)
			self.text = self.objects[0]
			self.path = self.objects[1]
		else:
			if _blended_text is not None:
				self.text = _blended_text
				self.path = path
				Compound.__init__(self, [self.text, self.path])
			elif text is not None:
				self.text = InternalPathText(text.Text(),
												start_pos = start_pos,
												model = model,
												duplicate = text)
				self.path = path
				Compound.__init__(self, [self.text, self.path])
			else:
				# we're being loaded
				self.text = self.path = None
				Compound.__init__(self)

	def ChildChanged(self, child):
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)
		Compound.ChildChanged(self, child)
		if child is self.path:
			self.text.PathChanged()
		if self.document is not None:
			self.document.AddClearRect(self.bounding_rect)

	def load_AppendObject(self, object):
		Compound.load_AppendObject(self, object)
		if len(self.objects) == 2:
			self.text, self.path = self.objects

	def SelectSubobject(self, p, rect, device, path = None, *rest):
		idx = self.Hit(p, rect, device) - 1
		obj = self.objects[idx]
		if path:
			path_idx = path[0]
			path = path[1:]
			if path_idx == idx:
				obj = obj.SelectSubobject(p, rect, device, path)
		elif path == ():
			obj = obj.SelectSubobject(p, rect, device)
		else:
			return  self
		return selinfo.prepend_idx(idx, obj)

	def ReplaceChild(self, child, object):
		if child is self.path and object.is_curve:
			undo = self.ReplaceChild, object, child
			self.path = self.objects[1] = object
			object.SetParent(self)
			object.SetDocument(self.document)
			child.SetParent(None)
			self.ChildChanged(object)
			#self._changed()
			return undo
		else:
			raise SketchError('Cannot replace child')

	def Info(self):
		return _("Path Text: `%(text)s'") % {'text':self.text.Text()[:10]}

	def SaveToFile(self, file):
		file.BeginPathText()
		self.text.SaveToFile(file)
		self.path.SaveToFile(file)
		file.EndPathText()

	def SelectTextObject(self):
		self.document.SelectObject(self.text)
	#AddCmd(commands, SelectTextObject, _("Select Text"), key_stroke = 't')

	def SelectPathObject(self):
		self.document.SelectObject(self.path)
	#AddCmd(commands, SelectPathObject, _("Select Path"), key_stroke = 'p')

	def get_paths(self):
		return self.path.Paths()

	def SetModel(self, model):
		return self.text.SetModel(model)
	#AddCmd(commands, 'SetModelRotate', _("Rotate Letters"), SetModel, args = PATHTEXT_ROTATE)
	#AddCmd(commands, 'SetModelSkew', _("Skew Letters"), SetModel, args = PATHTEXT_SKEW)

	def Model(self):
		return self.text.Model()

	def Blend(self, other, p, q):
		if self.__class__ != other.__class__:
			raise MismatchError
		return self.__class__(_blended_text = Blend(self.text,other.text, p,q),
								path = Blend(self.path, other.path, p, q))

	context_commands = ('SelectTextObject', 'SelectPathObject', None,
						'SetModelRotate', 'SetModelSkew')


RegisterCommands(PathText)

def CanCreatePathText(objects):
	if len(objects) == 2:
		if objects[0].is_Text:
			return objects[1].is_curve
		elif objects[0].is_curve:
			return objects[1].is_Text


def CreatePathText(objects):
	if len(objects) == 2:
		if objects[0].is_Text:
			text, curve = objects
		elif objects[1].is_Text:
			curve, text = objects
		if not curve.is_curve:
				# XXX what do we do here?
				return text
		return PathText(text, curve)


