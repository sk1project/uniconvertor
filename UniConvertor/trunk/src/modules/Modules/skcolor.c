/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1997, 1998, 1999, 2000, 2001, 2002 by Bernhard Herzog
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include <math.h>
#include <Python.h>
#include <structmember.h>

#include "_sketchmodule.h"
#include "skcolor.h"

/*
 *	RGBColor
 */

#define SKCOLOR_COUNT_ALLOC 1
#define SKCOLOR_SUBALLOCATE 1


#if SKCOLOR_COUNT_ALLOC
static int skcolor_allocated = 0;
#endif

#if SKCOLOR_SUBALLOCATE
#define BLOCK_SIZE	1000	/* 1K less typical malloc overhead */
#define N_COLOROBJECTS	(BLOCK_SIZE / sizeof(SKColorObject))
static SKColorObject *
fill_free_list(void)
{
    SKColorObject *p, *q;
    p = PyMem_NEW(SKColorObject, N_COLOROBJECTS);
    if (p == NULL)
	return (SKColorObject *)PyErr_NoMemory();
    q = p + N_COLOROBJECTS;
    while (--q > p)
	q->ob_type = (PyTypeObject*)(q-1);
    q->ob_type = NULL;
    return p + N_COLOROBJECTS - 1;
}

static SKColorObject *free_list = NULL;
#endif /* SKCOLOR_SUBALLOCATE */

#define SKColor_CHECK_COMPONENT(comp) (0.0 <= (comp) && (comp) <= 1.0)
PyObject *
SKColor_FromRGB(double red, double green, double blue)
{
    SKColorObject * self;

    if (!SKColor_CHECK_COMPONENT(red)
	|| !SKColor_CHECK_COMPONENT(green)
	|| !SKColor_CHECK_COMPONENT(blue))
    {
	/*fprintf(stderr, "SKColor_FromRGB %g, %g, %g\n", red, green, blue);*/
	PyErr_SetString(PyExc_ValueError,
			"color components must be in the range [0.0 .. 1.0]");
	return NULL;
    }
    
#if SKCOLOR_SUBALLOCATE
    if (free_list == NULL) {
	if ((free_list = fill_free_list()) == NULL)
	    return NULL;
    }
    self = free_list;
    free_list = (SKColorObject *)(free_list->ob_type);
    self->ob_type = &SKColorType;
    _Py_NewReference(self);
#else
    self = PyObject_NEW(SKColorObject, &SKColorType);
    if (!self)
	return NULL;
#endif
    self->red = red;
    self->green = green;
    self->blue = blue;

#if SKCOLOR_COUNT_ALLOC
    skcolor_allocated++;
#endif

    return (PyObject*)self;
}

static void
skcolor_dealloc(SKColorObject * self)
{
#if SKCOLOR_SUBALLOCATE
    self->ob_type = (PyTypeObject*)free_list;
    free_list = self;
#else
    PyMem_DEL(self);
#endif
#if SKCOLOR_COUNT_ALLOC
    skcolor_allocated--;
#endif
}

#define COMPARE(c1,c2) ((c1) < (c2) ? -1 : ((c1) > (c2) ? +1 : 0 ))
static int
skcolor_compare(SKColorObject * v, SKColorObject * w)
{
    int result;

    if ((result = COMPARE(v->red, w->red)) != 0)
	return result;
    if ((result = COMPARE(v->green, w->green)) != 0)
	return result;
    return COMPARE(v->blue, w->blue);
}
#undef COMPARE

static long
skcolor_hash(SKColorObject * self)
{
    long x;

    x = self->red * 65535.0;
    x = (255 * x) ^ (long)(self->green * 65535.0);
    x = (255 * x) ^ (long)(self->blue * 65535.0);
    
    if (x == -1)
	return -2;
    return x;
}

static PyObject *
skcolor_repr(SKColorObject * self)
{
    char buf[1000];
    sprintf(buf, "RGBColor(%g,%g,%g)", self->red, self->green, self->blue);
    return PyString_FromString(buf);
}


static int
skcolor_length(PyObject *self)
{
    return 3;
}

