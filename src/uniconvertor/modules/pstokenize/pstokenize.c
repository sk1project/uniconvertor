/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1998, 1999, 2000, 2001, 2003, 2006 by Bernhard Herzog
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

/*
 * Functions to tokenize PostScript-files.
 */

#include <locale.h>
#include <Python.h>
#include <structmember.h>
#include "filterobj.h"

#include "pschartab.c"

static PyObject * Filter_Type = NULL;
static Filter_Functions *filter_functions = NULL;


typedef struct {
    PyObject_HEAD
    FilterObject * source;
    int beginning_of_line;
    char ai_pseudo_comments;
    char ai_dsc;
} PSTokenizerObject;

staticforward PyTypeObject PSTokenizerType;


#define	NAME		258
#define	INT		259
#define	FLOAT		260
#define	STRING		261
#define MAX_DATA_TOKEN  261
#define	OPERATOR	262
#define DSC_COMMENT	263
#define END		264


#define GETC()	(Filter_DL_GETC((filter_functions), (self->source)))
#define BACK(c)	\
(filter_functions->Filter_Ungetc(((PyObject*)self->source), (c)))


static int
read_newline(PSTokenizerObject * self, int c)
{
    if (c == '\r')
    {
	c = GETC();
	if (c != '\n')
	{
	    BACK(c);
	}
    }
    self->beginning_of_line = 1;
    return 0;
}

/* Return the contents of a DSC-comment as a string object.
 *
 * The stream is assumed to be positioned after the '%%' or '%!'.
 * Afterwards, the stream is positioned at the beginning of the next
 * line or EOF. The string does not contain the final newline character.
 */
static PyObject *
read_dsc_comment(PSTokenizerObject * self)
{
    int size;
    int maxsize = 256;
    PyObject * value;
    char * buf, * end;

    value = PyString_FromStringAndSize((char*)NULL, maxsize);
    if (!value)
	return NULL;
    buf = PyString_AsString(value);
    end = buf + maxsize;

    for (;;)
    {
	int c = GETC();
	if (c == EOF)
	    break;
	    
	*buf++ = c;
	    
	if ((char_types[c] & NEWLINE) == NEWLINE)
	{
	    read_newline(self, c);
	    buf -= 1;
	    break;
	}

	if (buf == end)
	{
	    size = maxsize;
	    maxsize = maxsize + 1000;
	    if (_PyString_Resize(&value, maxsize) < 0)
		return NULL;
	    buf = PyString_AsString(value) + size;
	    end = PyString_AsString(value) + maxsize;
	}
    }

    if (buf < end)
    {
	size = buf - PyString_AsString(value);
	if (_PyString_Resize(&value, size) < 0)
	    return NULL;
    }
    
    return value;
}


static void
discard_comment(PSTokenizerObject * self)
{
    int c;

    for (;;)
    {
	c = GETC();
	if (c == EOF)
	    return;
	if (char_types[c] & NEWLINE)
	{
	    read_newline(self, c);
	    return;
	}
    }
}

/* Read a comment. The stream is assumed to be positioned just after the
 * initial '%'. If the comment is a DSC-comment (the next char is a '%'
 * or a '!' and the comment is at the beginning of a line), the contents
 * of the comment (without the leading '%%' or '%!') are returned as a
 * string object.
 *
 * In a normal comments discard all input until the next newline and
 * return NULL.
 *
 * Furthermore, if ai_pseudo_comments is true, recognize Adobe
 * Illustrator pseudo comments, which start with '%_' and discard just
 * these two characters. The rest of the comment is treated as normal
 * input.
 */
static PyObject *
read_comment(PSTokenizerObject * self)
{
    int c;
    PyObject * value = NULL;

    c = GETC();
    if (self->beginning_of_line && (c == '%' || c == '!'))
    {
	value = read_dsc_comment(self);
    }
    else 
    {
	if (c == '_' && self->ai_pseudo_comments)
	{
	}
	else if (self->beginning_of_line && c == 'A' && self->ai_dsc)
	{
	    BACK(c);
	    value = read_dsc_comment(self);
	}
	else if (c != EOF && (char_types[c] & NEWLINE))
	    read_newline(self, c);
	else
	    discard_comment(self);
    }

    return value;
}

