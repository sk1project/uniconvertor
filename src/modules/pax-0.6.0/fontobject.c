#include "Python.h"
#include "modsupport.h"

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

#include "fontobject.h"

#ifndef offsetof
#define offsetof(type, member) ( (int) & ((type*)0) -> member )
#endif

#define OFF(member) offsetof(XFontStruct, member)
static struct Fontattr {
	char *type;
	char *name;
	int offset;
} Fontattrdefs[] = {
	{"Font", "fid", OFF(fid)},
	{"unsigned", "direction", OFF(direction)},
	{"unsigned", "min_char_or_byte2", OFF(min_char_or_byte2)},
	{"unsigned", "max_char_or_byte2", OFF(max_char_or_byte2)},
	{"unsigned", "min_byte1", OFF(min_byte1)},
	{"unsigned", "max_byte1", OFF(max_byte1)},
	{"Bool", "all_chars_exist", OFF(all_chars_exist)},
	{"unsigned", "default_char", OFF(default_char)},
	{"int", "n_properties", OFF(n_properties)},
	{"XFontProp[]", "properties", OFF(properties)},
	{"XCharStruct", "min_bounds", OFF(min_bounds)},
	{"XCharStruct", "max_bounds", OFF(max_bounds)},
	{"XCharStruct[]", "per_char", OFF(per_char)},
	{"int", "ascent", OFF(ascent)},
	{"int", "descent", OFF(descent)},
	{0, 0, 0}
};
#undef OFF

Font
PaxFont_AsFont(PyObject *self)
{
    if (self->ob_type != &PaxFontType)
    {
	PyErr_BadArgument();
	return 0;
    }
    return ((PaxFontObject *) self)->font_struct->fid;
}

XFontStruct *
PaxFont_AsFontStruct(PyObject *self)
{
    if (self->ob_type != &PaxFontType)
    {
	PyErr_BadArgument();
	return 0;
    }
    return ((PaxFontObject *) self)->font_struct;
}

PyObject *
PaxFont_FromName(Display *display, char *name)
{
    PaxFontObject *f = PyObject_NEW(PaxFontObject, &PaxFontType);
    if (f == NULL)
	return NULL;
    f->from_id = 0;
    f->display = display;
    f->font_struct = XLoadQueryFont(display, name);
    if (f->font_struct == NULL)
    {
	PyMem_DEL(f);
	PyErr_SetString(PyExc_RuntimeError, "no such font");
	return NULL;
    }
    return (PyObject *)f;
}

PyObject *
PaxFont_FromFont(Display *display, Font fid)
{
    PaxFontObject *f = PyObject_NEW(PaxFontObject, &PaxFontType);
    if (f == NULL)
	return NULL;
    f->from_id = 1;
    f->display = display;
    f->font_struct = XQueryFont(display, fid);
    if (f->font_struct == NULL)
    {
	PyMem_DEL(f);
	PyErr_SetString(PyExc_RuntimeError, "no such font");
	return NULL;
    }
    return (PyObject *)f;
}