static PyObject *
skcolor_concat(PyObject *self, PyObject *bb)
{
    PyErr_SetString(PyExc_RuntimeError,
		    "concat not supported for SKColorObjects");
    return NULL;
}

static PyObject *
skcolor_repeat(PyObject *self, int n)
{
    PyErr_SetString(PyExc_RuntimeError,
		    "repeat not supported for SKColorObjects");
    return NULL;
}

static PyObject *
skcolor_item(SKColorObject *self, int i)
{
    double item;
    switch (i)
    {
    case 0:
	item = self->red;
	break;
    case 1:
	item = self->green;
	break;
    case 2:
	item = self->blue;
	break;
    default:
	PyErr_SetString(PyExc_IndexError, "index must be 0, 1 or 2");
	return NULL;
    }

    return PyFloat_FromDouble(item);
}

static PyObject *
skcolor_slice(PyObject *self, int ilow, int ihigh)
{
    PyErr_SetString(PyExc_RuntimeError,
		    "slicing not supported for SKColorObjects");
    return NULL;
}

static PySequenceMethods skcolor_as_sequence = {
	skcolor_length,			/*sq_length*/
	skcolor_concat,			/*sq_concat*/
	skcolor_repeat,			/*sq_repeat*/
	(intargfunc)skcolor_item,	/*sq_item*/
	skcolor_slice,			/*sq_slice*/
	0,				/*sq_ass_item*/
	0,				/*sq_ass_slice*/
};



/*
 *	Python methods
 */

static PyObject *
skcolor_blend(SKColorObject * self, PyObject * args)
{
    SKColorObject * color2;
    double frac1, frac2;

    if (!PyArg_ParseTuple(args, "O!dd", &SKColorType, &color2, &frac1, &frac2))
	return NULL;

    return SKColor_FromRGB(frac1 * self->red + frac2 * color2->red,
			   frac1 * self->green + frac2 * color2->green,
			   frac1 * self->blue + frac2 * color2->blue);
}


#define OFF(x) offsetof(SKColorObject, x)
static struct memberlist skcolor_memberlist[] = {
    {"red",		T_FLOAT,	OFF(red),	RO},
    {"green",		T_FLOAT,	OFF(green),	RO},
    {"blue",		T_FLOAT,	OFF(blue),	RO},
    {NULL} 
};
#undef OFF


static struct PyMethodDef skcolor_methods[] = {
    {"Blend",		(PyCFunction)skcolor_blend,		1},
    {NULL,	NULL}
};


static PyObject *
skcolor_getattr(PyObject * self, char * name)
{
    PyObject * result;

    result = Py_FindMethod(skcolor_methods, self, name);
    if (result != NULL)
	return result;
    PyErr_Clear();

    return PyMember_Get((char *)self, skcolor_memberlist, name);
}



PyTypeObject SKColorType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"skcolor",
	sizeof(SKColorObject),
	0,
	(destructor)skcolor_dealloc,	/*tp_dealloc*/
	(printfunc)NULL,		/*tp_print*/
	skcolor_getattr,		/*tp_getattr*/
	0,				/*tp_setattr*/
	(cmpfunc)skcolor_compare,	/*tp_compare*/
	(reprfunc)skcolor_repr,		/*tp_repr*/
	0,				/*tp_as_number*/
	&skcolor_as_sequence,		/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	(hashfunc)&skcolor_hash,	/*tp_hash*/
	(ternaryfunc)0,			/*tp_call */
};





/*
 * SKVisual
 *
 * Handle the color capabilities of variuous X visuals. This type
 * provides methods to convert device independent color descriptions
 * (currently RGBColor) to device dependent pixel values.
 */


/*
 *	functions for true color visuals
 */

// static PyObject *
// skvisual_truecolor_get_pixel(SKVisualObject * self, SKColorObject * color)
// {
//     int r, g, b;
// /*    double gamma = 1.0 / 2.2;*/
//     
//     r = rint(pow(color->red, self->gamma_inv) * 255);
//     g = rint(pow(color->green, self->gamma_inv) * 255);
//     b = rint(pow(color->blue, self->gamma_inv) * 255);
//     
// /*    r = rint(color->red * 255);
//     g = rint(color->green * 255);
//     b = rint(color->blue * 255);*/
// 
//     return PyInt_FromLong(self->red_bits[r] | self->green_bits[g]
// 			  | self->blue_bits[b]);
// }

