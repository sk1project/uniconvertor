#include "Python.h"
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include "tkwinobject.h"
#include "gcobject.h"
#include "pixmapobject.h"
#include "regionobject.h"


static PyObject *
pixmap_CreateGC(PaxPixmapObject *self, PyObject *args, PyObject * kwargs)
{
    Display *display;
    Drawable d;
    unsigned long mask = 0;
    XGCValues values;
    GC gc;
    PyObject * dict;

    if (PySequence_Length(args) > 0)
    {
	if (!PyArg_ParseTuple(args, "O", &dict))
	    return NULL;
    }
    else
	dict = kwargs;
    
    display = self->display;
    d = self->pixmap;

    if (dict)
    {
	if (!PaxGC_MakeValues(dict, &mask, &values))
	    return NULL;
    }
    
    gc = XCreateGC(display, d, mask, &values);
    return PaxGC_FromGC(display, d, gc, PAXGC_OWNED, (PyObject*)self);
}



static PyObject *
pixmap_CopyArea(PaxPixmapObject *self, PyObject *args)
{
    PyObject *destobj, *gcobj;
    Drawable dest;
    GC gc;
    int src_x, src_y, dest_x, dest_y;
    unsigned int width, height;

    if (!PyArg_ParseTuple(args, "OOiiiiii", &destobj, &gcobj, &src_x,
			  &src_y, &width, &height, &dest_x, &dest_y))
	return NULL;
    if (TkWin_Check(destobj))
    {
	dest = Tk_WindowId(((TkWinObject*) destobj)->tkwin);
    }
    else if (PaxPixmap_Check(destobj))
    {
	dest = ((PaxPixmapObject *) destobj)->pixmap;
    }
    else
    {
	PyErr_SetString(PyExc_RuntimeError, "bad arguments");
	return NULL;
    }
    if (gcobj == Py_None)
	gc = DefaultGCOfScreen(DefaultScreenOfDisplay(self->display));
    else
    {
	gc = PaxGC_AsGC(gcobj);
	if (PyErr_Occurred())
	    return NULL;
    }

    XCopyArea(self->display, self->pixmap, dest, gc, src_x, src_y,
	      width, height, dest_x, dest_y);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
pixmap_CopyPlane(PaxPixmapObject *self, PyObject *args)
{
    PyObject *destobj, *gcobj;
    Tk_Window w = NULL;
    Drawable dest;
    GC gc;
    int src_x, src_y, dest_x, dest_y;
    unsigned int width, height;
    unsigned long plane;

    if (!PyArg_ParseTuple(args, "OOiiiiiii", &destobj, &gcobj, &src_x,
			  &src_y, &width, &height, &dest_x, &dest_y, &plane))
	return NULL;
    if (TkWin_Check(destobj))
    {
	w = TkWin_AsTkWindow(destobj);
	dest = Tk_WindowId(w);
    }
    else if (PaxPixmap_Check(destobj))
    {
	dest = PaxPixmap_AsPixmap(destobj);
    }
    else
    {
	PyErr_SetString(PyExc_RuntimeError, "bad arguments");
	return NULL;
    }
    if (gcobj == Py_None && w)
	gc = DefaultGCOfScreen(Tk_Screen(w));
    else
    {
	gc = PaxGC_AsGC(gcobj);
	if (PyErr_Occurred())
	    return NULL;
    }

    XCopyPlane(self->display, self->pixmap, dest, gc, src_x, src_y,
	       width, height, dest_x, dest_y, plane);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
pixmap_GetGeometry(PaxPixmapObject *self, PyObject *args)
{
    Window root;
    int x, y;
    unsigned int width, height, border_width, depth;

    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    if (!XGetGeometry(self->display, self->pixmap,
		      &root, &x, &y, &width, &height,
		      &border_width, &depth))
    {
	Py_INCREF(Py_None);
	return Py_None;
    }
    return Py_BuildValue("(iiiiiii)", root, x, y, width, height,
			 border_width, depth);
}


/* return the data of the bitmap in a list of strings as suitable for the
 * lines of an xbm file. These lines only describe the part of the c array
 * inside the braces.
 */

/* the following two functions are taken from the XFree86 sources and modified
 * for Python.
 */

static char * Format_Image(XImage *image, int *resultsize);

#define BYTES_PER_OUTPUT_LINE 12
static PyObject *
pixmap_GetXbmStrings(PaxPixmapObject * self, PyObject * args)
{
    char *data, *ptr;
    char line[BYTES_PER_OUTPUT_LINE * 10];
    int size, byte;
    int c;
    XImage *image;
    int x, y;
    Window root;
    unsigned int width, height, border_width, depth;
    PyObject * result, *string;

    if (!XGetGeometry(self->display, self->pixmap,
		      &root, &x, &y, &width, &height,
		      &border_width, &depth))
    {
	PyErr_SetString(PyExc_RuntimeError, "Cannot get pixmap geometry");
	return NULL;
    }
	    
	
    /* Convert bitmap to an image */
    image = XGetImage(self->display, self->pixmap,
		      0, 0, width, height, 1L, XYPixmap);
    if (!image)
    {
	PyErr_SetString(PyExc_RuntimeError,
			"Cannot create intermediate ximage");
	return NULL;
    }

    /* Get standard format for data */
    data = Format_Image(image, &size);
    XDestroyImage(image);
    if (!data) 
	return NULL;

    result = PyList_New(0);
    if (!result)
	goto fail;
	
    line[0] = '\0';
    for (byte = 0, ptr = data; byte < size; byte++, ptr++)
    {
	char buf[10];
	if (byte)
	{
	    if (byte % BYTES_PER_OUTPUT_LINE == 0)
	    {
		strcat(line, ",");
		string = PyString_FromString(line);
		if (!string)
		    goto fail;
		if (PyList_Append(result, string) == -1)
		    goto fail;
		line[0] = '\0';
	    }
	    else
		strcat(line, ", ");
	}
	c = *ptr;
	if (c < 0)
	    c += 256;
	sprintf(buf, "0x%02x", c);
	strcat(line, buf);
    }

    if (line[0])
    {
	string = PyString_FromString(line);
	if (!string)
	    goto fail;
	if (PyList_Append(result, string) == -1)
	    goto fail;
    }
    
    return result;

fail:
    free(data);
    Py_XDECREF(result);
    return NULL;
}



static char *
Format_Image(XImage *image, int *resultsize)
{
    register int x, c, b;
    register char *ptr;
    int y;
    char *data;
    int width, height;
    int bytes_per_line;

    width = image->width;
    height = image->height;

    bytes_per_line = (width + 7) / 8;
    *resultsize = bytes_per_line * height;	/* Calculate size of data */

    data = (char *) malloc(*resultsize);     /* Get space for data */
    if (!data)
    {
	PyErr_NoMemory();
	return NULL;
    }

    /*
     * The slow but robust brute force method of converting the image:
     */
    ptr = data;
    c = 0; b = 1;
    for (y = 0; y < height; y++)
    {
	for (x = 0; x < width;)
	{
	    if (XGetPixel(image, x, y))
		c |= b;
	    b <<= 1;
	    if (!(++x & 7))
	    {
		*(ptr++) = c;
		c = 0; b = 1;
	    }
	}
	if (x & 7) {
	    *(ptr++) = c;
	    c = 0; b = 1;
	}
    }

    return data;
}

static PyObject *
pixmap_Intersected(PaxPixmapObject * self, PyObject * args)
{
    PyObject * other;
    XGCValues values;
    GC gc;
    Pixmap bitmap;
    Window root;
    int x, y;
    unsigned int width, height, border_width, depth;

    if (!PyArg_ParseTuple(args, "O", &other))
	return NULL;

    if (!XGetGeometry(self->display, self->pixmap,
		      &root, &x, &y, &width, &height,
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
    
    bitmap = XCreatePixmap(self->display, self->pixmap, width, height, 1);

    values.foreground = 0;
    values.background = 0;
    gc = XCreateGC(self->display, bitmap, GCForeground | GCBackground,
		   &values);
    XFillRectangle(self->display, bitmap, gc, 0, 0, width, height);
    XSetForeground(self->display, gc, 1);
    
    if (PaxRegion_Check(other))
    {
	XSetRegion(self->display, gc, PaxRegion_AsRegion(other));
	XCopyPlane(self->display, self->pixmap, bitmap, gc,
		   0, 0, width, height, 0, 0, 1);
    }
    else if (PaxPixmap_Check(other))
    {
	XCopyPlane(self->display, self->pixmap, bitmap, gc,
		   0, 0, width, height, 0, 0, 1);
	XSetFunction(self->display, gc, GXand);
	XCopyPlane(self->display, PaxPixmap_AsPixmap(other), bitmap, gc,
		   0, 0, width, height, 0, 0, 1);
    }
    else
    {
	XFreeGC(self->display, gc);
	XFreePixmap(self->display, bitmap);
	PyErr_SetString(PyExc_TypeError,
			"argument must be either pixmap or region");
	return NULL;
    }
	
    XFreeGC(self->display, gc);

    return PaxPixmap_FromPixmap(self->display, bitmap, 1);
}



static PyMethodDef pixmap_methods[] = {
    {"GetGeometry",	(PyCFunction)pixmap_GetGeometry,	1},
    {"CopyArea",	(PyCFunction)pixmap_CopyArea,		1},
    {"CopyPlane",	(PyCFunction)pixmap_CopyPlane,		1},
    {"CreateGC",	(PyCFunction)pixmap_CreateGC,		3},
    {"Intersected",	(PyCFunction)pixmap_Intersected,	1},
    {"GetXbmStrings",	(PyCFunction)pixmap_GetXbmStrings,	1},
    {NULL,		NULL}
};

static PyObject *
pixmap_getattr(PyObject *self, char *name)
{
    return Py_FindMethod(pixmap_methods, self, name);
}

static void pixmap_dealloc(PaxPixmapObject *self)
{
    if (self->owner)
	XFreePixmap(self->display, self->pixmap);
    PyMem_DEL(self);
}

PyTypeObject PaxPixmapType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxPixmap",		/*tp_name*/
	sizeof(PaxPixmapObject),/*tp_size*/
	0,			/*tp_itemsize*/
	(destructor)pixmap_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)pixmap_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};

PyObject *
PaxPixmap_FromPixmap(Display *display, Pixmap pixmap, int owner)
{
    PaxPixmapObject *p = PyObject_NEW(PaxPixmapObject, &PaxPixmapType);
    if (p == NULL)
	return NULL;
    p->display = display;
    p->pixmap = pixmap;
    p->owner = owner;
    return (PyObject *) p;
}

Pixmap
PaxPixmap_AsPixmap(PyObject *obj)
{
    if (obj && PaxPixmap_Check(obj))
	return ((PaxPixmapObject *) obj)->pixmap;
    PyErr_BadInternalCall();
    return 0;
}
