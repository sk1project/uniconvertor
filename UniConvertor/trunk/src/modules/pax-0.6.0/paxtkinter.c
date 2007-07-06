/***********************************************************
Copyright (C) 1994, 2001 Steen Lumholt.
Copyright 1994-1995 by Stichting Mathematisch Centrum, Amsterdam,
The Netherlands.

                        All Rights Reserved

Permission to use, copy, modify, and distribute this software and its
documentation for any purpose and without fee is hereby granted,
provided that the above copyright notice appear in all copies and that
both that copyright notice and this permission notice appear in
supporting documentation, and that the names of Stichting Mathematisch
Centrum or CWI or Corporation for National Research Initiatives or
CNRI not be used in advertising or publicity pertaining to
distribution of the software without specific, written prior
permission.

While CWI is the initial source for this software, a modified version
is made available by the Corporation for National Research Initiatives
(CNRI) at the Internet address ftp://ftp.python.org.

STICHTING MATHEMATISCH CENTRUM AND CNRI DISCLAIM ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS, IN NO EVENT SHALL STICHTING MATHEMATISCH
CENTRUM OR CNRI BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

******************************************************************/

/* This is a slightly modified version of _tkinter.c as distributed with
 * Python 1.5.2.
 *
 * If Python 1.5.2 is compiled with thread support, its _tkinter module
 * is incompatible with pax because of the new (in Python 1.5.2) TclLock
 * which cannot be accessed from outside of _tkinter.c, but pax would
 * have to do just that to work correctly with Python 1.5.2.
 *
 * To solve this problem, pax is now distributed with its own, non
 * threadable version of _tkinter. This modules is used by Sketch
 * instead of Python's _tkinter only if it runs on Python 1.5.2.
 *
 * This workaround is really only necessary if Python was compiled with
 * thread suport, so if your Python is compiled without threads, you can
 * delete the installed pyxtkinter.so module if you like.
 */

/* _tkinter.c -- Interface to libtk.a and libtcl.a. */

/* TCL/TK VERSION INFO:

   Unix:
	Tcl/Tk 8.0 (even alpha or beta) or 7.6/4.2 are recommended.
	Versions 7.5/4.1 are the earliest versions still supported.
	Versions 7.4/4.0 or Tk 3.x are no longer supported.

   Mac and Windows:
	Use Tcl 8.0 if available (even alpha or beta).
	The oldest usable version is 4.1p1/7.5p1.

   XXX Further speed-up ideas, involving Tcl 8.0 features:

   - In Tcl_Call(), create Tcl objects from the arguments, possibly using
   intelligent mappings between Python objects and Tcl objects (e.g. ints,
   floats and Tcl window pointers could be handled specially).

   - Register a new Tcl type, "Python callable", which can be called more
   efficiently and passed to Tcl_EvalObj() directly (if this is possible).

*/


#include "Python.h"
#include <ctype.h>

/* Thread support hacking. Added for pax */
#ifdef WITH_THREAD
/* define to get readline/EventHook to work in a single-threaded but
   thread-enabled program */
#define PAX_THREAD_HACK 
#endif
/* turn off all other threading specific code here */
#undef WITH_THREAD


#ifdef WITH_THREAD
#include "pythread.h"
#endif

#ifdef MS_WINDOWS
#include <windows.h>
#endif

#ifdef macintosh
#define MAC_TCL
#include "myselect.h"
#endif

#ifdef PYOS_OS2
#include "myselect.h"
#endif

/* Starting with Tcl 8.4, many APIs offer const-correctness.
   Unfortunately, making _tkinter correct for this API means to break
   earlier versions. USE_COMPAT_CONST allows to make Pax work with both
   8.4 and earlier versions. Once Tcl releases before 8.4 don't need to
   be supported anymore, this should go. */
#define USE_COMPAT_CONST

#include <tcl.h>
#include <tk.h>

#define TKMAJORMINOR (TK_MAJOR_VERSION*1000 + TK_MINOR_VERSION)

#if TKMAJORMINOR < 4001
	#error "Tk 4.0 or 3.x are not supported -- use 4.1 or higher"
#endif

#if TKMAJORMINOR >= 8000 && defined(macintosh)
/* Sigh, we have to include this to get at the tcl qd pointer */
#include <tkMac.h>
/* And this one we need to clear the menu bar */
#include <Menus.h>
#endif

#if TKMAJORMINOR < 8000 || !defined(MS_WINDOWS)
#define HAVE_CREATEFILEHANDLER
#endif

#ifdef HAVE_CREATEFILEHANDLER

/* Tcl_CreateFileHandler() changed several times; these macros deal with the
   messiness.  In Tcl 8.0 and later, it is not available on Windows (and on
   Unix, only because Jack added it back); when available on Windows, it only
   applies to sockets. */

#ifdef MS_WINDOWS
#define FHANDLETYPE TCL_WIN_SOCKET
#else
#define FHANDLETYPE TCL_UNIX_FD
#endif

#if TKMAJORMINOR < 8000
#define FHANDLE Tcl_File
#define MAKEFHANDLE(fd) Tcl_GetFile((ClientData)(fd), FHANDLETYPE)
#else
#define FHANDLE int
#define MAKEFHANDLE(fd) (fd)
#endif

/* If Tcl can wait for a Unix file descriptor, define the EventHook() routine
   which uses this to handle Tcl events while the user is typing commands. */

#if FHANDLETYPE == TCL_UNIX_FD
#define WAIT_FOR_STDIN
#endif

#endif /* HAVE_CREATEFILEHANDLER */

#ifdef MS_WINDOWS
#include <conio.h>
#define WAIT_FOR_STDIN
#endif


#ifdef WITH_THREAD

/* The threading situation is complicated.  Tcl is not thread-safe, except for
   Tcl 8.1, which will probably remain in alpha status for another 6 months
   (and the README says that Tk will probably remain thread-unsafe forever).
   So we need to use a lock around all uses of Tcl.  Previously, the Python
   interpreter lock was used for this.  However, this causes problems when
   other Python threads need to run while Tcl is blocked waiting for events.

   To solve this problem, a separate lock for Tcl is introduced.  Holding it
   is incompatible with holding Python's interpreter lock.  The following four
   macros manipulate both locks together.

   ENTER_TCL and LEAVE_TCL are brackets, just like Py_BEGIN_ALLOW_THREADS and
   Py_END_ALLOW_THREADS.  They should be used whenever a call into Tcl is made
   that could call an event handler, or otherwise affect the state of a Tcl
   interpreter.  These assume that the surrounding code has the Python
   interpreter lock; inside the brackets, the Python interpreter lock has been 
   released and the lock for Tcl has been acquired.

   Sometimes, it is necessary to have both the Python lock and the Tcl lock.
   (For example, when transferring data from the Tcl interpreter result to a
   Python string object.)  This can be done by using different macros to close
   the ENTER_TCL block: ENTER_OVERLAP reacquires the Python lock (and restores
   the thread state) but doesn't release the Tcl lock; LEAVE_OVERLAP_TCL
   releases the Tcl lock.

   By contrast, ENTER_PYTHON and LEAVE_PYTHON are used in Tcl event
   handlers when the handler needs to use Python.  Such event handlers are
   entered while the lock for Tcl is held; the event handler presumably needs
   to use Python.  ENTER_PYTHON releases the lock for Tcl and acquires
   the Python interpreter lock, restoring the appropriate thread state, and
   LEAVE_PYTHON releases the Python interpreter lock and re-acquires the lock
   for Tcl.  It is okay for ENTER_TCL/LEAVE_TCL pairs to be contained inside
   the code between ENTER_PYTHON and LEAVE_PYTHON.

   These locks expand to several statements and brackets; they should not be
   used in branches of if statements and the like.

*/

static PyThread_type_lock tcl_lock = 0;
static PyThreadState *tcl_tstate = NULL;

