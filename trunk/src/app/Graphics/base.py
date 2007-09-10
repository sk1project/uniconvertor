# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2001 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


#
# This file contains the root of the Sketch graphics class hierarchy.
#

from traceback import print_stack

from app.events.warn import warn, INTERNAL
from app.conf.const import CHANGED, SelectSet, Button1Mask, ConstraintMask, \
		SCRIPT_GET, SCRIPT_OBJECT, SCRIPT_UNDO
from app import NullUndo, CreateMultiUndo, Undo, UndoAfter

from app import Point, NullPoint, UnionRects, Identity, Translation, Trafo

from blend import Blend, MismatchError, BlendTrafo
from properties import PropertyStack
import properties


# Class Draggable
#
# This class maintains some instance variables for a click and drag
# operation on a graphics object.
#
# The scenario is this: The user has selected a graphics object, say a
# straight line between the points A and B, for editing. As a hint for
# the user where to click, the application shows two inverted rectangles
# at the endpoints. These rectangles are called handles. The user clicks
# on one of the handles, and, with the mouse button still pressed, drags
# the mouse to the new location of the selected endpoint. As feedback to
# the user, the application shows a `rubber-band' line during the drag
# to indicate what the line would look like if the user released the
# button.
#
# Two aspects of this operation are handled by the classes Draggable and
# EditSelect: Keeping track of the start point, the current point, the
# amount dragged, drawing the object during the drag and, in the case of
# Selectable, which parts of the object the user selected.
#
# Keeping track of where the drag started and how far in which direction
# the user has moved the mouse so far, is important, because, in the
# above example the endpoint should be moved not simply to the point the
# user dragged to, but by the amount the user dragged.
#
# To make this a little clearer: the handle is usually a few pixels
# wide, so the user may not click exactly on the pixel the endpoint lies
# on, but some pixels away. In that case, releasing the button without
# moving the mouse would still move the endpoint which is not what the
# user expected.
#
# Using only the offset of the drag is even more important when the
# entire object is being moved. In the above example, clicking on the
# middle of the line should select the entire line, i.e. both endpoints,
# for the drag. During the drag and at the end of the drag we can't move
# one or both endpoints to the current location of the mouse pointer, we
# have to move both endpoints by the same offset.
#
# To achieve this, an instance of Draggable has the following instance
# variables:
#
#	dragging	True, while being dragged
#	drag_start	start point
#	drag_cur	current point
#	off		offset by which the pointer was moved,
#			i.e. drag_cur - drag_start
#	drawn		true, if the object is visible on the screen in its
#			dragged form (see Hide() and Show())
#
# These variables only have meaningful values during the drag, that is,
# between the calls to DragStart() and DragStop(), see below.
# drag_start, drag_cur and off are of type Point. (See the developer's guide)


