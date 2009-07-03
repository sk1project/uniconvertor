# Sketch - A Python-based interactive drawing program
# Copyright (C) 1996, 1997, 1998, 1999 by Bernhard Herzog
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
#       The layer classes. 
#

from types import TupleType
from app.conf.const import LAYER_STATE, LAYER_COLOR

from app import _, NullUndo, EmptyRect, InfinityRect, Point, config, _sketch

import color
import selinfo

from compound import EditableCompound

class Layer(EditableCompound):

	can_be_empty = 1
	is_Layer = 1
	is_SpecialLayer = 0
	is_GridLayer = 0
	is_GuideLayer = 0
	is_MasterLayer = 0
	is_Page=0

	def __init__(self, name = _("New Layer"),
					visible = 1, printable = 1, locked = 0,
					outlined = 0, outline_color = config.preferences.layer_color,
					is_MasterLayer=0, is_Page=0):
		EditableCompound.__init__(self, [])
		self.name = name
		self.visible = visible
		self.printable = printable
		self.locked = locked
		self.outlined = outlined
		self.is_MasterLayer = is_MasterLayer
		self.is_Page = is_Page
		if type(outline_color) == TupleType:
			if len(outline_color)==3:
				outline_color=('RGB',outline_color[0],outline_color[1],outline_color[2])
			self.outline_color = apply(color.ParseSKColor, outline_color)
		else:
			self.outline_color = outline_color

	def Draw(self, device, rect = None):
		# Draw all objects on the device device. RECT, if provided,
		# gives the bounding rect of the region to be drawn allowing to
		# optimize the redisplay by drawing only those objects that
		# overlap with this rect.
		if device.draw_visible and self.visible \
			or device.draw_printable and self.printable:
			outlined = self.outlined or device.IsOutlineActive()
			if outlined:
				device.StartOutlineMode(self.outline_color)
			EditableCompound.DrawShape(self, device, rect)
			if outlined:
				device.EndOutlineMode()

	def SelectSubobject(self, p, rect, device, path = (), *rest):
		if not self.CanSelect():
			return None
		if self.outlined:
			device.StartOutlineMode()
		try:
			result = EditableCompound.SelectSubobject(self, p, rect, device,
														path)
		finally:
			if self.outlined:
				device.EndOutlineMode()

		return result

	def SelectRect(self, rect):
		if not self.CanSelect():
			return []
		test = rect.contains_rect
		build_info = selinfo.build_info
		selected = []
		objects = self.objects
		for idx in range(len(objects)):
			obj = objects[idx]
			if test(obj.bounding_rect):
				selected.append(build_info(idx, obj))
		return selected

	def SelectAll(self):
		if self.CanSelect():
			return selinfo.select_all(self.objects)
		else:
			return []

	def SelectionInfo(self, child, cache = None):
		info = selinfo.build_info(_sketch.IdIndex(self.objects, child), child)
		return selinfo.prepend_idx(self.document.LayerIndex(self), info)

	def PickObject(self, p, rect, device):
		if not self.visible:
			return None
		if self.outlined:
			device.StartOutlineMode()
		result = EditableCompound.PickObject(self, p, rect, device)
		if self.outlined:
			device.EndOutlineMode()
		return result

	def SetName(self, name):
		undo = (self.SetName, self.name)
		self.name = name
		return undo

	def Name(self):
		return self.name

	def NumObjects(self):
		return len(self.objects)

	def Visible(self):
		return self.visible

	def Printable(self):
		return self.printable

	def Locked(self):
		return self.locked

	def CanSelect(self):
		return not self.locked and self.visible

	def get_state(self):
		return (self.visible, self.printable, self.locked, self.outlined)

	def SetState(self, visible, printable, locked, outlined):
		# set the layer state. Return undo info.
		#
		# Side Effect:
		# Queue a LAYER message with parameter LAYER_STATE + tuple.
		# The tuple has the form
		#
		# (layer, visible_changed, printable_changed, outline_changed)
		#
		# We assume here that the receiver (usually SketchCanvas or
		# SketchView) uses this to determine whether to repaint parts of
		# the screen. If the receiver shows only visible layers and
		# allows outline, it should use the following expression to
		# determine whether to redraw or not:
		#
		#    layer.NumObjects() and (visible_changed or
		#				(outlined_changed and layer.Visible()))
		#
		# If you only show printable layers:
		#
		#    layer.NumObjects() and printable_changed
		#
		# (in that case outline mode should be ignored as it is only
		# meant for quicker or clearer display while editing)
		#
		# The bounding rect of the now invalid region is
		# layer.bounding_rect

		oldstate = self.get_state()
		visible_changed = self.visible != visible
		self.visible = visible
		printable_changed = self.printable != printable
		self.printable = printable
		locked_changed = self.locked != locked
		self.locked = locked
		outlined_changed = self.outlined != outlined
		self.outlined = outlined

		if oldstate != self.get_state():
			undo = (self.SetState,) + oldstate
			visibility = (self, visible_changed, printable_changed,
							outlined_changed)
			if self.document is not None:
				self.document.queue_layer(LAYER_STATE, visibility)
			if locked_changed:
				self.document.update_active_layer()
			return undo
		
		return NullUndo

	def SetOutlineColor(self, color):
		undo = (self.SetOutlineColor, self.outline_color)
		self.outline_color = color
		if self.document is not None:
			self.document.queue_layer(LAYER_COLOR, self)
		return undo

	def OutlineColor(self):
		return self.outline_color

	def Outlined(self):
		return self.outlined

	def SaveToFile(self, file):
		if self.is_MasterLayer:
			file.BeginMasterLayer(self.name, self.visible, self.printable, self.locked,
							self.outlined, self.outline_color)
		else:
			file.BeginLayer(self.name, self.visible, self.printable, self.locked,
							self.outlined, self.outline_color)
		for obj in self.objects:
			obj.SaveToFile(file)
		file.EndLayer()

