#include "Python.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "regionobject.h"
#include "gcobject.h" 

PyObject *
PaxRegion_FromRegion(Region region)
{
    PaxRegionObject  *self;
    self = PyObject_NEW(PaxRegionObject,  &PaxRegionType);
    if (self == NULL)
	return NULL;
    self->region  = region;
    return (PyObject*)self;
}


static PyObject *
region_ClipBox(PaxRegionObject *self, PyObject *args)
{
    XRectangle r;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    XClipBox(self->region, &r);
    return Py_BuildValue("(iiii)", r.x, r.y, r.width, r.height);
}

static PyObject *
region_EmptyRegion(PaxRegionObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    return PyInt_FromLong(XEmptyRegion(self->region));
}

static PyObject *
region_EqualRegion(PaxRegionObject *self, PyObject *args)
{
    PaxRegionObject *r;
    if (!PyArg_ParseTuple(args, "O!", &PaxRegionType, &r))
	return NULL;
    return PyInt_FromLong(XEqualRegion(self->region, r->region));
}

static PyObject *
region_PointInRegion(PaxRegionObject *self, PyObject *args)
{
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y))
	return NULL;
    return PyInt_FromLong(XPointInRegion(self->region, x, y));
}

static PyObject *
region_RectInRegion(PaxRegionObject *self, PyObject *args)
{
    int x, y;
    unsigned int width, height;
    if (!PyArg_ParseTuple(args, "iiii", &x, &y, &width, &height))
	return NULL;
    return PyInt_FromLong(XRectInRegion(self->region, x, y, width, height));
}

static PyObject *
region_IntersectRegion(PaxRegionObject *self, PyObject *args)
{
    PaxRegionObject *r;
    if (!PyArg_ParseTuple(args, "O!", &PaxRegionType, &r))
	return NULL;
    XIntersectRegion(self->region, r->region, self->region);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_UnionRegion(PaxRegionObject *self, PyObject *args)
{
    PaxRegionObject *r;
    if (!PyArg_ParseTuple(args, "O!", &PaxRegionType, &r))
	return NULL;
    XUnionRegion(self->region, r->region, self->region);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_UnionRectWithRegion(PaxRegionObject *self,
					     PyObject *args)
{
    XRectangle r;
    int x, y, width, height;

    /* don't use 'h' here because Python 2.0 does some range checking
     * but tests for signed shorts not the unsigned we need. It
     * introduces H for unsigned short but that's not available in 1.5.2
     */
    if (!PyArg_ParseTuple(args, "iiii", &x, &y, &width, &height))
	return NULL;
    r.x = x;
    r.y = y;
    r.width = width;
    r.height = height;
    XUnionRectWithRegion(&r, self->region, self->region);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_SubtractRegion(PaxRegionObject *self, PyObject *args)
{
    PaxRegionObject *r;
    if (!PyArg_ParseTuple(args, "O!", &PaxRegionType, &r))
	return NULL;
    XSubtractRegion(self->region, r->region, self->region);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_XorRegion(PaxRegionObject *self, PyObject *args)
{
    PaxRegionObject *r;
    if (!PyArg_ParseTuple(args, "O!", &PaxRegionType, &r))
	return NULL;
    XXorRegion(self->region, r->region, self->region);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_OffsetRegion(PaxRegionObject *self, PyObject *args)
{
    int dx, dy;
    if (!PyArg_ParseTuple(args, "ii", &dx, &dy))
	return NULL;
    XOffsetRegion(self->region, dx, dy);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
region_ShrinkRegion(PaxRegionObject *self, PyObject *args)
{
    int dx, dy;
    if (!PyArg_ParseTuple(args, "ii", &dx, &dy))
	return NULL;
    XShrinkRegion(self->region, dx, dy);
    Py_INCREF(Py_None);
    return Py_None;
}


static PyMethodDef region_methods[] = {
	{"ClipBox",		(PyCFunction)region_ClipBox,		1},
	{"EmptyRegion",		(PyCFunction)region_EmptyRegion,	1},
	{"EqualRegion",		(PyCFunction)region_EqualRegion,	1},
	{"IntersectRegion",	(PyCFunction)region_IntersectRegion,	1},
	{"OffsetRegion",	(PyCFunction)region_OffsetRegion,	1},
	{"PointInRegion",	(PyCFunction)region_PointInRegion,	1},
	{"RectInRegion",	(PyCFunction)region_RectInRegion,	1},
	{"ShrinkRegion",	(PyCFunction)region_ShrinkRegion,	1},
	{"SubtractRegion",	(PyCFunction)region_SubtractRegion,	1},
	{"UnionRectWithRegion", (PyCFunction)region_UnionRectWithRegion,1},
	{"UnionRegion",		(PyCFunction)region_UnionRegion,	1},
	{"XorRegion",		(PyCFunction)region_XorRegion,		1},
	{0, 0} 
};

static
PyObject * region_getattr(PaxRegionObject  *self, char *name)
{
    return Py_FindMethod(region_methods, (PyObject *)self, name);
}

static void
region_dealloc(PaxRegionObject  *self)
{
    XDestroyRegion(self->region);
    PyMem_DEL(self);
}


PyTypeObject PaxRegionType  = {
    PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxRegion" ,		/*tp_name*/
	sizeof(PaxRegionObject),	/*tp_size*/
	0,			/*tp_itemsize*/
	(destructor)region_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)region_getattr , /*tp_getattr*/
	(setattrfunc)0 ,	/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};



Region
PaxRegion_AsRegion(PyObject *self)
{
    if (self && PaxRegion_Check(self))
	return ((PaxRegionObject  *)self)-> region ;
    PyErr_BadInternalCall();
    return NULL;
}