/*
 * Return the PostScript string literal as a Python string object.
 *
 * The stream is assumed to be positioned just after the initial '('.
 * Afterwards, the stream is positioned just after the closing ')'.
 */
static PyObject *
read_string(PSTokenizerObject * self)
{
    int depth = 0;
    int size;
    int maxsize = 256;
    PyObject * value;
    char * buf, * end;

    value = PyString_FromStringAndSize((char*)NULL, maxsize);
    if (!value)
	return NULL;
    buf = PyString_AsString(value);
    end = buf + maxsize;
    
    for (;;)
    {
	int c = GETC();
	switch (c)
	{
	case EOF:
	    /* end of input in string constant! */
	    Py_DECREF(value);
	    PyErr_SetString(PyExc_EOFError, "unexpected end of input");
	    return NULL;
	    
	case '(':
	    depth += 1;
	    *buf++ = c;
	    break;
	case ')':
	    depth -= 1;
	    if (depth < 0)
	    {
		size = buf - PyString_AsString(value);
		if (_PyString_Resize(&value, size) < 0)
		{
		    return NULL;
		}
		return value;
	    }
	    else
		*buf++ = c;
	    break;

	case '\\':
	    c = GETC();
	    switch(c)
	    {
	    case 'b':	*buf++ = '\b'; break;
	    case 'f':	*buf++ = '\f'; break;
	    case 'n':	*buf++ = '\n'; break;
	    case 'r':	*buf++ = '\r'; break;
	    case 't':	*buf++ = '\t'; break;
	    case '\\':	*buf++ = '\\'; break;
	    case '(':	*buf++ = '('; break;
	    case ')':	*buf++ = ')'; break;
	    case '0': case '1': case '2': case '3': case '4':
	    case '5': case '6': case '7':
	    {
		int code = c - '0';
		c = GETC();
		if ('0' <= c && c <= '7')
		{
		    code = code * 8 + c - '0';
		    c = GETC();
		    if ('0' <= c && c <= '7')
		    {
			code = code * 8 + c - '0';
			c = GETC();
		    }
		}
		*buf++ = code;
		BACK(c);
	    }
	    break;
	    case '\r':
		c = GETC();
		if (c != '\n')
		    BACK(c);
		break;
	    case '\n':
		break;
		
	    default:
		*buf++ = c;
	    }
	    break;

	case '\r':
	    c = GETC();
	    if (c != '\n')
		BACK(c);
	    *buf++ = '\n';
	    break;
	    
	default:
	    *buf++ = c;
	}

	if (buf == end)
	{
	    size = maxsize;
	    maxsize = maxsize + 1000;
	    if (_PyString_Resize(&value, maxsize) < 0)
		return NULL;
	    buf = PyString_AsString(value) + size;
	    end = PyString_AsString(value) + maxsize;
	}
    }  /* for (;;) */

    /* unreachable */
    return NULL;
} 

/*
 * Return the PostScript hex string literal as a Python string object.
 *
 * The stream is assumed to be positioned just after the initial '<'.
 * Afterwards, the stream is positioned just after the closing '>'.
 */