class Draggable:

	drawn	= 0
	dragging	= 0
	drag_start	= NullPoint
	drag_cur	= NullPoint
	off		= NullPoint

	drag_mask = Button1Mask # XXX move this to some other class ?


	def __init__(self):
		# not needed here, but if some derived class wants to call the
		# base class constructor...
		pass

	def DragStart(self, p):
		# Start the drag at P. Initialize the instance variables. Set
		# dragging to true.
		# XXX: document the meaning of the return value
		self.drawn = 0		# the object is not visible yet
		self.dragging = 1
		self.drag_start = p
		self.drag_cur = p
		self.off = NullPoint
		return self.off

	def DragMove(self, p):
		# The pointer has moved to p. Compute the new offset.
		self.off = p - self.drag_start
		self.drag_cur = p


	def MouseMove(self, p, state):
		# XXX add documentation for this
		if state & self.drag_mask:
			self.off = p - self.drag_start
			self.drag_cur = p

	def DragStop(self, p):
		# The drag stopped at p. Update drag_cur and off for the last
		# time, and set dragging to false.
		self.dragging = 0
		self.off = p - self.drag_start
		self.drag_cur = p

	def DragCancel(self):
		self.dragging = 0

	# The rest of Draggable's methods deal with drawing the object in
	# `dragged' form (usually an outline) on the screen. The output
	# device is assumed to be set up in such a way that drawing the same
	# object twice removes it again (usually using GCxor). Currently,
	# this will be an instance of InvertingDevice (graphics.py)
	#
	# Show() and Hide() use this assumption and the instance variable
	# drawn, to make certain that the object is visible or invisible,
	# respectively. If drawn is false Show() calls DrawDragged() to draw
	# the object and then sets drawn to true. This way Show() may be
	# called multiple times by the canvas widget if it thinks the
	# outline of the object should be visible, without removing the
	# outline accidentally.
	#
	# DrawDragged(), which obviously has to be implemented by some
	# derived class, has to draw the outline of the object on the output
	# device, using drag_cur or off to compute coordinates. The internal
	# state of the object, for example the endpoints of lines, should
	# only be changed temporarily during DrawDragged; the state of the
	# object should only change if the drag is completed successfully.
	#
	# The boolean parameter PARTIALLY indicates whether the object has
	# to be drawn completely or if it is sufficient to draw only the
	# parts that are changed by the drag. For instance, if a vertex of a
	# polygon is dragged, it might suffice to draw the two edges sharing
	# this vertex. It is safe to ignore this parameter and always draw
	# the whole object. It is especially useful for complex objects like
	# polygons or poly beziers, where it improves performance and
	# reduces flickering on the screen
	#
	# Implementation Note: Show and Hide are the methods normally used
	# by the canvas to show or hide the object while dragging. An
	# exception is the RedrawMethod of the canvas object where
	# DrawDragged is called directly.

	def DrawDragged(self, device, partially):
		pass

	def Show(self, device, partially = 0):
		if not self.drawn:
			self.DrawDragged(device, partially)
		self.drawn = 1

	def Hide(self, device, partially = 0):
		if self.drawn:
			self.DrawDragged(device, partially)
		self.drawn = 0

#
# Class Selectable
#
# This class defines the interface and default implementation for
# objects that can be selected by the user with a mouse click.
#

class Selectable:

	def __init__(self):
		# only needed for derived classes.
		pass

	def Hit(self, p, rect, device):
		return None

	def SelectSubobject(self, p, rect, device, path = None, *rest):
		return self

	def GetObjectHandle(self, multiple):
		# Return a single point marking an important point of the
		# object. This point is highlighted by a small rectangle in the
		# canvas to indicate that the object is selected. Alternatively,
		# a list of such points can be returned to mark several points,
		# but that feature should only be used by compound objects.
		#
		# If multiple is false, self is the only object selected. If
		# it's true, there may be more than one selected object.
		return []


class EditSelect(Selectable):

	def SelectPoint(self, p, rect, device, mode = SelectSet):
		# Select (sub)object at P. If something is selected, return
		# true, false otherwise.
		return 0

	def SelectHandle(self, handle, mode = SelectSet):
		pass

	def SelectRect(self, rect, mode = SelectSet):
		# select (sub-)object(s) in RECT
		pass

	def GetHandles(self):
		# In edit mode, this method will be called to get a list of
		# handles. A handle should be shown at every `hot' spot of the
		# object (e.g. the nodes of a PolyBezier). Handles are described
		# by tuples which can be easily created by the functions in
		# handle.py
		return []



class SelectAndDrag(Draggable, EditSelect):

	def __init__(self):
		Draggable.__init__(self)
		Selectable.__init__(self)

	def CurrentInfoText(self):
		# return a string describing the current state of the object
		# during a drag
		return ''


#
#	Class Protocols
#
#	Some boolean flags that describe the object's capabilities
#

class Protocols:

	is_GraphicsObject   = 0
	is_Primitive        = 0
	is_Editor           = 0
	is_Creator          = 0

	has_edit_mode = 0	# true if object has an edit mode. If true, the
						# Editor() method must be implemented

	is_curve = 0	# true, if object can be represented by and
						# converted to a PolyBezier object. If true, the
						# AsBezier() and Paths() methods must be
						# implemented
	is_clip = 0

	has_fill		= 0	# True, iff object can have fill properties
	has_line		= 0	# True, iff object can have line properties
	has_font		= 0	# True, iff object can have a font
	has_properties	= 0

	is_Bezier	= 0
	is_Rectangle	= 0
	is_Ellipse	= 0
	is_Text		= 0	# Text objects must have a Font() method
								# returning a font.
	is_SimpleText       = 0
	is_PathTextGroup    = 0 
	is_PathTextText     = 0     # The text part of a path text group
	is_Image	    = 0
	is_Eps		    = 0

	is_Group		= 0
	is_Compound		= 0
	is_Layer		= 0

	is_Blend		= 0     # The blendgroup
	is_BlendInterpolation   = 0     # The interpolation child of a blend group
	is_Clone		= 0
	is_MaskGroup            = 0
	is_GuideLine	        = 0

	is_Plugin		= 0