#define ENTER_TCL \
	{ PyThreadState *tstate = PyThreadState_Get(); Py_BEGIN_ALLOW_THREADS \
	    PyThread_acquire_lock(tcl_lock, 1); tcl_tstate = tstate;

#define LEAVE_TCL \
	tcl_tstate = NULL; PyThread_release_lock(tcl_lock); Py_END_ALLOW_THREADS}

#define ENTER_OVERLAP \
	Py_END_ALLOW_THREADS

#define LEAVE_OVERLAP_TCL \
	tcl_tstate = NULL; PyThread_release_lock(tcl_lock); }

#define ENTER_PYTHON \
	{ PyThreadState *tstate = tcl_tstate; tcl_tstate = NULL; \
            PyThread_release_lock(tcl_lock); PyEval_RestoreThread((tstate)); }

#define LEAVE_PYTHON \
	{ PyThreadState *tstate = PyEval_SaveThread(); \
            PyThread_acquire_lock(tcl_lock, 1); tcl_tstate = tstate; }

#else

#define ENTER_TCL
#define LEAVE_TCL
#define ENTER_OVERLAP
#define LEAVE_OVERLAP_TCL
#define ENTER_PYTHON
#define LEAVE_PYTHON

#endif

#ifdef macintosh

/*
** Additional cruft needed by Tcl/Tk on the Mac.
** This is for Tcl 7.5 and Tk 4.1 (patch release 1).
*/

/* ckfree() expects a char* */
#define FREECAST (char *)

#include <Events.h> /* For EventRecord */

typedef int (*TclMacConvertEventPtr) Py_PROTO((EventRecord *eventPtr));
/* They changed the name... */
#if TKMAJORMINOR < 8000
#define Tcl_MacSetEventProc TclMacSetEventProc
#endif
void Tcl_MacSetEventProc Py_PROTO((TclMacConvertEventPtr procPtr));
int TkMacConvertEvent Py_PROTO((EventRecord *eventPtr));

staticforward int PyMacConvertEvent Py_PROTO((EventRecord *eventPtr));

#if defined(__CFM68K__) && !defined(__USING_STATIC_LIBS__)
	#pragma import on
#endif

#include <SIOUX.h>
extern int SIOUXIsAppWindow(WindowPtr);

#if defined(__CFM68K__) && !defined(__USING_STATIC_LIBS__)
	#pragma import reset
#endif
#endif /* macintosh */

#ifndef FREECAST
#define FREECAST (char *)
#endif

/**** Tkapp Object Declaration ****/

staticforward PyTypeObject Tkapp_Type;

typedef struct {
	PyObject_HEAD
	Tcl_Interp *interp;
} TkappObject;

#define Tkapp_Check(v) ((v)->ob_type == &Tkapp_Type)
#define Tkapp_Interp(v) (((TkappObject *) (v))->interp)
#define Tkapp_Result(v) (((TkappObject *) (v))->interp->result)

#define DEBUG_REFCNT(v) (printf("DEBUG: id=%p, refcnt=%i\n", \
(void *) v, ((PyObject *) v)->ob_refcnt))



/**** Error Handling ****/

static PyObject *Tkinter_TclError;
static int quitMainLoop = 0;
static int errorInCmd = 0;
static PyObject *excInCmd;
static PyObject *valInCmd;
static PyObject *trbInCmd;



static PyObject *
Tkinter_Error(PyObject *v)
{
	PyErr_SetString(Tkinter_TclError, Tkapp_Result(v));
	return NULL;
}



/**** Utils ****/

#ifdef WITH_THREAD
#ifndef MS_WINDOWS
#include "mytime.h"
#include "myselect.h"

/* Millisecond sleep() for Unix platforms. */

static void
Sleep(int milli)
{
	/* XXX Too bad if you don't have select(). */
	struct timeval t;
	double frac;
	t.tv_sec = milli/1000;
	t.tv_usec = (milli%1000) * 1000;
	select(0, (fd_set *)0, (fd_set *)0, (fd_set *)0, &t);
}
#endif /* MS_WINDOWS */
#endif /* WITH_THREAD */


static char *
AsString(PyObject *value, PyObject *tmp)
{
	if (PyString_Check(value))
		return PyString_AsString(value);
	else {
		PyObject *v = PyObject_Str(value);
		PyList_Append(tmp, v);
		Py_DECREF(v);
		return PyString_AsString(v);
	}
}



#define ARGSZ 64

static char *
Merge(PyObject *args)
{
	PyObject *tmp = NULL;
	char *argvStore[ARGSZ];
	char **argv = NULL;
	int fvStore[ARGSZ];
	int *fv = NULL;
	int argc = 0, i;
	char *res = NULL;

	if (!(tmp = PyList_New(0)))
	    return NULL;

	argv = argvStore;
	fv = fvStore;

	if (args == NULL)
		argc = 0;

	else if (!PyTuple_Check(args)) {
		argc = 1;
		fv[0] = 0;
		argv[0] = AsString(args, tmp);
	}
	else {
		argc = PyTuple_Size(args);

		if (argc > ARGSZ) {
			argv = (char **)ckalloc(argc * sizeof(char *));
			fv = (int *)ckalloc(argc * sizeof(int));
			if (argv == NULL || fv == NULL) {
				PyErr_NoMemory();
				goto finally;
			}
		}

		for (i = 0; i < argc; i++) {
			PyObject *v = PyTuple_GetItem(args, i);
			if (PyTuple_Check(v)) {
				fv[i] = 1;
				if (!(argv[i] = Merge(v)))
					goto finally;
			}
			else if (v == Py_None) {
				argc = i;
				break;
			}
			else {
				fv[i] = 0;
				argv[i] = AsString(v, tmp);
			}
		}
	}
	res = Tcl_Merge(argc, argv);

  finally:
	for (i = 0; i < argc; i++)
		if (fv[i]) {
			ckfree(argv[i]);
		}
	if (argv != argvStore)
		ckfree(FREECAST argv);
	if (fv != fvStore)
		ckfree(FREECAST fv);

	Py_DECREF(tmp);
	return res;
}



static PyObject *
Split(char *list)
{
	int argc;
	char **argv;
	PyObject *v;

	if (list == NULL) {
		Py_INCREF(Py_None);
		return Py_None;
	}

	if (Tcl_SplitList((Tcl_Interp *)NULL, list, &argc, &argv) != TCL_OK) {
		/* Not a list.
		 * Could be a quoted string containing funnies, e.g. {"}.
		 * Return the string itself.
		 */
		return PyString_FromString(list);
	}

	if (argc == 0)
		v = PyString_FromString("");
	else if (argc == 1)
		v = PyString_FromString(argv[0]);
	else if ((v = PyTuple_New(argc)) != NULL) {
		int i;
		PyObject *w;

		for (i = 0; i < argc; i++) {
			if ((w = Split(argv[i])) == NULL) {
				Py_DECREF(v);
				v = NULL;
				break;
			}
			PyTuple_SetItem(v, i, w);
		}
	}
	Tcl_Free(FREECAST argv);
	return v;
}



/**** Tkapp Object ****/

int
Tcl_AppInit(Tcl_Interp *interp)
{
	if (Tcl_Init(interp) == TCL_ERROR) {
		PySys_WriteStderr("Tcl_Init error: %s\n", interp->result);
		return TCL_ERROR;
	}
	if (Tk_Init(interp) == TCL_ERROR) {
		PySys_WriteStderr("Tk_Init error: %s\n", interp->result);
		return TCL_ERROR;
	}
	return TCL_OK;
}




/* Initialize the Tk application; see the `main' function in
 * `tkMain.c'.
 */

static void EnableEventHook(void); /* Forward */
static void DisableEventHook(void); /* Forward */

