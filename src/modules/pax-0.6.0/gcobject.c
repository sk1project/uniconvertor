#include "Python.h"
#include <tk.h>
#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "tkwinobject.h"
#include "gcobject.h"
#include "pixmapobject.h"
#include "regionobject.h"
#include "fontobject.h"
#include "imageobject.h"
#include "clipmask.h"
#include "paxutil.h"

#ifndef offsetof
#define offsetof(type, member) ( (int) & ((type*)0) -> member )
#endif


#define OFF(member) offsetof(XGCValues, member)
static struct GCattr {
	char *type;
	char *name;
	int offset;
	unsigned long mask;
} GCattrdefs[] = {
	{"int", "function", OFF(function), GCFunction},
	{"unsigned long", "plane_mask", OFF(plane_mask), GCPlaneMask},
	{"unsigned long", "foreground", OFF(foreground), GCForeground},
	{"unsigned long", "background", OFF(background), GCBackground},
	{"int", "line_width", OFF(line_width), GCLineWidth},
	{"int", "line_style", OFF(line_style), GCLineStyle},
	{"int", "cap_style", OFF(cap_style), GCCapStyle},
	{"int", "join_style", OFF(join_style), GCJoinStyle},
	{"int", "fill_style", OFF(fill_style), GCFillStyle},
	{"int", "fill_rule", OFF(fill_rule), GCFillRule},
	{"int", "arc_mode", OFF(arc_mode), GCArcMode},
	{"Pixmap", "tile", OFF(tile), GCTile},
	{"Pixmap", "stipple", OFF(stipple), GCStipple},
	{"int", "ts_x_origin", OFF(ts_x_origin), GCTileStipXOrigin},
	{"int", "ts_y_origin", OFF(ts_y_origin), GCTileStipYOrigin},
	{"Font", "font", OFF(font), GCFont},
	{"int", "subwindow_mode", OFF(subwindow_mode), GCSubwindowMode},
	{"Bool", "graphics_exposures", OFF(graphics_exposures),
		 					GCGraphicsExposures},
	{"int", "clip_x_origin", OFF(clip_x_origin), GCClipXOrigin},
	{"int", "clip_y_origin", OFF(clip_y_origin), GCClipYOrigin},
	{"Pixmask", "clip_mask", OFF(clip_mask), GCClipMask},
	{"int", "dash_offset", OFF(dash_offset), GCDashOffset},
	{"char", "dashes", OFF(dashes), GCDashList},
	{NULL}
};
#undef OFF

int
PaxGC_MakeValues(PyObject *dict, unsigned long *pmask, XGCValues *pvalues)
{
    int pos;
    struct GCattr *p;
    PyObject *key, *value;
    if (dict == NULL || !PyDict_Check(dict))
    {
	PyErr_SetString(PyExc_TypeError, "XGCValues should be dictionary");
	return 0;
    }
    *pmask = 0;
    pos = 0;
    while (PyDict_Next(dict, &pos, &key, &value))
    {
	char *name;
	if (!PyString_Check(key))
	{
	    PyErr_SetString(PyExc_TypeError,
			    "XGCValues' keys should be strings");
	    return 0;
	}
	name = PyString_AsString(key);
	for (p = GCattrdefs; ; p++)
	{
	    if (p->name == NULL)
	    {
		PyErr_SetString(PyExc_TypeError,
				"XGCValues contains unknown name");
		return 0;
	    }
	    if (strcmp(name, p->name) != 0)
		continue;
	    *pmask |= p->mask;
	    if (strcmp(p->type, "Pixmap") == 0)
	    {
		if (!PaxPixmap_Check(value))
		{
		    PyErr_SetString(PyExc_TypeError,
				"XGCValues should map to int, Pixmap or Font");
		    return 0;
		}
		*(Pixmap*)((char*)pvalues+p->offset)=PaxPixmap_AsPixmap(value);
	    }
	    else if (strcmp(p->type, "Font") == 0)
	    {
		if (!PaxFont_Check(value))
		{
		    PyErr_SetString(PyExc_TypeError, "XGCValues should map to "
				    "int, Pixmap or Font");
		    return 0;
		}
		*(Font*)((char*)pvalues+p->offset) = PaxFont_AsFont(value);
	    }
	    else
	    {
		if (!PyInt_Check(value))
		{
		    PyErr_SetString(PyExc_TypeError,
				"XGCValues should map to int, Pixmap or Font");
		    return 0;
		}
		if (p->type[0] == 'c')
		    *((char*)pvalues + p->offset) = PyInt_AsLong(value);
		else
		    /* XXX Assume sizeof(int) == sizeof(long)! */
		    *(long*)((char*)pvalues + p->offset) = PyInt_AsLong(value);
	    }
	    break;
	}
    }
    return 1;
}