#
# Class Bounded
#
# Instances of this class have various kinds of bounding rectangles
# These rectangles are accessible via instance variables to increase
# performance (important for bounding_rect, which is used when testing
# which object is selected by a click). All rectangles are given in
# document coords and are aligned with the axes. The variables are:
#
# coord_rect
#
#	The smallest rectangle that contains all points of the outline.
#	The line width, if applicable, is NOT taken into account here.
#	This rectangle is used to arrange objects (AlignSelected,
#	AbutHorizonal, ...)
#
# bounding_rect
#
#	Like coord rect but takes the line width into account. It is
#	meant to be useful as a PostScript BoundingBox.
#
# Method:
#
# LayoutPoint()
#
#	Return the point which should be snapped to a grid point.
#


class Bounded:

	_lazy_attrs = {'coord_rect' : 'update_rects',
					'bounding_rect' : 'update_rects'}

	def __init__(self):
		pass

	def del_lazy_attrs(self):
		for key in self._lazy_attrs.keys():
			try:
				delattr(self, key)
			except:
				pass

	def update_rects(self):
		# compute the various bounding rects and other attributes that
		# use `lazy evaluation'. This method MUST be implemented by
		# derived classes. It MUST set self.bounding_rect and
		# self.coord_rect and other attributes where appropriate.
		pass

	def __getattr__(self, attr):
		# if a lazy attribute is accessed, compute it.
		method = self._lazy_attrs.get(attr)
		if method:
			getattr(self, method)()
			# now it should work... use self.__dict__ directly to avoid
			# recursion if the method is buggy
			try:
				return self.__dict__[attr]
			except KeyError, msg:
				warn(INTERNAL, '%s did not compute %s for %s.', method, attr, self)
		if attr[:2] == attr[-2:] == '__':
			#if attr in ('__nonzero__', '__len__'):
			#	 print_stack()
			pass
		else:
			warn(INTERNAL, "%s instance doesn't have an attribute %s", self.__class__, attr)
		raise AttributeError, attr

	def LayoutPoint(self):
		return Point(self.coord_rect.left, self.coord_rect.bottom)

	def GetSnapPoints(self):
		return []

#
# Class HierarchyNode
#
# This is base class for all objects that are part of the object
# hierarchy of a document. It manages the parent child relationship and
# the references to the document and other methods (and standard
# behavior) that every object needs. No object derived from this class
# should override the methods defined here except as documented.
#

class HierarchyNode:

	def __init__(self, duplicate = None):
		if duplicate is not None:
			self.document = duplicate.document
			if duplicate.was_untied:
				self.was_untied = duplicate.was_untied

	def __del__(self):
		if self.document:
			self.document.connector.RemovePublisher(self)

	def Destroy(self):
		# remove all circular references here...
		# May be extended by derived classes.
		self.parent = None

	parent = None
	def SetParent(self, parent):
		self.parent = parent

	def depth(self):
		if self.parent is not None:
			return self.parent.depth() + 1
		return 1

	def SelectionInfo(self):
		if self.parent is not None:
			return self.parent.SelectionInfo(self)

	document = None	# the document self belongs to

	def SetDocument(self, doc):
		self.document = doc
		if doc is not None and self.was_untied:
			self.TieToDocument()
			del self.was_untied

	def UntieFromDocument(self):
		# this will be called when self is being stored in the clipboard
		# (CopyForClipboard/CutForClipboard), but before self.document
		# becomes None. Disconnect will not be called in this case.
		# May be extended by derived classes.
		self.was_untied = 1

	def TieToDocument(self):
		# this will be called when self is being inserted into the
		# document from the clipboard, after self.document has been set.
		# Connect will not be called in this case.
		# May be extended by derived classes.
		pass

	def Subscribe(self, channel, func, *args):
		# XXX: what do we do if document has not been set (yet)
		if self.document is not None:
			self.document.connector.Connect(self, channel, func, args)

	def Unsubscribe(self, channel, func, *args):
		if self.document is not None:
			self.document.connector.Disconnect(self, channel, func, args)

	def Issue(self, channel, *args):
		if self.document is not None:
			apply(self.document.connector.Issue, (self, channel,) + args)

	def issue_changed(self):
		self.Issue(CHANGED, self)
		if self.parent is not None:
			self.parent.ChildChanged(self)

	def Connect(self):
		# May be extended by derived classes.
		pass

	def Disconnect(self):
		# May be extended by derived classes.
		pass

	def Duplicate(self):
		# return a duplicate of self
		return self.__class__(duplicate = self)



