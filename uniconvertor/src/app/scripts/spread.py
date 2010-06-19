# -*- coding: utf-8 -*-

# Sketch script for spreading selected objects ("distribute" in XFig)
# (c) 2000 Michael Loßin
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
#
# these are based on abut_*.py

from app import _, Point
import app.Scripting


# spread objects horizontally (cascade left)

def spread_h_casc_l(context):
	pos = []
	for obj in context.document.SelectedObjects():
		pos.append((obj.coord_rect.left, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		left1, ob = pos[0]
		left2, ob = pos[-1]
		skip = (left2 - left1) / l
		next = left1 + skip
		for left, obj in pos[1:-1]:
			obj.Translate(Point(next - left, 0))
			next = next + skip

app.Scripting.AddFunction('spread_h_casc_l',
								_("Spread Horizontal (cascade left)"),
								spread_h_casc_l, menu = _("Arrange"))


# spread objects horizontally (cascade right)

def spread_h_casc_r(context):
	pos = []
	for obj in context.document.SelectedObjects():
		pos.append((obj.coord_rect.right, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		right1, ob = pos[0]
		right2, ob = pos[-1]
		skip = (right2 - right1) / l
		next = right1 + skip
		for right, obj in pos[1:-1]:
			obj.Translate(Point(next - right, 0))
			next = next + skip

app.Scripting.AddFunction('spread_h_casc_r',
								_("Spread Horizontal (cascade right)"),
								spread_h_casc_r, menu = _("Arrange"))


# spread objects horizontally (equidistant centers)

def spread_h_center(context):
	pos = []
	for obj in context.document.SelectedObjects():
		rect = obj.coord_rect
		pos.append(((rect.left + rect.right) / 2, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		center1, ob = pos[0]
		center2, ob = pos[-1]
		gap = (center2 - center1) / l
		next = center1 + gap
		for center, obj in pos[1:-1]:
			obj.Translate(Point(next - center, 0))
			next = next + gap

app.Scripting.AddFunction('spread_h_center',
								_("Spread Horizontal (center)"),
								spread_h_center, menu = _("Arrange"))


# spread objects horizontally (gaps/overlaps of equal width)

def spread_h_bbox(context):
	pos = []
	sum = 0
	for obj in context.document.SelectedObjects():
		rect = obj.coord_rect
		width = rect.right - rect.left
		pos.append((rect.left, width, obj))
		sum = sum + width
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		start, width1, ob = pos[0]
		end, width2, ob = pos[-1]
		gap = (end + width2 - start - sum) / l
		next = start + width1 + gap
		for left, width, obj in pos[1:-1]:
			obj.Translate(Point(next - left ,0))
			next = next + width + gap

app.Scripting.AddFunction('spread_h_bbox', _("Spread Horizontal (bbox)"),
								spread_h_bbox, menu = _("Arrange"))


# spread objects vertically (cascade bottom)

def spread_v_casc_b(context):
	pos = []
	for obj in context.document.SelectedObjects():
		pos.append((obj.coord_rect.bottom, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		pos.reverse()
		bottom1, ob = pos[0]
		bottom2, ob = pos[-1]
		skip = (bottom1 - bottom2) / l
		next = bottom1 - skip
		for bottom, obj in pos[1:-1]:
			obj.Translate(Point(0, next - bottom))
			next = next - skip

app.Scripting.AddFunction('spread_v_casc_b',
								_("Spread Vertical (cascade bottom)"),
								spread_v_casc_b, menu = _("Arrange"))


# spread objects vertically (cascade top)

def spread_v_casc_t(context):
	pos = []
	for obj in context.document.SelectedObjects():
		pos.append((obj.coord_rect.top, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		pos.reverse()
		top1, ob = pos[0]
		top2, ob = pos[-1]
		skip = (top1 - top2) / l
		next = top1 - skip
		for top, obj in pos[1:-1]:
			obj.Translate(Point(0, next - top))
			next = next - skip

app.Scripting.AddFunction('spread_v_casc_t',
								_("Spread Vertical (cascade top)"),
								spread_v_casc_t, menu = _("Arrange"))


# spread objects vertically (equidistant centers)

def spread_v_center(context):
	pos = []
	for obj in context.document.SelectedObjects():
		rect = obj.coord_rect
		pos.append(((rect.top + rect.bottom) / 2, obj))
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		pos.reverse()
		center1, ob = pos[0]
		center2, ob = pos[-1]
		gap = (center1 - center2) / l
		next = center1 - gap
		for center, obj in pos[1:-1]:
			obj.Translate(Point(0, next - center))
			next = next - gap

app.Scripting.AddFunction('spread_v_center', _("Spread Vertical (center)"),
								spread_v_center, menu = _("Arrange"))


# spread objects vertically (gaps/overlaps of equal height)

def spread_v_bbox(context):
	pos = []
	sum = 0
	for obj in context.document.SelectedObjects():
		rect = obj.coord_rect
		height = rect.top - rect.bottom
		pos.append((rect.top, height, obj))
		sum = sum + height
	l = len(pos) - 1
	if l > 1:
		pos.sort()
		pos.reverse()
		start, height1, ob = pos[0]
		end, height2, ob = pos[-1]
		gap = (start - end + height2 - sum) / l
		next = start - height1 - gap
		for top, height, obj in pos[1:-1]:
			obj.Translate(Point(0, next - top))
			next = next - height - gap

app.Scripting.AddFunction('spread_v_bbox', _("Spread Vertical (bbox)"),
								spread_v_bbox, menu = _("Arrange"))
