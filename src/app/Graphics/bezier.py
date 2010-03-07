# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2000, 2002 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

from math import pi, floor, atan2, ceil

from traceback import print_stack

from app.conf.const import SelectSet, SelectAdd, SelectSubtract, SelectDrag, \
		Button1Mask, ConstraintMask,\
		SCRIPT_GET, SCRIPT_OBJECT, SCRIPT_OBJECTLIST, SCRIPT_UNDO
from app.events.warn import pdebug, warn, INTERNAL
from app import Point, Polar, Rect, EmptyRect, UnionRects, PointsToRect
from app import _, _sketch, CreatePath, config, RegisterCommands, \
		CreateMultiUndo, NullUndo, Undo

#from app.UI.command import AddCmd

from app._sketch import ContAngle, ContSmooth, ContSymmetrical, \
		SelNone, SelNodes, SelSegmentFirst, SelSegmentLast, Bezier, Line

import handle
from base import Primitive, Creator, Editor
from blend import Blend, BlendPaths, MismatchError
from properties import DefaultGraphicsProperties

#
# PolyBezier
#
# The most important primitive, since it can be used to draw lines,
# curves and arbitrary contours (to some degree; circles for instance
# can only be approximated, but that works quite well).
#

def undo_path(undo, path):
	if undo is not None:
		return apply(getattr(path, undo[0]), undo[1:])
	else:
		return undo

class PolyBezier(Primitive):

	is_Bezier	  = 1
	has_edit_mode = 1
	is_curve	  = 1
	is_clip	  = 1

	script_access = Primitive.script_access.copy()

	def __init__(self, paths = None, properties = None, duplicate = None):
		if duplicate is not None:
			if paths is None:
				paths = []
				for path in duplicate.paths:
					paths.append(path.Duplicate())
				self.paths = tuple(paths)
			else:
				# This special case uses the properties kwarg now, I
				# hope.
				warn(INTERNAL, 'Bezier object created with paths and duplicte')
				print_stack()
				if type(paths) != type(()):
					paths = (paths,)
				self.paths = paths
		elif paths is not None:
			if type(paths) != type(()):
				paths = (paths,)
			self.paths = paths
		else:
			self.paths = (CreatePath(),)

		Primitive.__init__(self, properties = properties, duplicate=duplicate)

	def Hit(self, p, rect, device, clip = 0):
		for path in self.paths:
			if path.hit_point(rect):
				return 1
		return device.MultiBezierHit(self.paths, p, self.properties, clip or self.Filled(), ignore_outline_mode = clip)

	def do_undo(self, undo_list):
		undo = map(undo_path, undo_list, self.paths)
		self._changed()
		return (self.do_undo, undo)

	def Transform(self, trafo):
		undo = []
		undostyle = NullUndo
		try:
			rect = self.bounding_rect
			for path in self.paths:
				undo.append(path.Transform(trafo))
			self._changed()
			undo = (self.do_undo, undo)
			self.update_rects() # calling update_rects directly is a bit faster
			undostyle = Primitive.Transform(self, trafo, rects = (rect, self.bounding_rect))
			return CreateMultiUndo(undostyle, undo)
		except:
			Undo(undostyle)
			if type(undo) != type(()):
				undo = (self.do_undo, undo)
			Undo(undo)
			raise

	def Translate(self, offset):
		for path in self.paths:
			path.Translate(offset)
		self._changed()
		return self.Translate, -offset

	def DrawShape(self, device, rect = None, clip = 0):
		Primitive.DrawShape(self, device)
		device.MultiBezier(self.paths, rect, clip)

	def GetObjectHandle(self, multiple):
		if self.paths:
			return self.paths[0].Node(0)
		return Point(0, 0)

	def GetSnapPoints(self):
		points = []
		for path in self.paths:
			points = points + path.NodeList()
		return points

	def Snap(self, p):
		found = [(1e100, p)]
		for path in self.paths:
			t = path.nearest_point(p.x, p.y)
			if t is not None:
				#print p, t
				p2 = path.point_at(t)
				found.append((abs(p - p2), p2))
		return min(found)

	def update_rects(self):
		if not self.paths:
			# this should never happen...
			self.coord_rect = self.bounding_rect = Rect(0, 0, 0, 0)
			return

		rect = self.paths[0].accurate_rect()
		for path in self.paths[1:]:
			rect = UnionRects(rect, path.accurate_rect())
		self.coord_rect = rect
		if self.properties.HasLine():
			rect = self.add_arrow_rects(rect)
			self.bounding_rect = rect.grown(self.properties.GrowAmount())
		else:
			self.bounding_rect = rect

	def add_arrow_rects(self, rect):
		if self.properties.HasLine():
			arrow1 = self.properties.line_arrow1
			arrow2 = self.properties.line_arrow2
			if arrow1 or arrow2:
				width = self.properties.line_width
				for path in self.paths:
					if not path.closed and path.len > 1:
						if arrow1 is not None:
							type, controls, p3, cont = path.Segment(1)
							p = path.Node(0)
							if type == Bezier:
								dir = p - controls[0]
							else:
								dir = p - p3
							rect = UnionRects(rect, arrow1.BoundingRect(p,dir,width))
						if arrow2 is not None:
							type, controls, p, cont = path.Segment(-1)
							if type == Bezier:
								dir = p - controls[1]
							else:
								dir = p - path.Node(-2)
							rect = UnionRects(rect, arrow2.BoundingRect(p,dir,width))
		return rect

	def Info(self):
		nodes = 0
		for path in self.paths:
			nodes = nodes + path.len
			if path.closed:
				nodes = nodes - 1
		return _("PolyBezier (%(nodes)d nodes in %(paths)d paths)") \
				% {'nodes':nodes, 'paths':len(self.paths)}

	def set_paths(self, paths):
		undo = (self.set_paths, self.paths)
		self.paths = tuple(paths)
		self._changed()
		return undo

	SetPaths = set_paths
	def Paths(self):
		return self.paths

	def PathsAsObjects(self):
		result = []
		for path in self.paths:
			object = self.__class__(paths = (path.Duplicate(),), properties = self.properties.Duplicate())
			result.append(object)
		return result
	script_access['PathsAsObjects'] = SCRIPT_OBJECTLIST

	def AsBezier(self):
		# is `return self' enough ?
		return self.Duplicate()

	#
	#
	#

	def SaveToFile(self, file):
		Primitive.SaveToFile(self, file)
		file.PolyBezier(self.paths)

	def load_straight(self, *args):
		apply(self.paths[-1].AppendLine, args)

	def load_curve(self, *args):
		apply(self.paths[-1].AppendBezier, args)

	def load_close(self, copy_cont_from_last = 0):
		self.paths[-1].load_close(copy_cont_from_last)

	def guess_continuity(self):
		for path in self.paths:
			path.guess_continuity()

	def load_IsComplete(self):
		if self.paths[0].len < 2:
			# we need at least two nodes
			return 0
		return 1

	def Blend(self, other, frac1, frac2):
		if self.__class__ != other.__class__:
			try:
				other = other.AsBezier()
				if not other:
					raise MismatchError
			except AttributeError, value:
				if value == 'AsBezier':
					raise MismatchError
				else:
					raise

		paths = BlendPaths(self.paths, other.paths, frac1, frac2)
		blended = PolyBezier(paths = paths)
		self.set_blended_properties(blended, other, frac1, frac2)
		return blended

	def Editor(self):
		return PolyBezierEditor(self)



