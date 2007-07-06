#include "Python.h"
#include <tk.h>
#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "tkwinobject.h"
#include "gcobject.h"
#include "pixmapobject.h"
#include "borderobject.h"
#include "paxutil.h"

PyObject *
PaxBorder_FromTkBorder(Tk_3DBorder tkborder, Tk_Window tkwin, int borrowed)
{
    PaxBorderObject * self;

    self = PyObject_NEW(PaxBorderObject, &PaxBorderType);
    if (!self)
	return NULL;

    self->tkborder = tkborder;
    self->tkwin = tkwin;
    self->borrowed = borrowed;

    return (PyObject*)self;
}

Tk_3DBorder
PaxBorder_AsTkBorder(PyObject * self)
{
    return ((PaxBorderObject*)self)->tkborder;
}


static void
paxborder_dealloc(PaxBorderObject *self)
{
    if (!self->borrowed)
    {
	Tk_Free3DBorder(self->tkborder);
    }
    PyMem_DEL(self);
}

/* a converter function suitable for PyArg_ParseTuple */
static int pax_convert_drawable(PyObject * drawable_obj, void * drawable)
{
    if (PaxPixmap_Check(drawable_obj))
	*(Drawable*)drawable = PaxPixmap_AsPixmap(drawable_obj);
    else if (TkWin_Check(drawable_obj))
	*(Drawable*)drawable = TkWin_AsWindowID(drawable_obj);
    else
    {
	PyErr_SetString(PyExc_TypeError, "Drawable must be pixmap or window");
	return 0;
    }
    return 1;
}


static PyObject *
paxborder_Draw3DRectangle(PaxBorderObject * self, PyObject * args)
{
    int x = 0, y = 0, width, height, border_width, relief;
    Drawable drawable;
    
    if (!PyArg_ParseTuple(args, "O&iiiiii", pax_convert_drawable, &drawable,
			  &x, &y, &width, &height, &border_width, &relief))
	return NULL;

    Tk_Draw3DRectangle(self->tkwin, drawable, self->tkborder,
		       x, y, width, height, border_width, relief);

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
paxborder_Fill3DRectangle(PaxBorderObject * self, PyObject * args)
{
    int x = 0, y = 0, width, height, border_width, relief;
    Drawable drawable;
    
    if (!PyArg_ParseTuple(args, "O&iiiiii", pax_convert_drawable, &drawable,
			  &x, &y, &width, &height, &border_width, &relief))
	return NULL;

    Tk_Fill3DRectangle(self->tkwin, drawable, self->tkborder,
		       x, y, width, height, border_width, relief);
    
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
paxborder_Draw3DPolygon(PaxBorderObject * self, PyObject * args)
{
    Drawable drawable;
    PyObject *list;
    XPoint *points;
    int npoints;
    int border_width, left_relief;

    if (!PyArg_ParseTuple(args, "O&Oii", pax_convert_drawable, &drawable,
			  &list, &border_width, &left_relief))
	return NULL;
    if (!pax_checkshortlist(2, list, (short**)&points, &npoints))
    {
	if (!PyErr_Occurred())
	    PyErr_SetString(PyExc_TypeError, "argument should be XPoint[]");
	return NULL;
    }
    
    Tk_Draw3DPolygon(self->tkwin, drawable, self->tkborder, points, npoints,
		     border_width, left_relief);
    PyMem_DEL(points);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
paxborder_Fill3DPolygon(PaxBorderObject * self, PyObject * args)
{
    Drawable drawable;
    PyObject *list;
    XPoint *points;
    int npoints;
    int border_width, left_relief;

    if (!PyArg_ParseTuple(args, "O&Oii", pax_convert_drawable, &drawable,
			  &list, &border_width, &left_relief))
	return NULL;
    if (!pax_checkshortlist(2, list, (short**)&points, &npoints))
    {
	if (!PyErr_Occurred())
	    PyErr_SetString(PyExc_TypeError, "argument should be XPoint[]");
	return NULL;
    }
    
    Tk_Fill3DPolygon(self->tkwin, drawable, self->tkborder, points, npoints,
		     border_width, left_relief);
    PyMem_DEL(points);

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
paxborder_HorizontalBevel(PaxBorderObject * self, PyObject * args)
{
    Drawable drawable;
    int x, y, width, height, left_in, right_in, top_bevel, relief;

    if (!PyArg_ParseTuple(args, "O&iiiiiiii", pax_convert_drawable, &drawable,
			  &x, &y, &width, &height, &left_in, &right_in,
			  &top_bevel, &relief))
	return NULL;

    Tk_3DHorizontalBevel(self->tkwin, drawable, self->tkborder, x, y,
			 width, height, left_in, right_in, top_bevel, relief);
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
paxborder_VerticalBevel(PaxBorderObject * self, PyObject * args)
{
    Drawable drawable;
    int x, y, width, height, left_bevel, relief;

    if (!PyArg_ParseTuple(args, "O&iiiiiiii", pax_convert_drawable, &drawable,
			  &x, &y, &width, &height, &left_bevel, &relief))
	return NULL;

    Tk_3DVerticalBevel(self->tkwin, drawable, self->tkborder, x, y,
		       width, height, left_bevel, relief);
    Py_INCREF(Py_None);
    return Py_None;
}
    
static PyObject *
paxborder_BorderGC(PaxBorderObject * self, PyObject * args)
{
    int which;
    GC gc;
    
    if (!PyArg_ParseTuple(args, "i", &which))
	return NULL;

    if (which != TK_3D_FLAT_GC && which !=  TK_3D_LIGHT_GC
	&& which !=  TK_3D_DARK_GC)
    {
	PyErr_SetString(PyExc_ValueError, "which must be "
			"TK_3D_FLAT_GC, TK_3D_LIGHT_GC or TK_3D_DARK_GC");
	return NULL;
    }

    gc = Tk_3DBorderGC(self->tkwin, self->tkborder, which);

    return PaxGC_FromGC(Tk_Display(self->tkwin), Tk_WindowId(self->tkwin),
		       gc, PAXGC_BORROWED, NULL);
}

static struct PyMethodDef paxborder_methods[] = {
    {"Draw3DRectangle",	(PyCFunction)paxborder_Draw3DRectangle,		1},
    {"Fill3DRectangle",	(PyCFunction)paxborder_Fill3DRectangle,		1},
    {"Draw3DPolygon",	(PyCFunction)paxborder_Draw3DPolygon,		1},
    {"Fill3DPolygon",	(PyCFunction)paxborder_Fill3DPolygon,		1},
    {"HorizontalBevel",	(PyCFunction)paxborder_HorizontalBevel,		1},
    {"VerticalBevel",	(PyCFunction)paxborder_VerticalBevel,		1},
    {"BorderGC",	(PyCFunction)paxborder_BorderGC,			1},
    {NULL,	NULL}
};


static PyObject *
paxborder_getattr(PyObject * self, char * name)
{
    return Py_FindMethod(paxborder_methods, self, name);
}


PyTypeObject PaxBorderType =
{
	PyObject_HEAD_INIT(&PyType_Type)
	0,				/*ob_size*/
	"PaxBorder",			/*tp_name*/
	sizeof(PaxBorderObject),	/*tp_size*/
	0,				/*tp_itemsize*/
	(destructor)paxborder_dealloc,	/*tp_dealloc*/
	0,				/*tp_print*/
	(getattrfunc)paxborder_getattr,	/*tp_getattr*/
	(setattrfunc)0,			/*tp_setattr*/
	0,				/*tp_compare*/
	0,				/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};