// static int
// skvisual_init_truecolor(SKVisualObject * self)
// {
//     XVisualInfo * visualinfo = self->visualinfo;
//     if (visualinfo->depth == 16 || visualinfo->depth == 15 ||
// 	visualinfo->depth == 24 || visualinfo->depth == 32)
//     {
// 	int red_bit_count = 0, green_bit_count = 0, blue_bit_count = 0;
// 	int red_off = -1, green_off = -1, blue_off = -1;
// 	int bit, idx;
// 
// 	for (bit = 0; bit < 32; bit++)
// 	{
// 	    if (visualinfo->red_mask & (1 << bit))
// 	    {
// 		red_bit_count++;
// 		if (red_off < 0)
// 		    red_off = bit;
// 	    }
// 	    if (visualinfo->green_mask & (1 << bit))
// 	    {
// 		green_bit_count++;
// 		if (green_off < 0)
// 		    green_off = bit;
// 	    }
// 	    if (visualinfo->blue_mask & (1 << bit))
// 	    {
// 		blue_bit_count++;
// 		if (blue_off < 0)
// 		    blue_off = bit;
// 	    }
// 	}
// 	for (idx = 0; idx < 256; idx++)
// 	{
// 	    self->red_bits[idx] = (idx >> (8 - red_bit_count)) << red_off;
// 	    self->green_bits[idx] = (idx >> (8 - green_bit_count)) <<green_off;
// 	    self->blue_bits[idx] = (idx >> (8 - blue_bit_count)) << blue_off;
// 	}
// 	/* this will only work for depths 24/32 with 8 bits per
//            component and little endian...*/
// 	self->red_index = red_off / 8;
// 	self->green_index = green_off / 8;
// 	self->blue_index = blue_off / 8;
// 
// 	/*
// 	 * init function pointers
// 	 */
// 	self->get_pixel = skvisual_truecolor_get_pixel;
// 	self->free_extra = NULL;
//     }
//     else
//     {
// 	PyErr_SetString(PyExc_ValueError, "Only TrueColor visuals of depths "
// 			"15, 16, 24 and 32 are supported");
// 	return 0;
//     }
//     return 1;
// }

/*
 *	functions for PseudoColor visuals
 */


