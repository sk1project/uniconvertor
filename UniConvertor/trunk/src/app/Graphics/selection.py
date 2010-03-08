# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


# Classes for handling selections. These include classes that represent
# lists of selected objects and classes that represent the combined
# bounding rectangle of all selected objects. The user can interact in
# the usual fashion with these selection rects to transform (translate,
# rotate, scale, shear) the selected objects.


import operator, math
from types import ListType, InstanceType, TupleType
import time

from sk1libs.utils import flatten

#from app.UI.skpixmaps import pixmaps
from app.events.warn import pdebug, warn, INTERNAL
from app.conf import const
from app.conf.const import SelectSet

from app import _, Point, Polar, Rect, UnionRects, RectType, Identity, \
     Trafo, TrafoType, Rotation, CreateListUndo, NullUndo

import handle
from base import SelectAndDrag, Bounded
import selinfo

from math import floor, ceil

class SelRectBase(SelectAndDrag, Bounded):

    #
    # Handle/selection numbers:
    #	sx		ex
    #	1	2	3	sy
    #
    #	8		4
    #
    #	7	6	5	ey
    #
    #	-1: whole object

    selTop	= (1, 2, 3)
    selBottom	= (7, 6, 5)
    selLeft	= (1, 8, 7)
    selRight	= (3, 4, 5)
    selAspect	= (1, 3, 5, 7)	# constrain aspect ratio for these selections

    handle_idx_to_sel = (7, 6, 5, 8, 4, 1, 2, 3)

    def __init__(self):
	SelectAndDrag.__init__(self)
	self.outline_object = None

    def update_rects(self):
	self.coord_rect = Rect(self.start, self.end)
	self.bounding_rect = self.coord_rect

    def SetOutlineObject(self, obj):
	# XXX: this is a hack...
	if obj is not None:
	    if obj.is_Compound:
		objects = obj.GetObjects()
		if len(objects) == 1:
		    obj = objects[0]
		else:
		    return
	    if not obj.is_Compound and not obj.is_Text:
		self.outline_object = obj


class SelectionRectangle(SelRectBase):

    def __init__(self, rect, anchor = None):
	SelRectBase.__init__(self)
	if type(rect) == RectType:
	    self.start = Point(rect.left, rect.bottom)
	    self.end = Point(rect.right, rect.top)
	    self.Normalize()
	    self.anchor = anchor
	else:
	    # assume type Point and interactive creation
	    self.start = rect
	    self.end = rect
	    self.anchor = None
	    self.selection = 5

    def DrawDragged(self, device, partially):
	sel = self.selection

	if sel == -1:
	    sx, sy = self.start + self.off
	    ex, ey = self.end + self.off
	else:
	    if sel in self.selTop:
		sy = self.drag_cur.y
	    else:
		sy = self.start.y

	    if sel in self.selBottom:
		ey = self.drag_cur.y
	    else:
		ey = self.end.y

	    if sel in self.selLeft:
		sx = self.drag_cur.x
	    else:
		sx = self.start.x

	    if sel in self.selRight:
		ex = self.drag_cur.x
	    else:
		ex = self.end.x

	if sx > ex:
	    tmp = sx; sx = ex; ex = tmp
	if sy < ey:
	    tmp = sy; sy = ey; ey = tmp

	device.DrawRubberRect(Point(sx, sy), Point(ex, ey))

    def ButtonDown(self, p, button, state):
	SelectAndDrag.DragStart(self, p)
	sel = self.selection
	if sel == -1:
	    if self.anchor: #XXX shouldn't this be 'if self.anchor is not None'
		start = self.anchor
	    else:
		start = self.start
	    self.drag_start = self.drag_cur = start
	    return (p - start, self.coord_rect.translated(-start))
	ds_x , ds_y = (self.start + self.end) / 2
	if sel in self.selLeft:
	    ds_x = self.start.x
	if sel in self.selTop:
	    ds_y = self.start.y
	if sel in self.selRight:
	    ds_x = self.end.x
	if sel in self.selBottom:
	    ds_y = self.end.y
	self.drag_cur = self.drag_start = ds = Point(ds_x, ds_y)
	self.init_constraint()
	return p - ds

    def init_constraint(self):
	pass

    def apply_constraint(self, p, state):
	return p

    def MouseMove(self, p, state):
	p = self.apply_constraint(p, state)
	SelectAndDrag.MouseMove(self, p, state)

    def compute_endpoints(self):
	cur = self.drag_cur
	start = self.start
	end = self.end
	sel = self.selection
	if sel in self.selTop:
	    start = Point(start.x, cur.y)
	if sel in self.selBottom:
	    end	  = Point(end.x,   cur.y)
	if sel in self.selLeft:
	    start = Point(cur.x, start.y)
	if sel in self.selRight:
	    end = Point(cur.x, end.y)
	if sel == -1:
	    start = start + self.off
	    end = end + self.off
        return start, end

    def ButtonUp(self, p, button, state):
	p = self.apply_constraint(p, state)
	SelectAndDrag.DragStop(self, p)
	cur = self.drag_cur
	oldstart = self.start
	oldend = self.end
	start, end = self.compute_endpoints()
	self.start = start
	self.end = end
	result = self.ComputeTrafo(oldstart, oldend, start, end)
	self.Normalize()
	return result

    def ComputeTrafo(self, oldStart, oldEnd, start, end):
	pass

    def Normalize(self):
	sx, sy = self.start
	ex, ey = self.end
	if sx > ex:
	    sx, ex = ex, sx
	if sy > ey:
	    sy, ey = ey, sy
	self.start = Point(sx, sy)
	self.end = Point(ex, ey)

    def Hit(self, p, rect, device):
	pass

    def Select(self):
	self.selection = -1

    def SelectPoint(self, p, rect, device, mode = SelectSet):
	if p:
	    self.selection = 0
	else:
	    self.selection = -1
	return self.selection

    def SelectHandle(self, handle, mode = SelectSet):
	self.selection = self.handle_idx_to_sel[handle.index]

    def GetHandles(self):
	sx = self.start.x
	sy = self.start.y
	ex = self.end.x
	ey = self.end.y
	x2 = (sx + ex) / 2
	y2 = (sy + ey) / 2
	return map(handle.MakeOffsetHandle,
		   [Point(sx, ey),	Point(x2, ey),	Point(ex, ey),
		    Point(sx, y2),			Point(ex, y2),
		    Point(sx, sy),	Point(x2, sy),	Point(ex, sy)],
		   [(-1,  1),		(0,  1),	( 1,  1),
		    (-1,  0),				( 1,  0),
		    (-1, -1),		(0, -1),	( 1, -1)])



