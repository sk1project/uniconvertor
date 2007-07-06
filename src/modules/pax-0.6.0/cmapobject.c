#include "Python.h"
#include <X11/Xlib.h>
#include "cmapobject.h"

typedef struct PaxCMapObject_
{
    PyObject_HEAD
    int		owner;
    Colormap	colormap;
    Display *	display;
} PaxCMapObject;

static PyObject *
paxcm_AllocColorCells(PaxCMapObject *self, PyObject *args)
{
    int contig, nplanes, npixels;
    int i;
    unsigned long *plane_masks, *pixels;
    PyObject *res1, *res2, *res;

    if (!PyArg_ParseTuple(args, "iii", &contig, &nplanes, &npixels))
	return NULL;
    if (npixels <= 0 || nplanes < 0)
    {
	PyErr_BadArgument();
	return NULL;
    }
    plane_masks = PyMem_NEW(unsigned long, nplanes);
    pixels = PyMem_NEW(unsigned long, npixels);
    if (plane_masks == NULL || pixels == NULL)
    {
	if (plane_masks)
	    PyMem_DEL(plane_masks);
	if (pixels)
	    PyMem_DEL(pixels);
	return PyErr_NoMemory();
    }
    if (!XAllocColorCells(self->display, self->colormap, contig,
			  plane_masks, nplanes, pixels, npixels))
    {
	PyErr_SetString(PyExc_RuntimeError, "XAllocColorCells failed");
	PyMem_DEL(plane_masks);
	PyMem_DEL(pixels);
	return NULL;
    }

    res1 = PyList_New(nplanes);
    for (i = 0; i < nplanes; i++)
	PyList_SetItem(res1, i, PyInt_FromLong(plane_masks[i]));
    res2 = PyList_New(npixels);
    for (i = 0; i < npixels; i++)
	PyList_SetItem(res2, i, PyInt_FromLong(pixels[i]));
    PyMem_DEL(plane_masks);
    PyMem_DEL(pixels);
    if (PyErr_Occurred())
    {
	Py_XDECREF(res1);
	Py_XDECREF(res2);
	return NULL;
    }
    res = Py_BuildValue("(OO)", res1, res2);
    Py_DECREF(res1);
    Py_DECREF(res2);
    return res;
}

static PyObject *
paxcm_StoreColors(PaxCMapObject *self, PyObject *args)
{
    XColor *color;
    int ncolors;
    PyObject *colorlist;
    PyObject *item;
    int i;
    int red, green, blue;

    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &colorlist))
	return NULL;
    ncolors = PyList_Size(colorlist);
    color = PyMem_NEW(XColor, ncolors);
    if (color == NULL)
	return PyErr_NoMemory();
    for (i = 0; i < ncolors; i++)
    {
	item = PyList_GetItem(colorlist, i);
	if (!PyTuple_Check(item) || PyTuple_Size(item) != 5)
	{
	    PyMem_DEL(color);
	    PyErr_BadArgument();
	    return NULL;
	}
	/* don't use 'h' here because Python 2.0 does some range
	 * checking but tests for signed shorts not the unsigned we
	 * need. It introduces H for unsigned short but that's not
	 * available in 1.5.2 */
	if (!PyArg_ParseTuple(item, "liiib", &color[i].pixel,
			      &red, &green, &blue, &color[i].flags))
	{
	    PyMem_DEL(color);
	    return NULL;
	}
	color[i].red = red;
	color[i].green = green;
	color[i].blue = blue;
    }

    XStoreColors(self->display, self->colormap, color, ncolors);

    PyMem_DEL(color);
    if (PyErr_Occurred())
	return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
paxcm_AllocNamedColor(PaxCMapObject *self, PyObject *args)
{
    char *color_name;
    XColor screen_def, exact_def;

    if (!PyArg_ParseTuple(args, "s", &color_name))
	return NULL;
    if (!XAllocNamedColor(self->display, self->colormap,
			  color_name, &screen_def, &exact_def))
    {
	PyErr_SetString(PyExc_RuntimeError, "XAllocNamedColor failed");
	return NULL;
    }
    return Py_BuildValue("((iiiii)(iiiii))",
			 screen_def.pixel, screen_def.red,
			 screen_def.green, screen_def.blue, screen_def.flags,
			 exact_def.pixel, exact_def.red, exact_def.green,
			 exact_def.blue, exact_def.flags);
}