class PolyBezierCreator(Creator):

	creation_text = _("Create Curve")

	def __init__(self, start):
		self.path = CreatePath()
		Creator.__init__(self, start)

	def apply_constraints(self, p, state):
		if self.path.len > 0:
			node = self.path.Node(-1)
		elif self.dragging:
			node = self.drag_start
		else:
			return p
		
		if state & ConstraintMask:
			radius, angle = (p - node).polar()
			pi12 = pi / 12
			angle = pi12 * floor(angle / pi12 + 0.5)
			p = node + Polar(radius, angle)
		return p

	def ButtonDown(self, p, button, state):
		p = self.apply_constraints(p, state)
		if self.path.len == 0:
			self.path.AppendLine(p)
		else:
			self.path.AppendBezier(self.drag_cur, p, p)
		return self.DragStart(p)

	def MouseMove(self, p, state):
		if not (state & Button1Mask):
			return
		self.DragMove(self.apply_constraints(p, state))

	def ButtonUp(self, p, button, state):
		if not (state & Button1Mask):
			return
		p = self.apply_constraints(p, state)
		self.DragStop(p)
		if self.path.len > 1:
			type, (p1, p2), p, cont = self.path.Segment(-1)
			p2 = adjust_control_point(p2, p, self.drag_cur, ContSymmetrical)
			self.path.SetBezier(-1, p1, p2, p, ContSymmetrical)

	def EndCreation(self):
		return self.path.len > 1

	def AppendInteractive(self, p):
		return self

	def ContinueCreation(self):
		return self.AppendInteractive

	def DrawDragged(self, device, partially):
		if not partially:
			self.path.draw_not_last(device.Bezier, device.Line)
		device.DrawHandleLine(self.path.Node(-1), self.drag_cur)
		device.DrawSmallRectHandle(self.drag_cur)
		if self.path.len > 1:
			type, (p1, p2), p, cont = self.path.Segment(-1)
			p2 = adjust_control_point(p2, p, self.drag_cur, ContSymmetrical)
			device.Bezier(self.path.Node(-2), p1, p2, p)
			device.DrawHandleLine(p, p2)
			device.DrawSmallRectHandle(p2)

	def CreatedObject(self):
		return PolyBezier(paths = (self.path,), properties = DefaultGraphicsProperties())



class PolyLineCreator(Creator):

	creation_text = _("Create Poly-Line")

	def __init__(self, start):
		self.path = CreatePath()
		self.was_dragged = 0
		Creator.__init__(self, start)

	def apply_constraints(self, p, state):
		if self.path.len > 0:
			node = self.path.Node(-1)
		elif self.dragging:
			node = self.drag_start
		else:
			return p
		
		if state & ConstraintMask:
			radius, angle = (p - node).polar()
			pi12 = pi / 12
			angle = pi12 * floor(angle / pi12 + 0.5)
			p = node + Polar(radius, angle)
		return p

	def ButtonDown(self, p, button, state):
		return self.DragStart(self.apply_constraints(p, state))

	def MouseMove(self, p, state):
		if not (state & Button1Mask):
			return
		self.was_dragged = 1
		self.DragMove(self.apply_constraints(p, state))

	def ButtonUp(self, p, button, state):
		if not (state & Button1Mask):
			return
		self.DragStop(self.apply_constraints(p, state))
		if self.was_dragged and self.path.len == 0:
			self.path.AppendLine(self.drag_start)
		self.path.AppendLine(self.drag_cur)

	def EndCreation(self):
		return self.path.len > 1

	def AppendInteractive(self, p):
		return self

	def ContinueCreation(self):
		return self.AppendInteractive

	def DrawDragged(self, device, partially):
		if self.path.len > 1:
			if not partially:
				device.DrawBezierPath(self.path)
		if self.path.len >= 1:
			device.Line(self.path.Node(-1), self.drag_cur)
		else:
			if self.was_dragged:
				device.Line(self.drag_start, self.drag_cur)

	def CreatedObject(self):
		return PolyBezier(paths = (self.path,), properties = DefaultGraphicsProperties())

