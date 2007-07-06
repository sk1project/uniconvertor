#ifndef IMAGEOBJECT_H
#define IMAGEOBJECT_H

/* to disable shared memory define PAX_NO_XSHM before including this file */

#ifndef PAX_NO_XSHM
#include <sys/ipc.h>
#include <sys/shm.h>
#include <X11/extensions/XShm.h>
#endif

typedef struct {
	PyObject_HEAD
	XImage *ximage;
#ifndef PAX_NO_XSHM
	XShmSegmentInfo * shminfo;
	Display * display;
#endif
} PaxImageObject;

extern PyTypeObject PaxImageType;
#define PaxImage_Check(xp)	((xp)->ob_type == &PaxImageType)

XImage * PaxImage_AsImage(PyObject *self);

PyObject * PaxImage_FromImage(XImage *ximage);
#ifndef PAX_NO_XSHM
PyObject * PaxImage_FromShmImage(XImage *ximage, XShmSegmentInfo * shminfo,
				 Display * display);
#endif

#endif /* IMAGEOBJECT_H */
