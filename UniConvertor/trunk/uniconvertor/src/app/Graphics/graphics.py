# Sketch - A Python-based interactive drawing program
# Copyright (C) 1996, 1997, 1998, 1999, 2000, 2002, 2003 by Bernhard Herzog
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

# This file contains the classes that act as a more or less abstract
# graphics device. For the purposes of this file, a graphics device
# provides methods for drawing primitives like rectangles, curves or
# images and for setting the colors and pattern with which they are
# drawn. A graphics device is abstract in the sense that all coordinates
# are given in document coordinates and code using a graphics device
# need not know whether output goes to a window or a printer, etc.
#

import sys
from types import TupleType
import operator, string
from math import atan2, hypot, pi, sin, cos

from sk1libs import imaging

#from app.X11 import X
from app.conf import const
X=const
#from pax import PaxRegionType, IntersectMasks, CreateRegion

from app.events.warn import pdebug, warn, INTERNAL, USER
from app import _, SketchError, config
from sk1libs.utils import Empty

from app.conf import const
from app.conf.const import ArcPieSlice, ArcChord

from app import _sketch


from app import Point, Polar, Rect, UnitRect, Identity, SingularMatrix, \
		Trafo, Rotation, Scale, Translation, Undo, TransformRectangle

from color import StandardColors
import color
from properties import SolidLine, PropertyStack
from pattern import SolidPattern, EmptyPattern


# approximate a unit circle
circle_path = _sketch.approx_arc(0, 2 * pi)

# Flip y coordinates
FlipY = Trafo(1, 0, 0, -1, 0, 0)


# Define a device dependent color (as opposed to color.RGBColor, which
# is a bit device independent). Mainly interesting when drawing on a
# Bitmap or inverting device where it is important which bits are
# involved and not which color is actually used. The colors are
# currently represented as python integers.
def ScreenColor(color):
	return int(color)

color_0 = ScreenColor(0)
color_1 = ScreenColor(1)

# some default properties
black_line = PropertyStack()
black_line.AddStyle(SolidLine(StandardColors.black))
blue_line = PropertyStack()
blue_line.AddStyle(SolidLine(StandardColors.blue))
defaultLineStyle = black_line
default_outline_style = black_line
default_guide_style = blue_line
default_grid_style = blue_line


class GCDevice:

	#	The base class for devices dealing with X graphics contexts
	#	(GCs). Implements the methods for converting between window and
	#	doc coordinates, clipping and outline mode

	outline_style = default_outline_style
	line = defaultLineStyle

	def __init__(self):
		self.orig_x = self.orig_y = 0.0
		self.scale = 1.0
		self.win_to_doc = self.doc_to_win = Identity
		self.init_trafo_stack()
		self.gc = None
		self.outline_mode = 0
		self.font = None
		self.clip_region = None
		self.clip_stack = None
		self.proc_fill = 0

	def init_gc(self, widget, **gcargs):
		self.gc = widget.CreateGC(gcargs)
		self.widget = widget
		self.visual = color.skvisual
		self.InitClip()
		#width=self.widget.winfo_reqwidth()
		#height=self.widget.winfo_reqheight()
		

	#
	#	Clipping
	#
	#	Ideally, the clipping mechanism works as follows:
	#
	#	Before drawing anything, the canvas initializes the clipping
	#	mechanism with InitClip(). After this, no clipping is active
	#	(apart from clipping to the window which is always done by X)
	#
	#	Subsequently, whenever clipping is needed, you are expected to
	#	call PushClip to save the current clipping region on a stack and
	#	use one (or more) of the methods ClipRegion, ClipRect,
	#	ClipPolygon or ClipBitmap to establish a new clipping region.
	#	After this, only those parts of the device that lie within the
	#	clipping region are modified.
	#
	#	If there already is an active clipping region, the new clipping
	#	region will be the intersection of the old clipping region and
	#	the region specified in the method invocation.
	#
	#	To restore the old clipping region, finally call PopClip. There
	#	must be a call to PopClip for every call to PushClip, etc.
	#
	#	This mechanism allows arbitrarily nested clipping operations.
	#
	#	The clipping regions are given in device coordinates
	#


	def InitClip(self):
		# reset all clipping...
		self.gc.SetClipMask(None)
		self.clip_region = None
		self.clip_stack = ()

	def IsClipping(self):
		return self.clip_stack != ()

	def PushClip(self):
		self.clip_stack = (self.clip_region, self.clip_stack)

	def PopClip(self):
		# Pop the old clip region from the clip stack and make it the
		# active clip region.
		self.clip_region, self.clip_stack = self.clip_stack
		self.gc.SetClipMask(self.clip_region)

	def ClipRegion(self, region):
		# Itersect the current clip region and REGION and make the
		# result the new clip region. REGION may be a region object or a
		# pixmap object of depth 1
		self.clip_region = IntersectMasks(self.clip_region, region)
		self.gc.SetClipMask(self.clip_region)

	def ClipRect(self, recttuple):
		region = self.widget.CreateRegion()
		apply(region.UnionRectWithRegion, recttuple)
		self.ClipRegion(region)

	def ClipPolygon(self, pts):
		self.ClipRegion(self.widget.PolygonRegion(pts))

	ClipBitmap = ClipRegion

	def create_clip_bitmap(self):
		width = self.widget.width
		height = self.widget.height
		bitmap = self.widget.CreatePixmap(width, height, 1)
		bitmap_gc = bitmap.CreateGC(foreground = 0)
		bitmap_gc.FillRectangle(0, 0, width, height)
		bitmap_gc.foreground = 1
		return (bitmap, bitmap_gc)

	#
	# Convert document coordinates to window coordinates and vice versa.
	#

	def DocToWin(self, *args):
		# Return the point in window coords as a tuple of ints
		return apply(self.doc_to_win.DocToWin, args)

	def DocToWinPoint(self, p):
		# Return the point in window coords as a point object
		return self.doc_to_win(p)

	def LengthToWin(self, len):
		return int(len * self.scale + 0.5)

	def LengthToWinFloat(self, len):
		return len * self.scale

	def LengthToDoc(self, len):
		return len / self.scale

	def WinToDoc(self, *args):
		return apply(self.win_to_doc, args)

	def init_trafo_stack(self):
		self.trafo_stack = ()
		self.default_trafo = (self.win_to_doc, self.doc_to_win)

	def SetViewportTransform(self, scale, doc_to_win, win_to_doc):
		self.scale = scale
		self.doc_to_win = doc_to_win
		self.win_to_doc = win_to_doc
		self.init_trafo_stack()

	def InitTrafo():
		self.win_to_doc, self.doc_to_win = self.default_trafo
		self.trafo_stack = ()

	def PushTrafo(self):
		self.trafo_stack = (self.win_to_doc, self.doc_to_win, self.trafo_stack)

	def Concat(self, trafo):
		self.doc_to_win = self.doc_to_win(trafo)
		try:
			self.win_to_doc = trafo.inverse()(self.win_to_doc)
		except SingularMatrix:
			pass

	def Translate(self, *args):
		self.Concat(apply(Translation, args))

	def Scale(self, factor):
		self.Concat(Scale(factor))

	def Rotate(self, angle):
		self.Concat(Rotation(angle))

	def PopTrafo(self):
		self.win_to_doc, self.doc_to_win, self.trafo_stack = self.trafo_stack

	def WindowResized(self, width, height):
		pass


	#
	#	Double Buffering
	#

	def StartDblBuffer(self):
		self.buffer_pixmap = self.widget.CreatePixmap()
		self.gc.SetDrawable(self.buffer_pixmap)

	def EndDblBuffer(self):
		self.gc.SetDrawable(self.widget)
		self.buffer_pixmap.CopyArea(self.widget, self.gc, 0, 0,
									self.widget.width, self.widget.height,
									0, 0)
		self.buffer_pixmap = None