SelCurvePoint = -1

class PolyBezierEditor(Editor):

	EditedClass = PolyBezier
	commands = []

	def __init__(self, object):
		self.selected_path = -1
		self.selected_idx = -1
		self.selection_type = SelNone
		self.other_segment = -1
		Editor.__init__(self, object)
		self.Deselect()

	def SelectPoint(self, p, rect, device, mode):
		self.deselect()
		found = []
		for i in range(len(self.paths)):
			path = self.paths[i]
			t = path.nearest_point(p.x, p.y)
			if t is not None:
				p2 = path.point_at(t)
				found.append((abs(p - p2), i, t, p2))
		dist, i, t, p2 = min(found)
		self.selected_path = i
		self.selected_idx = t
		self.selection_type = SelCurvePoint
		return 1

	def SelectHandle(self, handle, mode = SelectSet):
		path_idx, segment = handle.code
		if segment < 0:
			segment = -segment
			if segment % 2:
				self.selection_type = SelSegmentFirst
			else:
				self.selection_type = SelSegmentLast
			self.selected_idx = (segment + 1) / 2
			segment = segment / 2
		else:
			self.selection_type = SelNodes
			self.selected_idx = segment
		self.selected_path = path_idx
		path = self.paths[path_idx]
		if mode == SelectSet or mode == SelectDrag:
			if not path.SegmentSelected(segment):
				self.deselect()
			path.SelectSegment(segment)
		elif mode == SelectAdd:
			path.SelectSegment(segment)
		elif mode == SelectSubtract:
			path.SelectSegment(segment, 0)

	def SelectRect(self, rect, mode = SelectSet):
		selected = 0
		for path in self.paths:
			selected = path.select_rect(rect, mode) or selected
		self.selection_type = SelNodes
		return selected

	def SelectAllNodes(self):
		for path in self.paths:
			for i in range(path.len):
				path.SelectSegment(i, 1)
	#AddCmd(commands, SelectAllNodes, _("Select All Nodes"))

	def deselect(self):
		for path in self.paths:
			path.deselect()

	def Deselect(self):
		self.deselect()
		self.selected_path = -1
		self.selected_idx = -1
		self.selection_type = SelNone

	def ButtonDown(self, p, button, state):
		if self.selected_path >= 0:
			path = self.paths[self.selected_path]
			if self.selection_type == SelNodes:
				start = path.Node(self.selected_idx)
				self.DragStart(start)
				return p - start
			elif self.selection_type == SelSegmentFirst:
				segment = self.selected_idx
				if segment > 1 \
					and path.SegmentType(segment - 1) == Bezier\
					and path.Continuity(segment - 1):
					self.other_segment = segment - 1
				elif path.closed and segment == 1 \
						and path.SegmentType(-1) == Bezier\
						and path.Continuity(-1):
					self.other_segment = path.len - 1
				else:
					self.other_segment = -1
				p1 = path.Segment(segment)[1][0]
				self.DragStart(p1)
				return p - p1
			elif self.selection_type == SelSegmentLast:
				segment = self.selected_idx
				self.other_segment = -1
				if path.Continuity(segment):
					if segment < path.len - 1 \
						and path.SegmentType(segment + 1) == Bezier:
						self.other_segment = segment + 1
					elif path.closed and segment == path.len - 1 \
							and path.SegmentType(1) == Bezier:
						self.other_segment = 1
				p2 = path.Segment(segment)[1][1]
				self.DragStart(p2)
				return p - p2
			elif self.selection_type == SelCurvePoint:
				start = path.point_at(self.selected_idx)
				segment = ceil(self.selected_idx)
				prev = next = -1
				type = path.SegmentType(segment)
				if type == Bezier:
					if path.Continuity(segment):
						if segment < path.len - 1 \
							and path.SegmentType(segment + 1) == Bezier:
							next = segment + 1
						elif path.closed and segment == path.len - 1 \
								and path.SegmentType(1) == Bezier:
							next = 1
					if segment > 1 \
						and path.SegmentType(segment - 1) == Bezier\
						and path.Continuity(segment - 1):
						prev = segment - 1
					elif path.closed and segment == 1 \
							and path.SegmentType(-1) == Bezier\
							and path.Continuity(-1):
						prev = path.len - 1
				else:
					if segment < path.len - 1:
						next = segment + 1
					elif path.closed and segment == path.len - 1:
						next = 1
					if segment >= 1:
						prev = segment - 1
					elif path.closed and segment == 1:
						prev = path.len - 1
				self.other_segment = (prev, next)
				self.DragStart(start)
				return p - start

	def apply_constraints(self, p, state):
		if state & ConstraintMask:
			if self.selection_type == SelNodes:
				pi4 = pi / 4
				off = p - self.drag_start
				d = Polar(pi4 * round(atan2(off.y, off.x) / pi4))
				p = self.drag_start + (off * d) * d
			elif self.selection_type in (SelSegmentFirst, SelSegmentLast):
				path = self.paths[self.selected_path]
				if self.selection_type == SelSegmentFirst:
					node = path.Node(self.selected_idx - 1)
				else:
					node = path.Node(self.selected_idx)
				radius, angle = (p - node).polar()
				pi12 = pi / 12
				angle = pi12 * floor(angle / pi12 + 0.5)
				p = node + Polar(radius, angle)
		return p
			
	def MouseMove(self, p, state):
		self.DragMove(self.apply_constraints(p, state))

	def ButtonUp(self, p, button, state):
		p = self.apply_constraints(p, state)
		self.DragStop(p)
		type = self.selection_type
		if type == SelNodes:
			undo = []
			for path in self.paths:
				if path.selection_count() > 0:
					undo.append(path.move_selected_nodes(self.off))
				else:
					undo.append(None)
			if undo:
				self._changed()
				return (self.do_undo, undo)
		elif type in (SelSegmentFirst, SelSegmentLast):
			idx = self.selected_path
			segment = self.selected_idx
			path = self.paths[idx].Duplicate()
			paths = self.paths[:idx] + (path,) + self.paths[idx + 1:]
			if type == SelSegmentFirst:
				type, (p1, p2), node, cont = path.Segment(segment)
				path.SetBezier(segment, self.drag_cur, p2, node, cont)
				if self.other_segment >= 0:
					other = self.other_segment
					type, (p1, p2), node, cont = path.Segment(other)
					p2 = adjust_control_point(p2, node, self.drag_cur, cont)
					path.SetBezier(other, p1, p2, node, cont)
				path.SelectSegment(segment - 1)
			elif type == SelSegmentLast:
				type, (p1, p2), node, cont = path.Segment(segment)
				path.SetBezier(segment, p1, self.drag_cur, node, cont)
				if self.other_segment >= 0:
					other = self.other_segment
					type, (p1, p2), node2, cont2 = path.Segment(other)
					p1 = adjust_control_point(p1, node, self.drag_cur, cont)
					path.SetBezier(other, p1, p2, node2, cont2)
				path.SelectSegment(segment)
			return self.set_paths(paths) # set_paths calls _changed()
		elif self.selection_type == SelCurvePoint:
			idx = self.selected_path
			path = self.paths[idx].Duplicate()
			paths = self.paths[:idx] + (path,) + self.paths[idx + 1:]

			segment = int(self.selected_idx)
			t = self.selected_idx - segment
			type, control, node, cont = path.Segment(segment + 1)
			if type == Bezier:
				p1, p2 = control
				if t <= 0.5:
					alpha = ((t * 2) ** 3) / 2
				else:
					alpha = 1 - (((1 - t) * 2) ** 3) / 2

				p1 = p1 + (self.off / (3 * t * (1 - t)**2)) * (1 - alpha)
				p2 = p2 + (self.off / (3 * t**2 * (1 - t))) * alpha

				path.SetBezier(segment + 1, p1, p2, node, cont)
			else:
				path.SetLine(segment + 1, node + self.off, cont)
			prev, next = self.other_segment
			if prev >= 0:
				_type, _control, _node, _cont = path.Segment(prev)
				if _type == Bezier:
					_p1, _p2 = _control
					if type == Bezier:
						_p2 = adjust_control_point(_p2, _node, p1, _cont)
					else:
						_p2 = _p2 + self.off
						_node = _node + self.off
					path.SetBezier(prev, _p1, _p2, _node, _cont)
				else:
					path.SetLine(prev, _node + self.off, _cont)
			if next >= 0:
				_type, _control, _node, _cont = path.Segment(next)
				if _type == Bezier:
					_p1, _p2 = _control
					if type == Bezier:
						_p1 = adjust_control_point(_p1, node, p2, cont)
					else:
						_p1 = _p1 + self.off
					path.SetBezier(next, _p1, _p2, _node, _cont)
			return self.set_paths(paths) # set_paths calls _changed()

	def DrawDragged(self, device, partially):
		if self.selection_type == SelNodes:
			for path in self.paths:
				path.draw_dragged_nodes(self.off, partially, device.Bezier, device.Line)
		elif self.selection_type == SelSegmentFirst:
			if not partially:
				for path in self.paths:
					path.draw_unselected(device.Bezier, device.Line)
			path = self.paths[self.selected_path]
			segment = self.selected_idx
			node = path.Node(segment - 1)
			type, (p1, p2), node2, cont = path.Segment(segment)
			device.Bezier(node, self.drag_cur, p2, node2)
			device.DrawSmallRectHandle(self.drag_cur)
			device.DrawHandleLine(node, self.drag_cur)
			if self.other_segment >= 0:
				other = self.other_segment
				type, (p1, p2), node, cont = path.Segment(other)
				p2 = adjust_control_point(p2, node, self.drag_cur, cont)
				device.Bezier(path.Node(other - 1), p1, p2, node)
				device.DrawSmallRectHandle(p2)
				device.DrawHandleLine(node, p2)
		elif self.selection_type == SelSegmentLast:
			if not partially:
				for path in self.paths:
					path.draw_unselected(device.Bezier, device.Line)
			path = self.paths[self.selected_path]
			segment = self.selected_idx
			type, (p1, p2), node, cont = path.Segment(segment)
			device.Bezier(path.Node(segment - 1), p1, self.drag_cur, node)
			device.DrawSmallRectHandle(self.drag_cur)
			device.DrawHandleLine(node, self.drag_cur)
			if self.other_segment >= 0:
				other = self.other_segment
				type, (p1, p2), node2, cont2 = path.Segment(other)
				p1 = adjust_control_point(p1, node, self.drag_cur, cont)
				device.Bezier(node, p1, p2, node2)
				device.DrawSmallRectHandle(p1)
				device.DrawHandleLine(node, p1)
		elif self.selection_type == SelCurvePoint:
			path = self.paths[self.selected_path]
			segment = int(self.selected_idx)
			t = self.selected_idx - segment
			prevnode = path.Node(segment)
			
			type, control, node, cont = path.Segment(segment + 1)
			if type == Bezier:
				p1, p2 = control
				if t <= 0.5:
					alpha = ((t * 2) ** 3) / 2
				else:
					alpha = 1 - (((1 - t) * 2) ** 3) / 2

				p1 = p1 + (self.off / (3 * t * (1 - t)**2)) * (1 - alpha)
				p2 = p2 + (self.off / (3 * t**2 * (1 - t))) * alpha

				device.Bezier(prevnode, p1, p2, node)
				device.DrawSmallRectHandle(p1)
				device.DrawHandleLine(prevnode, p1)
				device.DrawSmallRectHandle(p2)
				device.DrawHandleLine(node, p2)
			else:
				device.DrawLine(prevnode + self.off, node + self.off)
			prev, next = self.other_segment
			if prev > 0:
				_type, _control, _node, _cont = path.Segment(prev)
				if _type == Bezier:
					_p1, _p2 = _control
					if type == Bezier:
						_p2 = adjust_control_point(_p2, _node, p1, _cont)
						device.Bezier(path.Node(prev - 1), _p1, _p2, _node)
						device.DrawSmallRectHandle(_p2)
						device.DrawHandleLine(_node, _p2)
					else:
						device.Bezier(path.Node(prev - 1), _p1, _p2 + self.off,
										_node + self.off)
				else:
					device.DrawLine(path.Node(prev - 1), _node + self.off)
			if next >= 0:
				_type, _control, _node, _cont = path.Segment(next)
				if _type == Bezier:
					_p1, _p2 = _control
					if type == Bezier:
						_p1 = adjust_control_point(_p1, node, p2, cont)
						device.Bezier(node, _p1, _p2, _node)
						device.DrawSmallRectHandle(_p1)
						device.DrawHandleLine(node, _p1)
					else:
						device.Bezier(node + self.off, _p1 + self.off, _p2,
										_node)
				else:
					device.DrawLine(node + self.off, _node)

	def GetHandles(self):
		NodeHandle = handle.MakeNodeHandle
		ControlHandle = handle.MakeControlHandle
		LineHandle = handle.MakeLineHandle
		handles = []
		node_handles = []
		append = handles.append
		for path_idx in range(len(self.paths)):
			path = self.paths[path_idx]
			if path.len > 0:
				if not path.closed:
					node_handles.append(NodeHandle(path.Node(0), path.SegmentSelected(0), (path_idx, 0)))
				for i in range(1, path.len):
					selected = path.SegmentSelected(i)
					node_handles.append(NodeHandle(path.Node(i), selected, (path_idx, i)))
					if (path.SegmentType(i) == Bezier
						and (selected or path.SegmentSelected(i - 1))):
						type, (p1, p2), node, cont = path.Segment(i)
						append(ControlHandle(p1, (path_idx, -(2 * i - 1))))
						append(ControlHandle(p2, (path_idx, -(2 * i))))
						append(LineHandle(path.Node(i - 1), p1))
						append(LineHandle(p2, node))
		if self.selection_type == SelCurvePoint:
			p = self.paths[self.selected_path].point_at(self.selected_idx)
			handles.append(handle.MakeCurveHandle(p))
		return handles + node_handles

	def Info(self):
		selected = 0
		idx = None
		paths = self.paths
		for i in range(len(paths)):
			path = paths[i]
			count = path.selection_count()
			if count > 0:
				selected = selected + count
				idx = i
		if selected > 1:
			return _("%d nodes in PolyBezier") % selected
		else:
			if idx is not None:
				path = paths[idx]
				for i in range(path.len):
					if path.SegmentSelected(i):
						break
				else:
					warn(INTERNAL, 'Strange selection count')
					return _("PolyBezier")
				if i == 0:
					return _("First node of PolyBezier")
				elif i == path.len - 1:
					return _("Last node of PolyBezier")
				else:
					return _("1 node of PolyBezier")
			else:
				if self.selection_type == SelCurvePoint:
					return _("Point on curve at position %.2f") \
							% self.selected_idx
				else:
					return _("No Node of PolyBezier")

	#
	#	Special poly bezier protocol: closing, continuity
	#

	def OpenNodes(self):
		if self.selection_type == SelCurvePoint:
			index = self.selected_path
			paths = list(self.paths)
			path = paths[index]
			paths[index:index + 1] = split_path_at(path, self.selected_idx)
			self.selected_idx = int(self.selected_idx) + 1
			self.selection_type = SelNodes
		else:
			paths = []
			for path in self.paths:
				if path.selection_count() >= 1:
					if path.closed:
						for i in range(path.len - 1):
							if path.SegmentSelected(i):
								start_idx = i
								break
					else:
						start_idx = 0

					newpath = CreatePath()
					paths.append(newpath)
					p = path.Node(start_idx)
					newpath.AppendLine(p, ContAngle)

					for i in range(start_idx + 1, path.len):
						type, control, p, cont = path.Segment(i)
						if path.SegmentSelected(i):
							# XXX remove this ?
							cont = ContAngle
						newpath.AppendSegment(type, control, p, cont)
						if path.SegmentSelected(i) and i < path.len - 1:
							newpath = CreatePath()
							newpath.AppendLine(p, ContAngle)
							paths.append(newpath)

					if start_idx != 0:
						# the path was closed and the first node was not
						# selected
						for i in range(1, start_idx + 1):
							type, control, p, cont = path.Segment(i)
							newpath.AppendSegment(type, control, p, cont)
				else:
					paths.append(path)
		return self.set_paths(paths)
	#AddCmd(commands, OpenNodes, _("Cut Curve"), key_stroke = 'c')

	def CloseNodes(self):
		# find out if close is possible
		two = 0
		one = 0
		for i in range(len(self.paths)):
			path = self.paths[i]
			selected = path.selection_count()
			if not selected:
				continue
			if (path.closed and selected) or selected not in (1, 2):
				return
			if selected == 1:
				if path.SegmentSelected(0) or path.SegmentSelected(-1):
					one = one + 1
					continue
				return
			else:
				if path.SegmentSelected(0) and path.SegmentSelected(-1):
					two = two + 1
					continue
				return
		# now, close the nodes
		if one == 2 and two == 0:
			paths = []
			append_to = None
			for path in self.paths:
				if path.selection_count():
					if append_to:
						# path is the second of the paths involved
						end_node = append_to.Node(-1)
						if path.SegmentSelected(0):
							for i in range(1, path.len):
								type, p12, p, cont = path.Segment(i)
								if end_node is not None and type == Bezier:
									p12 = (p12[0] + end_node - path.Node(0),
											p12[1])
									end_node = None
								append_to.AppendSegment(type, p12, p, cont)
						else:
							for i in range(path.len - 1, 0, -1):
								type, p12, p3, cont = path.Segment(i)
								if end_node is not None and type == Bezier:
									p12 = (p12[0],
											p12[1] + end_node - path.Node(-1))
									end_node = None
								p = path.Node(i - 1)
								if type == Bezier:
									p12 = (p12[1], p12[0])
								append_to.AppendSegment(type, p12, p, path.Continuity(i - 1))
						continue
					else:
						# path is the first of the paths involved
						if path.SegmentSelected(0):
							# reverse the path
							append_to = CreatePath()
							p = path.Node(-1)
							append_to.AppendLine(p, ContAngle)
							for i in range(path.len - 1, 0, -1):
								type, p12, p3, cont = path.Segment(i)
								p = path.Node(i - 1)
								if type == Bezier:
									p12 = (p12[1], p12[0])
								append_to.AppendSegment(type, p12, p, path.Continuity(i - 1))
							path = append_to
						else:
							path = append_to = path.Duplicate()
						append_to.SetContinuity(-1, ContAngle)
				paths.append(path)
			undo = self.set_paths(paths)
		elif one == 0 and two == 1:
			undo_list = []
			for path in self.paths:
				if path.selection_count():
					undo_list.append(path.ClosePath())
				else:
					undo_list.append(None)
			undo = (self.object.do_undo, undo_list)
			self._changed()
		else:
			return
		return undo
	#AddCmd(commands, CloseNodes, _("Close Nodes"))

	def SetContinuity(self, cont):
		new_paths = []
		for path in self.paths:
			if path.selection_count():
				new_paths.append(set_continuity(path, cont))
			else:
				new_paths.append(path)
		return self.set_paths(new_paths)
	#AddCmd(commands, 'ContAngle', _("Angle"), SetContinuity,args = ContAngle, key_stroke = 'a')
	#AddCmd(commands, 'ContSmooth', _("Smooth"), SetContinuity, args = ContSmooth, key_stroke = 's')
	#AddCmd(commands, 'ContSymmetrical', _("Symmetrical"), SetContinuity, args = ContSymmetrical, key_stroke='y')

	def SegmentsToLines(self):
		if self.selection_type == SelCurvePoint:
			new_paths = list(self.paths)
			path = new_paths[self.selected_path]
			new_paths[self.selected_path] = segment_to_line(path, self.selected_idx)
		else:
			new_paths = []
			for path in self.paths:
				if path.selection_count() > 1:
					new_paths.append(segments_to_lines(path))
				else:
					new_paths.append(path)
		return self.set_paths(new_paths)
	#AddCmd(commands, SegmentsToLines, _("Curve->Line"), key_stroke = 'l')

	def SegmentsToCurve(self):
		if self.selection_type == SelCurvePoint:
			new_paths = list(self.paths)
			path = new_paths[self.selected_path]
			new_paths[self.selected_path] = segment_to_curve(path, self.selected_idx)
		else:
			new_paths = []
			for path in self.paths:
				if path.selection_count() > 1:
					new_paths.append(segments_to_beziers(path))
				else:
					new_paths.append(path)
		return self.set_paths(new_paths)
	#AddCmd(commands, SegmentsToCurve, _("Line->Curve"), key_stroke = 'b')

	def DeleteNodes(self):
		new_paths = []
		for path in self.paths:
			if path.selection_count() > 0:
				newpath = delete_segments(path)
			else:
				newpath = path
			if newpath.len > 1:
				new_paths.append(newpath)
			else:
				# all nodes of path have been deleted
				if __debug__:
					pdebug('bezier', 'path removed')
		if new_paths:
			return self.set_paths(new_paths)
		else:
			if __debug__:
				pdebug('bezier', 'PolyBezier removed')
			self.document.DeselectObject(self.object)
			return self.parent.Remove(self.object)
	#AddCmd(commands, DeleteNodes, _("Delete Nodes"), key_stroke = ('-', 'Delete'))

	def InsertNodes(self):
		if self.selection_type == SelCurvePoint:
			new_paths = list(self.paths)
			path = new_paths[self.selected_path]
			new_paths[self.selected_path] = insert_node_at(path, self.selected_idx)
			self.selected_idx = int(self.selected_idx) + 1
			self.selection_type = SelNodes
		else:
			new_paths = []
			for path in self.paths:
				if path.selection_count() > 1:
					new_paths.append(insert_segments(path))
				else:
					new_paths.append(path)
		return self.set_paths(new_paths)
	#AddCmd(commands, InsertNodes, _("Insert Nodes"), key_stroke = '+')

	def ChangeRect(self):
		prop = self.properties
		if prop.IsAlgorithmicFill() or prop.IsAlgorithmicLine() \
			or prop.line_arrow1 is not None or prop.line_arrow2 is not None \
			or self.selection_type == SelCurvePoint:
			return self.bounding_rect

		filled = self.Filled()
		pts = []
		for path in self.paths:
			if path.selection_count():
				for i in range(1, path.len):
					if path.SegmentSelected(i - 1) or path.SegmentSelected(i):
						pts.append(path.Node(i - 1))
						type, p12, p, cont = path.Segment(i)
						if type == Bezier:
							p1, p2 = p12
							pts.append(p1)
							pts.append(p2)
						pts.append(p)
				if filled and not path.closed:
					if path.SegmentSelected(-1):
						pts.append(path.Node(0))
					if path.SegmentSelected(0):
						pts.append(path.Node(-1))
		if pts:
			return PointsToRect(pts).grown(prop.GrowAmount())
		else:
			return EmptyRect

	context_commands = ('SelectAllNodes',)

