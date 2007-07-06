#include <Python.h>
#include <structmember.h>
#include "tkwinobject.h"
#include <X11/Xutil.h>
#include "gcobject.h"
#include "cmapobject.h"
#include "pixmapobject.h"
#include "regionobject.h"
#include "fontobject.h"
#include "imageobject.h"
#include "paxutil.h"

PyObject *
TkWin_FromTkWindow(Tcl_Interp * interp, Tk_Window tkwin)
{
    TkWinObject * self;

    self = PyObject_NEW(TkWinObject, &TkWinType);
    if (self == NULL)
	return NULL;

    self->interp = interp;
    self->tkwin = tkwin;
	
    return (PyObject*)self;
}

Tk_Window
TkWin_AsTkWindow(PyObject * self)
{
    if (self && TkWin_Check(self))
	return ((TkWinObject*)self)->tkwin;
    PyErr_BadInternalCall();
    return NULL;
}

Window
TkWin_AsWindowID(PyObject * self)
{
    if (self && TkWin_Check(self))
	return Tk_WindowId(((TkWinObject*)self)->tkwin);
    PyErr_BadInternalCall();
    return None;
}


static void
tkwin_dealloc(TkWinObject * self)
{
    PyMem_DEL(self);
}


static int
tkwin_compare(TkWinObject * self, TkWinObject * other)
{
    return strcmp(Tk_PathName(self->tkwin), Tk_PathName(other->tkwin));
}

static PyObject *
tkwin_repr(TkWinObject * self)
{
    return PyString_FromString(Tk_PathName(self->tkwin));
}


#define TKWIN_COBJ_METHOD(name,tkfunc) \
static PyObject * \
tkwin_##name(TkWinObject * self, PyObject * args)\
{\
    return PyCObject_FromVoidPtr(tkfunc(self->tkwin), NULL);\
}

/* these methods are good for passing the display and visual to other
   c-functions */
TKWIN_COBJ_METHOD(c_display, Tk_Display)
TKWIN_COBJ_METHOD(c_visual, Tk_Visual)
    

static PyObject *
tkwin_colormap(TkWinObject * self, PyObject * args)
{
    return PaxCMap_FromColormap(Tk_Colormap(self->tkwin),
				Tk_Display(self->tkwin), 0);
}


static PyObject *
tkwin_QueryPointer(TkWinObject * self, PyObject * args)
{
    Window root = None, child = None;
    int root_x = 0, root_y = 0, win_x = 0, win_y = 0;
    unsigned int mask = 0;
    Bool retval;
    
    if (!PyArg_ParseTuple(args, ""))
	return NULL;
    
    retval = XQueryPointer(Tk_Display(self->tkwin),
			   Tk_WindowId(self->tkwin),
			   &root, &child, &root_x, &root_y,
			   &win_x, &win_y, &mask);
    if (retval) {
	return Py_BuildValue("(iiiiiii)", root, child, root_x, root_y,
			     win_x, win_y, mask);
    } else {
	Py_INCREF(Py_None);
	return Py_None;
    }
}


static PyObject *
tkwin_CreateColormap(TkWinObject * self, PyObject * args)
{
    int alloc;
    Colormap colormap;

    if (!PyArg_ParseTuple(args, "i", &alloc))
	return NULL;
    colormap = XCreateColormap(Tk_Display(self->tkwin),
			       DefaultRootWindow(Tk_Display(self->tkwin)),
			       Tk_Visual(self->tkwin),
			       alloc);
    if (colormap == 0)
    {
	PyErr_SetString(PyExc_RuntimeError, "CreateColormap failed");
	return NULL;
    }
    return PaxCMap_FromColormap(colormap, Tk_Display(self->tkwin), 1);
}