// static int
// skvisual_fill_tile(SKVisualObject * self, SKColorObject * color)
// {
//     int red, green, blue;
//     int x, y;
//     long *colors = self->pseudocolor_table;
//     SKDitherInfo *dither_red = self->dither_red;
//     SKDitherInfo *dither_green = self->dither_green;
//     SKDitherInfo *dither_blue = self->dither_blue;
//     SKDitherInfo r, g, b;
//     unsigned char **dither_matrix;
//     unsigned char *matrix;
//     unsigned char *dest;
//     XImage * ximage = self->tile;
//     int equal = 1;
// 
//     red = (int)(255 * color->red) & 0xFF;
//     green = (int)(255 * color->green) & 0xFF;
//     blue = (int)(255 * color->blue) & 0xFF;
// 
//     for (y = 0; y < 8; y++)
//     {
// 	dither_matrix = self->dither_matrix[y];
// 	dest = (unsigned char*)(ximage->data + ximage->bytes_per_line * y);
// 
// 	for (x = 0; x < 8; x++, dest++)
// 	{
// 	    r = dither_red[red];
// 	    g = dither_green[green];
// 	    b = dither_blue[blue];
// 		
// 	    matrix = dither_matrix[x];
// 	    *dest = colors[(r.c[matrix[r.s[1]]] +
// 			    g.c[matrix[g.s[1]]] +
// 			    b.c[matrix[b.s[1]]])];
// 	    equal = equal && *dest == *(ximage->data);
// 	}
//     }
//     return equal;
// }
// 
// 
// static PyObject *
// skvisual_pseudocolor_get_pixel(SKVisualObject * self, SKColorObject * color)
// {
//     int idx;
// 
//     if (color->red == color->green && color->green == color->blue)
// 	/* XXX: gray should also be dithered */
// 	idx = self->cube_size + color->red * (self->shades_gray - 1) + 0.5;
//     else
//     {
// 	if (!skvisual_fill_tile(self, color))
// 	{
// 	    Pixmap tile = XCreatePixmap(self->display,
// 					DefaultRootWindow(self->display),
// 					8, 8, self->visualinfo->depth);
// 	    if (tile)
// 	    {
// 		XPutImage(self->display, tile, self->tilegc, self->tile,
// 			  0, 0, 0, 0, 8, 8);
// 		return pax_functions->Pixmap_FromPixmap(self->display, tile,
// 							1);
// 	    }
// 	    else
// 		fprintf(stderr, "Cannot allocate tile pixmap, "
// 			"using solid fill");
// 	}
// 	
// 	/* the tile is solid color or the creation of the pixmap failed */
// 	idx = (int)(color->blue * (self->shades_b - 1) + 0.5)
// 	    + (self->shades_b
// 	       * ((int)(color->green * (self->shades_g - 1) + 0.5)
// 		  + self->shades_g * (int)(color->red * (self->shades_r - 1)
// 					   + 0.5)));
//     }
// 	
//     if (idx < 0)
// 	idx = 0;
//     else if (idx > 255)
// 	idx = 255;
// 
//     return PyInt_FromLong(self->pseudocolor_table[idx]);
// }
// 
// static void
// skvisual_pseudocolor_free(SKVisualObject * self)
// {
//     int i, j;
// 
//     XDestroyImage(self->tile);
//     XFreeGC(self->display, self->tilegc);
//     if (self->dither_matrix)
//     {
// 	for (i = 0; i < 8; i++)
// 	{
// 	    for (j = 0; j < 8; j++)
// 	    {
// 		PyMem_DEL(self->dither_matrix[i][j]);
// 	    }
// 	    PyMem_DEL(self->dither_matrix[i]);
// 	}
// 	PyMem_DEL(self->dither_matrix);
//     }
//     if (self->dither_red)
// 	PyMem_DEL(self->dither_red);
//     if (self->dither_green)
// 	PyMem_DEL(self->dither_green);
//     if (self->dither_blue)
// 	PyMem_DEL(self->dither_blue);
//     if (self->dither_gray)
// 	PyMem_DEL(self->dither_gray);
// }
// 
// static int
// skvisual_init_pseudocolor(SKVisualObject * self, PyObject * args)
// {
//     int r, g, b, gray;
//     PyObject * list;
//     int length, i;
//     char * imgdata;
//     XGCValues gcvalues;
//     
//     if (!PyArg_ParseTuple(args, "iiiiO!", &r, &g, &b, &gray,
// 			  &PyList_Type, &list))
// 	return 0;
// 
//     self->shades_r = r;
//     self->shades_g = g;
//     self->shades_b = b;
//     self->shades_gray = gray;
//     self->cube_size = r * g * b;
// 
//     if (self->cube_size + self->shades_gray > self->visualinfo->colormap_size)
//     {
// 	PyErr_SetString(PyExc_ValueError,
// 			"color cube is larger that colormap");
// 	return 0;
//     }
// 
//     imgdata = malloc(8 * 8);
//     if (!imgdata)
//     {
// 	PyErr_NoMemory();
// 	return 0;
//     }
//     self->tile = XCreateImage(self->display, self->visualinfo->visual,
// 			      self->visualinfo->depth, ZPixmap, 0, imgdata,
// 			      8, 8, 32, 8);
//     if (!self->tile)
//     {
// 	free(imgdata);
// 	PyErr_NoMemory();
// 	return 0;
//     }
// 
//     self->tilegc = XCreateGC(self->display, DefaultRootWindow(self->display),
// 			     0L, &gcvalues);
//     if (!self->tilegc)
//     {
// 	XDestroyImage(self->tile);
// 	PyErr_SetString(PyExc_RuntimeError,
// 			"Cannot create gc for dither pattern");
// 	return 0;
//     }
// 
//     self->dither_matrix = NULL;
//     self->dither_red = NULL;
//     self->dither_green = NULL;
//     self->dither_blue = NULL;
//     self->dither_gray = NULL;
//     
//     length = PyList_Size(list);
//     /* XXX: compare length with color cube */
//     length = length > 256 ? 256 : length;
//     for (i = 0; i < length; i++)
//     {
// 	PyObject * entry = PyList_GetItem(list, i);
// 	if (PyInt_Check(entry))
// 	    self->pseudocolor_table[i] = PyInt_AsLong(entry);
// 	else
// 	{
// 	    PyErr_SetString(PyExc_TypeError, "list of ints expected");
// 	    return 0;
// 	}
//     }
// 
//     /* dither */
//     skvisual_init_dither(self);
// 
//     /*
//      * init function pointers
//      */
//     self->get_pixel = skvisual_pseudocolor_get_pixel;
//     self->free_extra = skvisual_pseudocolor_free;
//     
//     return 1;
// }
// 
//     
// 
// static PyObject *
// SKVisual_FromXVisualInfo(Display *display, XVisualInfo *info, PyObject * args)
// {
//     SKVisualObject * self = PyObject_NEW(SKVisualObject, &SKVisualType);
//     int result = 0;
//     
//     if (!self)
// 	return NULL;
// 
//     /* copy the XVisualInfo since it is probably allocated via Xlib */
//     self->visualinfo = PyMem_NEW(XVisualInfo, 1);
//     if (!self->visualinfo)
//     {
// 	PyMem_DEL(self);
// 	return PyErr_NoMemory();
//     }
//     memcpy(self->visualinfo, info, sizeof(XVisualInfo));
//     self->display = display;
// 
//     self->get_pixel = NULL;
//     self->free_extra = NULL;
// 
//     self->gamma = self->gamma_inv = 1.0;
// 
//     /* fill the visual specific attributes */
//     if (self->visualinfo->class == TrueColor)
// 	result = skvisual_init_truecolor(self);
//     else if (self->visualinfo->class == PseudoColor)
// 	result = skvisual_init_pseudocolor(self, args);
//     else
// 	PyErr_SetString(PyExc_ValueError, "specified visual not supported");
//     
//     if (!result)
//     {
// 	Py_DECREF(self);
// 	return NULL;
//     }
// 
//     return (PyObject*)self;
// }
//     
// 
// static void
// skvisual_dealloc(SKVisualObject * self)
// {
//     if (self->free_extra)
// 	self->free_extra(self);
//     free(self->visualinfo);
//     PyMem_DEL(self);
// }
// 
// static PyObject *
// skvisual_repr(SKVisualObject * self)
// {
//     char buf[100];
//     sprintf(buf, "<SKVisual at %ld>", (long)self);
//     return PyString_FromString(buf);
// }