RegisterCommands(PolyBezierEditor)

def adjust_control_point(p, node, control, continuity):
	if continuity == ContSymmetrical:
		return 2 * node - control
	elif continuity == ContSmooth:
		try:
			d = (control - node).normalized()
			length = abs(p - node)
			return node - length * d
		except ZeroDivisionError:
			# control == node
			return p
	else:
		return p

def subdivide(p0, p1, p2, p3, t = 0.5):
	t2 = 1 - t
	r = t2 * p1 + t * p2
	q1 = t2 * p0 + t * p1
	q2 = t2 * q1 + t * r
	q5 = t2 * p2 + t * p3
	q4 = t2 * r + t * q5
	q3 = t2 * q2 + t * q4
	return q1, q2, q3, q4, q5


def delete_segments(path):
	newpath = CreatePath()
	selected = path.selection_count()
	if (path.closed and selected == path.len - 1) or selected == path.len:
		return newpath
	f13 = 1.0 / 3.0;	f23 = 2.0 / 3.0
	i = 0
	while path.SegmentSelected(i):
		i = i + 1
	if path.closed and i > 0:
		if path.SegmentType(i) == Bezier:
			last_p2 = path.Segment(i)[1][1]
			last_type = Bezier
		else:
			last_p2 = f23 * path.Node(i - 1) + f13 * path.Node(i)
			last_type = Line
	else:
		last_p2 = None
	newpath.AppendLine(path.Node(i), path.Continuity(i))

	seg_p1 = None; seg_type = None
	for i in range(i + 1, path.len):
		type, p12, p, cont = path.Segment(i)
		if type == Bezier:
			p1, p2 = p12
		if path.SegmentSelected(i):
			if seg_type is None:
				seg_type = type
				if type == Bezier:
					seg_p1 = p1
				else:
					seg_p1 = f23 * path.Node(i - 1) + f13 * p
		else:
			if seg_type is not None:
				if type == Bezier or seg_type == Bezier:
					if type == Line:
						p2 = f13 * path.Node(i - 1) + f23 * p
					newpath.AppendBezier(seg_p1, p2, p, cont)
				else:
					newpath.AppendLine(p, cont)
				seg_type = None
			else:
				newpath.AppendSegment(type, p12, p, cont)
	if path.closed:
		if last_p2 is not None:
			if last_type == Bezier or seg_type == Bezier:
				newpath.AppendBezier(seg_p1, last_p2, newpath.Node(0), newpath.Continuity(0))
			else:
				newpath.AppendLine(newpath.Node(0), newpath.Continuity(0))
		newpath.ClosePath()
	return newpath