static PyObject *
paxcm_AllocColor(PaxCMapObject *self, PyObject *args)
{
    XColor screen;
    int red, green, blue;

    /* don't use 'h' here because Python 2.0 does some range checking
     * but tests for signed shorts not the unsigned we need. It
     * introduces H for unsigned short but that's not available in 1.5.2
     */
    if (!PyArg_ParseTuple(args, "iii", &red, &green, &blue))
	return NULL;
    screen.red = red;
    screen.green = green;
    screen.blue = blue;
    screen.pixel = 0;
    screen.flags = 0;
    if (!XAllocColor(self->display, self->colormap, &screen))
    {
	PyErr_SetString(PyExc_RuntimeError, "XAllocColor failed");
	return NULL;
    }

    return Py_BuildValue("(iiiii))", screen.pixel, screen.red, screen.green,
			 screen.blue, screen.flags);
}

static PyObject *
paxcm_QueryColor(PaxCMapObject *self, PyObject *args)
{
    XColor def;

    def.flags = 0;
    if (!PyArg_ParseTuple(args, "l", &def.pixel))
	return NULL;
    XQueryColor(self->display, self->colormap, &def);

    return Py_BuildValue("(iiiii))", def.pixel, def.red, def.green, def.blue,
			 def.flags);
}

static PyObject *
paxcm_QueryColors(PaxCMapObject *self, PyObject *args)
{
    XColor *defs;
    PyObject *pixels;
    PyObject *list = NULL;	/* init in case something goes wrong */
    PyObject *item;
    int i;
    int npixels;

    if (!PyArg_ParseTuple(args, "O!", &PyList_Type, &pixels))
	return NULL;
    
    npixels = PyList_Size(pixels);
    defs = PyMem_NEW(XColor, npixels);
    if (defs == NULL)
	return PyErr_NoMemory();
    
    for (i = 0; i < npixels; i++)
    {
	item = PyList_GetItem(pixels, i);
	if (!PyInt_Check(item))
	{
	    PyErr_BadArgument();
	    goto done;
	}
	defs[i].pixel = PyInt_AsLong(item);
    }

    XQueryColors(self->display, self->colormap, defs, npixels);

    list = PyList_New(npixels);
    if (list == NULL)
	goto done;
    for (i = 0; i < npixels; i++)
    {
	item = Py_BuildValue("(iiiii)", defs[i].pixel, defs[i].red,
			     defs[i].green, defs[i].blue, defs[i].flags);
	if (item == NULL || PyList_SetItem(list, i, item))
	{
	    Py_DECREF(list);
	    list = NULL;
	    goto done;
	}
    }
done:
    PyMem_DEL(defs);
    return list;
}

static PyObject *
paxcm_LookupColor(PaxCMapObject *self, PyObject *args)
{
    char *color_name;
    XColor screen_def, exact_def;

    if (!PyArg_ParseTuple(args, "s", &color_name))
	return NULL;

    if (!XLookupColor(self->display, self->colormap, color_name,
		      &exact_def, &screen_def))
    {
	PyErr_SetString(PyExc_RuntimeError, "XLookupColor failed");
	return NULL;
    }

    return Py_BuildValue("((iiiii)(iiiii))", exact_def.pixel, exact_def.red,
			 exact_def.green, exact_def.blue, exact_def.flags,
			 screen_def.pixel, screen_def.red, screen_def.green,
			 screen_def.blue, screen_def.flags);
}