#
# Class	GraphicsObject
#
# The base class for all `normal' objects that are part of the drawing
# itself, like rectangles or groups (the experimental clone objects are
# derived from HierarchyNode (Sep98))
#

class GraphicsObject(Bounded, HierarchyNode, Selectable, Protocols):

	is_GraphicsObject = 1

	keymap = None
	commands = []
	context_commands = ()
	was_untied = 0

	script_access = {}

	def __init__(self, duplicate = None):
		Selectable.__init__(self)
		HierarchyNode.__init__(self, duplicate = duplicate)

	def ChildChanged(self, child):
		# in compound objects, this method is called by the child
		# whenever it changes (normally via the issue_changed method)
		pass

	def __cmp__(self, other):
		return cmp(id(self), id(other))

	def _changed(self):
		self.del_lazy_attrs()
		self.issue_changed()
		return (self._changed,)

	def SetLowerLeftCorner(self, corner):
		# move self so that self's lower left corner is at CORNER. This
		# used when interactively placing an object
		rect = self.coord_rect
		ll = Point(rect.left, rect.bottom)
		return self.Translate(corner - ll)

	def RemoveTransformation(self):
		# Some objects accumulate the transformation applied by
		# Transform() and apply them every time the object is displayed
		# Restore this transformation to Identity.
		return NullUndo
	script_access['RemoveTransformation'] = SCRIPT_UNDO

	def AsBezier(self):
		# Return self as bezier if possible. See is_curve above.
		return None
	script_access['AsBezier'] = SCRIPT_OBJECT

	def Paths(self):
		# Return a tuple of curve objects describing the outline of self
		# if possible. The curve objects can be the ones used internally
		# by self. The calling code is expected not to modify the curve
		# objects in place.
		# See is_curve above.
		return None
	script_access['Paths'] = SCRIPT_GET

	def Blend(self, other, frac1, frac2):
		# Return the weighted average of SELF and OTHER. FRAC1 and FRAC2
		# are the weights (if SELF and OTHER were numbers this should be
		# FRAC1 * SELF + FRAC2 * OTHER).
		#
		# This method is used by the function Blend() in blend.py. If
		# SELF and OTHER can't be blended, raise the blend.MismatchError
		# exception. This is also the default behaviour.
		raise MismatchError
	script_access['Blend'] = SCRIPT_OBJECT

	def Snap(self, p):
		# Determine the point Q on self's outline closest to P and
		# return a tuple (abs(Q - P), Q)
		return (1e100, p)
	script_access['Snap'] = SCRIPT_GET

	def ObjectChanged(self, obj):
		return 0

	def ObjectRemoved(self, obj):
		return NullUndo

	# Add some inherited method's script access flags
	script_access['coord_rect'] = SCRIPT_GET
	script_access['bounding_rect'] = SCRIPT_GET
	script_access['LayoutPoint'] = SCRIPT_GET
	script_access['Duplicate'] = SCRIPT_OBJECT

	# and flags for standard methods
	script_access['Transform'] = SCRIPT_UNDO
	script_access['Translate'] = SCRIPT_UNDO

#
#
#