def insert_segments(path):
	newpath = CreatePath()
	newpath.AppendLine(path.Node(0), path.Continuity(0))
	newpath.select_segment(0, path.SegmentSelected(0))

	for i in range(1, path.len):
		type, p12, p, cont = path.Segment(i)
		if path.SegmentSelected(i) and path.SegmentSelected(i - 1):
			if type == Line:
				node = 0.5 * path.Node(i - 1) + 0.5 * path.Node(i)
				newpath.AppendLine(node)
				newpath.select_segment(-1)
				newpath.AppendLine(path.Node(i))
				newpath.select_segment(-1)
			else:
				if newpath.Continuity(-1) == ContSymmetrical:
					newpath.SetContinuity(-1, ContSmooth)
				p1, p2 = p12
				p1, p2, node, p3, p4 = subdivide(path.Node(i - 1), p1, p2, p)
				newpath.AppendBezier(p1, p2, node, ContSymmetrical)
				newpath.select_segment(-1)
				if cont == ContSymmetrical:
					cont = ContSmooth
				newpath.AppendBezier(p3, p4, p, cont)
				newpath.select_segment(-1)
		else:
			newpath.AppendSegment(type, p12, p, cont)
			newpath.select_segment(-1, path.SegmentSelected(i))
	if path.closed:
		newpath.ClosePath()
		newpath.SetContinuity(-1, path.Continuity(-1))
	return newpath

