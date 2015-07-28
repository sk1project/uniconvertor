/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1998, 1999, 2000, 2001, 2006 by Bernhard Herzog
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
 * Functions to parse SK-files and related formats.
 *
 * This modules contains functions to parse one line of a SK-file. Each
 * line looks just like a Python function call with any number of
 * positional- and keyword arguments. Arguments must be literals, that
 * is (float or int), strings, tuples or lists. Tuples and list must in
* turn be composed of these types of literals.
 */

#include <ctype.h>
#include <locale.h>
#include <string.h>
#include <Python.h>

typedef struct {
    int	length;
    char * buffer;
    PyObject * funcname;
    PyObject * args;
    PyObject * kwargs;

    int	token;
    PyObject * value;

    char * error;
} SKLineInfo;

#define	NAME	258
#define	INT	259
#define	FLOAT	260
#define	STRING	261


#define GETC()	(*(buffer->buffer++))
#define BACK()	(buffer->buffer--)
static int
sklex(PyObject ** lval, SKLineInfo * buffer)
{
    int c;

    *lval = NULL;

    for (;;)
    {
	c = GETC();
	switch (c)
	{
	case '#':	/* ignore comments */
	case '\n':	/* end of line/input */
	case '\0':
	    return 0;

	case '(': case ')': case '[': case ']': case ',': case '=':
	    /* a single character token */
	    return c;

	case '\'': case '"':
	{
	    int string_delimiter = c;
	    char * dest;
	    *lval = PyString_FromStringAndSize(NULL, buffer->length);
	    if (!*lval)
	    {
		buffer->error = "no memory";
		return 0;
	    }
	    dest = PyString_AsString(*lval);

	    for (;;)
	    {
		c = GETC();

		switch (c)
		{
		case '\0': case '\n':
		    /* end of input in string constant! */
		    Py_DECREF(*lval);
		    *lval = NULL;
		    buffer->error = "unexpected end of input";
		    return 0;

		case '\'': case '"':
		    if (c == string_delimiter)
		    {
			int size;
			size = dest - PyString_AsString(*lval);
			if (_PyString_Resize(lval, size) < 0)
			{
			    *lval = NULL;
			    buffer->error = "no memory";
			    return 0;
			}
			return STRING;
		    }
		    else
			*dest++ = c;
		    break;

		case '\\':
		    c = GETC();
		    switch(c)
		    {
		    case 'a':	*dest++ = '\a'; break;
		    case 'b':	*dest++ = '\b'; break;
		    case 'f':	*dest++ = '\f'; break;
		    case 'n':	*dest++ = '\n'; break;
		    case 'r':	*dest++ = '\r'; break;
		    case 't':	*dest++ = '\t'; break;
		    case 'v':	*dest++ = '\v'; break;
		    case '\\':	*dest++ = '\\'; break;
		    case '\'':	*dest++ = '\''; break;
		    case '"':	*dest++ = '"'; break;
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
				    (void)GETC();
				}
			    }
			    *dest++ = code;
			    BACK();
			}
			break;
		    case 'x':
			/* A hexcoded character. unlike in Python 1.5.2,
			 * we use the conventions of 2.1 here, that is,
			 * \x has to be followed by exactly 2 hex
			 * digits, because this code is really only
			 * needed for Python 2.1 compatibility.
			 * Beginning with Python 2.1 repr of a string
			 * generates \x escapes instead of octal */
		        {
			    int digit1, digit2;
			    digit1 = GETC();
			    digit2 = GETC();

			    if (isxdigit(digit1) && isxdigit(digit2))
			    {
				int code = 0;
				if (isdigit(digit1))
				    code = digit1 - '0';
				else if (islower(digit1))
				    code = digit1 - 'a' + 10;
				else
				    code = digit1 - 'A' + 10;
				code *= 16;
				if (isdigit(digit2))
				    code += digit2 - '0';
				else if (islower(digit2))
				    code += digit2 - 'a' + 10;
				else
				    code += digit2 - 'A' + 10;
				*dest++ = code;
			    }
			    else
			    {
				Py_DECREF(*lval);
				*lval = NULL;
				buffer->error = "Invalid \\x escape";
				return 0;
			    }
			}
			break;
		    default:
			/* copy the \ and character literally */
			*dest++ = '\\';
			*dest++ = c;
		    }
		    break;
		default:
		    *dest++ = c;
		}
	    }
	}	/* case string */
	case '0': case '1': case '2': case '3': case '4':
	case '5': case '6': case '7': case '8': case '9':
	case '+': case '-':
	{
	    char * p = buffer->buffer;
	    while(isdigit(*p))
		p += 1;
	    if (*p == '.' || *p == 'e' || *p == 'E')
	    {
		char * old_locale;
		double result;

		/* Change LC_NUMERIC locale to "C" around the strtod
		 * call so that it parses the number correctly. */
		old_locale = strdup(setlocale(LC_NUMERIC, NULL));
		setlocale(LC_NUMERIC, "C");

		result = strtod(buffer->buffer - 1, &(buffer->buffer));

		setlocale(LC_NUMERIC, old_locale);
		free(old_locale);

		*lval = PyFloat_FromDouble(result);
		return FLOAT;
	    }
	    else
	    {
		*lval = PyInt_FromLong(strtol(buffer->buffer - 1,
					      &(buffer->buffer), 10));
		return INT;
	    }
	}
	default:
	    if (isalpha(c) || c == '_')
	    {
		/* arbitrary limit for identifiers: */
		char ident[101];
		sscanf(buffer->buffer - 1, "%100[a-zA-Z0-9_]", ident);
		buffer->buffer = buffer->buffer + strlen(ident) - 1;
		*lval = PyString_FromString(ident);
		return NAME;
	    }
	    if (!isspace(c))
	    {
		buffer->error = "unexpected character";
		return 0;
	    }
	}	/* switch */
    } /* for ever */

    /* unreachable... */
    return 0;
}