static PyObject *
paxcm_ParseColor(PaxCMapObject *self, PyObject *args)
{
    XColor exact_def;
    char *color_name;

    if (!PyArg_ParseTuple(args, "s", &color_name))
	return NULL;
    if (!XParseColor(self->display, self->colormap, color_name, &exact_def))
    {
	PyErr_SetString(PyExc_RuntimeError, "XParseColor failed");
	return NULL;
    }

    return Py_BuildValue("(iiiii))", exact_def.pixel, exact_def.red,
			 exact_def.green, exact_def.blue, exact_def.flags);
}

static PyObject *
paxcm_FreeColors(PaxCMapObject *self, PyObject *args)
{
    PyObject *pixellist, *item;
    unsigned long planes;
    unsigned long *pixels;
    int npixels;
    int i;

    if (!PyArg_ParseTuple(args, "O!l", &PyList_Type, &pixellist, &planes))
	return NULL;
    npixels = PyList_Size(pixellist);
    pixels = PyMem_NEW(unsigned long, npixels);
    if (pixels == NULL)
	return PyErr_NoMemory();
    for (i = 0; i < npixels; i++)
    {
	item = PyList_GetItem(pixellist, i);
	if (!PyInt_Check(item))
	{
	    PyMem_DEL(pixels);
	    PyErr_BadArgument();
	    return NULL;
	}
	pixels[i] = PyInt_AsLong(item);
    }

    XFreeColors(self->display, self->colormap, pixels, npixels, planes);

    PyMem_DEL(pixels);
    if (PyErr_Occurred())
	return NULL;
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
paxcm_CopyColormapAndFree(PaxCMapObject *self, PyObject *args)
{
    Colormap cmap;
    
    if (!PyArg_ParseTuple(args, ""))
	return NULL;

    cmap = XCopyColormapAndFree(self->display, self->colormap);
    if (!cmap)
    {
	PyErr_SetString(PyExc_RuntimeError, "XCopyColormapAndFree failed");
	return NULL;
    }

    return PaxCMap_FromColormap(cmap, self->display, 1);
}

static PyMethodDef paxcm_methods[] = {
    {"AllocColor",	(PyCFunction)paxcm_AllocColor,		1},
    {"AllocColorCells", (PyCFunction)paxcm_AllocColorCells,	1},
    {"AllocNamedColor", (PyCFunction)paxcm_AllocNamedColor,	1},
    {"FreeColors",	(PyCFunction)paxcm_FreeColors,		1},
    {"LookupColor",	(PyCFunction)paxcm_LookupColor,		1},
    {"ParseColor",	(PyCFunction)paxcm_ParseColor,		1},
    {"QueryColor",	(PyCFunction)paxcm_QueryColor,		1},
    {"QueryColors",	(PyCFunction)paxcm_QueryColors,		1},
    {"StoreColors",	(PyCFunction)paxcm_StoreColors,		1},
    {"CopyColormapAndFree",(PyCFunction)paxcm_CopyColormapAndFree, 1},
    {NULL, NULL}, 
};

static PyObject *
paxcm_getattr(PaxCMapObject *self, char *name)
{
    return Py_FindMethod(paxcm_methods, (PyObject *) self, name);
}

void
paxcm_dealloc(PaxCMapObject *self)
{
    if (self->owner)
	XFreeColormap(self->display, self->colormap);

    PyMem_DEL(self);
}

PyTypeObject PaxCMapType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxColormap",		/*tp_name*/
	sizeof(PaxCMapObject),	/*tp_size*/
	0,			/*tp_itemsize*/
	(destructor)paxcm_dealloc,/*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)paxcm_getattr, /*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};

PyObject *
PaxCMap_FromColormap(Colormap colormap, Display *display, int owner)
{
    PaxCMapObject *obj = PyObject_NEW(PaxCMapObject, &PaxCMapType);
    if (obj == NULL)
	return NULL;
    obj->colormap = colormap;
    obj->display = display;
    obj->owner = owner;
    return (PyObject *) obj;
}


Colormap
PaxCMap_AsColormap(PyObject* self)
{
    if (PaxCMap_Check(self))
    {
	return ((PaxCMapObject*)self)->colormap;
    }

    PyErr_BadInternalCall();
    return 0;
}