class Selection(Bounded):

    is_EditSelection = 0

    _lazy_attrs = Bounded._lazy_attrs.copy()
    _lazy_attrs['rect'] = 'update_rectangle'
    
    def __init__(self, copy_from = None):
	if copy_from is not None:
	    if type(copy_from) == ListType:
		self.objects = copy_from[:]
	    else:
		# assume copy_from is another instance of a selection class
		self.objects = copy_from.objects
		self.coord_rect = copy_from.coord_rect
		self.bounding_rect = copy_from.bounding_rect
		self.anchor = copy_from.anchor

	else:
	    self.objects = []
	    self.anchor = None

    def normalize(self):
	# make sure that self.objects contains no object more than once
	# and that no two objects have a direct or indirect parent/child
	# relationship.
	objs = self.objects
	changed = 0
	if len(objs) > 1:
	    objs.sort()
	    last_info, obj = objs[-1]
	    for idx in range(len(objs) - 2, -1, -1):
		info, obj = objs[idx]
		if info == last_info:
		    del objs[idx]
		    changed = 1
		    continue
		if len(info) < len(last_info):
		    while info == last_info[:len(info)]:
			del objs[idx + 1]
			changed = 1
			if idx + 1 < len(objs):
			    last_info = objs[idx + 1][0]
			else:
			    break
		last_info = info
	return changed

    def update_selinfo(self):
        objs = self.objects
        for i in range(len(objs)):
            objs[i] = objs[i][-1].SelectionInfo()

    def SetSelection(self, info):
	old_objs = self.objects
	if info:
	    if type(info) == ListType:
		self.objects = info
		self.objects.sort()
	    else:
		self.objects = [info]
	else:
	    self.objects = []
	self.del_lazy_attrs()
	return old_objs != self.objects

    def SetSelectionTree(self, info):
	return self.SetSelection(selinfo.tree_to_list(info))

    def Add(self, info):
	if not info:
	    return 0
	if self.TestSubtract(info)==1:
		return self.Subtract(info)	
	old_len = len(self.objects)
	if type(info) == ListType:
	    self.objects = self.objects + info
	elif info:
	    self.objects.append(info)
	changed = self.normalize()
	self.del_lazy_attrs()
	return changed or old_len != len(self.objects)
	
    def TestSubtract(self, info):
    	result=0
	old_len = len(self.objects)
	if type(info) != ListType:
	    info = [info]
	objects = self.objects
	for item in info:
	    if item in objects:
		result=1
	return result

    def Subtract(self, info):
	if not info:
	    return 0
	old_len = len(self.objects)
	if type(info) != ListType:
	    info = [info]
	objects = self.objects
	for item in info:
	    if item in objects:
		objects.remove(item)
	self.del_lazy_attrs()
	return old_len != len(self.objects)

    def GetObjects(self):
	return map(operator.getitem, self.objects, [-1] * len(self.objects))

    def GetInfo(self):
	return self.objects

    def GetInfoTree(self):
	return selinfo.list_to_tree(self.objects)

    def Depth(self):
	if self.objects:
	    lengths = map(len, map(operator.getitem, self.objects,
				   [0] * len(self.objects)))
	    lmin = min(lengths)
	    lmax = max(lengths)
	    if lmin == lmax:
		return lmin
	    return (lmin, lmax)
	return 0

    def IsSingleDepth(self):
	if self.objects:
	    return type(self.Depth()) != TupleType
	return 1

    def GetPath(self):
	if len(self.objects) == 1:
	    return self.objects[0][0]
	return ()

    def for_all(self, func):
	return map(func, self.GetObjects())

    def ForAllUndo(self, func):
	undoinfo = self.for_all(func)
	self.del_lazy_attrs()
	if len(undoinfo) == 1:
	    undoinfo = undoinfo[0]
	if type(undoinfo) == ListType:
	    return CreateListUndo(undoinfo)
	return undoinfo

    def ForAllUndo2(self, method, *args):
	t = time.clock()
	methods = map(getattr, self.GetObjects(), [method] * len(self.objects))
	#print time.clock() - t,
	#undoinfo = self.for_all(func)
	undoinfo = map(apply, methods, [args] * len(methods))
	#print time.clock() - t
	self.del_lazy_attrs()
	if len(undoinfo) == 1:
	    undoinfo = undoinfo[0]
	if type(undoinfo) == ListType:
	    return CreateListUndo(undoinfo)
	return undoinfo

    def __len__(self):
	return len(self.objects)

    __nonzero__ = __len__

    def update_rects(self):
	objects = self.GetObjects()
	boxes = map(lambda o: o.coord_rect, objects)
	if boxes:
	    self.coord_rect = reduce(UnionRects, boxes)
	else:
	    self.coord_rect = None
	boxes = map(lambda o: o.bounding_rect, objects)
	if boxes:
	    self.bounding_rect = reduce(UnionRects, boxes)
	else:
	    self.bounding_rect = None
	if len(objects) == 1:
	    self.anchor = objects[0].LayoutPoint()
	else:
	    self.anchor = None

    def ChangeRect(self):
	return self.bounding_rect

    def ResetRectangle(self):
	self.del_lazy_attrs()

    def Hit(self, p, rect, device):
	test = rect.overlaps
	for obj in self.GetObjects():
	    if test(obj.bounding_rect):
		if obj.Hit(p, rect, device):
		    return 1
	return 0

    def DragCancel(self):
	self.rect.DragCancel()

    def GetHandles(self):
	rect_handles = self.rect.GetHandles()
	multiple = len(self.objects) > 1
	handles = flatten(self.for_all(lambda o, m = multiple:
				       o.GetObjectHandle(m)))
	rect_handles.append(handle.MakeObjectHandleList(handles))
	return rect_handles

    def CallObjectMethod(self, aclass, methodname, args):
	if len(self.objects) == 1:
	    obj = self.objects[0][-1]
	    if not isinstance(obj, aclass):
		return NullUndo
	    try:
		method = getattr(obj, methodname)
	    except AttributeError:
		return NullUndo

	    undo = apply(method, args)
	    if undo is None:
		undo = NullUndo
	    return undo
	return NullUndo

    def GetObjectMethod(self, aclass, method):
	if len(self.objects) == 1:
	    obj = self.objects[0][-1]
	    if isinstance(obj, aclass):
		try:
		    return getattr(obj, method)
		except AttributeError:
		    pass
	return None

    def InfoText(self):
	# Return a string describing the selected object(s)
        result = _("No Selection")
	if self.objects:
	    sel_info = self.objects
	    br = self.coord_rect
	    hor_sel=round((br.right - br.left)/.283465)/10
	    ver_sel=round((br.top - br.bottom)/.283465)/10