def copy_selection(path, newpath):
	for i in range(path.len):
		newpath.select_segment(i, path.SegmentSelected(i))

def segments_to_lines(path):
	newpath = CreatePath()
	newpath.AppendLine(path.Node(0))
	for i in range(1, path.len):
		if path.SegmentSelected(i) and path.SegmentSelected(i - 1):
			if path.SegmentType(i) == Bezier:
				cont = ContAngle
				newpath.SetContinuity(-1, ContAngle)
			else:
				cont = path.Continuity(i)
			newpath.AppendLine(path.Node(i), cont)
		else:
			apply(newpath.AppendSegment, path.Segment(i))
	if path.closed:
		cont = newpath.Continuity(-1)
		newpath.ClosePath()
		newpath.SetContinuity(-1, cont)
	copy_selection(path, newpath)
	return newpath

def segments_to_beziers(path):
	f13 = 1.0 / 3.0;	f23 = 2.0 / 3.0
	newpath = CreatePath()
	newpath.AppendLine(path.Node(0))
	for i in range(1, path.len):
		type, p12, p, cont = path.Segment(i)
		if path.SegmentSelected(i) and path.SegmentSelected(i - 1):
			cont = path.Continuity(i)
			if type == Line:
				node1 = path.Node(i - 1); node2 = path.Node(i)
				p1 = f23 * node1 + f13 * node2
				p2 = f13 * node1 + f23 * node2
				cont = ContAngle
			else:
				p1, p2 = p12
			newpath.AppendBezier(p1, p2, p, cont)
		else:
			newpath.AppendSegment(type, p12, p, cont)
	if path.closed:
		cont = newpath.Continuity(-1)
		newpath.ClosePath()
		newpath.SetContinuity(-1, cont)
	copy_selection(path, newpath)
	return newpath