static PyObject *
read_hex_string(PSTokenizerObject * self)
{
    int size;
    int maxsize = 256;
    int last_digit = -1, digit;
    PyObject * value;
    char * buf, * end;

    value = PyString_FromStringAndSize((char*)NULL, maxsize);
    if (!value)
	return NULL;
    buf = PyString_AsString(value);
    end = buf + maxsize;
    
    for (;;)
    {
	int c = GETC();
	digit = -1;
	switch (c)
	{
	case EOF:
	    /* end of input in string constant! */
	    Py_DECREF(value);
	    PyErr_SetString(PyExc_EOFError, "unexpected end of input");
	    return NULL;
	    
	case '>':
	    size = buf - PyString_AsString(value);
	    if (_PyString_Resize(&value, size) < 0)
	    {
		return NULL;
	    }
	    return value;

	case '0': case '1': case '2': case '3': case '4':
	case '5': case '6': case '7': case '8': case '9':
	    digit = c - '0';
	    break;

	case 'A': case 'B': case 'C': case 'D': case 'E': case 'F':
	    digit = c - 'A' + 10;
	    break;

	case 'a': case 'b': case 'c': case 'd': case 'e': case 'f':
	    digit = c - 'a' + 10;
	    break;
		
	default:
	    if (!(char_types[c] & WHITESPACE))
	    {
		Py_DECREF(value);
		PyErr_SetString(PyExc_SyntaxError,
				"invalid character in hex string");
		return NULL;
	    }
	}

	if (digit >= 0)
	{
	    if (last_digit < 0)
	    {
		last_digit = digit;
	    }
	    else
	    {
		*buf++ = last_digit * 16 + digit;
		last_digit = -1;
	    }

	    if (buf == end)
	    {
		size = maxsize;
		maxsize = maxsize + 1000;
		if (_PyString_Resize(&value, maxsize) < 0)
		    return NULL;
		buf = PyString_AsString(value) + size;
		end = PyString_AsString(value) + maxsize;
	    }
	}
		
    }  /* for (;;) */

    /* unreachable */
    return NULL;
} 



/*
 *
 */
static PyObject *
read_name_or_number(PSTokenizerObject * self, int * token, int isname)
{
    int size;
    int maxsize = 256;
    PyObject * value;
    char * buf, * end;

    *token = 0;

    value = PyString_FromStringAndSize((char*)NULL, maxsize);
    if (!value)
	return NULL;
    buf = PyString_AsString(value);
    end = buf + maxsize;
    
    for (;;)
    {
	int c = GETC();
	if (c == EOF)
	    break;
	    
	if ((char_types[c] & NAMECHAR) == 0)
	{
	    BACK(c);
	    *buf = '\0';
	    break;
	}
	*buf++ = c;

	if (buf == end)
	{
	    size = maxsize;
	    maxsize = maxsize + 1000;
	    if (_PyString_Resize(&value, maxsize) < 0)
		return NULL;
	    buf = PyString_AsString(value) + size;
	    end = PyString_AsString(value) + maxsize;
	}
    }

    /* check for a number */

    if (!isname)
    {
	char * start = PyString_AsString(value);
	char * p = start;
	char * numend;
	while(char_types[(int)*p] & INTCHAR)
	    p += 1;
	if (char_types[(int)*p] & FLOATCHAR)
	{
	    char * old_locale;
	    double result;

	    /* Change LC_NUMERIC locale to "C" around the strtod
	     * call so that it parses the number correctly. */
	    old_locale = strdup(setlocale(LC_NUMERIC, NULL));
	    setlocale(LC_NUMERIC, "C");
	    result = strtod(start, &numend);
	    setlocale(LC_NUMERIC, old_locale);
	    free(old_locale);

	    if (numend == buf)
	    {
		Py_DECREF(value);
		*token = FLOAT;
		return PyFloat_FromDouble(result);
	    }
	}
	else
	{
	    int result = strtol(start, &numend, 10);
	    if (numend == buf)
	    {
		Py_DECREF(value);
		*token = INT;
		return PyInt_FromLong(result);
	    }
	}
    }

    if (buf < end)
    {
	size = buf - PyString_AsString(value);
	if (_PyString_Resize(&value, size) < 0)
	    return NULL;
    }

    *token = OPERATOR;
    return value;
    
} 