#             hor_sel=ceil(floor(10**3*(br.right - br.left)/2.83465)/10)/100
#             ver_sel=ceil(floor(10**3*(br.top - br.bottom)/2.83465)/10)/100
	    document = sel_info[0][1].document
	    if len(sel_info) == 1:
                path, obj = sel_info[0]
                dict = {'layer': document[path[0]].Name()}
		info = obj.Info()
                if type(info) == TupleType:
                    dict.update(info[1])
                    # the %% is correct here. The result has to be a
                    # %-template itself.
                    text = _("%s on `%%(layer)s'") % info[0]+"\n Selection size: "+str(hor_sel)+" x "+str(ver_sel) +" mm"###
                else:
                    dict['object'] = info
                    text = _("%(object)s on `%(layer)s'")+"\n Selection size: "+str(hor_sel)+" x "+str(ver_sel) +" mm"    ###
                result = text, dict
	    else:
		layer = sel_info[0][0][0]
		if layer == sel_info[-1][0][0]:
		    # a single layer
		    layer_name = document.layers[layer].Name()
		    result = _("%(number)d objects on `%(layer)s'") \
                             % {'number':len(sel_info), 'layer':layer_name}
	 	    result = result + "\n Selection size: "+str(hor_sel)+" x "+str(ver_sel) +" mm"
		else:
		    result = _("%d objects on several layers") % len(sel_info)+"\n Selection size: "+str(hor_sel)+" x "+str(ver_sel) +" mm"  ###
	return result

    def CurrentInfoText(self):
        return ''

    def _dummy(self, *args):
	pass

    Hide	 = _dummy
    DragStart	 = None
    DragMove	 = None
    DragStop	 = None
    Show	 = _dummy
    Hide	 = _dummy
    SelectPoint	 = _dummy
    SelectHandle = _dummy

    drag_mask = SelectAndDrag.drag_mask



