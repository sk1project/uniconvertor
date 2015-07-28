/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1998, 1999, 2001 by Bernhard Herzog
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
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <Python.h>
#include <ctype.h>

/*
 *	Functions for decoding a PostScript Type1 font program.
 *
 *	Reference: "Adobe Type1 Font Format"
 *		   from Adobe Systems Incorporated
 */

/* decode(BUFFER[, R])	-> data, R
 *
 * Perform eexec/charstring decryption on the buffer BUFFER, using R as
 * the start value for the key. Return the decoded data as a string
 * object and the value of the key at the end of decoding.
 *
 * If not provided, R defaults to 4330, the initial key for char string
 * encryption/decryption.
 */
static PyObject * decode(PyObject * self, PyObject * args)
{
    unsigned char * buffer, *result;
    int buffer_length, i;
    unsigned short r = 4330, c1 = 52845, c2 = 22719;
    int temp = 4330;
    int cipher;
    PyObject * oresult, *tuple;

    /* Use a temporary int vrbl for the optional parameter instead of h
     * to make it work with Python >= 2.0 too */
    if (!PyArg_ParseTuple(args, "s#|i", &buffer, &buffer_length, &temp))
	return NULL;

    r = temp;

    oresult = PyString_FromStringAndSize(NULL, buffer_length);
    if (!oresult)
	return NULL;
    result = (unsigned char*)PyString_AsString(oresult);
    
    for (i = 0; i < buffer_length; i++)
    {
	cipher = buffer[i];
	result[i] = cipher ^ (r >> 8);
	r = (cipher + r) * c1 + c2;
    }

    tuple =  Py_BuildValue("Oi", oresult, r);
    Py_DECREF(oresult);
    return tuple;
}


/*
 * hexdecode(BUFFER)
 *
 * Convert a buffer of hex-digits to binary. Whitespace is ignored.
 *
 * Return a tuple (BINARY, REST). BINARY is a string containing the
 * binary bytes. REST is either the empty string (if BUFFER contained an
 * even number of hex-digits) or the last hex-digit of BUFFER if the
 * number of hex-digits in BUFFER was odd.
 */

static char * hex_digits = "0123456789ABCDEF";

static PyObject * hexdecode(PyObject * self, PyObject * args)
{
    unsigned char * hex, *result, *buffer;
    PyObject *tuple;
    int length, i, last_digit = -1, c;

    if (!PyArg_ParseTuple(args, "s#", &hex, &length))
	return NULL;

    buffer = malloc((length + 1) / 2);
    if (!buffer)
	return PyErr_NoMemory();

    for (i = 0, result = buffer; i < length; i++, hex++)
    {
	c = *hex;
	if (isspace(c))
	    continue;
	if (isxdigit(c))
	{
	    if (isdigit(c))
		c = c - '0';
	    else
	    {
		if (isupper(c))
		    c = c - 'A' + 10;
		else
		    c = c - 'a' + 10;
	    }

	    if (last_digit >= 0)
	    {
		*result++ = last_digit * 16 + c;
		last_digit = -1;
	    }
	    else
		last_digit = c;
	}
	else
	{
	    free(buffer);
	    PyErr_SetString(PyExc_ValueError, "invalid character found");
	    return NULL;
	}
    }

    if (last_digit >= 0)
    	tuple = Py_BuildValue("s#c", buffer, result - buffer,
			      hex_digits[last_digit]);
    else
	tuple = Py_BuildValue("s#s", buffer, result - buffer, "");
    free(buffer);
    return tuple;
}



/*
 *	Method table and module initialization
 */

static PyMethodDef type1_methods[] = {
    {"decode",		decode,		METH_VARARGS},
    {"hexdecode",	hexdecode,	METH_VARARGS},
    {NULL, NULL}
};


DL_EXPORT(void)
init_type1(void)
{
    Py_InitModule("_type1", type1_methods);
}