class SimpleGC(GCDevice):

	#
	#	Functions for drawing X-primitives (rectangles, lines, ...)
	#	with solid colors
	#
	#	These functions are used internally and by the Patterns
	#

	def __init__(self):
		GCDevice.__init__(self)
		self.current_color = StandardColors.black

	def SetFillColor(self, color):
		self.current_color = color
		try:
			self.gc.SetForegroundAndFill(self.visual.get_pixel(color.RGB()))
		except:
			self.gc.SetForegroundAndFill(self.visual.get_pixel(color))	

	def SetLineColor(self, color):
		self.current_color = color
		try:
			#print "Xlib outline0",color.RGB()
			self.gc.SetForegroundAndFill(self.visual.get_pixel(color.RGB()))
		except:
			#print "Xlib outline",color
			self.gc.SetForegroundAndFill(self.visual.get_pixel(color))


	def SetLineAttributes(self, width, cap = X.CapButt, join = X.JoinMiter, dashes = None):
		if dashes:
			line = X.LineOnOffDash
		else:
			line = X.LineSolid
		self.gc.SetLineAttributes(int(round(width * self.scale)), line, cap,
									join)
		if dashes:
			if width < 1.0:
				scale = self.scale
			else:
				scale = width * self.scale
			dashes = map(operator.mul, dashes, [scale] * len(dashes))
			dashes = map(int, map(round, dashes))
			for idx in range(len(dashes)):
				length = dashes[idx]
				if length <= 0:
					dashes[idx] = 1
				elif length > 255:
					dashes[idx] = 255
			self.gc.SetDashes(dashes)

	def SetLineSolid(self):
		self.gc.line_style = X.LineSolid

	def DrawLine(self, start, end):
		startx, starty	= self.DocToWin(start)
		endx,	endy	= self.DocToWin(end)
		self.gc.DrawLine(startx, starty, endx, endy)

	def DrawLineXY(self, x1, y1, x2, y2):
		startx, starty	= self.DocToWin(x1, y1)
		endx,	endy	= self.DocToWin(x2, y2)
		self.gc.DrawLine(startx, starty, endx, endy)

	def DrawLines(self, pts):
		pts = map(self.DocToWin, pts)
		self.gc.DrawLines(pts, X.CoordModeOrigin)

	def FillPolygon(self, pts):
		pts = map(self.DocToWin, pts)
		self.gc.FillPolygon(pts, X.Complex, X.CoordModeOrigin)

	def DrawRectangle(self, start, end):
		# draw the outline of the rectangle whose opposite corners are
		# start and end.
		pts = TransformRectangle(self.doc_to_win, Rect(start, end))
		if type(pts) == TupleType:
			apply(self.gc.DrawRectangle, pts)
		else:
			self.gc.DrawLines(pts, X.CoordModeOrigin)

	def FillRectangle(self, left, top, right, bottom):
		pts = TransformRectangle(self.doc_to_win,
									Rect(left, top, right, bottom))
		if type(pts) == TupleType:
			apply(self.gc.FillRectangle, pts)
		else:
			self.gc.FillPolygon(pts, X.Convex, X.CoordModeOrigin)

	def DrawEllipse(self, start, end):
		pts = TransformRectangle(self.doc_to_win, Rect(start, end))

		if type(pts) == TupleType:
			apply(self.gc.DrawArc, pts + (0, 360 * 64))
		else:
			d = end - start
			self.PushTrafo()
			self.Concat(Trafo(d.x, 0, 0, d.y, start.x, start.y))
			self.DrawBezierPath(circle_path)
			self.PopTrafo()

	def DrawCircle(self, center, radius):
		rect = Rect(center.x - radius, center.y - radius,
					center.x + radius, center.y + radius)
		pts = TransformRectangle(self.doc_to_win, rect)
		if type(pts) == TupleType:
			apply(self.gc.DrawArc, pts + (0, 360 * 64))
		else:
			self.PushTrafo()
			self.Concat(Trafo(radius, 0, 0, radius, center.x, center.y))
			self.DrawBezierPath(circle_path)
			self.PopTrafo()

	def FillCircle(self, center, radius):
		rect = Rect(center.x - radius, center.y - radius,
					center.x + radius, center.y + radius)
		pts = TransformRectangle(self.doc_to_win, rect)
		if type(pts) == TupleType:
			apply(self.gc.FillArc, pts + (0, 360 * 64))
		else:
			self.PushTrafo()
			self.Concat(Trafo(radius, 0, 0, radius, center.x, center.y))
			self.FillBezierPath(circle_path)
			self.PopTrafo()


	def DrawBezierPath(self, path, rect = None):
		path.draw_transformed(self.gc, self.doc_to_win, 1, 0, rect)

	def FillBezierPath(self, path, rect = None):
		path.draw_transformed(self.gc, self.doc_to_win, 0, 1, rect)



class CommonDevice:

	# some methods common to GraphicsDevice and PostScriptDevice

	def draw_arrow(self, arrow, width, pos, dir, rect = None):
		self.PushTrafo()
		self.Translate(pos.x, pos.y)
		self.Rotate(dir.polar()[1])
		if width >= 1.0:
			self.Scale(width)
		self.SetLineSolid()
		arrow.Draw(self) #, rect)
		self.PopTrafo()

	def draw_arrows(self, paths, rect = None):
		if self.line:
			arrow1 = self.properties.line_arrow1
			arrow2 = self.properties.line_arrow2
			if arrow1 or arrow2:
				width = self.properties.line_width
				for path in paths:
					if not path.closed and path.len > 1:
						if arrow1:
							type, controls, p3, cont = path.Segment(1)
							p = path.Node(0)
							if type == _sketch.Bezier:
								p1, p2 = controls
								dir = p - p1
								if not abs(dir):
									dir = p - p2
							else:
								dir = p - p3
							self.draw_arrow(arrow1, width, p, dir, rect)
						if arrow2:
							type, controls, p, cont = path.Segment(-1)
							p3 = path.Node(-2)
							if type == _sketch.Bezier:
								p1, p2 = controls
								dir = p - p2
								if not abs(dir):
									dir = p - p1
							else:
								dir = p - p3
							self.draw_arrow(arrow2, width, p, dir, rect)

	def draw_ellipse_arrows(self, trafo, start_angle, end_angle, arc_type,
							rect = None):
		if arc_type == const.ArcArc and self.line and start_angle != end_angle:
			pi2 = pi / 2
			width = self.properties.line_width
			arrow1 = self.properties.line_arrow1
			if arrow1 is not None:
				pos = trafo(Polar(1, start_angle))
				dir = trafo.DTransform(Polar(1, start_angle - pi2))
				self.draw_arrow(arrow1, width, pos, dir, rect)
			arrow2 = self.properties.line_arrow2
			if arrow2 is not None:
				pos = trafo(Polar(1, end_angle))
				dir = trafo.DTransform(Polar(1, end_angle + pi2))
				self.draw_arrow(arrow2, width, pos, dir, rect)

use_shm_images = 0
shm_images_supported = 0