class SizeRectangle(SelectionRectangle):

    def init_constraint(self):
	sel = self.selection
	if sel == 1:
	    self.reference = tuple(self.end)
	elif sel == 3:
	    self.reference = (self.start.x, self.end.y)
	elif sel == 5:
	    self.reference = tuple(self.start)
	elif sel == 7:
	    self.reference = (self.end.x, self.start.y)
	else:
	    return
	width = abs(self.start.x - self.end.x)
	height = abs(self.start.y - self.end.y)
	if width >= 1e-10:
	    self.aspect = height / width
	else:
	    self.aspect = None

    def apply_constraint(self, p, state):
	if state:
	    if self.selection in self.selAspect:
		ref_x, ref_y = self.reference
		aspect = self.aspect
		if aspect is None:
		    # width is 0
		    p = Point(self.drag_start.x, p.y)
		else:
		    w = p.x - ref_x
		    h = p.y - ref_y
		    if w == 0:
			w = 0.00001
		    a = h / w
		    if a > 0:
			sign = 1
		    else:
			sign = -1
		    if abs(a) > aspect:
			h = sign * w * aspect
		    else:
			w = sign * h / aspect
		    p = Point(ref_x + w, ref_y + h)
# 	if state & const.AlternateMask:
# 		pi4 = math.pi / 4
# 		off = p - self.drag_start
#                 d = Polar(pi4 * round(math.atan2(off.y, off.x) / pi4))
#                 p = self.drag_start + (off * d) * d
# 		print 'ALT'	
	if state & const.ConstraintMask:# and self.selection == -1:
		pi4 = math.pi / 4
		off = p - self.drag_start
                d = Polar(pi4 * round(math.atan2(off.y, off.x) / pi4))
                p = self.drag_start + (off * d) * d
	return p

    def ButtonDown(self, p, button, state):
        self.trafo = Identity
        return SelectionRectangle.ButtonDown(self, p, button, state)

    def MouseMove(self, p, state):
	p = self.apply_constraint(p, state)
	SelectAndDrag.MouseMove(self, p, state)
        start, end = self.compute_endpoints()
        text, self.trafo = self.ComputeTrafo(self.start, self.end, start, end)

    def ComputeTrafo(self, oldStart, oldEnd, start, end):
	oldDelta = oldEnd - oldStart
	delta	 = end - start
	if self.selection == -1:
	    # a translation.
	    return _("Move Objects"), start - oldStart
	else:
	    try:
		m11 = delta.x / oldDelta.x
	    except ZeroDivisionError:
		m11 = 0
		if __debug__:
		    pdebug(None, 'ComputeTrafo: ZeroDivisionError')
	    try:
		m22 = delta.y / oldDelta.y
	    except ZeroDivisionError:
		m22 = 0
		if __debug__:
		    pdebug(None, 'ComputeTrafo: ZeroDivisionError')
	    offx = start.x - m11 * oldStart.x
	    offy = start.y - m22 * oldStart.y
	    return _("Resize Objects"), Trafo(m11, 0, 0, m22, offx, offy)

    def DrawDragged(self, device, partial):
	SelectionRectangle.DrawDragged(self, device, partial)
	if self.outline_object is not None:
	    trafo = self.trafo
	    device.PushTrafo()
	    if type(trafo) == TrafoType:
		device.Concat(trafo)
	    else:
		device.Translate(trafo.x, trafo.y)
	    self.outline_object.DrawShape(device)
	    device.PopTrafo()

    def CurrentInfoText(self):
        t = self.trafo
        data = {}
        if type(t) == TrafoType:
            x = t.m11
            y = t.m22
            #if round(x, 3) == round(y, 3):
            #    text = _("Uniform Scale %(factor)[factor]")
            #    data['factor'] = x
            #else:
	    br = self.coord_rect
            hor_sel=ceil(floor(10**3*x*(br.right - br.left)/2.83465)/10)/100
            ver_sel=ceil(floor(10**3*y*(br.top - br.bottom)/2.83465)/10)/100
            text = _("Scale %(factorx)[factor], %(factory)[factor]")
	    text = text +"\n Changing size to: "+str(hor_sel)+" x "+str(ver_sel) +" mm"
            data['factorx'] = x
            data['factory'] = y
        else:
            text = _("Move %(x)[length], %(y)[length]")
            data['x'] = t.x
            data['y'] = t.y
        return text, data