class Creator(SelectAndDrag, Protocols):

	is_Creator = 1
	creation_text = 'Create Object'

	def __init__(self, start):
		self.start = start

	def EndCreation(self):
		# This method will be called when the object was being created
		# interactively using more than one click-drag-release cycle,
		# and the user has finished. This method is needed by the
		# PolyBezier primitive for instance.
		#
		# Return true if creation was successful, false otherwise.
		return 1

	def ContinueCreation(self):
		# called during interactive creation when the user releases the
		# mouse button. Return true, if the object may need another
		# click-drag-release cycle, false for objects that are always
		# complete after one cycle. (XXX the `true' return value is
		# interpreted in a special way, see the PolyBezier primitive)
		#
		# XXX: Should we distinguish more cases? A rectangle for example
		# is always complete after one click-drag-release cycle. A
		# PolyBezier object needs at least two cycles but accepts any
		# number of additional cycles. A polygon (with straight lines)
		# needs at least one. We might return a value that indicates
		# whether the user *must* supply additional points, whether it's
		# optional or whether the object is complete and the user
		# *cannot* add points.
		return None

class Editor(SelectAndDrag):

	is_Editor = 1

	EditedClass = GraphicsObject
	context_commands = ()

	def __init__(self, object):
		self.object = object

	def __getattr__(self, attr):
		return getattr(self.object, attr)

	def Destroy(self):
		# called by the edit mode selection when the editor it not
		# needed anymore.
		pass

	def ChangeRect(self):
		# ChangeRect indicates the area that is going to change during
		# the current click-drag-release cycle. It is safe to make this
		# equal to bounding_rect. This rectangle is used to determine
		# which parts of the window have to be redrawn.
		return self.bounding_rect


#
# Class Primitive
#
# The baseclass for all graphics primitives like Polygon, Rectangle, ...
# but not for composite objects. Basically, this adds the management of
# properties and styles to GraphicsObject


class Primitive(GraphicsObject):

	has_fill	= 1
	has_line	= 1
	has_properties = 1
	is_Primitive = 1

	tie_info = None
	script_access = GraphicsObject.script_access.copy()

	def __init__(self, properties = None, duplicate = None):
		GraphicsObject.__init__(self, duplicate = duplicate)
		if duplicate is not None:
			self.properties = duplicate.properties.Duplicate()
			if duplicate.tie_info:
				self.tie_info = duplicate.tie_info
		else:
			if properties is not None:
				self.properties = properties
			else:
				self.properties = PropertyStack()

	def Destroy(self):
		GraphicsObject.Destroy(self)

	def UntieFromDocument(self):
		info = self.properties.Untie()
		if info:
			self.tie_info = info
		GraphicsObject.UntieFromDocument(self)

	def TieToDocument(self):
		if self.tie_info:
			self.properties.Tie(self.document, self.tie_info)
			del self.tie_info

	def Transform(self, trafo, rects = None):
		# Apply the affine transformation trafo to all coordinates and
		# the properties.
		undo = self.properties.Transform(trafo, rects)
		if undo is not NullUndo:
			return self.properties_changed(undo)
		return undo

	def Translate(self, offset):
		# Move all points by OFFSET. OFFSET is an SKPoint instance.
		return NullUndo

	def DrawShape(self, device):
		# Draw the object on device. Here we just set the properties.
		device.SetProperties(self.properties, self.bounding_rect)

	# The following functions manage the properties

	def set_property_stack(self, properties):
		self.properties = properties
	load_SetProperties = set_property_stack

	def properties_changed(self, undo):
		if undo is not NullUndo:
			return (UndoAfter, undo, self._changed())
		return undo

	def AddStyle(self, style):
		return self.properties_changed(self.properties.AddStyle(style))
	script_access['AddStyle'] = SCRIPT_UNDO

	def Filled(self):
		return self.properties.HasFill()
	script_access['Filled'] = SCRIPT_GET

	def Properties(self):
		return self.properties
	script_access['Properties'] = SCRIPT_OBJECT

	def SetProperties(self, if_type_present = 0, **kw):
		if if_type_present:
			# change properties of that type if properties of that are
			# already present.
			prop_types = properties.property_types
			LineProperty = properties.LineProperty
			FillProperty = properties.FillProperty
			FontProperty = properties.FontProperty
			types = map(prop_types.get, kw.keys())
			if LineProperty in types and not self.properties.HasLine():
				for key in kw.keys():
					if prop_types[key] == LineProperty:
						del kw[key]
			if FillProperty in types and not self.properties.HasFill():
				for key in kw.keys():
					if prop_types[key] == FillProperty:
						del kw[key]
			if FontProperty in types and not self.properties.HasFont():
				for key in kw.keys():
					if prop_types[key] == FontProperty:
						del kw[key]
		return self.properties_changed(apply(self.properties.SetProperty, (),
												kw))
	script_access['SetProperties'] = SCRIPT_UNDO

	def LineWidth(self):
		if self.properties.HasLine:
			return self.properties.line_width
		return 0
	script_access['LineWidth'] = SCRIPT_GET

	def ObjectChanged(self, obj):
		if self.properties.ObjectChanged(obj):
			rect = self.bounding_rect
			self.del_lazy_attrs()
			self.document.AddClearRect(UnionRects(rect, self.bounding_rect))
			self.issue_changed()
			return 1
		return 0

	def ObjectRemoved(self, obj):
		return self.properties.ObjectRemoved(obj)


	def set_blended_properties(self, blended, other, frac1, frac2):
		blended.set_property_stack(Blend(self.properties, other.properties, frac1, frac2))


	def SaveToFile(self, file):
		# save object to file. Must be extended by the subclasses. Here,
		# we just save the properties.
		self.properties.SaveToFile(file)


