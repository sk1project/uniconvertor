#ifndef PAXPIXMAP_H
#define PAXPIXMAP_H

#include <X11/Xlib.h>
#include <X11/Xutil.h>

typedef struct {
	PyObject_HEAD
	Pixmap		pixmap;
	Display *	display;
	int		owner;
} PaxPixmapObject;

extern PyTypeObject PaxPixmapType;
#define PaxPixmap_Check(x)	((x)->ob_type == &PaxPixmapType)
#define PaxPixmap_CheckOpt(x)	((x) == Py_None || PaxPixmap_Check(x))
#define PaxPixmap_AsPixmapOpt(x) ((x) == Py_None ? None:PaxPixmap_AsPixmap(x))

PyObject *PaxPixmap_FromPixmap Py_PROTO((Display *, Pixmap, int));
Pixmap PaxPixmap_AsPixmap Py_PROTO((PyObject *));
#define PaxPixmap_DISPLAY(pixmap) (((PaxPixmapObject*)pixmap)->display)

typedef PyObject * (*PaxPixmap_FromPixmap_Func)Py_PROTO((Display*,Pixmap,int));

#endif /* PAXPIXMAP_H */
