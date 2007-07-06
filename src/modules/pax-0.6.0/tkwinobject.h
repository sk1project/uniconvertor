#ifndef TKWINOBJECT_H
#define TKWINOBJECT_H

#include <Python.h>
#include <tk.h>

typedef struct {
    PyObject_HEAD
    Tcl_Interp *interp;
    Tk_Window tkwin;
    
} TkWinObject;

extern PyTypeObject TkWinType;
#define TkWin_Check(v)		((v)->ob_type == &TkWinType)


PyObject * TkWin_FromTkWindow(Tcl_Interp* interp, Tk_Window tkwin);
Tk_Window TkWin_AsTkWindow(PyObject *);
Window TkWin_AsWindowID(PyObject *);

#endif /* TKWINOBJECT_H */