class SpecialLayer(Layer):

	is_SpecialLayer = 1

	def __none(self, *args):
		return None

	SelectSubobject = __none
	PickObject = __none

	def SelectRect(self, *rect):
		return []

	SelectAll = SelectRect


class GuideLayer(SpecialLayer):

	is_GuideLayer = 1

	def __init__(self, name = _("Guides"), visible = 1, printable = 0,
					locked = 0, outlined = 1, outline_color = None):
		if outline_color is None:
			outline_color = config.preferences.guide_color
		SpecialLayer.__init__(self, name, visible, 0, locked, 1,
								outline_color)

	def SetState(self, visible, printable, locked, outlined):
		return SpecialLayer.SetState(self, visible, 0, locked, outlined)

	def Draw(self, device, rect = None):
		if device.draw_visible and self.visible \
			or device.draw_printable and self.printable:
			device.StartOutlineMode(self.outline_color)
			SpecialLayer.DrawShape(self, device)
			device.EndOutlineMode()

	def SelectSubobject(self, p, rect, device, path = (), *rest):
		if not self.CanSelect():
			return None
		device.StartOutlineMode()
		try:
			objects = self.objects
			for obj_idx in range(len(objects) - 1, -1, -1):
				obj = objects[obj_idx]
				if obj.Hit(p, rect, device):
					result = obj.SelectSubobject(p, rect, device)
					return selinfo.prepend_idx(obj_idx, result)
			return None
		finally:
			device.EndOutlineMode()

	def SelectRect(self, rect):
		if not self.CanSelect():
			return []
		test = rect.contains_rect
		build_info = selinfo.build_info
		selected = []
		objects = self.objects
		for idx in range(len(objects)):
			obj = objects[idx]
			if not obj.is_GuideLine and test(obj.bounding_rect):
				selected.append(build_info(idx, obj))
		return selected

	def SelectAll(self):
		return self.SelectRect(InfinityRect)

	def compute_rects(self):
		if self.objects:
			self.bounding_rect = self.coord_rect = InfinityRect
		else:
			self.bounding_rect = self.coord_rect = EmptyRect

	def SaveToFile(self, file):
		file.BeginGuideLayer(self.name, self.visible, self.printable,
								self.locked, self.outlined, self.outline_color)
		for obj in self.objects:
			obj.SaveToFile(file)
		file.EndGuideLayer()

	def Snap(self, p):
		default = (1e100, p)
		horizontal = [default]
		vertical = [default]
		result = [default]
		for obj in self.objects:
			dist, snapped = obj.Snap(p)
			if type(snapped) == TupleType:
				if snapped[0] is None:
					horizontal.append((dist, snapped))
				else:
					vertical.append((dist, snapped))
			else:
				result.append((dist, snapped))

		return min(horizontal), min(vertical), min(result)

	def GuideLines(self):
		result = self.objects[:]
		for idx in range(len(result) - 1, -1, -1):
			if not result[idx].is_GuideLine:
				del result[idx]
		return result

	def issue_changed(self):
		Layer.issue_changed(self)
		if self.document is not None:
			self.document.GuideLayerChanged(self)

class GridLayer(SpecialLayer):

	is_GridLayer = 1
	geometry = (0, 0, 20, 20)

	def __init__(self, geometry = None, visible = None, outline_color = None,
					name = _("Grid")):
		# The grid is locked, outlined and not printable
		if geometry is None:
			geometry = config.preferences.grid_geometry
		if visible is None:
			visible = config.preferences.grid_visible
		if outline_color is None:
			outline_color = config.preferences.grid_color
		SpecialLayer.__init__(self, name, visible, 0, 1, 1, outline_color)
		if len(geometry) == 2:
			self.geometry = (0, 0) + geometry
		elif len(geometry) == 4:
			self.geometry = geometry
		else:
			raise ValueError, "grid tuple must have length 2 or 4"

	def Draw(self, device, rect = None):
		if device.draw_visible and self.visible \
			or device.draw_printable and self.printable:
			device.StartOutlineMode(self.outline_color)
			xorg, yorg, xwidth, ywidth = self.geometry
			device.DrawGrid(xorg, yorg, xwidth, ywidth, rect)
			device.EndOutlineMode()

	def update_rects(self):
		self.bounding_rect = self.coord_rect = InfinityRect

	def SaveToFile(self, file):
		file.BeginGridLayer(self.geometry, self.visible, self.outline_color,
							self.name)
		file.EndGridLayer()

	def Snap(self, p):
		xorg, yorg, xwidth, ywidth = self.geometry
		sx = round((p.x - xorg) / xwidth) * xwidth + xorg
		sy = round((p.y - yorg) / ywidth) * ywidth + yorg
		result = Point(sx, sy)
		return (abs(result - p), result)

	def SetState(self, visible, printable, locked, outlined):
		return SpecialLayer.SetState(self, visible, 0, 1, 1)

	def Geometry(self):
		return self.geometry

	def SetGeometry(self, geometry):
		undo = (self.SetGeometry, self.geometry)
		self.geometry = geometry
		if self.document:
			# a hack...
			self.document.queue_layer(LAYER_COLOR, self)
		return undo