class GraphicsDevice(SimpleGC, CommonDevice):

	#
	#	Graphics device that allows complex fill and line properties
	#	XXX This class should have a different name
	#

	ximage = None
	font_cache = None
	old_font_cache = None

	grid_style = default_grid_style
	guide_style = default_guide_style

	# the following flags may be used by the document and layer objects
	# to determine which parts to draw, depending on whether the user
	# marks them as visible or printable.
	draw_visible = 1
	draw_printable = 0

	def __init__(self):
		SimpleGC.__init__(self)
		self.line = 0
		self.fill = 0
		self.properties = PropertyStack()
		self.gradient_steps = config.preferences.gradient_steps_editor
		self.images_drawn = 0
		self.unknown_fonts = {}
		self.failed_fonts = {}
		self.cairo_draw=0

	def InitClip(self):
		SimpleGC.InitClip(self)
		self.images_drawn = 0

	proc_fill = proc_line = 0
	fill_rect = None

	def set_properties(self, properties):
		self.properties = properties
		if properties.HasFill():
			self.fill = 1
			self.proc_fill = properties.IsAlgorithmicFill()
		else:
			self.fill = 0
			self.proc_fill = 0
		if properties.HasLine():
			self.line = 1
			self.proc_line = properties.IsAlgorithmicLine()
		else:
			self.line = 0
			self.proc_line = 0


	def SetProperties(self, properties, rect = None):
		if not self.outline_mode:
			self.fill_rect = rect
			self.set_properties(properties)
		else:
			# if outline, set only font properties
			self.properties.SetProperty(font = properties.font,
											font_size = properties.font_size)

	#
	def activate_line(self):
		self.properties.ExecuteLine(self)

	def activate_fill(self):
		self.properties.ExecuteFill(self, self.fill_rect)

	#
	#	Patterns
	#

	def get_pattern_image(self):
		width = self.widget.width
		height = self.widget.height
		winrect = self.doc_to_win(self.fill_rect)
		left, top, right, bottom = map(int, map(round, winrect))
		l = max(left, 0);	r = min(right, width);
		t = max(top, 0);	b = min(bottom, height);
		if type(self.clip_region) == PaxRegionType:
			cx, cy, cw, ch = self.clip_region.ClipBox()
			l = max(l, cx);	r = min(r, cx + cw)
			t = max(t, cy);	b = min(b, cy + ch)
		if l >= r or t >= b:
			return None, None, None
		image = imaging.Image.new('RGB', (r - l, b - t), (255, 255, 255))
		trafo = Translation(-l, -t)(self.doc_to_win)
		return image, trafo, (l, t)

	def draw_pattern_image(self, image, pos):
		if use_shm_images and self.images_drawn:
			# force a shmimage to be drawn if ShmPutImage requests might
			# be in the queue
			self.widget.Sync()
		self.create_ximage()
		ximage = self.ximage
		x, y = pos
		w, h = image.size
		_sketch.copy_image_to_ximage(self.visual, image.im, ximage, x, y, w, h)
		if use_shm_images:
			self.gc.ShmPutImage(ximage, x, y, x, y, w, h, 0)
			self.images_drawn = 1
		else:
			self.gc.PutImage(ximage, x, y, x, y, w, h)

	has_axial_gradient = 1
	def AxialGradient(self, gradient, p0, p1):
		if config.preferences.cairo_enabled == 1:
			return
		# p0 and p1 may be PointSpecs
		image, trafo, pos = self.get_pattern_image()
		if image is None:
			return
		x0, y0 = trafo(p0)
		x1, y1 = trafo(p1)
		#import time
		#_t = time.clock()
		print 'AXIAL\n================'
		print 'x0',x0, 'y0',y0
		print 'x1',x1, 'y1',y1
		RGBgradient = []
		for position, color in gradient.Colors():
			RGBgradient.append((position, tuple(color.RGB())))
		_sketch.fill_axial_gradient(image.im, RGBgradient, x0,y0, x1,y1)
		#_t = time.clock() - _t
		self.draw_pattern_image(image, pos)		

	has_radial_gradient = 1
	def RadialGradient(self, gradient, p, r0, r1):
		if config.preferences.cairo_enabled == 1:
			return
		# p may be PointSpec
		image, trafo, pos = self.get_pattern_image()
		if image is None:
			return
		x, y = trafo.DocToWin(p)
		r0 = int(round(abs(trafo.DTransform(r0, 0))))
		r1 = int(round(abs(trafo.DTransform(r1, 0))))
		#import time
		#_t = time.clock()
		RGBgradient = []
		for position, color in gradient.Colors():
			RGBgradient.append((position, tuple(color.RGB())))
		_sketch.fill_radial_gradient(image.im, RGBgradient, x, y, r0, r1)
		#_t = time.clock() - _t
		#print 'radial:', _t
		self.draw_pattern_image(image, pos)


	has_conical_gradient = 1
	def ConicalGradient(self, gradient, p, angle):
		if config.preferences.cairo_enabled == 1:
			return
		# p may be PointSpec
		image, trafo, pos = self.get_pattern_image()
		if image is None:
			return
		cx, cy = trafo.DocToWin(p)
		#import time
		#_t = time.clock()
		RGBgradient = []
		for position, color in gradient.Colors():
			RGBgradient.append((position, tuple(color.RGB())))
		_sketch.fill_conical_gradient(image.im, RGBgradient, cx, cy,
										-angle)
		#_t = time.clock() - _t
		#print 'conical:', _t
		self.draw_pattern_image(image, pos)

	use_pixmap_tile = 1
	def TileImage(self, tile, trafo):
		# XXX this could be faster with some caching.
		width, height = self.doc_to_win(trafo).DTransform(tile.size)
		width = int(round(width))
		height = int(round(height))
		if self.use_pixmap_tile and trafo.m12 == 0 and trafo.m21 == 0 \
			and width * height < self.widget.width * self.widget.height:
			# the image is only scaled. Use a tile pixmap
			#
			# there are other cases where this could be done:
			# horizontal/vertical shearing, rotation by 90 degrees,...
			# This should also be done like in DrawImage, i.e. use the
			# integer coordintes of the transformed tile to determine if
			# pixmaps can be used. This would be a little less precise,
			# though.
			# degenerate cases
			if width == 0: width = 1
			if height == 0: height = 1
			ximage = self.create_sized_ximage(abs(width), abs(height))
			pixmap = self.widget.CreatePixmap(abs(width), abs(height),
												ximage.depth)
			_sketch.copy_image_to_ximage(self.visual, tile.im, ximage,
											0, 0, width, height)
			gc = pixmap.CreateGC()
			gc.PutImage(ximage, 0, 0, 0, 0, abs(width), abs(height))
			self.gc.SetForegroundAndFill(pixmap)
			x, y = trafo.DocToWin(0, 0)
			self.gc.SetTSOrigin(x, y)
			self.gc.FillRectangle(0, 0, self.widget.width, self.widget.height)
		else:
			image, temp_trafo, pos = self.get_pattern_image()
			if image is None:
				return
			trafo = temp_trafo(trafo)
			try:
				_sketch.fill_transformed_tile(image.im, tile.im,
												trafo.inverse())
				self.draw_pattern_image(image, pos)
			except SingularMatrix:
				pass


	#
	#	Outline Mode
	#
	#	StartOutlineMode(COLOR) starts drawing everything unfilled with
	#	a solid line of color COLOR.
	#
	#	EndOutlineMode() restores the previous mode.
	#
	#	As long as there are always matching calls to StartOutlineMode
	#	and EndOutlineMode outline modes can be arbitrarily nested. This
	#	allows activating the outline mode globally in the canvas widget
	#	and overriding the color in indiviual layers or drawing only
	#	some layers in outline mode in different colors.

	allow_outline = 1

	def StartOutlineMode(self, color = None):
		if self.allow_outline:
			self.outline_mode = (self.properties, self.outline_mode)
			if color is None:
				properties = self.outline_style
			else:
				properties = PropertyStack()
				properties.SetProperty(fill_pattern = EmptyPattern)
				properties.AddStyle(SolidLine(color))
			self.set_properties(properties)

	def EndOutlineMode(self):
		if self.allow_outline and self.outline_mode:
			properties, self.outline_mode = self.outline_mode
			self.set_properties(properties)

	def IsOutlineActive(self):
		return not not self.outline_mode
	
	def CairoSetFill(self):
		#print "SET_FILL\n================"
		if not self.properties.fill_pattern.is_Gradient:
			if config.preferences.alpha_channel_enabled <> 1:
				apply(self.gc.CairoSetSourceRGB, 
					  self.properties.fill_pattern.Color().cRGB())
			else:
				apply(self.gc.CairoSetSourceRGBA, 
					  self.properties.fill_pattern.Color().cRGBA())
		else:
			if self.properties.fill_pattern.is_AxialGradient:
				# Linear gradient processing for Cairo engine
				rect=self.fill_rect
				vx, vy = self.properties.fill_pattern.direction
				print 'direction', vx, vy
				angle = atan2(vy, vx) - pi / 2
				print 'angle', angle
				center = rect.center()
				print 'center', center
				print 'rect', rect
				rx0, ry0, rx1, ry1 = self.fill_rect
				print rx0, ry0, rx1, ry1
				
				rot = Rotation(angle, center)
				left, bottom, right, top = rot(rect)
				height = (top - bottom) * (1.0 - self.properties.fill_pattern.border)
				trafo = rot(Translation(center))
								
				gradient = self.properties.fill_pattern.gradient
				p0 = trafo(0, height / 2)
				p1 = trafo(0, -height / 2)
				print p0, p1
				
				#image, trafo, pos = self.get_pattern_image()
				#if image is None:
					#return
				
				x0, y0 = self.DocToWinPoint(trafo(p0))
				x1, y1 = self.DocToWinPoint(trafo(p1))

				x0, y0 = p0
				x1, y1 = p1
				print 'x0',x0, 'y0',y0
				print 'x1',x1, 'y1',y1
				self.gc.DrawLine(x0, y0, x1, y1)
				self.gc.CairoPatternCreateLinear(x0, y0, x1, y1)
				#self.gc.CairoPatternCreateLinear(0.25, 0.35, 100, 300)
				#stopcolors=[]
				#for position, color in gradient.Colors():
					#stopcolors.append((position, color))
				#stopcolors.reverse()
				for position, color in gradient.Colors():
					if config.preferences.alpha_channel_enabled <> 1:
						r,g,b = color.cRGB()
						print r,g,b
						self.gc.CairoPatternAddColorStopRGB(position, r, g, b)
					else:
						r,g,b,a = color.cRGBA()
						self.gc.CairoPatternAddColorStopRGBA(position, r, g, b, a)
								
			elif self.properties.fill_pattern.is_RadialGradient:
				print 'RadialGradient'
			elif self.properties.fill_pattern.is_ConicalGradient:
				print 'ConicalGradient'


	def CairoSetOutline(self):
		if config.preferences.alpha_channel_enabled == 1 and not self.IsOutlineActive():
			apply(self.gc.CairoSetSourceRGBA, 
				  self.properties.line_pattern.Color().cRGBA())
		else:
			apply(self.gc.CairoSetSourceRGB, 
				  self.properties.line_pattern.Color().cRGB())			
		cWidth = self.properties.line_width * self.scale
		if self.IsOutlineActive():
			cWidth = 1.0
		cCap = self.properties.line_cap
		cJoin = self.properties.line_join
		if cCap > 0:
			cCap = cCap - 1
		self.gc.CairoSetOutlineAttr(cWidth, cCap, cJoin)
		
		dashes = self.properties.line_dashes 
		if dashes:
			if self.properties.line_width < 1.0:
				scale = self.scale
			else:
				scale = self.properties.line_width * self.scale							
			dashes = map(operator.mul, dashes, [scale] * len(dashes))
			dashes = map(int, map(round, dashes))
			for idx in range(len(dashes)):
				length = dashes[idx]
				if length <= 0:
					dashes[idx] = 1
				elif length > 255:
					dashes[idx] = 255
			self.gc.CairoSetDash(dashes,0)
		else:
			self.gc.CairoSetDash([],0)
			
	#
	#	Primitives
	#

	def Rectangle(self, trafo, clip = 0):
		self.PushTrafo()
		self.Concat(trafo)
		pts = TransformRectangle(self.doc_to_win, UnitRect)
		self.PopTrafo()
		if type(pts) == TupleType:
			if self.fill or self.proc_fill:
				if config.preferences.cairo_enabled == 0:
					if self.proc_fill:
						if not clip:
							self.PushClip()
						self.ClipRect(pts)
						self.properties.ExecuteFill(self, self.fill_rect)
						if not clip:
							self.PopClip()
						clip = 0
					else:	
						self.properties.ExecuteFill(self, self.fill_rect)
						apply(self.gc.FillRectangle, pts)
				else:
					self.CairoSetFill()
					apply(self.gc.CairoFillRectangle, pts)
			if self.line:
				if config.preferences.cairo_enabled == 0:
					self.properties.ExecuteLine(self)
					apply(self.gc.DrawRectangle, pts)
				else:
					try:
						self.CairoSetOutline()
						apply(self.gc.CairoDrawRectangle, pts)							
					except:
						self.properties.ExecuteLine(self)
						apply(self.gc.DrawRectangle, pts)				

		else:
			if self.proc_fill:
				if not clip:
					self.PushClip()
				self.ClipPolygon(pts)
				self.properties.ExecuteFill(self, self.fill_rect)
				if not clip:
					self.PopClip()
				clip = 0
			elif self.fill:
				if config.preferences.cairo_enabled == 0:
					self.properties.ExecuteFill(self, self.fill_rect)
					self.gc.FillPolygon(pts, X.Convex, X.CoordModeOrigin)
				else:
					self.CairoSetFill()
					self.gc.CairoFillPolygon(pts)				

			if self.line:				
				if config.preferences.cairo_enabled == 0:
					self.properties.ExecuteLine(self)
					self.gc.DrawLines(pts, X.CoordModeOrigin)
				else:
					try:
						self.CairoSetOutline()
						self.gc.CairoDrawPolygon(pts)							
					except:
						self.properties.ExecuteLine(self)
						self.gc.DrawLines(pts, X.CoordModeOrigin)			

		if clip:
			if type(pts) == TupleType:
				self.ClipRect(pts)
			else:
				self.ClipPolygon(pts)

	def RoundedRectangle(self, trafo, radius1, radius2, clip = 0):
		path = _sketch.RoundedRectanglePath(trafo, radius1, radius2)		
		self.MultiBezier((path,), None, clip)

	def SimpleEllipse(self, trafo, start_angle, end_angle, arc_type,
						rect = None, clip = 0):
		trafo2 = self.doc_to_win(trafo)
		if trafo2.m12 == 0.0 and trafo2.m21 == 0.0 and not self.proc_fill \
			and start_angle == end_angle and not clip:
			x1, y1 = trafo2.DocToWin(1, 1)
			x2, y2 = trafo2.DocToWin(-1, -1)
			if x1 > x2:
				t = x1; x1 = x2; x2 = t
			if y1 > y2:
				t = y1; y1 = y2; y2 = t
			w = x2 - x1
			h = y2 - y1
			if self.fill:
				if config.preferences.cairo_enabled == 0:
					self.properties.ExecuteFill(self, self.fill_rect)
					self.gc.FillArc(x1, y1, w, h, 0, 23040) # 360 * 64
				else:
					self.CairoSetFill()
					self.gc.CairoFillArc(x1+w/2, y1+h/2, w, h)
			if self.line:
				if config.preferences.cairo_enabled == 0:
					self.properties.ExecuteLine(self)
					self.gc.DrawArc(x1, y1, w, h, 0, 23040)
				else:
					try:
						self.CairoSetOutline()
						self.gc.CairoDrawArc(x1+w/2, y1+h/2, w, h)
					except:
						self.properties.ExecuteLine(self)
						self.gc.DrawArc(x1, y1, w, h, 0, 23040)
		else:
			if self.line:
				line = self.activate_line
			else:
				line = None
			if self.fill:
				fill = self.activate_fill
			else:
				fill = None

			if start_angle != end_angle:
				arc = _sketch.approx_arc(start_angle, end_angle, arc_type)
			else:
				arc = circle_path
			# pass rect as None, because trafo2 is not really the
			# viewport transformation
			if config.preferences.cairo_enabled == 0:
				_sketch.draw_multipath(self.gc, trafo2, line, fill,
										self.PushClip, self.PopClip,
										self.ClipRegion, None, (arc,),
										CreateRegion(), self.proc_fill, clip)
				self.draw_ellipse_arrows(trafo, start_angle, end_angle, arc_type,
											rect)
			else:
				if self.fill:
					self.CairoSetFill()
					_sketch.cairo_fill_multipath(self.gc, trafo2, line, fill,
											self.PushClip, self.PopClip,
											self.ClipRegion, None, (arc,),
											CreateRegion(), self.proc_fill, clip)
					
				if self.line:
					try:
						self.CairoSetOutline()
						_sketch.cairo_draw_multipath(self.gc, trafo2, line, fill,
												self.PushClip, self.PopClip,
												self.ClipRegion, None, (arc,),
												CreateRegion(), self.proc_fill, clip)
					except:
						_sketch.draw_multipath(self.gc, trafo2, line, fill,
												self.PushClip, self.PopClip,
												self.ClipRegion, None, (arc,),
												CreateRegion(), self.proc_fill, clip)


	def MultiBezier(self, paths, rect = None, clip = 0):
		if self.line:
			line = self.activate_line
		else:
			line = None
		if self.fill:
			fill = self.activate_fill
		else:
			fill = None
		if config.preferences.cairo_enabled == 0:
			_sketch.draw_multipath(self.gc, self.doc_to_win, line, fill,
									self.PushClip, self.PopClip, self.ClipRegion,
									rect, paths, CreateRegion(), self.proc_fill,
									clip)
		else:
			if self.fill:
				self.CairoSetFill()
				_sketch.cairo_fill_multipath(self.gc, self.doc_to_win, line, fill,
										self.PushClip, self.PopClip, self.ClipRegion,
										rect, paths, CreateRegion(), self.proc_fill,
										clip)
				
			if self.line:
				try:
					self.CairoSetOutline()
					_sketch.cairo_draw_multipath(self.gc, self.doc_to_win, line, fill,
											self.PushClip, self.PopClip, self.ClipRegion,
											rect, paths, CreateRegion(), self.proc_fill,
											clip)
				except:
					_sketch.draw_multipath(self.gc, self.doc_to_win, line, fill,
											self.PushClip, self.PopClip, self.ClipRegion,
											rect, paths, CreateRegion(), self.proc_fill,
											clip)				

		if self.line:
			if config.preferences.cairo_enabled == 1:
				self.cairo_draw = 1
			self.draw_arrows(paths, rect)
			self.cairo_draw = 0

	def DrawBezierPath(self, path, rect = None):
		if self.cairo_draw == 0:
			path.draw_transformed(self.gc, self.doc_to_win, 1, 0, rect)
		else:
			path.cairo_draw_transformed(self.gc, self.doc_to_win, 1, 0, rect)
			

	def FillBezierPath(self, path, rect = None):
		if self.cairo_draw == 0:
			path.draw_transformed(self.gc, self.doc_to_win, 0, 1, rect)
		else:
			path.cairo_draw_transformed(self.gc, self.doc_to_win, 0, 1, rect)

	def draw_text_on_gc(self, gc, text, trafo, font, font_size, cache = None):
		self.PushTrafo()
		try:
			self.Concat(trafo)
			self.Scale(font_size)
			up = self.doc_to_win.DTransform(0, 1)
			if abs(up) >= config.preferences.greek_threshold:
				ptrafo = FlipY(self.doc_to_win)
				xlfd = font.GetXLFD(ptrafo)
				if (ptrafo and (ptrafo.m12 != 0 or ptrafo.m21 != 0
								or ptrafo.m11 > 40 or ptrafo.m11 < 0
								or ptrafo.m22 > 40 or ptrafo.m22 < 0)):
					xlfd = '%s[%s]' % (xlfd, _sketch.xlfd_char_range(text))
				try:
					xfont = self.load_font(xlfd, cache)
				except RuntimeError, val:
					# We must be careful here when reporting this to the
					# user. If warn pops up a message box and the user
					# clicks OK, the window gets another expose event
					# and sketch tries to draw the text again which will
					# also fail. To avoid infinite loops we try to
					# report unknown fonts only once for a given font.
					if not self.unknown_fonts.has_key(font.PostScriptName()):
						warn(USER, _("Cannot load %(font)s:\n%(text)s"),
								font = `xlfd`, text = val)
						self.unknown_fonts[font.PostScriptName()] = 1
					# Use a font that will hopefully be always available.
					# XXX Is there a better way to handle this situation?
					# We might try times roman with the same size and trafo
					xfont = self.load_font('fixed', None)
				gc.SetFont(xfont)

				pos = font.TypesetText(text)
				pos = map(self.DocToWin, pos)
				for i in range(len(text)):
					x, y = pos[i]
					gc.DrawString(x, y, text[i])
			else:
				# 'greek'. XXX is this really necessary. It avoids
				# rendering fonts that are too small to read.
				pos = font.TypesetText(text)
				pos = map(self.DocToWin, pos)
				ux, uy = up
				lx = ux / 2; ly = uy / 2
				uppercase = string.uppercase
				draw = gc.DrawLine # we should draw rectangles...
				for i in range(len(text)):
					x, y = pos[i]
					if text[i] in uppercase:
						draw(x, y, x + ux, y + uy)
					else:
						draw(x, y, x + lx, y + ly)
		finally:
			self.PopTrafo()

	def DrawText(self, text, trafo = None, clip = 0, cache = None):
		if text and self.properties.font:
			if self.fill or clip:
				if self.proc_fill or clip:
					bitmap, bitmapgc = self.create_clip_bitmap()
					self.draw_text_on_gc(bitmapgc, text, trafo,
											self.properties.font,
											self.properties.font_size,
											cache)
					if not clip:
						self.PushClip()
					self.ClipBitmap(bitmap)
					self.properties.ExecuteFill(self, self.fill_rect)
					if not self.proc_fill:
						w, h = bitmap.GetGeometry()[3:5]
						bitmap.CopyPlane(self.widget, self.gc, 0, 0, w, h,
											0, 0, 1)
					if not clip:
						self.PopClip()
				else:
					self.properties.ExecuteFill(self)
					self.draw_text_on_gc(self.gc, text, trafo,
											self.properties.font,
											self.properties.font_size,
											cache)
			elif self.IsOutlineActive():
				# in outline mode, draw text filled with the current
				# outline color, because we can't draw outlined text at
				# the moment. We could draw a rectangle, though. (?)
				self.properties.ExecuteLine(self)
				self.draw_text_on_gc(self.gc, text, trafo,
										self.properties.font,
										self.properties.font_size,
										cache)

	def ResetFontCache(self):
		self.font_cache = {}

	def load_font(self, xlfd, cache):
		font_cache = self.font_cache
		complex_text = self.complex_text
		
		if self.failed_fonts.has_key(xlfd):
			# the same xlfd failed before. use fixed as fallback
			# immediately to avoid delays. some servers apparantly take
			# very long to decide that they can't load a font.
			xlfd = 'fixed'

		if cache and cache.has_key(id(self)):
			old_xlfd, old_font = cache[id(self)]
			if old_xlfd == xlfd:
				font_cache[xlfd] = old_font
				return old_font

		if complex_text is not None:
			cache = complex_text.cache
			key = id(self), complex_text.idx
			if cache.has_key(key):
				old_xlfd, old_font = cache[key]
				if old_xlfd == xlfd:
					font_cache[xlfd] = old_font
					return old_font
			cache = None

		if font_cache is not None and font_cache.has_key(xlfd):
			font = font_cache[xlfd]
		else:
			#print 'load font', xlfd
			try:
				font = self.widget.LoadQueryFont(xlfd)
			except RuntimeError:
				self.failed_fonts[xlfd] = 1
				raise

		if font_cache is not None:
			font_cache[xlfd] = font
		if cache is not None:
			cache[id(self)] = (xlfd, font)
		elif complex_text is not None:
			complex_text.cache[(id(self), complex_text.idx)] = (xlfd, font)

		return font

	complex_text = None
	def BeginComplexText(self, clip = 0, cache = None):
		if self.fill or clip or self.IsOutlineActive():
			if cache is None:
				cache = {}
			if self.proc_fill or clip:
				bitmap, gc = self.create_clip_bitmap()
				self.complex_text = Empty(bitmap = bitmap, gc = gc,
											clip = clip, cache = cache, idx = 0)
			else:
				if self.fill:
					self.properties.ExecuteFill(self)
				else:
					# outline mode
					self.properties.ExecuteLine(self)
				self.complex_text = Empty(gc = self.gc, clip = 0,
											cache = cache, idx = 0)
		else:
			self.complex_text = None

	def DrawComplexText(self, text, trafo, font, font_size):
		if self.complex_text is not None:
			self.draw_text_on_gc(self.complex_text.gc, text, trafo, font,
									font_size)
			self.complex_text.idx = self.complex_text.idx + 1

	def EndComplexText(self):
		if self.complex_text is not None:
			if self.complex_text.clip or self.proc_fill:
				bitmap = self.complex_text.bitmap
				self.PushClip()
				self.ClipBitmap(bitmap)
				self.properties.ExecuteFill(self, self.fill_rect)
				if not self.proc_fill:
					w, h = bitmap.GetGeometry()[3:5]
					bitmap.CopyPlane(self.widget, self.gc, 0, 0, w, h,
										0, 0, 1)
				if not self.complex_text.clip:
					self.PopClip()
		self.complex_text = None

	def create_ximage(self):
		global use_shm_images
		if not self.ximage:
			w = self.widget
			if use_shm_images and not shm_images_supported:
				warn(INTERNAL,
						'tried to use unsupported shared memory images\n')
				use_shm_images = 0
			if use_shm_images:
				try:
					self.ximage = w.ShmCreateImage(w.depth, X.ZPixmap,
													None, w.width, w.height, 1)
				except:
					# Creating a shared memory image failed. Print a
					# message and don't use shmimages again. A likely
					# reason for this is that the test for shmimages in
					# pax succeeded but the ShmCreateImage here fails
					# because the limit for shm segments is too low, as
					# it is by default on Solaris.
					warn(INTERNAL, _("Can't create shared memory image: %s"),
							sys.exc_info()[1])
					use_shm_images = 0
			if not self.ximage:
				self.ximage = self.create_sized_ximage(w.width, w.height)

	def create_sized_ximage(self, width, height):
		w = self.widget
		depth = w.depth
		if depth > 16:
			bpl = 4 * width
		elif depth > 8:
			bpl = ((2 * width + 3) / 4) * 4
		elif depth == 8:
			bpl = ((width + 3) / 4) * 4
		else:
			raise SketchError('unsupported depth for images')
		return w.CreateImage(w.depth, X.ZPixmap, 0, None, width, height,
								32, bpl)


	def DrawImage(self, image, trafo, clip = 0):
		w, h = image.size
		if self.IsOutlineActive():
			self.PushTrafo()
			self.Concat(trafo)
			self.DrawRectangle(Point(0, 0), Point(w, h))
			self.PopTrafo()
			return
		self.create_ximage()
		ximage = self.ximage
		if use_shm_images and self.IsClipping() and self.images_drawn:
			# force a shmimage to be drawn if complex clipping is done
			# or ShmPutImage requests might be in the queue.
			self.widget.Sync()
			self.images_drawn = 0
		llx, lly = self.DocToWin(trafo.offset())
		lrx, lry = self.DocToWin(trafo(w, 0))
		ulx, uly = self.DocToWin(trafo(0, h))
		urx, ury = self.DocToWin(trafo(w, h))
		if llx == ulx and lly == lry:
			if llx < lrx:
				sx = llx;	w = lrx - llx + 1
			else:
				sx = lrx;	w = lrx - llx - 1
			if uly < lly:
				sy = uly;	h = lly - uly + 1
			else:
				sy = lly;	h = lly - uly - 1

			_sketch.copy_image_to_ximage(self.visual, image.im, ximage,
											sx, sy, w, h)
			if w < 0:	w = -w
			if h < 0:	h = -h
			if not clip:
				self.PushClip()
			self.ClipRect((sx, sy, w, h))
		else:
			self.PushTrafo()
			self.Concat(trafo)
			self.Concat(Trafo(1, 0, 0, -1, 0, h))
			inverse = self.win_to_doc
			dtw = self.DocToWin
			ulx, uly = dtw(0, 0)
			urx, ury = dtw(0, h)
			llx, lly = dtw(w, 0)
			lrx, lry = dtw(w, h)
			self.PopTrafo()
			sx = min(ulx, llx, urx, lrx)
			ex = max(ulx, llx, urx, lrx)
			sy = min(uly, lly, ury, lry)
			ey = max(uly, lly, ury, lry)

			if type(self.clip_region) == PaxRegionType:
				cx, cy, cw, ch = self.clip_region.ClipBox()
				cex = cx + cw; cey = cy + ch
				if cx >= ex or cex <= sx or cy >= ey or cey <= sy:
					return
				if cx  > sx and cx  < ex:	sx = cx
				if cex < ex and cex > sx:	ex = cex
				if cy  > sy and cy  < ey:	sy = cy
				if cey < ey and cey > sy:	ey = cey
			w = ex - sx
			h = ey - sy

			region = self.widget.CreateRegion()
			_sketch.transform_to_ximage(self.visual, inverse,
										image.im, ximage, sx, sy, w, h, region)
			if not clip:
				self.PushClip()
			self.ClipRegion(region)

		if sx+w <= 0 or sx >= ximage.width or sy+h <= 0 or sy >= ximage.height:
			if not clip:
				self.PopClip()
			return

		if sx < 0:
			w = w + sx
			sx = 0
		if sx + w > ximage.width:
			w = ximage.width - sx
		if sy < 0:
			h = h + sy
			sy = 0
		if sy + h > ximage.height:
			h = ximage.height - sy

		if use_shm_images:
			self.gc.ShmPutImage(ximage, sx, sy, sx, sy, w, h, 0)
			self.images_drawn = 1
		else:
			self.gc.PutImage(ximage, sx, sy, sx, sy, w, h)
		if not clip:
			self.PopClip()


	def DrawEps(self, data, trafo):
		if not data.image or self.IsOutlineActive():
			w, h = data.Size()
			self.PushTrafo()
			self.Concat(trafo)
			self.DrawRectangle(Point(0, 0), Point(w, h))
			self.PopTrafo()
		else:
			resolution = config.preferences.eps_preview_resolution
			self.DrawImage(data.image, trafo(Scale(72.0 / resolution)))

	#
	#

	def WindowResized(self, width, height):
		self.ximage = None
		SimpleGC.WindowResized(self, width, height)


	#
	#

	def DrawGrid(self, orig_x, orig_y, xwidth, ywidth, rect):
		# Draw a grid with a horitontal width XWIDTH and vertical width
		# YWIDTH whose origin is at (ORIG_X, ORIG_Y). RECT gives the
		# region of the document for which the grid has to be drawn.
		# RECT is usually the parameter of the same name of the
		# Draw/DrawShape methods of the various graphics objects and the
		# document/layer Note: This functions assumes that doc_to_win is
		# in its initial state
		self.SetProperties(self.grid_style)
		xwinwidth = self.LengthToWinFloat(xwidth)
		if not xwinwidth:
			if __debug__:
				pdebug(None, 'GraphicsDevice.DrawGrid: zero winwidth')
			return
		ywinwidth = self.LengthToWinFloat(ywidth)
		if not ywinwidth:
			if __debug__:
				pdebug(None, 'GraphicsDevice.DrawGrid: zero winwidth')
			return
		# make the minimum distance between drawn points at least 5
		# pixels XXX: should be configurable
		if xwinwidth < 5:
			xwinwidth = (int(5.0 / xwinwidth) + 1) * xwinwidth
			xwidth = self.LengthToDoc(xwinwidth)
		if ywinwidth < 5:
			ywinwidth = (int(5.0 / ywinwidth) + 1) * ywinwidth
			ywidth = self.LengthToDoc(ywinwidth)
		startx = int((rect.left - orig_x) / xwidth) * xwidth + orig_x
		starty = int((rect.top - orig_y) / ywidth) * ywidth + orig_y
		winx, winy = self.DocToWinPoint((startx, starty))
		nx = int((rect.right - rect.left) / xwidth) + 2
		ny = int((rect.top - rect.bottom) / ywidth) + 2
		if self.line:
			self.properties.ExecuteLine(self)
		_sketch.DrawGrid(self.gc, winx, winy, xwinwidth, ywinwidth, nx, ny)

	def DrawGuideLine(self, point, horizontal):
		temp_scale=self.scale
		self.scale=1
		if self.line:
			self.properties.ExecuteLine(self)
		self.gc.line_style = X.LineOnOffDash
		self.gc.dashes = 5
		x, y = self.DocToWin(point)
		if horizontal:
			self.gc.DrawLine(0, y, self.widget.width, y)
		else:
			self.gc.DrawLine(x, 0, x, self.widget.height)
		self.gc.line_style = X.LineSolid
		self.scale=temp_scale

	def DrawPageOutline(self, width, height):
		# Draw the outline of the page whose size is given by width and
		# height. The page's lower left corner is at (0,0) and its upper
		# right corner at (width, height) in doc coords. The outline is
		# drawn as a rectangle with a thin shadow.
		self.gc.line_width = 0
		self.gc.line_style = X.LineSolid
		left, bottom = self.DocToWin(0, 0)
		right, top = self.DocToWin(width, height)
		sw = 5	# shadow width	XXX: should be configurable ?
		w = right - left
		h = bottom - top
		self.SetFillColor(StandardColors.gray)
		self.gc.FillRectangles([(left + sw, bottom, w + 1, sw + 1),
								(right, top + sw, sw + 1, h + 1)])
		self.SetFillColor(StandardColors.black)
		self.gc.DrawRectangle(left, top, w, h)