def set_continuity(path, cont):
	f13 = 1.0 / 3.0;	f23 = 2.0 / 3.0
	newpath = path.Duplicate()
	for i in range(1, path.len):
		if path.SegmentSelected(i):
			newpath.SetContinuity(i, cont)
			if cont == ContAngle:
				continue
			if newpath.SegmentType(i) != Bezier:
				continue
			if i == path.len - 1:
				if newpath.closed:
					other = 1
				else:
					continue
			else:
				other = i + 1
			if newpath.SegmentType(other) != Bezier:
				continue
			type, (p1, p2), node, oldcont = newpath.Segment(i)
			type, (p3, p4), other_node, other_cont = newpath.Segment(other)

			d = p3 - p2
			if cont == ContSymmetrical:
				d = 0.5 * d
			p2 = adjust_control_point(p2, node, node + d, cont)
			p3 = adjust_control_point(p3, node, node - d, cont)
			newpath.SetBezier(i, p1, p2, node, cont)
			newpath.SetBezier(other, p3, p4, other_node, other_cont)
	return newpath


def copy_path(dest, src, start = 0, end = -1, copy_selection = 1):
	if start < 0:
		start = src.len + start
	if end < 0:
		end = src.len + end
	for i in range(start, end + 1):
		type, control, node, cont = src.Segment(i)
		dest.AppendSegment(type, control, node, cont)
		if copy_selection:
			dest.select_segment(-1, src.SegmentSelected(i))


