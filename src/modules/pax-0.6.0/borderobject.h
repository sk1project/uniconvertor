#ifndef BORDEROBJECT_H
#define BORDEROBJECT_H

#include <Python.h>
#include <tk.h>

typedef struct {
    PyObject_HEAD
    Tk_3DBorder tkborder;
    Tk_Window	tkwin;
    int		borrowed;	/* whether the Tk_3DBOrder is borrowed
				   from some widget or was explicitly
				   allocated for this object */
} PaxBorderObject;

extern PyTypeObject PaxBorderType;
#define PaxBorder_Check(v)	((v)->ob_type == &PaxBorderType)


PyObject * PaxBorder_FromTkBorder(Tk_3DBorder tkborder, Tk_Window tkwin,
				  int borrowed);
Tk_3DBorder PaxBorder_AsTkBorder(PyObject *);

#endif /* BORDEROBJECT_H */