/*
 *	Python methods
 */

/*
 *	visual.get_pixel(COLOR)
 */

// static PyObject *
// skvisual_get_pixel(SKVisualObject * self, PyObject * args)
// {
//     PyObject * color;
// 
//     if (!PyArg_ParseTuple(args, "O", &color))
// 	return NULL;
// 
//     if (PyInt_Check(color))
//     {
// 	/* pass ints back unchanged. Special feature to support device
// 	dependent colors for highlighting etc.*/
// 	Py_INCREF(color);
// 	return color;
//     }
//     if (!SKColor_Check(color))
//     {
// 	PyErr_SetString(PyExc_TypeError, "Argument must be SKColor or int");
// 	return NULL;
//     }
//     if (self->get_pixel)
// 	return self->get_pixel(self, (SKColorObject*)color);
// 
//     PyErr_SetString(PyExc_RuntimeError, "Visual is not initialized correctly");
//     return NULL;
// }
// 
// static PyObject *
// skvisual_set_gamma(SKVisualObject * self, PyObject * args)
// {
//     double gamma;
// 
//     if (!PyArg_ParseTuple(args, "d", &gamma))
// 	return NULL;
// 
//     self->gamma = gamma;
//     self->gamma_inv = 1.0 / gamma;
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// #define OFF(x) offsetof(XVisualInfo, x)
// static struct memberlist skvisual_memberlist[] = {
//     {"depth",		T_INT,		OFF(depth),		RO},
//     {"c_class",		T_INT,		OFF(class),		RO},
//     {"red_mask",	T_ULONG,	OFF(red_mask),		RO},
//     {"green_mask",	T_ULONG,	OFF(green_mask),	RO},
//     {"blue_mask",	T_ULONG,	OFF(blue_mask),		RO},
//     {"colormap_size",	T_INT,		OFF(colormap_size),	RO},
//     {"bits_per_rgb",	T_INT,		OFF(bits_per_rgb),	RO},
//     {NULL} 
// };
// #undef OFF
// 
// static struct PyMethodDef skvisual_methods[] = {
//     {"get_pixel",		(PyCFunction)skvisual_get_pixel, 1},
//     {"set_gamma",		(PyCFunction)skvisual_set_gamma, 1},
//     {NULL,	NULL}
// };
// 
// 
// static PyObject *
// skvisual_getattr(PyObject * self, char * name)
// {
//     PyObject * result;
// 
//     result = Py_FindMethod(skvisual_methods, self, name);
//     if (result != NULL)
// 	return result;
//     PyErr_Clear();
// 
//     return PyMember_Get((char *)(((SKVisualObject*)self)->visualinfo),
// 			skvisual_memberlist, name);
// }
// 
// 
// PyTypeObject SKVisualType = {
// 	PyObject_HEAD_INIT(&PyType_Type)
// 	0,
// 	"skvisual",
// 	sizeof(SKVisualObject),
// 	0,
// 	(destructor)skvisual_dealloc,	/*tp_dealloc*/
// 	(printfunc)NULL,		/*tp_print*/
// 	skvisual_getattr,		/*tp_getattr*/
// 	0,				/*tp_setattr*/
// 	(cmpfunc)0,			/*tp_compare*/
// 	(reprfunc)skvisual_repr,	/*tp_repr*/
// 	0,				/*tp_as_number*/
// 	0,				/*tp_as_sequence*/
// 	0,				/*tp_as_mapping*/
// 	0,				/*tp_hash*/
// 	(ternaryfunc)0,			/*tp_call*/
// };