static PyObject * 
pslex(PSTokenizerObject * self)
{
    int token = 0;
    PyObject * value = NULL;
    PyObject * result;
    int c, ctype;

    while (token == 0)
    {
	c = GETC();
	if (c != '%')
	    self->beginning_of_line = 0;
	switch (c)
	{
	case EOF:
	    Py_INCREF(Py_None);
	    value = Py_None;
	    token = END;
	    break;
	    
	case '%':
	    value = read_comment(self);
	    if (value)
		token = DSC_COMMENT;
	    break;
	    
	case '[': case ']': case '{': case '}':
	    /* a single character token */
	{
	    char buf[2] = "\000\000";
	    buf[0] = c;
	    value = PyString_FromString(buf);
	    token = OPERATOR;
	}
	break;

	case '(':
	    value = read_string(self);
	    token = STRING;
	    break;

	case '<':
	    /* this case should check the next character to also
               recognize the << operator and base85 encoded strings */
	    value = read_hex_string(self);
	    token = STRING;
	    break;

	case '/':
	    value = read_name_or_number(self, &token, 1);
	    token = NAME;
	    break;
	    
	default:
	    ctype = char_types[c];
	    if (ctype & WHITESPACE)
	    {
		while (ctype & WHITESPACE)
		{
		    self->beginning_of_line = (ctype & NEWLINE) == NEWLINE;

		    c = GETC();
		    if (c == EOF)
			break;
		    ctype = char_types[c];
		}
		if (c != EOF)
		    BACK(c);
	    }
	    else if (ctype & NAMECHAR)
	    {
		BACK(c);
		/* NAMECHAR includes digits */
		value = read_name_or_number(self, &token, 0);
	    }
	    else
	    {
		PyErr_Format(PyExc_IOError,
			     "unexpected character %d (flags %.4x)",
			     c, ctype);
		token = -1;
	    }
	}	/* switch */
    } /* while token == 0 */

    if (token < 0 || value == NULL)
	return NULL;
    
    result = Py_BuildValue("(iO)", token, value);
    Py_DECREF(value);
    return result;
}

/*
 *
 */

static PyObject *
pstokenizer_next(PSTokenizerObject * self, PyObject * args)
{
    return pslex(self);
}

/*
 *
 */

static PyObject *
pstokenizer_next_dsc(PSTokenizerObject * self, PyObject * args)
{
    PyObject * result = NULL;
    int c;

    for (;;)
    {
	c = GETC();
	if (c == EOF)
	    break;
	else if (char_types[c] & NEWLINE)
	{
	    read_newline(self, c);
	}
	else if (c == '%')
	{
	    result = read_comment(self);
	    if (result)
		break;
	}
	else
	{
	    self->beginning_of_line = 0;
	}
    }

    if (!result)
    {
	result = PyString_FromString("");
    }
    return result;
}

/*
 *
 */

static PyObject *
pstokenizer_read(PSTokenizerObject * self, PyObject * args)
{
    PyObject * result = NULL;
    long length, read;

    if (!PyArg_ParseTuple(args, "l", &length))
	return NULL;

    result = PyString_FromStringAndSize(NULL, length);
    if (!result)
	return NULL;

    read = filter_functions->Filter_Read((PyObject*)(self->source),
					 PyString_AsString(result), length);
    if (read == 0 && PyErr_Occurred())
    {
	Py_DECREF(result);
	return NULL;
    }
    if (_PyString_Resize(&result, read) < 0)
	return NULL;
    
    return result;
}

/*
 *
 */

static PyObject *
PSTokenizer_FromStream(FilterObject * filter)
{
    PSTokenizerObject * self;

    self = PyObject_New(PSTokenizerObject, &PSTokenizerType);
    if (!self)
	return NULL;

    Py_INCREF(filter);
    self->source = filter;
    self->beginning_of_line = 1;
    self->ai_pseudo_comments = 0;
    self->ai_dsc = 0;

    return (PyObject*)self;
}

static void 
pstokenizer_dealloc(PSTokenizerObject * self)
{
    Py_DECREF(self->source);
    PyObject_Del(self);
}

static PyObject *
pstokenizer_repr(PSTokenizerObject * self)
{
    char buf[1000];
    PyObject * streamrepr;

    streamrepr = PyObject_Repr((PyObject*)(self->source));
    if (!streamrepr)
	return NULL;

    sprintf(buf, "<pstokenizer reading from %.500s>",
	    PyString_AsString(streamrepr));
    Py_DECREF(streamrepr);
    return PyString_FromString(buf);
}

