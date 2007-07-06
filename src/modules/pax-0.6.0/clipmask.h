#ifndef CLIPMASK_H
#define CLIPMASK_H

PyObject * PaxClipMask_Intersect(PyObject * mask1, PyObject * mask2);
PyObject * PaxClipMask_IntersectMasks(PyObject * self, PyObject * args);

#endif /* CLIPMASK_H */
