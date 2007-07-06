#ifndef FONTOBJECT_h
#define FONTOBJECT_h

typedef struct {
	PyObject_HEAD
	Display *	display;
	XFontStruct *	font_struct;
	int		from_id;
} PaxFontObject;

extern PyTypeObject PaxFontType;
#define PaxFont_Check(xp)	((xp)->ob_type == &PaxFontType)

extern PyObject *PaxFont_FromName Py_PROTO((Display *, char *));
extern PyObject *PaxFont_FromFont Py_PROTO((Display *, Font));
extern Font PaxFont_AsFont Py_PROTO((PyObject *));
extern XFontStruct * PaxFont_AsFontStruct Py_PROTO((PyObject *));


#endif /* FONTOBJECT_h */