#define OFF(x) offsetof(PSTokenizerObject, x)
static struct memberlist pstokenizer_memberlist[] = {
    {"source",		   T_OBJECT,	OFF(source),			RO},
    {"ai_pseudo_comments", T_BYTE,	OFF(ai_pseudo_comments)},
    {"ai_dsc",		   T_BYTE,	OFF(ai_dsc)},
    {NULL}
};

static struct PyMethodDef pstokenizer_methods[] = {
    {"next",		(PyCFunction)pstokenizer_next,		1},
    {"next_dsc",	(PyCFunction)pstokenizer_next_dsc,	1},
    {"read",		(PyCFunction)pstokenizer_read,		1},
    {NULL,	NULL}
};

static PyObject *
pstokenizer_getattr(PyObject * self, char * name)
{
    PyObject * result;

    result = Py_FindMethod(pstokenizer_methods, self, name);
    if (result != NULL)
	return result;
    PyErr_Clear();

    return PyMember_Get((char *)self, pstokenizer_memberlist, name);
}

static int
pstokenizer_setattr(PyObject * self, char * name, PyObject * v)
{
    if (v == NULL) {
	PyErr_SetString(PyExc_AttributeError,
			"can't delete object attributes");
	return -1;
    }
    return PyMember_Set((char *)self, pstokenizer_memberlist, name, v);
}


static PyTypeObject PSTokenizerType = {
	PyObject_HEAD_INIT(NULL)
	0,
	"pstokenizer",
	sizeof(PSTokenizerObject),
	0,
	(destructor)pstokenizer_dealloc,/*tp_dealloc*/
	(printfunc)0,			/*tp_print*/
	pstokenizer_getattr,		/*tp_getattr*/
	pstokenizer_setattr,		/*tp_setattr*/
	(cmpfunc)0,			/*tp_compare*/
	(reprfunc)pstokenizer_repr,	/*tp_repr*/
	0,				/*tp_as_number*/
	0,				/*tp_as_sequence*/
	0,				/*tp_as_mapping*/
	0,				/*tp_hash*/
};


/*
 *
 */

static PyObject *
pstokenizer_new(PyObject * self, PyObject * args)
{
    FilterObject * source;
    
    if (!PyArg_ParseTuple(args, "O!", Filter_Type, &source))
	return NULL;

    return PSTokenizer_FromStream(source);
}

/*
 *	Method table and module initialization
 */

static PyMethodDef pstokenize_functions[] = {
    {"PSTokenizer",	pstokenizer_new,	1},
    {NULL,		NULL}
};


static void
add_int(PyObject * dict, int i, char * name)
{
    PyObject *v;

    v = Py_BuildValue("i", i);
    if (!v)
	PyErr_Clear();
    if (PyDict_SetItemString(dict, name, v) < 0)
	PyErr_Clear();
}

DL_EXPORT(void)
initpstokenize(void)
{
    PyObject * d, *m, *r, *filter;

    PSTokenizerType.ob_type = &PyType_Type;
    m = Py_InitModule("pstokenize", pstokenize_functions);
    d = PyModule_GetDict(m);

#define ADD_INT(name) add_int(d, name, #name)
    ADD_INT(NAME);
    ADD_INT(INT);
    ADD_INT(FLOAT);
    ADD_INT(STRING);
    ADD_INT(OPERATOR);
    ADD_INT(DSC_COMMENT);
    ADD_INT(END);
    ADD_INT(MAX_DATA_TOKEN);
    
    /* import some objects from filter */
    filter = PyImport_ImportModule("streamfilter");
    if (filter)
    {
	Filter_Type = PyObject_GetAttrString(filter, "FilterType");
	if (!Filter_Type)
	    return;
	r = PyObject_GetAttrString(filter, "Filter_Functions");
	if (!r)
	    return;
	filter_functions = (Filter_Functions*)PyCObject_AsVoidPtr(r);
	Py_DECREF(r);
    }

}