static PyObject *
MemberList(void)
{
    int i, n;
    PyObject *v;
    for (n = 0; Fontattrdefs[n].name != NULL; n++)
	;
    v = PyList_New(n);
    if (v != NULL)
    {
	for (i = 0; i < n; i++)
	    PyList_SetItem(v, i, PyString_FromString(Fontattrdefs[i].name));
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
TextWidth(PaxFontObject *self, PyObject *args)
{
    char *string;
    int nchars;
    if (!PyArg_ParseTuple(args, "s#", &string, &nchars))
	return NULL;
    return PyInt_FromLong(XTextWidth(self->font_struct, string, nchars));
}

static PyObject *
TextExtents(PaxFontObject *self, PyObject *args)
{
    char *string;
    int nchars;
    int direction, font_ascent, font_descent;
    XCharStruct overall;
    if (!PyArg_ParseTuple(args, "s#", &string, &nchars))
	return NULL;
    XTextExtents(self->font_struct, string, nchars,
		 &direction, &font_ascent, &font_descent, &overall);
    return Py_BuildValue("(iii(iiiiii))",
			 direction,
			 font_ascent,
			 font_descent,
			 overall.lbearing,
			 overall.rbearing,
			 overall.width,
			 overall.ascent,
			 overall.descent,
			 overall.attributes);
}

static PyObject *
GetPropertyDict(PaxFontObject *self, PyObject *args)
{
    PyObject * dict = PyDict_New();
    XFontStruct * fs = self->font_struct;
    int nprop = fs->n_properties;
    int idx;
    char * name;
    PyObject * val;
    int result;

    if (!dict)
	return NULL;

    for (idx = 0; idx < nprop; idx++)
    {
	name = XGetAtomName(self->display, fs->properties[idx].name);
	val = PyInt_FromLong(fs->properties[idx].card32);
	if (!val)
	{
	    Py_DECREF(dict);
	    return NULL;
	}

	result = PyMapping_SetItemString(dict, name, val);
	Py_DECREF(val);
	if (result == -1)
	{
	    Py_DECREF(dict);
	    return NULL;
	}
    }
    return dict;
}

static PyObject *
GetCharStruct(PaxFontObject *self, PyObject *args)
{
    XFontStruct * fs = self->font_struct;
    XCharStruct * cs;
    int idx;

    if (!PyArg_ParseTuple(args, "i", &idx))
	return NULL;

    if (idx < fs->min_char_or_byte2 || idx > fs->max_char_or_byte2)
    {
	PyErr_SetString(PyExc_ValueError, "index out of range");
	return NULL;
    }

    if (!fs->per_char)
    {
	/* mono spaced font */
	cs = &(fs->max_bounds);
    }
    else
    {
	cs = fs->per_char + idx - fs->min_char_or_byte2;
    }

    return Py_BuildValue("(iiiiii)",
			 cs->lbearing,
			 cs->rbearing,
			 cs->width,
			 cs->ascent,
			 cs->descent,
			 cs->attributes);
}


static PyMethodDef FontMethods[] =
{
    {"TextExtents", (PyCFunction)TextExtents, 1},
    {"TextWidth", (PyCFunction)TextWidth, 1},
    {"GetPropertyDict", (PyCFunction)GetPropertyDict, 1},
    {"GetCharStruct", (PyCFunction)GetCharStruct, 1},
    {0, 0}
};

static PyObject *
GetAttr(PaxFontObject *self, char *name)
{
    struct Fontattr *p;
    PyObject *result;
    if (name[0] == '_' && strcmp(name, "__members__") == 0)
	return MemberList();
    result = Py_FindMethod(FontMethods, (PyObject *)self, name);
    if (result != NULL)
	return result;
    PyErr_Clear();
    for (p = Fontattrdefs; ; p++)
    {
	if (p->name == NULL)
	{
	    PyErr_SetString(PyExc_AttributeError, name);
	    return NULL;
	}
	if (strcmp(name, p->name) == 0)
	    break;
    }
    if (p->type[0] == 'X')
    {
	PyErr_SetString(PyExc_AttributeError,
			"non-int attr not yet supported");
	return NULL;
    }
    return PyInt_FromLong(*(long *)((char *)(self->font_struct) + p->offset));
}

static void
Dealloc(PaxFontObject *self)
{
    if (self->from_id)
	XFreeFontInfo(NULL, self->font_struct, 1);
    else
	XFreeFont(self->display, self->font_struct);
    PyMem_DEL(self);
}

PyTypeObject PaxFontType = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,			/*ob_size*/
	"PaxFont",		/*tp_name*/
	sizeof(PaxFontObject),	/*tp_size*/
	0,			/*tp_itemsize*/
	(void (*) Py_PROTO((PyObject *)))
	(destructor)Dealloc,	/*tp_dealloc*/
	0,			/*tp_print*/
	(getattrfunc)GetAttr,	/*tp_getattr*/
	0,			/*tp_setattr*/
	0,			/*tp_compare*/
	0,			/*tp_repr*/
	0,			/*tp_as_number*/
	0,			/*tp_as_sequence*/
	0,			/*tp_as_mapping*/
	0,			/*tp_hash*/
};