#
# Class InvertingDevice
#
# Draws objects always in outline mode, regardless of the object's
# properties. Also draws with function = GXxor.
#
# This class defines a few additional drawing methods that are used by
# the primitives Rectangle and PolyBezier during interactive creation
# and dragging
#

# DummyLineStyle is needed for the InvertingDevice and the HitTestDevice
class DummyAttr(PropertyStack):
	def ExecuteLine(self, gc):
		pass


dummyLineStyle = DummyAttr(SolidLine(color_0))



class InvertingDevice(GraphicsDevice):

	normal_line_style = X.LineSolid
	handle_line_style = X.LineOnOffDash
	caret_line_style = X.LineSolid
	caret_line_width = 2

	def __init__(self):
		GraphicsDevice.__init__(self)
		self.handle_size = 3
		self.small_handle_size = 2
		self.properties = dummyLineStyle
		self.fill = 0
		self.line = 1
		self.gc = None
		self.font_cache = {}

	def init_gc(self, widget, **gcargs):
		self.visual = color.skvisual
		line_width = config.preferences.editor_line_width
		self.gc = widget.CreateGC(foreground = ~0,
									function = X.GXxor,
									background = 0,
									line_width = line_width,
									line_style = self.normal_line_style)
		self.widget = widget

	# make sure that the properties are not changed
	def SetProperties(self, properties, rect = None):
		pass

	def IsOutlineActive(self):
		return 1

	# Bezier and Line are currently only needed for the bezier objects
	# during a drag
	def Bezier(self, p1, p2, p3, p4):
		dtw = self.DocToWin
		pts = dtw(p1) + dtw(p2) + dtw(p3) + dtw(p4)
		apply(_sketch.DrawBezier, (self.gc,) + pts)

	def Line(self, p1, p2):
		if self.line:
			startx,	starty	= self.DocToWin(p1)
			endx,	endy	= self.DocToWin(p2)
			self.gc.DrawLine(startx, starty, endx, endy)

	# draw a rectangular 'handle' at P. The size of the handle is given
	# by self.handle_size and is always in window coordinates (i.e. is
	# independent of scaling)

	def DrawRectHandle(self, p, filled = 1):
		x, y = self.DocToWin(p)
		size = self.handle_size
		x = x - size
		y = y - size
		if filled:
			self.gc.FillRectangle(x, y, 2 * size + 1, 2 * size + 1)
		else:
			self.gc.DrawRectangle(x, y, 2 * size, 2 * size)

	def DrawSmallRectHandle(self, p, filled = 1):
		x, y = self.DocToWin(p)
		size = self.small_handle_size
		x = x - size
		y = y - size
		if filled:
			self.gc.FillRectangle(x, y, 2 * size + 1, 2 * size + 1)
		else:
			self.gc.DrawRectangle(x, y, 2 * size, 2 * size)

	def DrawCircleHandle(self, p, filled = 1):
		x, y = self.DocToWin(p)
		size = self.handle_size
		x = x - size
		y = y - size
		if filled:
			# 23040 = 360 * 64
			self.gc.FillArc(x, y, 2 * size + 1, 2 * size + 1, 0, 23040)
		else:
			self.gc.DrawArc(x, y, 2 * size, 2 * size, 0, 23040)

	def DrawSmallCircleHandle(self, p, filled = 1):
		x, y = self.DocToWin(p)
		size = self.small_handle_size
		x = x - size
		y = y - size
		if filled:
			# 23040 = 360 * 64
			self.gc.FillArc(x, y, 2 * size + 1, 2 * size + 1, 0, 23040)
		else:
			self.gc.DrawArc(x, y, 2 * size, 2 * size, 0, 23040)

	def DrawSmallRectHandleList(self, pts, filled = 1):
		pts = map(self.doc_to_win.DocToWin, pts)
		size = self.small_handle_size
		size2 = 2 * size
		if filled:
			size = size + 1
		rects = []
		pts.sort()
		lx = ly = None
		for x, y in pts:
			if y != ly or x != lx:
				rects.append((x - size, y - size, size2, size2))
				lx = x
				ly = y
		if rects:
			if filled:
				self.gc.FillRectangles(rects)
			else:
				self.gc.DrawRectangles(rects)

	def DrawHandleLine(self, start, end):
		self.gc.line_style = self.handle_line_style
		self.DrawLine(start, end)
		self.gc.line_style = self.normal_line_style

	def DrawRubberRect(self, start, end):
		self.gc.line_style = self.handle_line_style
		self.DrawRectangle(start, end)
		self.gc.line_style = self.normal_line_style

	def DrawPixmapHandle(self, p, pixmap):
		x, y = self.DocToWin(p)
		width, height = pixmap.GetGeometry()[3:5]
		x = x - width / 2
		y = y - height / 2
		pixmap.CopyPlane(self.widget, self.gc, 0, 0, width, height, x, y, 1)

	def DrawCaretHandle(self, p, up):
		line_width = self.gc.line_width
		self.gc.line_width = self.caret_line_width
		self.gc.line_style = self.caret_line_style
		self.DrawLine(p, p + up)
		self.gc.line_style = self.normal_line_style
		self.gc.line_width = line_width