#
# Class RectangularObject
#
# A mix-in class for graphics objects that are more or less rectangular
# and store their position and orientation in a SKTrafoObject.

class RectangularObject:

	def __init__(self, trafo = None, duplicate = None):
		if duplicate is not None:
			self.trafo = duplicate.trafo
		else:
			if not trafo:
				self.trafo = Identity
			else:
				self.trafo = trafo

	def Trafo(self):
		return self.trafo

	def LayoutPoint(self, *rest):
		# accept arguments to use this function as GetObjectHandle
		return self.trafo.offset()

	GetObjectHandle = LayoutPoint

	def Translate(self, offset):
		return self.Transform(Translation(offset))

	def set_transformation(self, trafo):
		undo = (self.set_transformation, self.trafo)
		self.trafo = trafo
		self._changed()
		return undo

	def Transform(self, trafo):
		trafo = trafo(self.trafo)
		return self.set_transformation(trafo)

	def Blend(self, other, p, q):
		if other.__class__ == self.__class__:
			blended = self.__class__(BlendTrafo(self.trafo, other.trafo, p, q))
			self.set_blended_properties(blended, other, p, q)
			return blended
		raise MismatchError


class RectangularPrimitive(RectangularObject, Primitive):

	def __init__(self, trafo = None, properties = None, duplicate = None):
		RectangularObject.__init__(self, trafo, duplicate = duplicate)
		Primitive.__init__(self, properties = properties,
							duplicate = duplicate)

	def Transform(self, trafo, transform_properties = 1):
		undostyle = undo = NullUndo
		try:
			rect = self.bounding_rect
			undo = RectangularObject.Transform(self, trafo)
			if transform_properties:
				rects = (rect, self.bounding_rect)
				undostyle = Primitive.Transform(self, trafo, rects = rects)
			return CreateMultiUndo(undostyle, undo)
		except:
			Undo(undo)
			Undo(undostyle)
			raise

	def Translate(self, offset):
		return self.Transform(Translation(offset), transform_properties = 0)


class RectangularCreator(Creator):

	def __init__(self, start):
		Creator.__init__(self, start)
		self.trafo = Trafo(1, 0, 0, 1, start.x, start.y)

	def ButtonDown(self, p, button, state):
		Creator.DragStart(self, p)

	def apply_constraint(self, p, state):
		if state & ConstraintMask:
			trafo = self.trafo
			w, h = p - self.drag_start
			if w == 0:
				w = 0.00001
			a = h / w
			if a > 0:
				sign = 1
			else:
				sign = -1
			if abs(a) > 1.0:
				h = sign * w
			else:
				w = sign * h
			p = self.drag_start + Point(w, h)
		return p

	def MouseMove(self, p, state):
		p = self.apply_constraint(p, state)
		Creator.MouseMove(self, p, state)

	def ButtonUp(self, p, button, state):
		p = self.apply_constraint(p, state)
		Creator.DragStop(self, p)
		x, y = self.off
		self.trafo = Trafo(x, 0, 0, y, self.trafo.v1, self.trafo.v2)