/*
 *		Module Functions
 */

/*
 *	skcolor.RGBColor(RED, GREEN, BLUE)
 */
PyObject *
skcolor_rgbcolor(PyObject * self, PyObject * args)
{
    double red, green, blue;

    if (!PyArg_ParseTuple(args, "ddd", &red, &green, &blue))
	return NULL;

    return SKColor_FromRGB(red, green, blue);
}

PyObject *
skcolor_num_allocated(PyObject * self, PyObject * args)
{
#if SKCOLOR_COUNT_ALLOC
    return PyInt_FromLong(skcolor_allocated);
#else
    return PyInt_FromLong(-1);
#endif
}


/*
 *	skcolor.XVisual(DISPLAY, VISUAL)
 */
// PyObject *
// skcolor_xvisual(PyObject * self, PyObject * args)
// {
//     PyObject * skvisual, *additional_args = NULL;
//     PyObject * ODisplay;
//     Display * display;
//     PyObject * OVisual;
//     Visual * visual;
//     XVisualInfo vtemplate;
//     XVisualInfo *vinfo;
//     int nreturn;
// 
//     if (!PyArg_ParseTuple(args, "O!O!|O!", &PyCObject_Type, &ODisplay,
// 			  &PyCObject_Type, &OVisual,
// 			  &PyTuple_Type, &additional_args))
// 	return NULL;
// 
//     display = (Display *)PyCObject_AsVoidPtr(ODisplay);
//     visual = (Visual *)PyCObject_AsVoidPtr(OVisual);
// 
//     vtemplate.visual = visual;
//     vtemplate.visualid = XVisualIDFromVisual(visual);
//     vinfo = XGetVisualInfo(display, VisualIDMask, &vtemplate, &nreturn);
//     if (!vinfo)
//     {
// 	PyErr_SetString(PyExc_RuntimeError, "Cannot get VisualInfo");
// 	return NULL;
//     }
// 
//     skvisual = SKVisual_FromXVisualInfo(display, vinfo, additional_args);
// 
//     XFree(vinfo);
// 
//     return skvisual;
// }