#
#	Class HitTestDevice
#

pixmap_width_2 = 4
pixmap_width = 2 * pixmap_width_2 + 1


hit_properties = PropertyStack()
hit_properties.SetProperty(fill_pattern = SolidPattern(color_1))
hit_properties.AddStyle(SolidLine(color_1, width = 3))

class HitTestDevice(GraphicsDevice):

	outline_style = hit_properties

	def __init__(self):
		GraphicsDevice.__init__(self)
		self.properties = hit_properties
		self.fill = 1
		self.line = 1
		self.gc = None

	def init_gc(self, widget, **gcargs):
		self.pixmap = widget.CreatePixmap(pixmap_width, pixmap_width, 1)
		self.gc = self.pixmap.CreateGC(foreground = 1, line_width = 3)
		self.visual = color.skvisual

	# make sure that the properties are not changed
	def SetProperties(self, properties, rect = None):
		if properties.HasLine():
			self.line_width = properties.line_width
		else:
			self.line_width = 0

	#
	#
	def SetViewportTransform(self, scale, doc_to_win, win_to_doc):
		GraphicsDevice.SetViewportTransform(self, scale, doc_to_win,
											win_to_doc)
		self.hit_radius_doc = self.LengthToDoc(self.hit_radius)
		hit_properties.SetProperty(line_width = self.hit_radius_doc * 2)
	#
	# Detect various `hits'
	#

	hit_radius = 2

	def SetHitRadius(self, radius):
		self.hit_radius = radius

	def HitRadiusDoc(self):
		return self.LengthToDoc(self.hit_radius)

	def HitRectAroundPoint(self, p):
		rad = self.HitRadiusDoc()
		return Rect(p.x - rad, p.y - rad, p.x + rad, p.y + rad)

	def LineHit(self, start, end, p, line_width = 0):
		radius = self.hit_radius / self.scale
		if line_width:
			w = line_width / 2
			if radius < w:
				radius = w
		# check bounding box
		if p.x < min(start.x, end.x) - radius:
			return 0
		if p.x > max(start.x, end.x) + radius:
			return 0
		if p.y < min(start.y, end.y) - radius:
			return 0
		if p.y > max(start.y, end.y) + radius:
			return 0
		# check if line is hit
		try:
			d = end - start
			len = abs(d)
			if len < 1:
				return abs(start.x - p.x) <= radius \
						and abs(start.y - p.y) <= radius
			off = p - start
			dist = abs((float(off.x) * d.y - float(off.y) * d.x) / len)
			linepos = (off * d) / len
			return dist <= radius and linepos > 0 and linepos < len
		except OverflowError:
			warn(INTERNAL, 'HitTestDevice.LineHit: start = %s end = %s p = %s',
					start, end, p)
			return 0

	def ParallelogramHit(self, p, trafo, maxx, maxy, filled, properties=None,
							ignore_outline_mode = 0):
		filled = filled and (ignore_outline_mode or not self.outline_mode)
		if filled:
			try:
				inverse = trafo.inverse()
				x, y = inverse(p)
				return 0 <= x <= maxx and 0 <= y <= maxy
			except SingularMatrix:
				if properties is not None and properties.HasLine():
					properties = defaultLineStyle
					return self.ParallelogramHit(p, trafo, maxx, maxy,
													0, properties)

		if self.outline_mode or (properties is not None
									and properties.HasLine()):
			p1 = trafo.offset()
			p2 = trafo(0, maxy)
			p3 = trafo(maxx, 0)
			p4 = trafo(maxx, maxy)
			if self.outline_mode:
				line_width = 0
			else:
				line_width = properties.line_width
			return self.LineHit(p1, p2, p, line_width)\
					or self.LineHit(p1, p3, p, line_width) \
					or self.LineHit(p2, p4, p, line_width) \
					or self.LineHit(p3, p4, p, line_width)

	def SimpleEllipseHit(self, p, trafo, start_angle, end_angle, arc_type,
							properties, filled, ignore_outline_mode = 0):
		# Hmm, the ellipse is not that simple anymore, maybe we should
		# change the name?
		filled = filled and (ignore_outline_mode or not self.outline_mode)
		try:
			inverse = trafo.inverse()
			p2 = inverse(p)
			dist, phi = p2.polar()
			has_line = properties.HasLine() or self.outline_mode
			if has_line:
				# Check whether p is on the outline of the complete
				# ellipse. This check is not entirely correct, but it
				# works well enough for now.
				if not self.outline_mode:
					line_width = properties.line_width
				else:
					line_width = 0
				d = max(line_width / 2, self.HitRadiusDoc())
				d = abs(inverse.DTransform(Point(d, 0)))
				border_hit = abs(1.0 - dist) < d
			else:
				border_hit = 0
			if start_angle == end_angle:
				# The most common case: a complete ellipse
				if filled and dist <= 1.0:
					# p is inside of the ellipse -> Hit!
					return 1
				# Either ellipse is not filled or dist > 1.0. NOw it
				# only depends on the outline.
				return border_hit
			else:
				# The ellipse is not complete. Now it depends on the
				# arc_type.
				if phi < 0:
					phi = phi + pi + pi # map phi into the range 0 - 2*PI
				if start_angle < end_angle:
					between = start_angle <= phi <= end_angle
				else:
					between = start_angle <= phi or phi <= end_angle
				center = trafo.offset()
				start = Polar(start_angle)
				end = Polar(end_angle)
				if arc_type == ArcPieSlice:
					if between:
						# p is somewhere in the painted sector. Just
						# like for a full ellipse:
						if filled and dist <= 1:
							return 1
						return border_hit
					else:
						# p is outside of the painted sector. It might
						# still be on the lines:
						if has_line:
							if (self.LineHit(center, trafo(start), p,
												line_width)
								or self.LineHit(center, trafo(end), p,
												line_width)):
								return 1
						# no line was hit
						return 0
				else:
					# ArcArc or ArcChord.
					if filled:
						# this is identical for both arc_types.
						# Strategy: p is inside of the ellipse if it is
						# in the intersection of the full ellipse the
						# half plane defined by the line through start
						# and end (the plane to the left of the vector
						# (start - end)).
						v = start - end
						d = p2 - end
						in_plane = (v.x * d.y - v.y * d.x) > 0
						if dist <= 1 and in_plane:
							return 1
					#
					if between and border_hit:
						return 1
					if has_line and arc_type == ArcChord:
						return self.LineHit(trafo(start), trafo(end), p,
											line_width)
			return 0
		except SingularMatrix:
			# ellipse degenerates into a line
			# XXX we should use the eigenvectors. The following code is
			# incorrect.
			start = trafo.offset()
			right = Point(trafo.m11, trafo.m21)
			up = Point(trafo.m12, trafo.m22)
			if abs(up) > abs(right):
				dir = up
			else:
				dir = right
			return self.LineHit(start - dir, start + dir, p,
								properties.line_width)

	def MultiBezierHit(self, paths, p, properties, filled,
						ignore_outline_mode = 0):
		x, y = self.DocToWin(p)
		filled = filled and (ignore_outline_mode or not self.outline_mode)
		result = _sketch.test_transformed(paths, self.doc_to_win, x, y,
											filled)
		if properties.HasLine():
			line_width = properties.line_width
		else:
			line_width = 0
		if result or self.outline_mode or self.LengthToWin(line_width) <= 1:
			return result
		odtw = self.doc_to_win
		self.doc_to_win = Trafo(odtw.m11, odtw.m21, odtw.m12, odtw.m22,
								-x + pixmap_width_2 + odtw.v1,
								-y + pixmap_width_2 + odtw.v2)
		top_left = self.WinToDoc(x - pixmap_width_2 - 1,
									y - pixmap_width_2 - 1)
		bot_right = self.WinToDoc(x + pixmap_width_2 + 1,
									y + pixmap_width_2 + 1)
		rect = Rect(top_left, bot_right)
		self.gc.function = X.GXclear
		self.gc.FillRectangle(0, 0, pixmap_width + 1, pixmap_width + 1)
		self.gc.function = X.GXcopy
		self.fill = 0
		line_width = max(line_width, hit_properties.line_width)
		undo = self.properties.SetProperty(line_width = line_width,
											line_pattern = SolidPattern(color_1))
		self.MultiBezier(paths, rect)
		self.doc_to_win = odtw
		Undo(undo)
		self.fill = 1
		return _sketch.GetPixel(self.gc, pixmap_width_2, pixmap_width_2)


#
#	Initialization that can only be done after widgets were realized
#

_init_from_widget_done = 0

def check_for_shm_images(widget):
	global shm_images_supported
	shm_images_supported = 0
	try:
		img = widget.ShmCheckExtension()
	except RuntimeError, exc:
		print "Exception in ShmCheckExtension:", exc
		img = None
	if img is not None:
		if img.depth not in (15, 16, 24, 32, 8):
			# XXX: warn
			print 'depth =', img.depth
			return

		if img.format != X.ZPixmap:
			# XXX: warn
			print 'format =', img.format
			return

		shm_images_supported = 1


def InitFromWidget(widget):
	global _init_from_widget_done, use_shm_images
	if not _init_from_widget_done:
		color.InitFromWidget(widget) # make certain that color is initialized
		check_for_shm_images(widget)
		if shm_images_supported:
			warn(INTERNAL, 'shared memory images supported')
			use_shm_images = 1
		else:
			warn(INTERNAL, 'shared memory images not supported')
			use_shm_images = 0
	_init_from_widget_done = 1

