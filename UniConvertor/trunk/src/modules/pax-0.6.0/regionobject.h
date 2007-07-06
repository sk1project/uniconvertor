#ifndef PAXREGION_H
#define PAXREGION_H

#include <X11/X.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>

typedef struct {
    PyObject_HEAD
    Region	region;
} PaxRegionObject;


extern PyTypeObject PaxRegionType;

#define PaxRegion_Check(x) 	((x)->ob_type == &PaxRegionType)

extern Region PaxRegion_AsRegion Py_PROTO((PyObject *));

extern PyObject * PaxRegion_FromRegion(Region);



#endif /* PAXREGION_H */