class SizeSelection(Selection):

    def __init__(self, arg = None):
	Selection.__init__(self, arg)

    def update_rectangle(self):
	if self:
	    self.rect = SizeRectangle(self.coord_rect, self.anchor)
	else:
	    self.rect = SizeRectangle(Rect(0, 0, 0, 0))

    def ButtonDown(self, p, button, state):
	if len(self.objects) == 1:
	    self.rect.SetOutlineObject(self.objects[0][-1])
	return self.rect.ButtonDown(p, button, state)

    def MouseMove(self, p, state):
	self.rect.MouseMove(p, state)

    def ButtonUp(self, p, button, state, forget_trafo = 0):
	self.rect.SetOutlineObject(None)
	undo_text, trafo = self.rect.ButtonUp(p, button, state)
	if forget_trafo:
	    return None, None
	t = time.clock()
	if type(trafo) == TrafoType:
	    #undo = self.ForAllUndo(lambda o, t = trafo: o.Transform(t))
	    undo = self.ForAllUndo2('Transform', trafo)
	else:
	    # trafo is point representing a translation
	    undo = self.ForAllUndo2('Translate', trafo)
	#print 'transform/translate', time.clock() - t
	self.del_lazy_attrs()
	return undo_text, undo

    def Show(self, device, partially = 0):
	self.rect.Show(device, partially)

    def Hide(self, device, partially = 0):
	self.rect.Hide(device, partially)

    def DrawDragged(self, device, partial):
	self.rect.DrawDragged(device, partial)

    def SelectPoint(self, p, rect, device, mode = SelectSet):
	if not self.rect.SelectPoint(p, rect, device, mode):
	    if self.Hit(p, rect, device):
		self.rect.Select()

    def SelectHandle(self, handle, mode = SelectSet):
	self.rect.SelectHandle(handle, mode)

    def Hit(self, p, rect, device):
	if self.objects:
	    return (rect.overlaps(self.bounding_rect)
		    and Selection.Hit(self, p, rect, device))
	return 0

    def CurrentInfoText(self):
        return self.rect.CurrentInfoText()