static PyObject *
tkwin_SetColormap(TkWinObject * self, PyObject * args)
{
    Colormap cmap;
    PyObject * cmap_obj;

    if (!PyArg_ParseTuple(args, "O!", &PaxCMapType, &cmap_obj))
	return NULL;

    cmap = PaxCMap_AsColormap(cmap_obj);
    Tk_SetWindowColormap(self->tkwin, cmap);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
tkwin_SetBackground(TkWinObject * self, PyObject * args)
{
    PyObject * bgobject;

    if (!PyArg_ParseTuple(args, "O", &bgobject))
	return NULL;

    if (PyInt_Check(bgobject))
	Tk_SetWindowBackground(self->tkwin, PyInt_AsLong(bgobject));
    else if (PaxPixmap_Check(bgobject))
	Tk_SetWindowBackgroundPixmap(self->tkwin,
				     PaxPixmap_AsPixmap(bgobject));
    else
	return PyErr_Format(PyExc_TypeError,
			    "argument must be integer or pixmap");
	
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
tkwin_SetBorderWidth(TkWinObject * self, PyObject * args)
{
    int width;

    if (!PyArg_ParseTuple(args, "i", &width))
	return NULL;

    Tk_SetWindowBorderWidth(self->tkwin, width);
	
    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
tkwin_SetBorder(TkWinObject * self, PyObject * args)
{
    unsigned long pixel;

    if (!PyArg_ParseTuple(args, "l", &pixel))
	return NULL;

    Tk_SetWindowBorder(self->tkwin, pixel);
	
    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
tkwin_CreateGC(TkWinObject * self, PyObject* args, PyObject * kwargs)
{
    Window win;
    Display * display;
    GC gc;
    unsigned long mask = 0;
    XGCValues values;
    PyObject * dict;

    if (PySequence_Length(args) > 0)
    {
	if (!PyArg_ParseTuple(args, "O", &dict))
	    return NULL;
    }
    else
	dict = kwargs;

    win = Tk_WindowId(self->tkwin);
    display = Tk_Display(self->tkwin);

    if (dict)
    {
	if (!PaxGC_MakeValues(dict, &mask, &values))
	    return NULL;
    }

    gc = XCreateGC(display, win, mask, &values);
    return PaxGC_FromGC(display, win, gc, PAXGC_OWNED, NULL);
}

static PyObject *
tkwin_GetGC(TkWinObject * self, PyObject* args, PyObject * kwargs)
{
    Display * display;
    GC gc;
    unsigned long mask = 0;
    XGCValues values;
    PyObject * dict;

    if (PySequence_Length(args) > 0)
    {
	if (!PyArg_ParseTuple(args, "O", &dict))
	    return NULL;
    }
    else
	dict = kwargs;

    display = Tk_Display(self->tkwin);

    if (dict)
    {
	if (!PaxGC_MakeValues(dict, &mask, &values))
	    return NULL;
    }
    gc = Tk_GetGC(self->tkwin, mask, &values);
    return PaxGC_FromGC(display, Tk_WindowId(self->tkwin), gc, PAXGC_SHARED,
		       NULL);
}

static PyObject *
tkwin_CreatePixmap(TkWinObject * self, PyObject * args)
{
    Tk_Window tkwin = self->tkwin;
    Display *display = Tk_Display(self->tkwin);
    int width, height;
    int depth;
    Pixmap pixmap;
    Drawable d;
	    
    display = Tk_Display(tkwin);
    width = Tk_Width(tkwin);
    height = Tk_Height(tkwin);
    depth = Tk_Depth(tkwin);
    if (!PyArg_ParseTuple(args, "|iii", &width, &height, &depth))
	return NULL;
	
    d = RootWindowOfScreen(Tk_Screen(tkwin));
    
    pixmap = XCreatePixmap(display, d, width, height, depth);
    return PaxPixmap_FromPixmap(display, pixmap, 1);
}


PyObject *
tkwin_ReadBitmapFile(TkWinObject * self, PyObject * args)
{
    Display	*display;
    Drawable	d;
    char *	arg1;
    unsigned int width, height;
    int hotspot_x, hotspot_y, error;
    Pixmap	bitmap;
    PyObject *pixmap, *tuple;
    
    if (!PyArg_ParseTuple(args, "s", &arg1))
	return NULL;
    
    display = Tk_Display(self->tkwin);
    d = RootWindowOfScreen(Tk_Screen(self->tkwin));
    error = XReadBitmapFile(display, d, arg1,
			    &width, &height, &bitmap,
			    &hotspot_x, &hotspot_y);
    /* Check error code, create a message to be returned as well as the error
     * code when the exception is raised.
     */
    tuple = NULL;
    switch (error)
    {
    case BitmapOpenFailed:
	PyErr_SetString(PyExc_IOError,
			"XReadBitMapFile - cannot open file");
	break;
    case BitmapFileInvalid:
	PyErr_SetString(PyExc_RuntimeError,
			"XReadBitMapFile - invalid bitmap data in file");
	break;
    case BitmapNoMemory:
	PyErr_SetString(PyExc_MemoryError,
			"XReadBitMapFile - no memory !!");
	break;
    case BitmapSuccess:
	/*
	 * Setup a tuple to be returned containing the info.
	 * returned from the call.
	 */
	pixmap = PaxPixmap_FromPixmap(display, bitmap, 1);
	if (pixmap != NULL)
	{
	    tuple = Py_BuildValue("(iiOii)", width, height, pixmap,
				  hotspot_x, hotspot_y);
	    Py_DECREF(pixmap);
	}
	break;
    default:
	PyErr_SetString(PyExc_SystemError,
			"XReadBitMapFile returned strange error");
	break;
    }

    return tuple;		/* will be NULL on error */
}


static PyObject *
tkwin_CreateImage(TkWinObject *self, PyObject *args)
{
    unsigned int depth, width, height;
    int format, offset, bitmap_pad, bytes_per_line;
    char *data, *newdata;
    int datalength;
    XImage *ximage;

    if (!PyArg_ParseTuple(args, "iiiz#iiii", &depth, &format, &offset,
			  &data, &datalength, &width, &height, &bitmap_pad,
			  &bytes_per_line))
	return NULL;
    newdata = PyMem_NEW(char, bytes_per_line * height);
    if (newdata == NULL)
	return PyErr_NoMemory();
    if (data)
    	memcpy(newdata, data, datalength);
    
    ximage = XCreateImage(Tk_Display(self->tkwin), Tk_Visual(self->tkwin),
			  depth, format, offset, newdata, width,
			  height, bitmap_pad, bytes_per_line);
    if (ximage == NULL)
    {
	PyErr_SetString(PyExc_RuntimeError, "XCreateImage failed");
	PyMem_DEL(newdata);
	return NULL;
    }
    return PaxImage_FromImage(ximage);
}

#ifndef PAX_NO_XSHM
static PyObject *
tkwin_ShmCreateImage(TkWinObject *self, PyObject *args)
{
    /* XXX error handling in this function is incomplete */
    unsigned int depth, width, height;
    int format;
    char *data;
    int datalength;
    XImage *ximage = NULL;
    XShmSegmentInfo * shminfo = NULL;
    PyObject * retval = NULL;
    int read_only = 0;

    if (!PyArg_ParseTuple(args, "iiz#ii|i", &depth, &format,
			  &data, &datalength, &width, &height, &read_only))
	return NULL;
	
    /* create shminfo */
    shminfo = PyMem_NEW(XShmSegmentInfo, 1);
    if (shminfo == NULL)
	return PyErr_NoMemory();
    shminfo->shmid = -1;
    shminfo->shmaddr = (char*) -1;

    ximage = XShmCreateImage(Tk_Display(self->tkwin), Tk_Visual(self->tkwin),
			     depth, format, NULL, shminfo,
			     width, height);
    if (ximage == NULL)
    {
	PyErr_SetString(PyExc_RuntimeError, "XShmCreateImage failed");
	goto error;
    }

    /* allocate the shm segment */
    shminfo->shmid = shmget(IPC_PRIVATE,
			    ximage->bytes_per_line * ximage->height,
			    IPC_CREAT | 0777);
    if (shminfo->shmid == -1)
    {
	PyErr_SetFromErrno(PyExc_RuntimeError);
	goto error;
    }

    shminfo->shmaddr = ximage->data = shmat(shminfo->shmid, 0, 0);
    if (shminfo->shmaddr == (char*)-1)
    {
	PyErr_SetFromErrno(PyExc_RuntimeError);
	goto error;
    }
	
    if (read_only)
	shminfo->readOnly = True;
    else
	shminfo->readOnly = False;

    if (!XShmAttach(Tk_Display(self->tkwin), shminfo))
    {
	PyErr_SetString(PyExc_RuntimeError, "XShmAttach failed");
	goto error;
    }
    XSync(Tk_Display(self->tkwin), False);
	
    retval = PaxImage_FromShmImage(ximage, shminfo, Tk_Display(self->tkwin));
    if (!retval)
	goto error;

    /* copy the data */
    if (data)
    {
	/*printf("ShmCreateImage: copy data\n");*/
	if (datalength <= ximage->bytes_per_line * ximage->height)
	{
	    memcpy(shminfo->shmaddr, data, datalength);
	}
	else
	{
	    fprintf(stderr, "image data longer that ximage\n");
	}
    }
	
    return (PyObject*)retval;

 error:
    if (ximage)
	XDestroyImage(ximage);
    if (shminfo)
    {
	if (shminfo->shmaddr != (char*) -1)
	    shmdt(shminfo->shmaddr);
	if (shminfo->shmid != -1)
	    shmctl(shminfo->shmid, IPC_RMID, 0);
	PyMem_DEL(shminfo);
    }
    return NULL;
}


static PyObject *
tkwin_ShmQueryExtension(TkWinObject *self, PyObject *args)
{
    return PyInt_FromLong(XShmQueryExtension(Tk_Display(self->tkwin)));
}

static PyObject *
tkwin_ShmQueryVersion(TkWinObject *self, PyObject *args)
{
    int major, minor;
    Bool pixmaps;

    XShmQueryVersion(Tk_Display(self->tkwin), &major, &minor, &pixmaps);
        
    return Py_BuildValue("iii", major, minor, pixmaps);
}

static PyObject *
tkwin_ShmCompletionEventType(TkWinObject * self, PyObject *args)
{
    return PyInt_FromLong(XShmGetEventBase(Tk_Display(self->tkwin))
			  + ShmCompletion);
}

static int shmerror = 0;

static int
shm_error_handler(Display* display, XErrorEvent * errevent)
{
    shmerror += 1;
    return 0;
}

static PyObject * try_shm_image(TkWinObject * self)
{
    XImage *ximage = NULL;
    XShmSegmentInfo * shminfo = NULL;
	
    /* create shminfo */
    shminfo = PyMem_NEW(XShmSegmentInfo, 1);
    if (shminfo == NULL)
	return PyErr_NoMemory();
    shminfo->shmid = -1;
    shminfo->shmaddr = (char*) -1;

    ximage = XShmCreateImage(Tk_Display(self->tkwin),
			     Tk_Visual(self->tkwin),
			     Tk_Depth(self->tkwin), ZPixmap, NULL,
			     shminfo, 1, 1);
    if (ximage == NULL)
    {
	PyErr_SetString(PyExc_RuntimeError, "XShmCreateImage failed");
	goto error;
    }

    /* allocate the shm segment */
    shminfo->shmid = shmget(IPC_PRIVATE,
			    ximage->bytes_per_line * ximage->height,
			    IPC_CREAT | 0777);
    if (shminfo->shmid == -1)
    {
	PyErr_SetFromErrno(PyExc_RuntimeError);
	goto error;
    }

    shminfo->shmaddr = ximage->data = shmat(shminfo->shmid, 0, 0);
    if (shminfo->shmaddr == (char*) -1)
    {
	PyErr_SetFromErrno(PyExc_RuntimeError);
	goto error;
    }
	
    shminfo->readOnly = True;
    
    XShmAttach(Tk_Display(self->tkwin), shminfo);
    XSync(Tk_Display(self->tkwin), False);

    if (shmerror)
    {
	XDestroyImage(ximage);
	shmdt(shminfo->shmaddr);
	shmctl(shminfo->shmid, IPC_RMID, 0);
	PyMem_DEL(shminfo);
	Py_INCREF(Py_None);
	return Py_None;
    }

    return PaxImage_FromShmImage(ximage, shminfo, Tk_Display(self->tkwin));

 error:
    if (ximage)
	XDestroyImage(ximage);
    if (shminfo)
    {
	if (shminfo->shmaddr != (char*) -1)
	    shmdt(shminfo->shmaddr);
	if (shminfo->shmid != -1)
	    shmctl(shminfo->shmid, IPC_RMID, 0);
	PyMem_DEL(shminfo);
    }
    return NULL;
}
    

static PyObject *
tkwin_ShmCheckExtension(TkWinObject * self, PyObject * args)
{
    PyObject * result;
    
    if (XShmQueryExtension(Tk_Display(self->tkwin)))
    {
	int (*orighandler)(Display *, XErrorEvent *);

	shmerror = 0;
	orighandler = XSetErrorHandler(shm_error_handler);
	result = try_shm_image(self);
	XSetErrorHandler(orighandler);
    }
    else
    {
	Py_INCREF(Py_None);
	result = Py_None;
    }

    return result;
}


#else /* ifdef PAX_NO_XSHM */

/* if shared memory images are not compiled in, provide the query
 * function nonetheless, to allow programs to check for availability of this
 * feature. In this case the return value will always be false.
 */

static PyObject *
tkwin_ShmCheckExtension(TkWinObject *self, PyObject *args)
{
    Py_INCREF(Py_None);
    return Py_None;
}

#endif /* ifdef PAX_NO_XSHM */

static PyObject *
tkwin_ClearArea(TkWinObject *self, PyObject *args)
{
    int x;
    int y;
    unsigned int width;
    unsigned int height;
    int exposures;
    
    if (!PyArg_ParseTuple(args, "iiiii", &x, &y, &width, &height, &exposures))
	return NULL;

    if (Tk_IsMapped(self->tkwin))
        XClearArea(Tk_Display(self->tkwin),Tk_WindowId(self->tkwin),
		   x, y, width, height, (Bool)exposures);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *
tkwin_CopyArea(TkWinObject * self, PyObject * args)
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
	if (Tk_IsMapped(self->tkwin))
	    dest = Tk_WindowId(((TkWinObject*) destobj)->tkwin);
	else
	{
	    Py_INCREF(Py_None);
	    return Py_None;
	}
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
    if (gcobj == Py_None)
	gc = DefaultGCOfScreen(Tk_Screen(self->tkwin));
    else
    {
	gc = PaxGC_AsGC(gcobj);
	if (PyErr_Occurred())
	    return NULL;
    }

    XCopyArea(Tk_Display(self->tkwin), Tk_WindowId(self->tkwin),
	      dest, gc, src_x, src_y, width, height, dest_x, dest_y);

    Py_INCREF(Py_None);
    return Py_None;
}


static PyObject *
tkwin_CreateRegion(TkWinObject * self, PyObject * args)
{
    return PaxRegion_FromRegion(XCreateRegion());
}

static PyObject *
tkwin_PolygonRegion(TkWinObject *self, PyObject *args)
{
    Region reg;
    PyObject *list;
    XPoint *points;
    int npoints, fill_rule = EvenOddRule;

    if (!PyArg_ParseTuple(args, "O|i", &list, &fill_rule))
	return NULL;
    if (!pax_checkshortlist(2, list, (short**)&points, &npoints))
    {
	if (!PyErr_Occurred())
	    PyErr_SetString(PyExc_TypeError, "arg1 should be XPoint[]");
	return NULL;
    }
    reg = XPolygonRegion(points, npoints, fill_rule);
    PyMem_DEL(points);
    if (reg == NULL)
	return PyErr_NoMemory();
    return PaxRegion_FromRegion(reg);
}


static PyObject *
tkwin_ListFonts(TkWinObject *self, PyObject *args)
{
    char *pattern;
    char **fontnames;
    int count;
    PyObject *list;
    
    if (!PyArg_ParseTuple(args, "s", &pattern))
	return NULL;
    
    fontnames = XListFonts(Tk_Display(self->tkwin), pattern, 10000, &count);
    if (fontnames == NULL)
	count = 0;
    list = PyList_New(count);
    if (list != NULL)
    {
	int i;
	for (i = 0; i < count; i++)
	{
	    PyObject *item = PyString_FromString(fontnames[i]);
	    if (item == NULL)
	    {
		Py_DECREF(list);
		list = NULL;
		break;
	    }
	    PyList_SetItem(list, i, item);
	}
    }
    if (fontnames != NULL)
	XFreeFontNames(fontnames);
    return list;
}

static PyObject *
tkwin_LoadQueryFont(TkWinObject *self, PyObject *args)
{
    char *name;
    PyObject *result;
    
    if (!PyArg_ParseTuple(args, "s", &name))
	return NULL;
    result = PaxFont_FromName(Tk_Display(self->tkwin), name);
    return result;
}

static PyObject *
tkwin_QueryBestCursor(TkWinObject * self, PyObject * args)
{
    unsigned int width, height, ret_width, ret_height;

    if (!PyArg_ParseTuple(args, "ii", &width, &height))
	return NULL;

    XQueryBestCursor(Tk_Display(self->tkwin), Tk_WindowId(self->tkwin),
		     width, height, &ret_width, &ret_height);
    return Py_BuildValue("ii", ret_width, ret_height);
}

static PyObject *
tkwin_Sync(TkWinObject * self, PyObject * args)
{
    XSync(Tk_Display(self->tkwin), False);
    Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef tkwin_methods[] = {
    {"QueryPointer",	(PyCFunction)tkwin_QueryPointer,	1},
    {"CreatePixmap",	(PyCFunction)tkwin_CreatePixmap,	1},
    {"ReadBitmapFile",	(PyCFunction)tkwin_ReadBitmapFile,	1},
    {"ClearArea",	(PyCFunction)tkwin_ClearArea,		1},
    {"CopyArea",	(PyCFunction)tkwin_CopyArea,		1},
    {"CreateRegion",	(PyCFunction)tkwin_CreateRegion,	1},
    {"PolygonRegion",	(PyCFunction)tkwin_PolygonRegion,	1},
    {"CreateColormap",	(PyCFunction)tkwin_CreateColormap,	1},
    {"SetColormap",	(PyCFunction)tkwin_SetColormap,		1},
    {"CreateGC",	(PyCFunction)tkwin_CreateGC,		3},
    {"GetGC",		(PyCFunction)tkwin_GetGC,		3},
    {"colormap",	(PyCFunction)tkwin_colormap,		1},
    {"ListFonts",	(PyCFunction)tkwin_ListFonts,		1},
    {"LoadQueryFont",	(PyCFunction)tkwin_LoadQueryFont,	1},
    {"CreateImage",	(PyCFunction)tkwin_CreateImage,		1},
    {"SetBackground",	(PyCFunction)tkwin_SetBackground,	1},
    {"SetBorder",	(PyCFunction)tkwin_SetBorder,		1},
    {"SetBorderWidth",	(PyCFunction)tkwin_SetBorderWidth,	1},
#ifndef PAX_NO_XSHM
    {"ShmCreateImage",	(PyCFunction)tkwin_ShmCreateImage,	1},
    {"ShmQueryVersion",	(PyCFunction)tkwin_ShmQueryVersion,	1},
    {"ShmCompletionEventType", (PyCFunction)tkwin_ShmCompletionEventType, 1},
    {"ShmQueryExtension",(PyCFunction)tkwin_ShmQueryExtension,	1},
#endif
    /* ShmCheckExtension is always available. see above */
    {"ShmCheckExtension",(PyCFunction)tkwin_ShmCheckExtension,	1},
    
    {"QueryBestCursor",	(PyCFunction)tkwin_QueryBestCursor,	1},
    {"Sync",		(PyCFunction)tkwin_Sync,		1},
    {"c_display",	(PyCFunction)tkwin_c_display,		1},
    {"c_visual",	(PyCFunction)tkwin_c_visual,		1},
    {NULL,	NULL}
};


static PyObject * getintattr(TkWinObject * self, char * name)
{
    int value;

    if (*name == 'w' && strcmp(name, "width") == 0)
	value = Tk_Width(self->tkwin);
    else if (*name == 'h' && strcmp(name, "height") == 0)
	value = Tk_Height(self->tkwin);
    else if (*name == 'x' && name[1] == '\0')
	value = Tk_X(self->tkwin);
    else if (*name == 'y' && name[1] == '\0')
	value = Tk_Y(self->tkwin);
    else if (*name == 'd' && strcmp(name, "depth") == 0)
	value = Tk_Depth(self->tkwin);
    else
	return NULL;

    return PyInt_FromLong(value);
}

static PyObject *
tkwin_getattr(PyObject * self, char * name)
{
    PyObject * result;
    result = getintattr((TkWinObject*)self, name);
    if (result)
	return result;
    return Py_FindMethod(tkwin_methods, self, name);
}


PyTypeObject TkWinType = {
    PyObject_HEAD_INIT(&PyType_Type)
    0,
    "tkwin",
    sizeof(TkWinObject),
    0,
    (destructor)tkwin_dealloc,	/*tp_dealloc*/
    (printfunc)NULL,		/*tp_print*/
    tkwin_getattr,		/*tp_getattr*/
    0,				/*tp_setattr*/
    (cmpfunc)tkwin_compare,	/*tp_compare*/
    (reprfunc)tkwin_repr,	/*tp_repr*/
    0,				/*tp_as_number*/
    0,				/*tp_as_sequence*/
    0,				/*tp_as_mapping*/
    0,				/*tp_hash*/
    (ternaryfunc)0,		/*tp_call*/ 
};
