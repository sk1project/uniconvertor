#include <stdio.h>

#include "Python.h"
#include "modsupport.h"
#include "structmember.h"

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "imageobject.h"

#include "tkwinobject.h"
#include "pixmapobject.h"

#define OFF(x) offsetof(XImage, x)
static struct memberlist image_memberlist[] = {
    {"width",		T_INT,		OFF(width),		RO},
    {"height",		T_INT,		OFF(height),		RO},
    {"xoffset",		T_INT,		OFF(xoffset),		RO},
    {"format",		T_INT,		OFF(format)},
    {"byte_order",	T_INT,		OFF(byte_order)},
    {"bitmap_unit",	T_INT,		OFF(bitmap_unit),	RO},
    {"bitmap_bit_order",T_INT,		OFF(bitmap_bit_order)},
    {"bitmap_pad",	T_INT,		OFF(bitmap_pad),	RO},
    {"depth",		T_INT,		OFF(depth),		RO},
    {"bytes_per_line",	T_INT,		OFF(bytes_per_line),	RO},
    {"bits_per_pixel",	T_INT,		OFF(bits_per_pixel),	RO},
    
    {"red_mask",	T_ULONG,	OFF(red_mask)},
    {"green_mask",	T_ULONG,	OFF(green_mask)},
    {"blue_mask",	T_ULONG,	OFF(blue_mask)},
    {NULL} 
};


static PyObject *
image_PutPixel(PaxImageObject * self, PyObject * args)
{
    int x, y;
    unsigned long value;

    if (!PyArg_ParseTuple(args, "iil", &x, &y, &value))
	return NULL;

    XPutPixel(self->ximage, x, y, value);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
image_GetPixel(PaxImageObject * self, PyObject * args)
{
    int x, y;

    if (!PyArg_ParseTuple(args, "ii", &x, &y))
	return NULL;

    return PyInt_FromLong(XGetPixel(self->ximage, x, y));
}

static PyObject *
image_dump_data(PaxImageObject * self, PyObject * args)
{
    char * filename;
    FILE * file;

    if (!PyArg_ParseTuple(args, "s", &filename))
	return NULL;

    file = fopen(filename, "w");
    if (!file)
    {
	PyErr_SetString(PyExc_IOError, "cannot open file");
	return NULL;
    }

    fwrite(self->ximage->data,
	   self->ximage->bytes_per_line, self->ximage->height, file);
    fclose(file);

    Py_INCREF(Py_None);
    return Py_None;
}

#ifndef PAX_NO_XSHM
static PyObject *
image_shm_get_image(PaxImageObject * self, PyObject * args)
{
    PyObject * drawable;
    Drawable d;
    int x, y;
    unsigned long plane_mask = 0xFFFFFFFF;

    if (!self->shminfo)
	return PyErr_Format(PyExc_TypeError,
			    "image is not a shared memory image");

    if (!PyArg_ParseTuple(args, "Oii|i", &drawable, &x, &y, &plane_mask))
	return NULL;

    if (PaxPixmap_Check(drawable))
	d = PaxPixmap_AsPixmap(drawable);
    else if (TkWin_Check(drawable))
	d = TkWin_AsWindowID(drawable);
    else
    {
	PyErr_SetString(PyExc_ValueError, "drawable must be window or pixmap");
	return NULL;
    }

    XShmGetImage(self->display, d, self->ximage, x, y, plane_mask);

    Py_INCREF(Py_None);
    return Py_None;
}
#endif
	
    

static PyMethodDef image_methods[] = {
    {"GetPixel",	(PyCFunction)image_GetPixel,		1},
    {"PutPixel",	(PyCFunction)image_PutPixel,		1},
    {"dump_data",	(PyCFunction)image_dump_data,		1},
#ifndef PAX_NO_XSHM
    {"shm_get_image",	(PyCFunction)image_shm_get_image,	1},
#endif
    {NULL, NULL}, 
};

static PyObject *
image_getattr(PaxImageObject *self, char *name)
{
    PyObject * result;
    
    result = PyMember_Get((char *)(self->ximage), image_memberlist, name);
    if (result != NULL)
	return result;
    /* PyMember_Get failed. reset exceptions */
    PyErr_Clear(); 

    return Py_FindMethod(image_methods, (PyObject *) self, name);
}

static void
image_dealloc(PaxImageObject *self)
{
#ifndef PAX_NO_XSHM
    if (self->shminfo)
    {
	XShmDetach(self->display, self->shminfo);
	XDestroyImage(self->ximage);
	shmdt(self->shminfo->shmaddr);
	shmctl(self->shminfo->shmid, IPC_RMID, 0);
	PyMem_DEL(self->shminfo);
    }
    else
#endif
	XDestroyImage(self->ximage);
    
    PyMem_DEL(self);
}

PyTypeObject PaxImageType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxXImage",		/*tp_name*/
	sizeof(PaxImageObject),	/*tp_size*/
	0,			/*tp_itemsize*/
	(destructor)image_dealloc, /*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)image_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};

XImage *
PaxImage_AsImage(PyObject *self)
{
    if (self->ob_type != &PaxImageType) {
	PyErr_BadArgument();
	return NULL;
    }
    return ((PaxImageObject *) self)->ximage;
}

PyObject *
PaxImage_FromImage(XImage *ximage)
{
	PaxImageObject *self = PyObject_NEW(PaxImageObject, &PaxImageType);

	if (self == NULL)
		return NULL;
	self->ximage = ximage;
#ifndef PAX_NO_XSHM
	self->shminfo = NULL;
	self->display = NULL;
#endif
	return (PyObject *) self;
}

#ifndef PAX_NO_XSHM
PyObject *
PaxImage_FromShmImage(XImage *ximage, XShmSegmentInfo * shminfo,
		      Display * display)
{
    PaxImageObject * self;

    self = (PaxImageObject*)PaxImage_FromImage(ximage);
    if (!self)
    {
	PyMem_DEL(shminfo);
	return NULL;
    }

    self->shminfo = shminfo;
    self->display = display;

    return (PyObject*)self;
}

#endif