class TrafoRectangle(SelRectBase):

    selTurn = [1, 3, 5, 7]
    selShear = [2, 4, 6, 8]
    selCenter = 100

    def __init__(self, rect, center = None):
	SelRectBase.__init__(self)
	self.start = Point(rect.left, rect.bottom)
	self.end = Point(rect.right, rect.top)
	if center is None:
	    self.center = rect.center()
	else:
	    self.center = center


    def compute_trafo(self, state = 0):
	sel = self.selection
	if sel in self.selTurn:
	    # rotation
	    vec = self.drag_cur - self.center
	    angle = math.atan2(vec.y, vec.x)
	    angle = angle - self.start_angle + 2 * math.pi
	    if state & const.ConstraintMask:
		pi12 = math.pi / 12
		angle = pi12 * int(angle / pi12 + 0.5)
            self.trafo = Rotation(angle, self.center)
            self.trafo_desc = (1, angle)
	elif sel in self.selShear:
	    if sel in (2,6):
		# horiz. shear
		height = self.drag_start.y - self.reference
		if height:
		    ratio = self.off.x / height
		    self.trafo = Trafo(1, 0, ratio, 1,
                                       - ratio * self.reference, 0)
                    self.trafo_desc = (2, ratio)
	    else:
		# vert. shear
		width = self.drag_start.x - self.reference
		if width:
		    ratio = self.off.y / width
		    self.trafo = Trafo(1, ratio, 0, 1, 0,
                                       - ratio * self.reference)
                    self.trafo_desc = (3, ratio)

    def DrawDragged(self, device, partially):
	sel = self.selection
	if sel == self.selCenter:
		pass
	    #device.DrawPixmapHandle(self.drag_cur, pixmaps.Center)
	else:
	    trafo = self.trafo
	    if trafo:
		device.PushTrafo()
		device.Concat(trafo)
		device.DrawRubberRect(self.start, self.end)
		if self.outline_object is not None:
		    self.outline_object.DrawShape(device)
		device.PopTrafo()

    def ButtonDown(self, p, button, state):
	self.drag_state = state
        self.trafo = Identity
        self.trafo_desc = (0, 0)
	SelectAndDrag.DragStart(self, p)
	sel = self.selection
	if sel == self.selCenter:
	    self.drag_cur = self.drag_start = self.center
	    return p - self.center
	ds_x = ds_y = 0
	if sel in self.selLeft:
	    ds_x = self.start.x
	if sel in self.selTop:
	    ds_y = self.start.y
	if sel in self.selRight:
	    ds_x = self.end.x
	if sel in self.selBottom:
	    ds_y = self.end.y
	self.drag_cur = self.drag_start = ds = Point(ds_x, ds_y)
	if sel in self.selTurn:
	    vec = ds - self.center
	    self.start_angle = math.atan2(vec.y, vec.x)
	else:
	    if sel == 2:
		self.reference = self.end.y
	    elif sel == 4:
		self.reference = self.start.x
	    elif sel == 6:
		self.reference = self.start.y
	    elif sel == 8:
		self.reference = self.end.x
	return p - ds

    def constrain_center(self, p, state):
	if state & const.ConstraintMask:
	    start = self.start
	    end = self.end
	    if p.x < 0.75 * start.x + 0.25 * end.x:
		x = start.x
	    elif p.x > 0.25 * start.x + 0.75 * end.x:
		x = end.x
	    else:
		x = (start.x + end.x) / 2
	    if p.y < 0.75 * start.y + 0.25 * end.y:
		y = start.y
	    elif p.y > 0.25 * start.y + 0.75 * end.y:
		y = end.y
	    else:
		y = (start.y + end.y) / 2
	    return Point(x, y)
	return p

    def MouseMove(self, p, state):
	self.drag_state = state
	if self.selection == self.selCenter:
	    p = self.constrain_center(p, state)
	SelectAndDrag.MouseMove(self, p, state)
        self.compute_trafo(state)

    def ButtonUp(self, p, button, state):
	if self.selection == self.selCenter:
	    p = self.constrain_center(p, state)
	SelectAndDrag.DragStop(self, p)
	sel = self.selection
	if sel == self.selCenter:
	    self.center = self.drag_cur
	    return '', None
	else:
            self.compute_trafo(state)
	    trafo = self.trafo
	    if self.selection in self.selShear:
		text = _("Shear Objects")
	    else:
		text = _("Rotate Objects")
	    return text, trafo

    def CurrentInfoText(self):
        if self.selection == self.selCenter:
            text = _("Rotation Center at %(position)[position]")
            data = {'position': self.drag_cur}
        else:
            type, value = self.trafo_desc
            if type == 1:
                text = _("Rotate by %(angle)[angle]")
                data = {'angle': value}
            elif type == 2:
                text = _("Horizontal Shear by %(ratio)[factor]")
                data = {'ratio': value}
            elif type == 3:
                text = _("Vertical Shear by %(ratio)[factor]")
                data = {'ratio': value}
            else:
                text = _("Identity Transform")
                data = {}
        return text, data

    def Hit(self, p, rect, device):
	pass

    def Select(self):
	pass

    def SelectPoint(self, p, rect, device, mode = SelectSet):
	self.selection = 0
	return self.selection

    def SelectHandle(self, handle, mode = SelectSet):
	handle = handle.index
	if handle == len(self.handle_idx_to_sel):
	    self.selection = self.selCenter
	else:
	    self.selection = self.handle_idx_to_sel[handle]

    def GetHandles(self):
	return None
	#sx = self.start.x
	#sy = self.start.y
	#ex = self.end.x
	#ey = self.end.y
	#x2 = (sx + ex) / 2
	#y2 = (sy + ey) / 2
	#return map(handle.MakePixmapHandle,
		   #[Point(sx, ey),	Point(x2, ey),	Point(ex, ey),
		    #Point(sx, y2),			Point(ex, y2),
		    #Point(sx, sy),	Point(x2, sy),	Point(ex, sy)],
		   #[(-1,  1),		(0,  1),	( 1,  1),
		    #(-1,  0),				( 1,  0),
		    #(-1, -1),		(0, -1),	( 1, -1)],
		   #[pixmaps.TurnTL, pixmaps.ShearLR,	pixmaps.TurnTR,
		    #pixmaps.ShearUD,			pixmaps.ShearUD,
		    #pixmaps.TurnBL, pixmaps.ShearLR,	pixmaps.TurnBR],
		   #[const.CurTurn] * 8) \
	     #+ [handle.MakePixmapHandle(self.center, (0, 0), pixmaps.Center)]