def insert_node_at(path, at):
	index = int(at)
	t = at - index
	newpath = CreatePath()
	copy_path(newpath, path, 0, index)
	type, control, node, cont = path.Segment(index + 1)
	if type == Line:
		newpath.AppendLine((1 - t) * path.Node(index) + t * node)
		newpath.select_segment(-1)
		newpath.AppendLine(node)
	else:
		if newpath.Continuity(-1) == ContSymmetrical:
			newpath.SetContinuity(-1, ContSmooth)
		p1, p2 = control
		p1, p2, q, p3, p4 = subdivide(newpath.Node(-1), p1, p2, node, t)
		newpath.AppendBezier(p1, p2, q, ContSmooth)
		newpath.select_segment(-1)
		if cont == ContSymmetrical:
			cont = ContSmooth
		newpath.AppendBezier(p3, p4, node, cont)
	copy_path(newpath, path, index + 2)
	if path.closed:
		newpath.ClosePath()
		newpath.SetContinuity(-1, path.Continuity(-1))
	return newpath

def split_path_at(path, at):
	index = int(at)
	t = at - index
	if path.closed:
		path1 = path2 = CreatePath()
		result = [path1]
	else:
		path1 = CreatePath()
		path2 = CreatePath()
		result = [path1, path2]
		copy_path(path1, path, 0, 0, copy_selection = 0)

	type, control, node, cont = path.Segment(index + 1)
	if type == Line:
		q = (1 - t) * path.Node(index) + t * node
		path2.AppendLine(q)
		path2.AppendLine(node)
		path2.select_segment(0)
		function = path1.AppendLine
		args = (q,)
	else:
		p1, p2 = control
		p1, p2, q, p3, p4 = subdivide(path.Node(index), p1, p2, node, t)
		path2.AppendLine(q)
		path2.AppendBezier(p3, p4, node, cont)
		path2.select_segment(0)
		function = path1.AppendBezier
		args = (p1, p2, q, ContSymmetrical)
	copy_path(path2, path, index + 2, copy_selection = 0)
	copy_path(path1, path, 1, index, copy_selection = 0)
	apply(function, args)
	return result
	
def segment_to_line(path, at):
	index = int(at)
	if path.SegmentType(index + 1) == Bezier:
		newpath = CreatePath()
		copy_path(newpath, path, 0, index)
		newpath.SetContinuity(-1, ContAngle)
		newpath.AppendLine(path.Node(index + 1), ContAngle)
		copy_path(newpath, path, index + 2)
		if path.closed:
			cont = newpath.Continuity(-1)
			newpath.ClosePath()
			newpath.SetContinuity(-1, cont)
	else:
		newpath = path
	return newpath

def segment_to_curve(path, at):
	index = int(at)
	if path.SegmentType(index + 1) == Line:
		newpath = CreatePath()
		copy_path(newpath, path, 0, index)
		f13 = 1.0 / 3.0;
		f23 = 2.0 / 3.0
		node1 = path.Node(index);
		node2 = path.Node(index + 1)
		p1 = f23 * node1 + f13 * node2
		p2 = f13 * node1 + f23 * node2
		newpath.AppendBezier(p1, p2, node2, path.Continuity(index + 1))
		copy_path(newpath, path, index + 2)
		if path.closed:
			cont = newpath.Continuity(-1)
			newpath.ClosePath()
			newpath.SetContinuity(-1, cont)
	else:
		newpath = path
	return newpath
	


def CombineBeziers(beziers):
	combined = beziers[0].Duplicate()
	paths = combined.paths
	for bezier in beziers[1:]:
		paths = paths + bezier.paths
	combined.paths = paths
	return combined