static TkappObject *
Tkapp_New(char *screenName, char *baseName, char *className, int interactive)
{
	TkappObject *v;
	char *argv0;
  
	v = PyObject_NEW(TkappObject, &Tkapp_Type);
	if (v == NULL)
		return NULL;

	v->interp = Tcl_CreateInterp();

#if defined(macintosh) && TKMAJORMINOR >= 8000
	/* This seems to be needed since Tk 8.0 */
	ClearMenuBar();
	TkMacInitMenus(v->interp);
#endif
	/* Delete the 'exit' command, which can screw things up */
	Tcl_DeleteCommand(v->interp, "exit");

	if (screenName != NULL)
		Tcl_SetVar2(v->interp, "env", "DISPLAY",
			    screenName, TCL_GLOBAL_ONLY);

	if (interactive)
		Tcl_SetVar(v->interp, "tcl_interactive", "1", TCL_GLOBAL_ONLY);
	else
		Tcl_SetVar(v->interp, "tcl_interactive", "0", TCL_GLOBAL_ONLY);

	/* This is used to get the application class for Tk 4.1 and up */
	argv0 = (char*)ckalloc(strlen(className) + 1);
	if (!argv0) {
		PyErr_NoMemory();
		Py_DECREF(v);
		return NULL;
	}

	strcpy(argv0, className);
	if (isupper((int)(argv0[0])))
		argv0[0] = tolower(argv0[0]);
	Tcl_SetVar(v->interp, "argv0", argv0, TCL_GLOBAL_ONLY);
	ckfree(argv0);

	if (Tcl_AppInit(v->interp) != TCL_OK)
		return (TkappObject *)Tkinter_Error((PyObject *)v);

	EnableEventHook();

	return v;
}



/** Tcl Eval **/

static PyObject *
Tkapp_Call(PyObject *self, PyObject *args)
{
	/* This is copied from Merge() */
	PyObject *tmp = NULL;
	char *argvStore[ARGSZ];
	char **argv = NULL;
	int fvStore[ARGSZ];
	int *fv = NULL;
	int argc = 0, i;
	PyObject *res = NULL; /* except this has a different type */
	Tcl_CmdInfo info; /* and this is added */
	Tcl_Interp *interp = Tkapp_Interp(self); /* and this too */

	if (!(tmp = PyList_New(0)))
	    return NULL;

	argv = argvStore;
	fv = fvStore;

	if (args == NULL)
		argc = 0;

	else if (!PyTuple_Check(args)) {
		argc = 1;
		fv[0] = 0;
		argv[0] = AsString(args, tmp);
	}
	else {
		argc = PyTuple_Size(args);

		if (argc > ARGSZ) {
			argv = (char **)ckalloc(argc * sizeof(char *));
			fv = (int *)ckalloc(argc * sizeof(int));
			if (argv == NULL || fv == NULL) {
				PyErr_NoMemory();
				goto finally;
			}
		}

		for (i = 0; i < argc; i++) {
			PyObject *v = PyTuple_GetItem(args, i);
			if (PyTuple_Check(v)) {
				fv[i] = 1;
				if (!(argv[i] = Merge(v)))
					goto finally;
			}
			else if (v == Py_None) {
				argc = i;
				break;
			}
			else {
				fv[i] = 0;
				argv[i] = AsString(v, tmp);
			}
		}
	}
	/* End code copied from Merge() */

	/* All this to avoid a call to Tcl_Merge() and the corresponding call
	   to Tcl_SplitList() inside Tcl_Eval()...  It can save a bundle! */
	if (Py_VerboseFlag >= 2) {
		for (i = 0; i < argc; i++)
			PySys_WriteStderr("%s ", argv[i]);
	}
	ENTER_TCL
	info.proc = NULL;
	if (argc < 1 ||
	    !Tcl_GetCommandInfo(interp, argv[0], &info) ||
	    info.proc == NULL)
	{
		char *cmd;
		cmd = Tcl_Merge(argc, argv);
		i = Tcl_Eval(interp, cmd);
		ckfree(cmd);
	}
	else {
		Tcl_ResetResult(interp);
		i = (*info.proc)(info.clientData, interp, argc, argv);
	}
	ENTER_OVERLAP
	if (info.proc == NULL && Py_VerboseFlag >= 2)
		PySys_WriteStderr("... use TclEval ");
	if (i == TCL_ERROR) {
		if (Py_VerboseFlag >= 2)
			PySys_WriteStderr("... error: '%s'\n",
				interp->result);
		Tkinter_Error(self);
	}
	else {
		if (Py_VerboseFlag >= 2)
			PySys_WriteStderr("-> '%s'\n", interp->result);
		res = PyString_FromString(interp->result);
	}
	LEAVE_OVERLAP_TCL

	/* Copied from Merge() again */
  finally:
	for (i = 0; i < argc; i++)
		if (fv[i]) {
			ckfree(argv[i]);
		}
	if (argv != argvStore)
		ckfree(FREECAST argv);
	if (fv != fvStore)
		ckfree(FREECAST fv);

	Py_DECREF(tmp);
	return res;
}


static PyObject *
Tkapp_GlobalCall(PyObject *self, PyObject *args)
{
	/* Could do the same here as for Tkapp_Call(), but this is not used
	   much, so I can't be bothered.  Unfortunately Tcl doesn't export a
	   way for the user to do what all its Global* variants do (save and
	   reset the scope pointer, call the local version, restore the saved
	   scope pointer). */

	char *cmd;
	PyObject *res = NULL;

	cmd  = Merge(args);
	if (!cmd)
		PyErr_SetString(Tkinter_TclError, "merge failed");

	else {
		int err;
		ENTER_TCL
		err = Tcl_GlobalEval(Tkapp_Interp(self), cmd);
		ENTER_OVERLAP
		if (err == TCL_ERROR)
			res = Tkinter_Error(self);
		else
			res = PyString_FromString(Tkapp_Result(self));
		LEAVE_OVERLAP_TCL
	}

	if (cmd)
		ckfree(cmd);

	return res;
}