class TrafoSelection(Selection):

    def __init__(self, copy_from = None):
	Selection.__init__(self, copy_from)
	self.center = None

    def update_rectangle(self, same_center = 1):
	if self:
	    self.rect = TrafoRectangle(self.coord_rect, self.center)
	else:
	    self.rect = TrafoRectangle(Rect(0, 0, 0, 0))

    def ButtonDown(self, p, button, state):
	if len(self.objects) == 1:
	    self.rect.SetOutlineObject(self.objects[0][-1])
	return self.rect.ButtonDown(p, button, state)

    def MouseMove(self, p, state):
	self.rect.MouseMove(p, state)

    def ButtonUp(self, p, button, state, forget_trafo = 0):
	self.rect.SetOutlineObject(None)
	undo_text, trafo = self.rect.ButtonUp(p, button, state)
	self.center = self.rect.center
	if forget_trafo:
	    return None, None
	if trafo is not None:
	    t = time.clock()
	    #undo = self.ForAllUndo(lambda o, t = trafo: o.Transform(t))
	    undo = self.ForAllUndo2('Transform', trafo)
	    self.del_lazy_attrs()
	    #print 'transform/translate', time.clock() - t
	    return undo_text, undo
	return '', None

    def Show(self, device, partially = 0):
	self.rect.Show(device, partially)

    def Hide(self, device, partially = 0):
	self.rect.Hide(device, partially)

    def DrawDragged(self, device, partial):
	self.rect.DrawDragged(device, partial)

    def SelectPoint(self, p, rect, device, mode = SelectSet):
	if not self.rect.SelectPoint(p, rect, device, mode):
	    if self.Hit(p, rect, device):
		self.rect.Select()

    def SelectHandle(self, handle, mode = SelectSet):
	self.rect.SelectHandle(handle, mode)

    def Hit(self, p, rect, device):
	if self.objects:
	    return (rect.overlaps(self.rect.bounding_rect)
		    and Selection.Hit(self, p, rect, device))
	return 0

    def CurrentInfoText(self):
        return self.rect.CurrentInfoText()

class EditorWrapper:

    def __init__(self, editor):
	self.editor = editor

    def __del__(self):
	self.editor.Destroy()

    def __getattr__(self, attr):
	return getattr(self.editor, attr)

    def compatible(self, aclass):
	obj = self.editor
	return isinstance(obj, aclass) or issubclass(obj.EditedClass, aclass)



