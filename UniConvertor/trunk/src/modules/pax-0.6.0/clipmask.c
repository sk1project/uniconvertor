#include <Python.h>
#include "regionobject.h"
#include "pixmapobject.h"
#include "clipmask.h"

static PyObject *
mask_intersect_regions(Region region1, Region region2)
{
    Region result = XCreateRegion();

    XIntersectRegion(region1, region2, result);

    return PaxRegion_FromRegion(result);
}

static PyObject *
mask_intersect_region_with_bitmap(Display * display, Region region,
				  Pixmap bitmap)
{
    XGCValues values;
    GC gc;
    Pixmap result;
    Window root;
    int x, y;
    unsigned int width, height, border_width, depth;

    if (!XGetGeometry(display, bitmap, &root, &x, &y, &width, &height,
		      &border_width, &depth))
    {
	PyErr_SetString(PyExc_RuntimeError, "Cannot get pixmap geometry");
	return NULL;
    }
    if (depth != 1)
    {
	PyErr_SetString(PyExc_TypeError, "pixmap must have depth 1");
	return NULL;
    }
    
    result = XCreatePixmap(display, bitmap, width, height, 1);

    values.foreground = 0;
    values.background = 0;
    gc = XCreateGC(display, bitmap, GCForeground | GCBackground, &values);
    XFillRectangle(display, result, gc, 0, 0, width, height);

    XSetForeground(display, gc, 1);
    XSetRegion(display, gc, region);
    XCopyPlane(display, bitmap, result, gc, 0, 0, width, height, 0, 0, 1);
	
    XFreeGC(display, gc);

    return PaxPixmap_FromPixmap(display, result, 1);
}


static PyObject *
mask_intersect_bitmaps(Display * display, Pixmap bitmap1, Pixmap bitmap2)
{
    XGCValues values;
    GC gc;
    Pixmap result;
    Window root;
    int x, y;
    unsigned int border_width, depth;
    unsigned int width, height, width2, height2;

    if (!XGetGeometry(display, bitmap1, &root, &x, &y, &width, &height,
		      &border_width, &depth))
    {
	PyErr_SetString(PyExc_RuntimeError, "Cannot get pixmap geometry");
	return NULL;
    }
    if (depth != 1)
    {
	PyErr_SetString(PyExc_TypeError, "pixmap1 must have depth 1");
	return NULL;
    }

    if (!XGetGeometry(display, bitmap2, &root, &x, &y, &width2, &height2,
		      &border_width, &depth))
    {
	PyErr_SetString(PyExc_RuntimeError, "Cannot get pixmap geometry");
	return NULL;
    }
    if (depth != 1)
    {
	PyErr_SetString(PyExc_TypeError, "pixmap2 must have depth 1");
	return NULL;
    }
    if (width != width2 || height != height2)
    {
	PyErr_SetString(PyExc_ValueError, "bitmaps must have the same size");
	return NULL;
    }
    
    result = XCreatePixmap(display, bitmap1, width, height, 1);

    values.foreground = 1;
    values.background = 0;
    gc = XCreateGC(display, bitmap1, GCForeground | GCBackground, &values);

    XCopyPlane(display, bitmap1, result, gc, 0, 0, width, height, 0, 0, 1);
    XSetFunction(display, gc, GXand);
    XCopyPlane(display, bitmap2, result, gc, 0, 0, width, height, 0, 0, 1);
	
    XFreeGC(display, gc);

    return PaxPixmap_FromPixmap(display, result, 1);
}

PyObject *
PaxClipMask_Intersect(PyObject * mask1, PyObject * mask2)
{
    if (mask1 == Py_None)
    {
	Py_INCREF(mask2);
	return mask2;
    }
    if (mask2 == Py_None)
    {
	Py_INCREF(mask1);
	return mask1;
    }
    
    if (PaxRegion_Check(mask1))
    {
	if (PaxRegion_Check(mask2))
	    return mask_intersect_regions(PaxRegion_AsRegion(mask1),
					  PaxRegion_AsRegion(mask2));
	else if (PaxPixmap_Check(mask2))
	    return mask_intersect_region_with_bitmap(PaxPixmap_DISPLAY(mask2),
						     PaxRegion_AsRegion(mask1),
						    PaxPixmap_AsPixmap(mask2));
    }
    else if (PaxPixmap_Check(mask1))
    {
	if (PaxRegion_Check(mask2))
	    return mask_intersect_region_with_bitmap(PaxPixmap_DISPLAY(mask1),
						     PaxRegion_AsRegion(mask2),
						    PaxPixmap_AsPixmap(mask1));
	else if (PaxPixmap_Check(mask2))
	    return mask_intersect_bitmaps(PaxPixmap_DISPLAY(mask1),
					  PaxPixmap_AsPixmap(mask1),
					  PaxPixmap_AsPixmap(mask2));
    }

    PyErr_SetString(PyExc_TypeError,
		    "arguments must be regions and/or bitmaps");
    return NULL;
}


PyObject *
PaxClipMask_IntersectMasks(PyObject * self, PyObject * args)
{
    PyObject * object1, *object2;

    if (!PyArg_ParseTuple(args, "OO", &object1, &object2))
	return NULL;

    return PaxClipMask_Intersect(object1, object2);
}