#define GET_TOKEN(line) ((line)->token = sklex(&((line)->value), (line)))

static PyObject * parse_literal(SKLineInfo * line);

static PyObject *
parse_litlist(SKLineInfo * line)
{
    PyObject * list = PyList_New(0);

    if (!list)
	return NULL;

    for (;;)
    {
	PyObject * literal = parse_literal(line);
	if (literal)
	{
	    PyList_Append(list, literal);
	    Py_DECREF(literal);
	    if (line->token == ',')
		GET_TOKEN(line);
	    else
		break;
	}
	else
	    break;
    }

    return list;
}

static PyObject *
parse_literal(SKLineInfo * line)
{
    PyObject * result = NULL;

    switch (line->token)
    {
    case INT:
    case FLOAT:
    case STRING:
	result = line->value;
	GET_TOKEN(line);
	break;

    case '(':
    {
	PyObject * list = NULL;

	GET_TOKEN(line);
	list = parse_litlist(line);
	if (list)
	{
	    if (line->token == ')')
	    {
		GET_TOKEN(line);
		result = PySequence_Tuple(list);
	    }
	}
	Py_DECREF(list);
    }
    break;

    case '[':
	GET_TOKEN(line);
	result = parse_litlist(line);
	if (result)
	{
	    if (line->token != ']')
	    {
		Py_DECREF(result);
		result = NULL;
	    }
	    else
		GET_TOKEN(line);
	}
	break;

    default:
	break;
    }

    return result;
}




static int
parse_arg(SKLineInfo * line)
{
    PyObject * literal = NULL;
    if (line->token == NAME)
    {
	/* keyword argument */
	PyObject * name = line->value;

	GET_TOKEN(line);
	if (line->token == '=')
	{
	    GET_TOKEN(line);
	    literal = parse_literal(line);
	    if (literal)
	    {
		PyObject_SetItem(line->kwargs, name, literal);
	    }
	    else
	    {
		line->error = "literal expected";
	    }
	}
	else
	{
	    line->error = "'=' expected";
	}
	Py_XDECREF(literal);
	Py_XDECREF(name);
    }
    else
    {
	literal = parse_literal(line);
	if (literal)
	{
	    PyList_Append(line->args, literal);
	}
	Py_XDECREF(literal);
    }

    return literal == NULL;
}


static int
parse_arglist(SKLineInfo * line)
{
    if (parse_arg(line) != 0)
	return 0;

    while (line->token == ',')
    {
	GET_TOKEN(line);
	if (parse_arg(line) != 0)
	    return 1;
    }
    return 0;
}


static int
parse_line(SKLineInfo * line)
{
    GET_TOKEN(line);
    switch (line->token)
    {
    case 0:
	/* empty line */
	return 0;

    case NAME:
    {
	PyObject * temp;

	line->funcname = line->value;

	GET_TOKEN(line);
	if (line->token != '(')
	{
	    line->error = "'(' expected";
	    return 1;
	}
	GET_TOKEN(line);

	/* experimental code that makes the parens optional
	if (line->token == '(')
	{
	    GET_TOKEN(line);
	}
	*/
	if (parse_arglist(line))
	    return 1;

	if (line->token != ')')
	{
	    line->error = "')' expected";
	    return 1;
	}
	GET_TOKEN(line);

	/* experimental
	if (line->token == ')')
	{
	    GET_TOKEN(line);
	}
	*/
	if (line->token != 0)
	    return 1;

	temp = PySequence_Tuple(line->args);
	Py_DECREF(line->args);
	line->args = temp;
    }
    break;
    default:
	return 1;
    }
    return 0;
}


