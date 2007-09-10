/* Generated automatically from /usr/local/lib/sK1/lib/python2.4/config/config.c.in by makesetup. */
/* -*- C -*- ***********************************************
Copyright (c) 2000, BeOpen.com.
Copyright (c) 1995-2000, Corporation for National Research Initiatives.
Copyright (c) 1990-1995, Stichting Mathematisch Centrum.
All rights reserved.

See the file "Misc/COPYRIGHT" for information on usage and
redistribution of this file, and for a DISCLAIMER OF ALL WARRANTIES.
******************************************************************/

/* Module configuration */

/* !!! !!! !!! This file is edited by the makesetup script !!! !!! !!! */

/* This file contains the table of built-in modules.
   See init_builtin() in import.c. */

#include "Python.h"


extern void initposix(void);
extern void initerrno(void);
extern void init_sre(void);
extern void init_codecs(void);
extern void initzipimport(void);
extern void init_symtable(void);
extern void initxxsubtype(void);

/* -- ADDMODULE MARKER 1 -- */

extern void PyMarshal_Init(void);
extern void initimp(void);
extern void initgc(void);

struct _inittab _PyImport_Inittab[] = {

	{"posix", initposix},
	{"errno", initerrno},
	{"_sre", init_sre},
	{"_codecs", init_codecs},
	{"zipimport", initzipimport},
	{"_symtable", init_symtable},
	{"xxsubtype", initxxsubtype},

/* -- ADDMODULE MARKER 2 -- */

	/* This module lives in marshal.c */
	{"marshal", PyMarshal_Init},

	/* This lives in import.c */
	{"imp", initimp},

	/* These entries are here for sys.builtin_module_names */
	{"__main__", NULL},
	{"__builtin__", NULL},
	{"sys", NULL},
	{"exceptions", NULL},

	/* This lives in gcmodule.c */
	{"gc", initgc},

	/* Sentinel */
	{0, 0}
};