static PyObject *
Tkapp_Eval(PyObject *self, PyObject *args)
{
	char *script;
	PyObject *res = NULL;
	int err;
  
	if (!PyArg_ParseTuple(args, "s", &script))
		return NULL;

	ENTER_TCL
	err = Tcl_Eval(Tkapp_Interp(self), script);
	ENTER_OVERLAP
	if (err == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = PyString_FromString(Tkapp_Result(self));
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_GlobalEval(PyObject *self, PyObject *args)
{
	char *script;
	PyObject *res = NULL;
	int err;

	if (!PyArg_ParseTuple(args, "s", &script))
		return NULL;

	ENTER_TCL
	err = Tcl_GlobalEval(Tkapp_Interp(self), script);
	ENTER_OVERLAP
	if (err == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = PyString_FromString(Tkapp_Result(self));
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_EvalFile(PyObject *self, PyObject *args)
{
	char *fileName;
	PyObject *res = NULL;
	int err;

	if (!PyArg_ParseTuple(args, "s", &fileName))
		return NULL;

	ENTER_TCL
	err = Tcl_EvalFile(Tkapp_Interp(self), fileName);
	ENTER_OVERLAP
	if (err == TCL_ERROR)
		res = Tkinter_Error(self);

	else
		res = PyString_FromString(Tkapp_Result(self));
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_Record(PyObject *self, PyObject *args)
{
	char *script;
	PyObject *res = NULL;
	int err;

	if (!PyArg_ParseTuple(args, "s", &script))
		return NULL;

	ENTER_TCL
	err = Tcl_RecordAndEval(Tkapp_Interp(self), script, TCL_NO_EVAL);
	ENTER_OVERLAP
	if (err == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = PyString_FromString(Tkapp_Result(self));
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_AddErrorInfo(PyObject *self, PyObject *args)
{
	char *msg;

	if (!PyArg_ParseTuple(args, "s", &msg))
		return NULL;
	ENTER_TCL
	Tcl_AddErrorInfo(Tkapp_Interp(self), msg);
	LEAVE_TCL

	Py_INCREF(Py_None);
	return Py_None;
}



/** Tcl Variable **/

static PyObject *
SetVar(PyObject *self, PyObject *args, int flags)
{
	char *name1, *name2, *s;
	const char *ok;
	PyObject *newValue;
	PyObject *tmp;

	tmp = PyList_New(0);
	if (!tmp)
		return NULL;

	if (PyArg_ParseTuple(args, "sO", &name1, &newValue)) {
		/* XXX Merge? */
		s = AsString(newValue, tmp);
		ENTER_TCL
		ok = Tcl_SetVar(Tkapp_Interp(self), name1, s, flags);
		LEAVE_TCL
	}
	else {
		PyErr_Clear();
		if (PyArg_ParseTuple(args, "ssO", &name1, &name2, &newValue)) {
			s = AsString (newValue, tmp);
			ENTER_TCL
			ok = Tcl_SetVar2(Tkapp_Interp(self), name1, name2, 
					 s, flags);
			LEAVE_TCL
		}
		else {
			Py_DECREF(tmp);
			return NULL;
		}
	}
	Py_DECREF(tmp);

	if (!ok)
		return Tkinter_Error(self);

	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
Tkapp_SetVar(PyObject *self, PyObject *args)
{
	return SetVar(self, args, TCL_LEAVE_ERR_MSG);
}

static PyObject *
Tkapp_GlobalSetVar(PyObject *self, PyObject *args)
{
	return SetVar(self, args, TCL_LEAVE_ERR_MSG | TCL_GLOBAL_ONLY);
}



static PyObject *
GetVar(PyObject *self, PyObject *args, int flags)
{
	char *name1, *name2=NULL;
	const char *s;
	PyObject *res = NULL;

	if (!PyArg_ParseTuple(args, "s|s", &name1, &name2))
		return NULL;
	ENTER_TCL
	if (name2 == NULL)
		s = Tcl_GetVar(Tkapp_Interp(self), name1, flags);

	else
		s = Tcl_GetVar2(Tkapp_Interp(self), name1, name2, flags);
	ENTER_OVERLAP

	if (s == NULL)
		res = Tkinter_Error(self);
	else
		res = PyString_FromString(s);
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_GetVar(PyObject *self, PyObject *args)
{
	return GetVar(self, args, TCL_LEAVE_ERR_MSG);
}

static PyObject *
Tkapp_GlobalGetVar(PyObject *self, PyObject *args)
{
	return GetVar(self, args, TCL_LEAVE_ERR_MSG | TCL_GLOBAL_ONLY);
}



static PyObject *
UnsetVar(PyObject *self, PyObject *args, int flags)
{
	char *name1, *name2=NULL;
	PyObject *res = NULL;
	int code;

	if (!PyArg_ParseTuple(args, "s|s", &name1, &name2))
		return NULL;
	ENTER_TCL
	if (name2 == NULL)
		code = Tcl_UnsetVar(Tkapp_Interp(self), name1, flags);

	else
		code = Tcl_UnsetVar2(Tkapp_Interp(self), name1, name2, flags);
	ENTER_OVERLAP

	if (code == TCL_ERROR)
		res = Tkinter_Error(self);
	else {
		Py_INCREF(Py_None);
		res = Py_None;
	}
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_UnsetVar(PyObject *self, PyObject *args)
{
	return UnsetVar(self, args, TCL_LEAVE_ERR_MSG);
}

static PyObject *
Tkapp_GlobalUnsetVar(PyObject *self, PyObject *args)
{
	return UnsetVar(self, args, TCL_LEAVE_ERR_MSG | TCL_GLOBAL_ONLY);
}



/** Tcl to Python **/

static PyObject *
Tkapp_GetInt(PyObject *self, PyObject *args)
{
	char *s;
	int v;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	if (Tcl_GetInt(Tkapp_Interp(self), s, &v) == TCL_ERROR)
		return Tkinter_Error(self);
	return Py_BuildValue("i", v);
}

static PyObject *
Tkapp_GetDouble(PyObject *self, PyObject *args)
{
	char *s;
	double v;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	if (Tcl_GetDouble(Tkapp_Interp(self), s, &v) == TCL_ERROR)
		return Tkinter_Error(self);
	return Py_BuildValue("d", v);
}

static PyObject *
Tkapp_GetBoolean(PyObject *self, PyObject *args)
{
	char *s;
	int v;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	if (Tcl_GetBoolean(Tkapp_Interp(self), s, &v) == TCL_ERROR)
		return Tkinter_Error(self);
	return Py_BuildValue("i", v);
}

static PyObject *
Tkapp_ExprString(PyObject *self, PyObject *args)
{
	char *s;
	PyObject *res = NULL;
	int retval;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	ENTER_TCL
	retval = Tcl_ExprString(Tkapp_Interp(self), s);
	ENTER_OVERLAP
	if (retval == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = Py_BuildValue("s", Tkapp_Result(self));
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_ExprLong(PyObject *self, PyObject *args)
{
	char *s;
	PyObject *res = NULL;
	int retval;
	long v;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	ENTER_TCL
	retval = Tcl_ExprLong(Tkapp_Interp(self), s, &v);
	ENTER_OVERLAP
	if (retval == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = Py_BuildValue("l", v);
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_ExprDouble(PyObject *self, PyObject *args)
{
	char *s;
	PyObject *res = NULL;
	double v;
	int retval;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	PyFPE_START_PROTECT("Tkapp_ExprDouble", return 0)
	ENTER_TCL
	retval = Tcl_ExprDouble(Tkapp_Interp(self), s, &v);
	ENTER_OVERLAP
	PyFPE_END_PROTECT(retval)
	if (retval == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = Py_BuildValue("d", v);
	LEAVE_OVERLAP_TCL
	return res;
}

static PyObject *
Tkapp_ExprBoolean(PyObject *self, PyObject *args)
{
	char *s;
	PyObject *res = NULL;
	int retval;
	int v;

	if (!PyArg_ParseTuple(args, "s", &s))
		return NULL;
	ENTER_TCL
	retval = Tcl_ExprBoolean(Tkapp_Interp(self), s, &v);
	ENTER_OVERLAP
	if (retval == TCL_ERROR)
		res = Tkinter_Error(self);
	else
		res = Py_BuildValue("i", v);
	LEAVE_OVERLAP_TCL
	return res;
}



static PyObject *
Tkapp_SplitList(PyObject *self, PyObject *args)
{
	char *list;
	int argc;
	char **argv;
	PyObject *v;
	int i;

	if (!PyArg_ParseTuple(args, "s", &list))
		return NULL;

	if (Tcl_SplitList(Tkapp_Interp(self), list, &argc, &argv) == TCL_ERROR)
		return Tkinter_Error(self);

	if (!(v = PyTuple_New(argc)))
		return NULL;
	
	for (i = 0; i < argc; i++) {
		PyObject *s = PyString_FromString(argv[i]);
		if (!s || PyTuple_SetItem(v, i, s)) {
			Py_DECREF(v);
			v = NULL;
			goto finally;
		}
	}

  finally:
	ckfree(FREECAST argv);
	return v;
}

static PyObject *
Tkapp_Split(PyObject *self, PyObject *args)
{
	char *list;

	if (!PyArg_ParseTuple(args, "s", &list))
		return NULL;
	return Split(list);
}

static PyObject *
Tkapp_Merge(PyObject *self, PyObject *args)
{
	char *s = Merge(args);
	PyObject *res = NULL;

	if (s) {
		res = PyString_FromString(s);
		ckfree(s);
	}
	else
		PyErr_SetString(Tkinter_TclError, "merge failed");

	return res;
}



/** Tcl Command **/

/* Client data struct */
typedef struct {
	PyObject *self;
	PyObject *func;
} PythonCmd_ClientData;

static int
PythonCmd_Error(Tcl_Interp *interp)
{
	errorInCmd = 1;
	PyErr_Fetch(&excInCmd, &valInCmd, &trbInCmd);
	LEAVE_PYTHON
	return TCL_ERROR;
}

/* This is the Tcl command that acts as a wrapper for Python
 * function or method.
 */
static int
PythonCmd(ClientData clientData, Tcl_Interp *interp, int argc, char *argv[])
{
	PythonCmd_ClientData *data = (PythonCmd_ClientData *)clientData;
	PyObject *self, *func, *arg, *res, *tmp;
	int i;

	ENTER_PYTHON

	/* TBD: no error checking here since we know, via the
	 * Tkapp_CreateCommand() that the client data is a two-tuple
	 */
	self = data->self;
	func = data->func;

	/* Create argument list (argv1, ..., argvN) */
	if (!(arg = PyTuple_New(argc - 1)))
		return PythonCmd_Error(interp);

	for (i = 0; i < (argc - 1); i++) {
		PyObject *s = PyString_FromString(argv[i + 1]);
		if (!s || PyTuple_SetItem(arg, i, s)) {
			Py_DECREF(arg);
			return PythonCmd_Error(interp);
		}
	}
	res = PyEval_CallObject(func, arg);
	Py_DECREF(arg);

	if (res == NULL)
		return PythonCmd_Error(interp);

	if (!(tmp = PyList_New(0))) {
		Py_DECREF(res);
		return PythonCmd_Error(interp);
	}

	Tcl_SetResult(Tkapp_Interp(self), AsString(res, tmp), TCL_VOLATILE);
	Py_DECREF(res);
	Py_DECREF(tmp);

	LEAVE_PYTHON

	return TCL_OK;
}

static void
PythonCmdDelete(ClientData clientData)
{
	PythonCmd_ClientData *data = (PythonCmd_ClientData *)clientData;

	ENTER_PYTHON
	Py_XDECREF(data->self);
	Py_XDECREF(data->func);
	PyMem_DEL(data);
	LEAVE_PYTHON
}



static PyObject *
Tkapp_CreateCommand(PyObject *self, PyObject *args)
{
	PythonCmd_ClientData *data;
	char *cmdName;
	PyObject *func;
	Tcl_Command err;

	if (!PyArg_ParseTuple(args, "sO", &cmdName, &func))
		return NULL;
	if (!PyCallable_Check(func)) {
		PyErr_SetString(PyExc_TypeError, "command not callable");
		return NULL;
	}

	data = PyMem_NEW(PythonCmd_ClientData, 1);
	if (!data)
		return NULL;
	Py_XINCREF(self);
	Py_XINCREF(func);
	data->self = self;
	data->func = func;

	ENTER_TCL
	err = Tcl_CreateCommand(Tkapp_Interp(self), cmdName, PythonCmd,
				(ClientData)data, PythonCmdDelete);
	LEAVE_TCL
	if (err == NULL) {
		PyErr_SetString(Tkinter_TclError, "can't create Tcl command");
		PyMem_DEL(data);
		return NULL;
	}

	Py_INCREF(Py_None);
	return Py_None;
}



static PyObject *
Tkapp_DeleteCommand(PyObject *self, PyObject *args)
{
	char *cmdName;
	int err;

	if (!PyArg_ParseTuple(args, "s", &cmdName))
		return NULL;
	ENTER_TCL
	err = Tcl_DeleteCommand(Tkapp_Interp(self), cmdName);
	LEAVE_TCL
	if (err == -1) {
		PyErr_SetString(Tkinter_TclError, "can't delete Tcl command");
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}



#ifdef HAVE_CREATEFILEHANDLER
/** File Handler **/

typedef struct _fhcdata {
	PyObject *func;
	PyObject *file;
	int id;
	struct _fhcdata *next;
} FileHandler_ClientData;

static FileHandler_ClientData *HeadFHCD;

static FileHandler_ClientData *
NewFHCD(PyObject *func, PyObject *file, int id)
{
	FileHandler_ClientData *p;
	p = PyMem_NEW(FileHandler_ClientData, 1);
	if (p != NULL) {
		Py_XINCREF(func);
		Py_XINCREF(file);
		p->func = func;
		p->file = file;
		p->id = id;
		p->next = HeadFHCD;
		HeadFHCD = p;
	}
	return p;
}

static void
DeleteFHCD(int id)
{
	FileHandler_ClientData *p, **pp;
	
	pp = &HeadFHCD; 
	while ((p = *pp) != NULL) {
		if (p->id == id) {
			*pp = p->next;
			Py_XDECREF(p->func);
			Py_XDECREF(p->file);
			PyMem_DEL(p);
		}
		else
			pp = &p->next;
	}
}

static void
FileHandler(ClientData clientData, int mask)
{
	FileHandler_ClientData *data = (FileHandler_ClientData *)clientData;
	PyObject *func, *file, *arg, *res;

	ENTER_PYTHON
	func = data->func;
	file = data->file;

	arg = Py_BuildValue("(Oi)", file, (long) mask);
	res = PyEval_CallObject(func, arg);
	Py_DECREF(arg);

	if (res == NULL) {
		errorInCmd = 1;
		PyErr_Fetch(&excInCmd, &valInCmd, &trbInCmd);
	}
	Py_XDECREF(res);
	LEAVE_PYTHON
}

static int
GetFileNo(PyObject *file) /* Either an int >= 0 or an object with
			   * .fileno() method that returns an int >= 0
			   */
{
	PyObject *meth, *args, *res;
	int id;
	if (PyInt_Check(file)) {
		id = PyInt_AsLong(file);
		if (id < 0)
			PyErr_SetString(PyExc_ValueError, "invalid file id");
		return id;
	}
	args = PyTuple_New(0);
	if (args == NULL)
		return -1;

	meth = PyObject_GetAttrString(file, "fileno");
	if (meth == NULL) {
		Py_DECREF(args);
		return -1;
	}

	res = PyEval_CallObject(meth, args);
	Py_DECREF(args);
	Py_DECREF(meth);
	if (res == NULL)
		return -1;

	if (PyInt_Check(res))
		id = PyInt_AsLong(res);
	else
		id = -1;

	if (id < 0)
		PyErr_SetString(PyExc_ValueError,
				"invalid fileno() return value");
	Py_DECREF(res);
	return id;
}

static PyObject *
Tkapp_CreateFileHandler(PyObject *self, PyObject *args)
    /* Is (file, mask, func) */
{
	FileHandler_ClientData *data;
	PyObject *file, *func;
	int mask, id;
	FHANDLE tfile;

	if (!PyArg_ParseTuple(args, "OiO", &file, &mask, &func))
		return NULL;
	id = GetFileNo(file);
	if (id < 0)
		return NULL;
	if (!PyCallable_Check(func)) {
		PyErr_SetString(PyExc_TypeError, "bad argument list");
		return NULL;
	}

	data = NewFHCD(func, file, id);
	if (data == NULL)
		return NULL;

	tfile = MAKEFHANDLE(id);
	/* Ought to check for null Tcl_File object... */
	ENTER_TCL
	Tcl_CreateFileHandler(tfile, mask, FileHandler, (ClientData) data);
	LEAVE_TCL
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
Tkapp_DeleteFileHandler(PyObject *self, PyObject *args)
    /* Args: file */
{
	PyObject *file;
	int id;
	FHANDLE tfile;
  
	if (!PyArg_ParseTuple(args, "O", &file))
		return NULL;
	id = GetFileNo(file);
	if (id < 0)
		return NULL;

	DeleteFHCD(id);

	tfile = MAKEFHANDLE(id);
	/* Ought to check for null Tcl_File object... */
	ENTER_TCL
	Tcl_DeleteFileHandler(tfile);
	LEAVE_TCL
	Py_INCREF(Py_None);
	return Py_None;
}
#endif /* HAVE_CREATEFILEHANDLER */


/**** Tktt Object (timer token) ****/

staticforward PyTypeObject Tktt_Type;

typedef struct {
	PyObject_HEAD
	Tcl_TimerToken token;
	PyObject *func;
} TkttObject;

static PyObject *
Tktt_DeleteTimerHandler(PyObject *self, PyObject *args)
{
	TkttObject *v = (TkttObject *)self;
	PyObject *func = v->func;

	if (!PyArg_ParseTuple(args, ""))
		return NULL;
	if (v->token != NULL) {
		Tcl_DeleteTimerHandler(v->token);
		v->token = NULL;
	}
	if (func != NULL) {
		v->func = NULL;
		Py_DECREF(func);
		Py_DECREF(v); /* See Tktt_New() */
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyMethodDef Tktt_methods[] =
{
	{"deletetimerhandler", Tktt_DeleteTimerHandler, 1},
	{NULL, NULL}
};

static TkttObject *
Tktt_New(PyObject *func)
{
	TkttObject *v;
  
	v = PyObject_NEW(TkttObject, &Tktt_Type);
	if (v == NULL)
		return NULL;

	Py_INCREF(func);
	v->token = NULL;
	v->func = func;

	/* Extra reference, deleted when called or when handler is deleted */
	Py_INCREF(v);
	return v;
}

static void
Tktt_Dealloc(PyObject *self)
{
	TkttObject *v = (TkttObject *)self;
	PyObject *func = v->func;

	Py_XDECREF(func);

	PyMem_DEL(self);
}

static PyObject *
Tktt_Repr(PyObject *self)
{
	TkttObject *v = (TkttObject *)self;
	char buf[100];

	sprintf(buf, "<tktimertoken at 0x%lx%s>", (long)v,
		v->func == NULL ? ", handler deleted" : "");
	return PyString_FromString(buf);
}

static PyObject *
Tktt_GetAttr(PyObject *self, char *name)
{
	return Py_FindMethod(Tktt_methods, self, name);
}

static PyTypeObject Tktt_Type =
{
	PyObject_HEAD_INIT(NULL)
	0,				     /*ob_size */
	"tktimertoken",			     /*tp_name */
	sizeof(TkttObject),		     /*tp_basicsize */
	0,				     /*tp_itemsize */
	Tktt_Dealloc,			     /*tp_dealloc */
	0,				     /*tp_print */
	Tktt_GetAttr,			     /*tp_getattr */
	0,				     /*tp_setattr */
	0,				     /*tp_compare */
	Tktt_Repr,			     /*tp_repr */
	0,				     /*tp_as_number */
	0,				     /*tp_as_sequence */
	0,				     /*tp_as_mapping */
	0,				     /*tp_hash */
};



/** Timer Handler **/

static void
TimerHandler(ClientData clientData)
{
	TkttObject *v = (TkttObject *)clientData;
	PyObject *func = v->func;
	PyObject *res;

	if (func == NULL)
		return;

	v->func = NULL;

	ENTER_PYTHON

	res  = PyEval_CallObject(func, NULL);
	Py_DECREF(func);
	Py_DECREF(v); /* See Tktt_New() */

	if (res == NULL) {
		errorInCmd = 1;
		PyErr_Fetch(&excInCmd, &valInCmd, &trbInCmd);
	}
	else
		Py_DECREF(res);

	LEAVE_PYTHON
}

static PyObject *
Tkapp_CreateTimerHandler(PyObject *self, PyObject *args)
    /* Is (milliseconds, func) */
{
	int milliseconds;
	PyObject *func;
	TkttObject *v;

	if (!PyArg_ParseTuple(args, "iO", &milliseconds, &func))
		return NULL;
	if (!PyCallable_Check(func)) {
		PyErr_SetString(PyExc_TypeError, "bad argument list");
		return NULL;
	}
	v = Tktt_New(func);
	v->token = Tcl_CreateTimerHandler(milliseconds, TimerHandler,
					  (ClientData)v);

	return (PyObject *) v;
}


/** Event Loop **/

static PyObject *
Tkapp_MainLoop(PyObject *self, PyObject *args)
{
	int threshold = 0;
#ifdef WITH_THREAD
	PyThreadState *tstate = PyThreadState_Get();
#endif

	if (!PyArg_ParseTuple(args, "|i", &threshold))
		return NULL;

	quitMainLoop = 0;
	while (Tk_GetNumMainWindows() > threshold &&
	       !quitMainLoop &&
	       !errorInCmd)
	{
		int result;

#ifdef WITH_THREAD
		Py_BEGIN_ALLOW_THREADS
		PyThread_acquire_lock(tcl_lock, 1);
		tcl_tstate = tstate;
		result = Tcl_DoOneEvent(TCL_DONT_WAIT);
		tcl_tstate = NULL;
		PyThread_release_lock(tcl_lock);
		if (result == 0)
			Sleep(20);
		Py_END_ALLOW_THREADS
#else
		result = Tcl_DoOneEvent(0);
#endif

		if (PyErr_CheckSignals() != 0)
			return NULL;
		if (result < 0)
			break;
	}
	quitMainLoop = 0;

	if (errorInCmd) {
		errorInCmd = 0;
		PyErr_Restore(excInCmd, valInCmd, trbInCmd);
		excInCmd = valInCmd = trbInCmd = NULL;
		return NULL;
	}
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
Tkapp_DoOneEvent(PyObject *self, PyObject *args)
{
	int flags = 0;
	int rv;

	if (!PyArg_ParseTuple(args, "|i", &flags))
		return NULL;

	ENTER_TCL
	rv = Tcl_DoOneEvent(flags);
	LEAVE_TCL
	return Py_BuildValue("i", rv);
}

static PyObject *
Tkapp_Quit(PyObject *self, PyObject *args)
{

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	quitMainLoop = 1;
	Py_INCREF(Py_None);
	return Py_None;
}

static PyObject *
Tkapp_InterpAddr(PyObject *self, PyObject *args)
{

	if (!PyArg_ParseTuple(args, ""))
		return NULL;

	return PyInt_FromLong((long)Tkapp_Interp(self));
}

static PyObject *
Tkapp_UTF8_to_Latin1 (PyObject *self, PyObject *args)
#if TKMAJORMINOR < 8001
{
    PyObject * string;

    if (!PyArg_ParseTuple(args, "S", &string))
	return NULL;

    Py_INCREF(string);
    return string;
}
#else
{
    PyObject * utf8;
    PyObject * latin1;
    Tcl_DString dstring;
    Tcl_Encoding encoding;

    if (!PyArg_ParseTuple(args, "S", &utf8))
	return NULL;

    encoding = Tcl_GetEncoding(Tkapp_Interp(self), "iso8859-1");
    if (!encoding)
    {
	/* encoding can't be found */
	PyErr_SetString(PyExc_RuntimeError,
			"Can't find Tcl's iso8859-1 encoding");
	return NULL;
    }
    Tcl_UtfToExternalDString(encoding, PyString_AsString(utf8),
			     PyString_Size(utf8), &dstring);

    latin1 = PyString_FromString(dstring.string);

    Tcl_FreeEncoding(encoding);
    Tcl_DStringFree(&dstring);

    return latin1;
}
#endif


static PyObject *
Tkapp_UTF8_to_System (PyObject *self, PyObject *args)
#if TKMAJORMINOR < 8001
{
    PyObject * string;

    if (!PyArg_ParseTuple(args, "S", &string))
	return NULL;

    Py_INCREF(string);
    return string;
}
#else
{
    PyObject * utf8;
    PyObject * system;
    Tcl_DString dstring;

    if (!PyArg_ParseTuple(args, "S", &utf8))
	return NULL;

    Tcl_UtfToExternalDString(NULL, PyString_AsString(utf8),
			     PyString_Size(utf8), &dstring);

    system = PyString_FromString(dstring.string);

    Tcl_DStringFree(&dstring);

    return system;
}
#endif

/* Yet another sketch specific hack: Starting with Python 2.3 Tkinter
 * calls the wantobjects method, so we provide one that doesn't do
 * anything.
 */
static PyObject *
Tkapp_WantObjects(PyObject *self, PyObject *args)
{
    int wantobjects;
    if (!PyArg_ParseTuple(args, "i:wantobjects", &wantobjects))
	return NULL;
    
    Py_INCREF(Py_None);
    return Py_None;
}


/**** Tkapp Method List ****/

static PyMethodDef Tkapp_methods[] =
{
	{"call", 	       Tkapp_Call, 0},
	{"globalcall", 	       Tkapp_GlobalCall, 0},
	{"eval", 	       Tkapp_Eval, 1},
	{"globaleval", 	       Tkapp_GlobalEval, 1},
	{"evalfile", 	       Tkapp_EvalFile, 1},
	{"record", 	       Tkapp_Record, 1},
	{"adderrorinfo",       Tkapp_AddErrorInfo, 1},
	{"setvar", 	       Tkapp_SetVar, 1},
	{"globalsetvar",       Tkapp_GlobalSetVar, 1},
	{"getvar", 	       Tkapp_GetVar, 1},
	{"globalgetvar",       Tkapp_GlobalGetVar, 1},
	{"unsetvar", 	       Tkapp_UnsetVar, 1},
	{"globalunsetvar",     Tkapp_GlobalUnsetVar, 1},
	{"getint", 	       Tkapp_GetInt, 1},
	{"getdouble", 	       Tkapp_GetDouble, 1},
	{"getboolean", 	       Tkapp_GetBoolean, 1},
	{"exprstring", 	       Tkapp_ExprString, 1},
	{"exprlong", 	       Tkapp_ExprLong, 1},
	{"exprdouble", 	       Tkapp_ExprDouble, 1},
	{"exprboolean",        Tkapp_ExprBoolean, 1},
	{"splitlist", 	       Tkapp_SplitList, 1},
	{"split", 	       Tkapp_Split, 1},
	{"merge", 	       Tkapp_Merge, 0},
	{"createcommand",      Tkapp_CreateCommand, 1},
	{"deletecommand",      Tkapp_DeleteCommand, 1},
#ifdef HAVE_CREATEFILEHANDLER
	{"createfilehandler",  Tkapp_CreateFileHandler, 1},
	{"deletefilehandler",  Tkapp_DeleteFileHandler, 1},
#endif
	{"createtimerhandler", Tkapp_CreateTimerHandler, 1},
	{"mainloop", 	       Tkapp_MainLoop, 1},
	{"dooneevent", 	       Tkapp_DoOneEvent, 1},
	{"quit", 	       Tkapp_Quit, 1},
	{"interpaddr",         Tkapp_InterpAddr, 1},
	{"utf8_to_latin1",     Tkapp_UTF8_to_Latin1, 1},
	{"utf8_to_system",     Tkapp_UTF8_to_System, 1},
	{"wantobjects",	       Tkapp_WantObjects, METH_VARARGS},
	{NULL, 		       NULL}
};



/**** Tkapp Type Methods ****/

static void
Tkapp_Dealloc(PyObject *self)
{
	ENTER_TCL
	Tcl_DeleteInterp(Tkapp_Interp(self));
	LEAVE_TCL
	PyMem_DEL(self);
	DisableEventHook();
}

static PyObject *
Tkapp_GetAttr(PyObject *self, char *name)
{
	return Py_FindMethod(Tkapp_methods, self, name);
}

static PyTypeObject Tkapp_Type =
{
	PyObject_HEAD_INIT(NULL)
	0,				     /*ob_size */
	"tkapp",			     /*tp_name */
	sizeof(TkappObject),		     /*tp_basicsize */
	0,				     /*tp_itemsize */
	Tkapp_Dealloc,			     /*tp_dealloc */
	0,				     /*tp_print */
	Tkapp_GetAttr,			     /*tp_getattr */
	0,				     /*tp_setattr */
	0,				     /*tp_compare */
	0,				     /*tp_repr */
	0,				     /*tp_as_number */
	0,				     /*tp_as_sequence */
	0,				     /*tp_as_mapping */
	0,				     /*tp_hash */
};



/**** Tkinter Module ****/

static PyObject *
Tkinter_Create(PyObject *self, PyObject *args)
{
	char *screenName = NULL;
	char *baseName = NULL;
	char *className = NULL;
	int interactive = 0;

	int ignored_int = 0;
	char *ignored_charp = NULL;

	baseName = strrchr(Py_GetProgramName(), '/');
	if (baseName != NULL)
		baseName++;
	else
		baseName = Py_GetProgramName();
	className = "Tk";
  
	if (!PyArg_ParseTuple(args, "|zssiiiiz:create",
			      &screenName, &baseName, &className,
			      &interactive, &ignored_int, &ignored_int,
			      &ignored_int, &ignored_charp))
		return NULL;

	return (PyObject *) Tkapp_New(screenName, baseName, className, 
				      interactive);
}

static PyMethodDef moduleMethods[] =
{
	{"create",             Tkinter_Create, 1},
#ifdef HAVE_CREATEFILEHANDLER
	{"createfilehandler",  Tkapp_CreateFileHandler, 1},
	{"deletefilehandler",  Tkapp_DeleteFileHandler, 1},
#endif
	{"createtimerhandler", Tkapp_CreateTimerHandler, 1},
	{"mainloop",           Tkapp_MainLoop, 1},
	{"dooneevent",         Tkapp_DoOneEvent, 1},
	{"quit",               Tkapp_Quit, 1},
	{NULL,                 NULL}
};

#ifdef WAIT_FOR_STDIN

static int stdin_ready = 0;

#ifndef MS_WINDOWS
static void
MyFileProc(void *clientData, int mask)
{
	stdin_ready = 1;
}
#endif

#if defined(WITH_THREAD) || defined(PAX_THREAD_HACK)
static PyThreadState *event_tstate = NULL;
#endif

static int
EventHook(void)
{
#ifndef MS_WINDOWS
	FHANDLE tfile;
#endif
#if defined(WITH_THREAD) || defined(PAX_THREAD_HACK)
	PyEval_RestoreThread(event_tstate);
#endif
	stdin_ready = 0;
	errorInCmd = 0;
#ifndef MS_WINDOWS
	tfile = MAKEFHANDLE(fileno(stdin));
	Tcl_CreateFileHandler(tfile, TCL_READABLE, MyFileProc, NULL);
#endif
	while (!errorInCmd && !stdin_ready) {
		int result;
#ifdef MS_WINDOWS
		if (_kbhit()) {
			stdin_ready = 1;
			break;
		}
#endif
#if defined(WITH_THREAD) || defined(MS_WINDOWS)
		Py_BEGIN_ALLOW_THREADS
		PyThread_acquire_lock(tcl_lock, 1);
		tcl_tstate = event_tstate;

		result = Tcl_DoOneEvent(TCL_DONT_WAIT);

		tcl_tstate = NULL;
		PyThread_release_lock(tcl_lock);
		if (result == 0)
			Sleep(20);
		Py_END_ALLOW_THREADS
#else
		result = Tcl_DoOneEvent(0);
#endif

		if (result < 0)
			break;
	}
#ifndef MS_WINDOWS
	Tcl_DeleteFileHandler(tfile);
#endif
	if (errorInCmd) {
		errorInCmd = 0;
		PyErr_Restore(excInCmd, valInCmd, trbInCmd);
		excInCmd = valInCmd = trbInCmd = NULL;
		PyErr_Print();
	}
#if defined(WITH_THREAD) || defined(PAX_THREAD_HACK)
	PyEval_SaveThread();
#endif
	return 0;
}

#endif

static void
EnableEventHook(void)
{
#ifdef WAIT_FOR_STDIN
	if (PyOS_InputHook == NULL) {
#if defined(WITH_THREAD) || defined(PAX_THREAD_HACK)
		event_tstate = PyThreadState_Get();
#endif
		PyOS_InputHook = EventHook;
	}
#endif
}

static void
DisableEventHook(void)
{
#ifdef WAIT_FOR_STDIN
	if (Tk_GetNumMainWindows() == 0 && PyOS_InputHook == EventHook) {
		PyOS_InputHook = NULL;
	}
#endif
}


/* all errors will be checked in one fell swoop in init_tkinter() */
static void
ins_long(PyObject *d, char *name, long val)
{
	PyObject *v = PyInt_FromLong(val);
	if (v) {
		PyDict_SetItemString(d, name, v);
		Py_DECREF(v);
	}
}
static void
ins_string(PyObject *d, char *name, char *val)
{
	PyObject *v = PyString_FromString(val);
	if (v) {
		PyDict_SetItemString(d, name, v);
		Py_DECREF(v);
	}
}


void
initpaxtkinter(void) /* function name changed for pax */
{
	PyObject *m, *d;

	Tkapp_Type.ob_type = &PyType_Type;

#ifdef WITH_THREAD
	tcl_lock = PyThread_allocate_lock();
#endif

	/* module name changed for pax */
	m = Py_InitModule("paxtkinter", moduleMethods);

	d = PyModule_GetDict(m);
	Tkinter_TclError = Py_BuildValue("s", "TclError");
	PyDict_SetItemString(d, "TclError", Tkinter_TclError);

	ins_long(d, "READABLE", TCL_READABLE);
	ins_long(d, "WRITABLE", TCL_WRITABLE);
	ins_long(d, "EXCEPTION", TCL_EXCEPTION);
	ins_long(d, "WINDOW_EVENTS", TCL_WINDOW_EVENTS);
	ins_long(d, "FILE_EVENTS", TCL_FILE_EVENTS);
	ins_long(d, "TIMER_EVENTS", TCL_TIMER_EVENTS);
	ins_long(d, "IDLE_EVENTS", TCL_IDLE_EVENTS);
	ins_long(d, "ALL_EVENTS", TCL_ALL_EVENTS);
	ins_long(d, "DONT_WAIT", TCL_DONT_WAIT);
	ins_string(d, "TK_VERSION", TK_VERSION);
	ins_string(d, "TCL_VERSION", TCL_VERSION);

	PyDict_SetItemString(d, "TkappType", (PyObject *)&Tkapp_Type);

	Tktt_Type.ob_type = &PyType_Type;
	PyDict_SetItemString(d, "TkttType", (PyObject *)&Tktt_Type);

	/* This helps the dynamic loader; in Unicode aware Tcl versions
	   it also helps Tcl find its encodings. */
	Tcl_FindExecutable(Py_GetProgramName());

	if (PyErr_Occurred())
		return;

#if 0
	/* This was not a good idea; through <Destroy> bindings,
	   Tcl_Finalize() may invoke Python code but at that point the
	   interpreter and thread state have already been destroyed! */
#if TKMAJORMINOR >= 8000
	Py_AtExit(Tcl_Finalize);
#endif
#endif

#ifdef macintosh
	/*
	** Part of this code is stolen from MacintoshInit in tkMacAppInit.
	** Most of the initializations in that routine (toolbox init calls and
	** such) have already been done for us, so we only need these.
	*/
#if TKMAJORMINOR >= 8000
	tcl_macQdPtr = &qd;
#endif

	Tcl_MacSetEventProc(PyMacConvertEvent);
#if GENERATINGCFM
	mac_addlibresources();
#endif /* GENERATINGCFM */
#endif /* macintosh */
}



#ifdef macintosh

/*
** Anyone who embeds Tcl/Tk on the Mac must define panic().
*/

void
panic(char * format, ...)
{
	va_list varg;
	
	va_start(varg, format);
	
	vfprintf(stderr, format, varg);
	(void) fflush(stderr);
	
	va_end(varg);

	Py_FatalError("Tcl/Tk panic");
}

/*
** Pass events to SIOUX before passing them to Tk.
*/

static int
PyMacConvertEvent(EventRecord *eventPtr)
{
	WindowPtr frontwin;
	/*
	** Sioux eats too many events, so we don't pass it everything.  We
	** always pass update events to Sioux, and we only pass other events if
	** the Sioux window is frontmost. This means that Tk menus don't work
	** in that case, but at least we can scroll the sioux window.
	** Note that the SIOUXIsAppWindow() routine we use here is not really
	** part of the external interface of Sioux...
	*/
	frontwin = FrontWindow();
	if ( eventPtr->what == updateEvt || SIOUXIsAppWindow(frontwin) ) {
		if (SIOUXHandleOneEvent(eventPtr))
			return 0; /* Nothing happened to the Tcl event queue */
	}
	return TkMacConvertEvent(eventPtr);
}

#if defined(USE_GUSI) && TKMAJORMINOR < 8000
/*
 * For Python we have to override this routine (from TclMacNotify),
 * since we use GUSI for our sockets, not Tcl streams. Hence, we have
 * to use GUSI select to see whether our socket is ready. Note that
 * createfilehandler (above) sets the type to TCL_UNIX_FD for our
 * files and sockets.
 *
 * NOTE: this code was lifted from Tcl 7.6, it may need to be modified
 * for other versions.  */

int
Tcl_FileReady(Tcl_File file, /* File handle for a stream. */
	      int mask)      /* OR'ed combination of TCL_READABLE,
			      * TCL_WRITABLE, and TCL_EXCEPTION,
			      * indicates conditions caller cares about. */
{
    int type;
    int fd;

    fd = (int) Tcl_GetFileInfo(file, &type);

    if (type == TCL_MAC_SOCKET) {
	return TclMacSocketReady(file, mask);
    } else if (type == TCL_MAC_FILE) {
	/*
	 * Under the Macintosh, files are always ready, so we just 
	 * return the mask that was passed in.
	 */

	return mask;
    } else if (type == TCL_UNIX_FD) {
	fd_set readset, writeset, excset;
	struct timeval tv;
	
	FD_ZERO(&readset);
	FD_ZERO(&writeset);
	FD_ZERO(&excset);
	
	if ( mask & TCL_READABLE ) FD_SET(fd, &readset);
	if ( mask & TCL_WRITABLE ) FD_SET(fd, &writeset);
	if ( mask & TCL_EXCEPTION ) FD_SET(fd, &excset);
	
	tv.tv_sec = tv.tv_usec = 0;
	if ( select(fd+1, &readset, &writeset, &excset, &tv) <= 0 )
		return 0;
	
	mask = 0;
	if ( FD_ISSET(fd, &readset) ) mask |= TCL_READABLE;
	if ( FD_ISSET(fd, &writeset) ) mask |= TCL_WRITABLE;
	if ( FD_ISSET(fd, &excset) ) mask |= TCL_EXCEPTION;

	return mask;
    }
    
    return 0;
}
#endif /* USE_GUSI */

#if GENERATINGCFM

/*
** Additional Mac specific code for dealing with shared libraries.
*/

#include <Resources.h>
#include <CodeFragments.h>

static int loaded_from_shlib = 0;
static FSSpec library_fss;

/*
** If this module is dynamically loaded the following routine should
** be the init routine. It takes care of adding the shared library to
** the resource-file chain, so that the tk routines can find their
** resources.
*/
OSErr pascal
init_tkinter_shlib(CFragInitBlockPtr data)
{
	__initialize();
	if ( data == nil ) return noErr;
	if ( data->fragLocator.where == kDataForkCFragLocator ) {
		library_fss = *data->fragLocator.u.onDisk.fileSpec;
		loaded_from_shlib = 1;
	} else if ( data->fragLocator.where == kResourceCFragLocator ) {
		library_fss = *data->fragLocator.u.inSegs.fileSpec;
		loaded_from_shlib = 1;
	}
	return noErr;
}

/*
** Insert the library resources into the search path. Put them after
** the resources from the application. Again, we ignore errors.
*/
static
mac_addlibresources()
{
	if ( !loaded_from_shlib ) 
		return;
	(void)FSpOpenResFile(&library_fss, fsRdPerm);
}

#endif /* GENERATINGCFM */
#endif /* macintosh */