static
PyObject * parse_sk_line(PyObject * self, PyObject * args)
{
    char * string;
    int length;
    SKLineInfo info;
    PyObject * result, * function, *funcdict;

    if (!PyArg_ParseTuple(args, "s#O", &string, &length, &funcdict))
	return NULL;

    info.buffer = string;
    info.length = length;
    info.error = NULL;

    info.funcname = NULL;
    info.args = PyList_New(0);
    info.kwargs = PyDict_New();
    if (!info.args || !info.kwargs)
	goto fail;

    if (parse_line((void*)&info))
    {
	if (info.error)
	    PyErr_SetString(PyExc_SyntaxError, info.error);
	else
	    PyErr_SetString(PyExc_SyntaxError, "parse error");
	goto fail;
    }

    if (info.funcname)
    {
	function = PyObject_GetItem(funcdict, info.funcname);
	if (function)
	{
	    result = PyEval_CallObjectWithKeywords(function, info.args,
						   info.kwargs);
	}
	else
	{
	    char buffer[200];
	    sprintf(buffer, "unknown function %.100s",
		    PyString_AsString(info.funcname));
	    PyErr_SetString(PyExc_NameError, buffer);
	    result = NULL;
	}
	Py_XDECREF(function);
    }
    else
    {
	Py_INCREF(Py_None);
	result = Py_None;
    }
    Py_XDECREF(info.funcname);
    Py_XDECREF(info.args);
    Py_XDECREF(info.kwargs);
    return result;

 fail:
    Py_XDECREF(info.funcname);
    Py_XDECREF(info.args);
    Py_XDECREF(info.kwargs);
    return NULL;
}

static
PyObject * parse_sk_line2(PyObject * self, PyObject * args)
{
    char * string;
    int length;
    SKLineInfo info;
    PyObject * result = NULL;

    if (!PyArg_ParseTuple(args, "s#", &string, &length))
	return NULL;

    info.buffer = string;
    info.length = length;
    info.error = NULL;

    info.funcname = NULL;
    info.args = PyList_New(0);
    info.kwargs = PyDict_New();
    if (!info.args || !info.kwargs)
	goto fail;

    if (parse_line((void*)&info))
    {
	if (info.error)
	    PyErr_SetString(PyExc_SyntaxError, info.error);
	else
	    PyErr_SetString(PyExc_SyntaxError, "parse error");
	goto fail;
    }

    if (!info.funcname)
    {
	/* an empty or comment line */
	Py_INCREF(Py_None);
	info.funcname = Py_None;
    }
    result = Py_BuildValue("OOO", info.funcname, info.args, info.kwargs);

 fail:
    Py_XDECREF(info.funcname);
    Py_XDECREF(info.args);
    Py_XDECREF(info.kwargs);
    return result;
}

static
PyObject * tokenize_line(PyObject * self, PyObject * args)
{
    char * string;
    int length, max_tokens = -1;
    SKLineInfo info;
    PyObject * result;

    if (!PyArg_ParseTuple(args, "s#|i", &string, &length, &max_tokens))
	return NULL;

    info.buffer = string;
    info.length = length;
    info.error = NULL;

    info.funcname = NULL;
    info.args = NULL;
    info.kwargs = NULL;

    result = PyList_New(0);
    if (!result)
	return NULL;

    GET_TOKEN(&info); /* XXX case max_tokens == 0 ?*/
    while (info.token && max_tokens != 0)
    {
	switch (info.token)
	{
	case STRING:
	case NAME:
	case FLOAT:
	case INT:
	    if (PyList_Append(result, info.value) == -1)
		goto fail;
	    Py_DECREF(info.value);
	    if (max_tokens > 0)
		max_tokens--;
	    break;

	default:
	    /* this must be a single character: ()[],=
	     * just ignore for now...
	     */
	    break;
	}
	if (max_tokens != 0)
	    GET_TOKEN(&info);
    }
    info.value = NULL;

    if (max_tokens == 0)
    {
	/*info.buffer -= 1;*/
	if (info.buffer - string < length)
	{
	    PyObject *rest = PyString_FromString(info.buffer);
	    if (PyList_Append(result, rest) == -1)
		goto fail;
	}
    }

    return result;

 fail:
    Py_DECREF(result);
    Py_XDECREF(info.value);
    return NULL;
}

/*
 *	Method table and module initialization
 */

static PyMethodDef sk_methods[] = {
	{"parse_sk_line",	parse_sk_line,		METH_VARARGS},
	{"parse_sk_line2",	parse_sk_line2,		METH_VARARGS},
	{"tokenize_line",	tokenize_line,		METH_VARARGS},
	{NULL,		NULL}
};


DL_EXPORT(void)
initskread(void)
{
    Py_InitModule("skread", sk_methods);
}