static int
pax_checkcharlist(PyObject *list, char **parray, int *pnitems)
{
    int i, n;
    if (!PyList_Check(list))
    {
	PyErr_SetString(PyExc_TypeError, "list of ints expected");
	return 0;
    }
    
    n = PyList_Size(list);
    *pnitems = n;
    *parray = PyMem_NEW(char, n);
    if (*parray == NULL)
    {
	PyErr_NoMemory();
	return 0;
    }
    
    for (i = 0; i < n; i++)
    {
	PyObject *item = PyList_GetItem(list, i);
	if (!PyInt_Check(item))
	{
	    PyMem_DEL(*parray);
	    PyErr_SetString(PyExc_TypeError, "list of ints expected");
	    return 0;
	}
	(*parray)[i] = PyInt_AsLong(item);
    }
    return 1;
}


extern PyTypeObject PaxGCType; /* Really forward */

GC
PaxGC_AsGC(PyObject *gcobj)
{
    if (!PaxGC_Check(gcobj))
    {
	PyErr_BadInternalCall();
	return (GC) NULL;
    }

    return ((PaxGCObject *) gcobj)->gc;
}

PyObject *
PaxGC_FromGC(Display *display, Drawable drawable, GC gc, int shared,
	     PyObject * drawable_object)
{
    PaxGCObject *gp = PyObject_NEW(PaxGCObject, &PaxGCType);
    if (gp == NULL)
	return NULL;
    gp->display = display;
    gp->drawable = drawable;
    gp->gc = gc;
    gp->shared = shared;
    gp->drawable_object = drawable_object;
    Py_XINCREF(gp->drawable_object);
    
    return (PyObject *)gp;
}