class EditSelection(Selection):

    is_EditSelection = 1
    
    drag_this = None
    editor = None

    def __init__(self, copy_from = None):
	Selection.__init__(self, copy_from)
	self.check_edit_mode()
	if type(copy_from) == InstanceType \
	   and copy_from.__class__ == self.__class__:
	    self.editor = copy_from.editor
	else:
	    self.get_editor()

    def check_edit_mode(self):
	# allow only one object for editing at a time
	if self.objects:
	    if len(self.objects) > 1 or not self.objects[0][-1].has_edit_mode:
		self.objects = []

    def get_editor(self):
	if self.objects:
	    self.editor = EditorWrapper(self.objects[0][-1].Editor())
	else:
	    self.editor = None

    def GetHandles(self):
	if self.editor is not None:
	    return self.editor.GetHandles()
	return []

    def ButtonDown(self, p, button, state):
	if self.drag_this is not None:
	    return self.drag_this.ButtonDown(p, button, state)
	else:
	    return None

    def MouseMove(self, p, state):
	if self.drag_this is not None:
	    self.drag_this.MouseMove(p, state)

    def ButtonUp(self, p, button, state, forget_trafo = 0):
	if self.drag_this is not None:
	    self.del_lazy_attrs()
	    return _("Edit Object"), self.drag_this.ButtonUp(p, button, state)
	return ('', None)
	# XXX make the undo text more general by a method of graphics objects

    def Show(self, device, partially = 0):
	if self.editor is not None:
	    self.editor.Show(device, partially)

    def Hide(self, device, partially = 0):
	if self.editor is not None:
	    self.editor.Hide(device, partially)

    def DrawDragged(self, device, partial):
	if self.editor is not None:
            self.editor.DrawDragged(device, partial)

    def SetSelection(self, info):
	old_sel = self.objects
	Selection.SetSelection(self, info)
	self.check_edit_mode()
	if old_sel != self.objects:
	    self.get_editor()
	    return 1
	return 0

    def SelectPoint(self, p, rect, device, mode = const.SelectSet):
	self.drag_this = None
	if self.editor is not None:
	    if self.editor.SelectPoint(p, rect, device, mode):
		self.drag_this = self.editor
	return self.drag_this != None

    def SelectHandle(self, handle, mode = SelectSet):
	if self.editor is not None:
	    self.editor.SelectHandle(handle, mode)
	    self.drag_this = self.editor
	else:
	    self.drag_this = None

    def SelectRect(self, rect, mode = SelectSet):
	self.drag_this = None
	if self.editor is not None:
	    if self.editor.SelectRect(rect, mode):
		self.drag_this = self.editor
	return self.drag_this != None

    def CallObjectMethod(self, aclass, methodname, args):
	if len(self.objects) == 1:
	    if self.editor is not None:
		obj = self.editor
		if not obj.compatible(aclass):
		    warn(INTERNAL, 'EditSelection.GetObjectMethod: '
			 'editor %s is not compatible with class %s',
			 self.editor, aclass)
		    return NullUndo
	    else:
		obj = self.objects[0][-1]
		if not isinstance(obj, aclass):
		    warn(INTERNAL, 'EditSelection.GetObjectMethod: '
			 'object is not instance of %s', aclass)
		    return NullUndo
	    try:
		method = getattr(obj, methodname)
	    except AttributeError:
		warn(INTERNAL, 'EditSelection.GetObjectMethod: '
		     'no method %s for class %s', methodname, aclass)
		return NullUndo

	    undo = apply(method, args)
	    if undo is None:
		undo = NullUndo
	    return undo
	return NullUndo

    def GetObjectMethod(self, aclass, method):
	if len(self.objects) == 1:
	    if self.editor is not None:
		obj = self.editor
		if not obj.compatible(aclass):
		    warn(INTERNAL, 'EditSelection.GetObjectMethod: '
			 'editor is not compatible with class %s', aclass)
		    return None
	    else:
		obj = self.objects[0][-1]
		if not isinstance(obj, aclass):
		    warn(INTERNAL, 'EditSelection.GetObjectMethod: '
			 'object is not instance of %s', aclass)
		    return None
	    try:
		return getattr(obj, method)
	    except AttributeError:
		warn(INTERNAL, 'EditSelection.GetObjectMethod: '
		     'no method %s for class %s', method, aclass)
		pass
	return None


    def ChangeRect(self):
	if self.editor is not None:
	    return self.editor.ChangeRect()
	return self.bounding_rect

    def InfoText(self):
	# Return a string describing the selected object(s)
	# XXX we shouldn't access document.layers directly
	if self.editor is not None:
	    return self.editor.Info()
	else:
	    return _("No Selection")

    def CurrentInfoText(self):
	if self.editor is not None:
	    return self.editor.CurrentInfoText()
	else:
	    return ""
        
