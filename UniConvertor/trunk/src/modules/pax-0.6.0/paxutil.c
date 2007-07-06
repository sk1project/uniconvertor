#include <Python.h>
#include "paxutil.h"

int
pax_checkshortlist(int width, PyObject *list, short **parray, int *pnitems)
{
    int i, n;
    if (!PyList_Check(list))
    {
	PyErr_SetString(PyExc_TypeError, "list of tuples expected");
	return 0;
    }
    n = PyList_Size(list);
    *pnitems = n;
    *parray = PyMem_NEW(short, n*width);
    if (*parray == NULL)
    {
	PyErr_NoMemory();
	return 0;
    }
    for (i = 0; i < n; i++)
    {
	PyObject *item = PyList_GetItem(list, i);
	int j;
	if (!PyTuple_Check(item) || PyTuple_Size(item) != width)
	{
	    char buf[100];
	    PyMem_DEL(*parray);
	    sprintf(buf, "list of %d-tuples expected", width);
	    PyErr_SetString(PyExc_TypeError, buf);
	    return 0;
	}
	for (j = 0; j < width; j++)
	{
	    PyObject *elem = PyTuple_GetItem(item, j);
	    if (!PyInt_Check(elem))
	    {
		PyMem_DEL(*parray);
		PyErr_SetString(PyExc_TypeError,
				"list of tuples of ints expected");
		return 0;
	    }
	    (*parray)[i*width+j] = PyInt_AsLong(elem);
	}
    }
    return 1;
}