static PyObject *
PaxGC_SetDrawable(PaxGCObject * self, PyObject * args)
{
    PyObject * obj;

    if (!PyArg_ParseTuple(args, "O", &obj))
	return NULL;

    if (PaxPixmap_Check(obj))
    {
	Py_XDECREF(self->drawable_object);
	self->drawable = PaxPixmap_AsPixmap(obj);
	self->drawable_object = obj;
	Py_INCREF(self->drawable_object);
    }
    else if (TkWin_Check(obj))
    {
	self->drawable = TkWin_AsWindowID(obj);
	Py_XDECREF(self->drawable_object);
	self->drawable_object = NULL;
    }
    else
    {
	PyErr_SetString(PyExc_TypeError,
			"The new drawable must be a Tkwindow or a pixmap");
	return NULL;
    }

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
PaxGC_SetDashes(PaxGCObject * self, PyObject * args)
{
    PyObject * list;
    char * dashes;
    int num_dashes;
    int dash_offset = 0;

    if (!PyArg_ParseTuple(args, "O|i", &list, &dash_offset))
	return NULL;

    if (!pax_checkcharlist(list, &dashes, &num_dashes))
	return NULL;

    XSetDashes(self->display, self->gc, dash_offset, dashes, num_dashes);
    PyMem_DEL(dashes);

    Py_INCREF(Py_None);
    return Py_None;
}
	
   
static PyObject *
PaxGC_SetForegroundAndFill(PaxGCObject *self, PyObject *args)
{
    PyObject * pixel_or_pixmap;
    
    if (self->shared != PAXGC_OWNED)
    {
	PyErr_SetString(PyExc_TypeError, "can't modify shared GC");
	return NULL;
    }
    if (!PyArg_ParseTuple(args, "O", &pixel_or_pixmap))
	return NULL;
    if (PyInt_Check(pixel_or_pixmap))
    {
	XSetForeground(self->display, self->gc, PyInt_AsLong(pixel_or_pixmap));
	XSetFillStyle(self->display, self->gc, FillSolid);
    }
    else if (PaxPixmap_Check(pixel_or_pixmap))
    {
	XSetTile(self->display, self->gc, PaxPixmap_AsPixmap(pixel_or_pixmap));
	XSetFillStyle(self->display, self->gc, FillTiled);
    }
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
PaxGC_SetClipMask(PaxGCObject *self, PyObject *args)
{
    PyObject *object;
    
    if (self->shared)
    {
	PyErr_SetString(PyExc_TypeError, "can't modify shared GC");
	return NULL;
    }
    if (!PyArg_ParseTuple(args, "O", &object))
	return NULL;
    if (PaxPixmap_CheckOpt(object))
    {
	XSetClipMask(self->display, self->gc, PaxPixmap_AsPixmapOpt(object));
    }
    else if (PaxRegion_Check(object))
    {
	XSetRegion(self->display, self->gc, PaxRegion_AsRegion(object));
    }
    else
    {
	PyErr_SetString(PyExc_TypeError,
		     "arg must be a region, a bitmap o a clkip mask object");
	return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}
    

#ifndef PAX_NO_XSHM
static PyObject *
PaxGC_ShmPutImage(PaxGCObject *self, PyObject *args)
{
    PyObject *image;
    int srcx;
    int srcy;
    int destx;
    int desty;
    unsigned int width;
    unsigned int height;
    int send_event;
    if (!PyArg_ParseTuple(args, "O!iiiiiii", &PaxImageType, &image,
			  &srcx, &srcy, &destx, &desty, &width, &height,
			  &send_event))
	return NULL;
    XShmPutImage(self->display, self->drawable, self->gc,
		 PaxImage_AsImage(image), srcx, srcy, destx, desty,
		 width, height, send_event);
    Py_INCREF(Py_None);
    return Py_None;
}
#else
static PyObject *
PaxGC_ShmPutImage(PaxGCObject *self, PyObject *args)
{
    PyErr_SetString(PyExc_RuntimeError,
		    "gcobject compiled without XShm support");
    return NULL;
}
#endif /* PAX_NO_XSHM */


#include "gcmethods.c"

static PyObject *
MemberList(void)
{
    int i, n;
    PyObject *v;
    for (n = 0; GCattrdefs[n].name != NULL; n++)
	;
    v = PyList_New(n);
    if (v != NULL)
    {
	for (i = 0; i < n; i++)
	    PyList_SetItem(v, i, PyString_FromString(GCattrdefs[i].name));
	if (PyErr_Occurred())
	{
	    Py_DECREF(v);
	    v = NULL;
	}
	else
	{
	    PyList_Sort(v);
	}
    }
    return v;
}

static PyObject *
GetAttr(PaxGCObject *self, char *name)
{
    struct GCattr *p;
    XGCValues values;
    PyObject *result;
    
    if (name[0] == '_' && strcmp(name, "__members__") == 0)
	return MemberList();
    
    result = Py_FindMethod(PaxGC_methods, (PyObject *)self, name);
    if (result != NULL)
	return result;
    PyErr_Clear();

    if (name[0] == 'd' && strcmp(name, "drawable") == 0)
    {
	if (self->drawable_object)
	{
	    Py_INCREF(self->drawable_object);
	    return self->drawable_object;
	}
	PyErr_SetString(PyExc_AttributeError, "drawable object is not set");
	return NULL;
    }
    
    for (p = GCattrdefs; ; p++)
    {
	if (p->name == NULL)
	{
	    PyErr_SetString(PyExc_AttributeError, name);
	    return NULL;
	}
	if (strcmp(name, p->name) == 0)
	    break;
    }
    if (!XGetGCValues(self->display, self->gc, p->mask, &values))
    {
	PyErr_SetString(PyExc_TypeError, "write-only (!) GC attribute");
	return NULL;
    }
    if (strcmp(p->type, "Pixmap") == 0)
    {
	return PaxPixmap_FromPixmap(self->display,
				   *(Pixmap*)((char*)(&values) + p->offset),
				   0);
    }
    else if (strcmp(p->type, "Font") == 0)
    {
	if (* (Font *) ((char *)(&values) + p->offset) == (Font) -1)
	{
	    Py_INCREF(Py_None);
	    return Py_None;
	}
	return PaxFont_FromFont(self->display,
			       * (Font *) ((char *)(&values) + p->offset));
    }
    else
    {
	/* XXX Assume sizeof(int) == sizeof(long) */
	return PyInt_FromLong(* (long *)((char *)(&values) + p->offset));
    }
}

static int
SetAttr(PaxGCObject *self, char *name, PyObject *value)
{
    struct GCattr *p;
    XGCValues values;
    
    if (self->shared != PAXGC_OWNED)
    {
	PyErr_SetString(PyExc_TypeError, "can't modify shared GC");
	return -1;
    }
    if (value == NULL)
    {
	PyErr_SetString(PyExc_TypeError, "can't delete GC attribute");
	return -1;
    }
    if (!PyInt_Check(value))
    {
	PyErr_SetString(PyExc_TypeError, "GC attribute value must be integer");
	return -1;
    }
    for (p = GCattrdefs; ; p++)
    {
	if (p->name == NULL)
	{
	    PyErr_SetString(PyExc_AttributeError, name);
	    return -1;
	}
	if (strcmp(name, p->name) == 0)
	    break;
    }
    if (p->type[0] == 'c')
	*((char*)(&values) + p->offset) = PyInt_AsLong(value);
    else
        /* XXX Assume sizeof(int) == sizeof(long) */
	*(long*)((char *)(&values) + p->offset) = PyInt_AsLong(value);
    XChangeGC(self->display, self->gc, p->mask, &values);
    return 0;
}

static void
Dealloc(PaxGCObject *self)
{
    if (self->shared == PAXGC_SHARED)
	Tk_FreeGC(self->display, self->gc);
    else if (self->shared == PAXGC_OWNED)
	XFreeGC(self->display, self->gc);
    Py_XDECREF(self->drawable_object);
    PyMem_DEL(self);
}

PyTypeObject PaxGCType =
{
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxGC",		/*tp_name*/
	sizeof(PaxGCObject),	/*tp_size*/
	0,			/*tp_itemsize*/
	(destructor)Dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)GetAttr,	/*tp_getattr*/
	(setattrfunc)SetAttr,	/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};

