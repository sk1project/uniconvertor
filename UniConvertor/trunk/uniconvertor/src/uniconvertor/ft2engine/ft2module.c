/*
(c) 2007 Igor E.Novikov <igor.e.novikov@gmail.com>
http://sk1project.org

(c) 2002 Abel Deuring <a.deuring@satzbau-gmbh.de>
http://www.satzbau-gmbh.de/staff/abel/ft2/index.html

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

*/

#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_GLYPH_H

/* relations between Freetype objects and Python objects:

   The Freetype library has roughly the following class structure
   (see freetype2/docs/design/design-4.html)

   - the "core" is an instance of FT_Library
   - the FT_Library has (via FT_Module instances) one or more
     FT_Face objects.
   - An FT_Face object has an FT_Stream, an FT_CharMap,
     an FT_GlypSlot, and an FT_Size instance.
     Moreover, FT_Glyph instances can be copied.

   If an FT_xxx instance is destroyed via the FT_xxx_Done call, its
   child objects are destroyed, except glyph objects. (But probably
   certain glyph operations require an existing face object...)

   Hence it must be ensured that no parent object is destroyed before
   its parent object. So each Python object keeps a reference to its
   parent object in order to guarantee that Python code like:

   def get_a_face(filename):
       lib = ft2.Library()
       f = open(filename)
       return ft2.Face(lib, f, 0)

   does not crash, because the FT_Library object is destroyed during
   the "return".
*/

/* TODO
   - add FT_Attach_File resp. FT_Attach_Stream
*/

/* see freetype2/freetype/fterrors.h for an explanation of the following */
#undef __FTERRORS_H__
#define FT_ERRORDEF(e, v, s) {e, s},
#define FT_ERROR_START_LIST {
#define FT_ERROR_END_LIST {0, NULL} };

const struct {
    int err_code;
    const char* err_msg;
} ft_errors[] =
#include FT_ERRORS_H

#include <Python.h>
static PyObject *ft2Error;


static PyObject* pFT_Error(FT_Error error) {
    int i = 0;
    while (error != ft_errors[i].err_code && ft_errors[i].err_msg)
        i++;
    if (ft_errors[i].err_msg)
        PyErr_SetString(ft2Error, ft_errors[i].err_msg);
    else
        PyErr_SetString(ft2Error, "unknown error");
    return NULL;
}

/* converters for basic FT types */

#ifdef COMPILE_UNUSED
static PyObject* FT_Byte_conv(FT_Byte *fbyte) {
    return PyInt_FromLong(*fbyte);
}

static PyObject* FT_Char_conv(FT_Char *fchar) {
    char r[2];
    r[0] = *fchar;
    r[1] = 0;
    return PyString_FromString(r);
}
#endif

static PyObject* FT_Int_conv(FT_Int *i) {
    return PyInt_FromLong(*i);
}

#ifdef COMPILE_UNUSED
static PyObject* FT_UInt_conv(FT_UInt *i) {
    return PyInt_FromLong(*i);
}
#endif

static PyObject *FT_Short_conv(FT_Short *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_UShort_conv(FT_UShort *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_Long_conv(FT_Long *i) {
    return PyInt_FromLong(*i);
}

#ifdef COMPILE_UNUSED
static PyObject *FT_ULong_conv(FT_ULong *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_Bool_conv(FT_Bool *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_Offset_conv(FT_Offset *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_PtrDist_conv(FT_PtrDist *i) {
    return PyInt_FromLong(*i);
}
#endif

/* "typedef char FT_String": We assume that FT_String* is used
   everywhere
*/
static PyObject *FT_String_conv(FT_String **s) {
    return PyString_FromString(*s);
}

#ifdef COMPILE_UNUSED
static PyObject *FT_Fixed_conv(FT_Fixed *i) {
    return PyInt_FromLong(*i);
}

/* FT_Pointer conversion is pointless for Python ;) */

/* FT_Pos may be a "plain" integer or a 26.6 number... */
static PyObject *FT_Pos_conv(FT_Pos *i) {
    return PyInt_FromLong(*i);
}
#endif

static PyObject *FT_Vector_conv(FT_Vector *v) {
    return Py_BuildValue("ll", v->x, v->y);
}

static PyObject *FT_BBox_conv(FT_BBox *b) {
    return Py_BuildValue("llll", b->xMin, b->yMin, b->xMax, b->yMax);
}

#ifdef COMPILE_UNUSED
static PyObject *FT_Matrix_conv(FT_Matrix *m) {
    return Py_BuildValue("llll", m->xx, m->xy, m->yx, m->yy);
}

static PyObject *FT_FWord_conv(FT_FWord *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_UFWord_conv(FT_UFWord *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_F2Dot14_conv(FT_F2Dot14 *i) {
    return PyInt_FromLong(*i);
}

static PyObject *FT_UnitVector_conv(FT_UnitVector *v) {
    return Py_BuildValue("hh", v->x, v->y);
}

static PyObject *FT_Bitmap_Size_conv(FT_Bitmap_Size *v) {
    return Py_BuildValue("hh", v->width, v->height);
}
#endif

static PyObject *int_conv(int *i) {
    return PyInt_FromLong(*i);
}

static PyObject *short_conv(short *i) {
    return PyInt_FromLong(*i);
}

static PyObject *char_as_int_conv(char *i) {
    return PyInt_FromLong(*i);
}


/*-------------------------------------------------------*/
/* we need to access a few dozen attributes of FT objects
   from Python, i.e., via an attribute name, so we use
   hashes to find the proper converter function

   Since we are in the comfortable position to know which
   values to hash at program start, we need to check only
   there for duplicates. And we can use a small hash table.

   This implementation is stolen from freetype's bdflib.c
*/

#define HASHTABLESIZE 512
#define HASHMASK 511

static unsigned short  strhash(const char *s) {
    const char *p = s;
    unsigned short res = 0;
    while (*p) {
        res = (res << 5) - res + *p++;
    }
    return res & HASHMASK;
}

typedef PyObject* PyObP;
typedef PyObP (*ConverterFunction)(void*);

typedef struct {
    ConverterFunction conv;
    size_t offset;
} hashEntry;

#define STRINGIFY(x) #x

#define ACCESSOR(hArray, ftStruct, ftField, convFunc) 		\
    { ftStruct s; 						\
      size_t offs = (char*) &s.ftField - (char*) &s; 		\
      unsigned short index = strhash(STRINGIFY(ftField));	\
      if (hArray[index].conv != NULL) { 			\
        fprintf(stderr, "hash value %i used twice\n", index);	\
        assert(hArray[index].conv == NULL); 			\
      }								\
      hArray[index].conv = (ConverterFunction) convFunc;	\
      hArray[index].offset = offs;				\
    }

typedef struct {
    PyObject *pyVal;
    ConverterFunction f;
} conversionResult;

/* return:
   res.f == NULL -> attribute not found
               Python error must be set by caller
   res.f != NULL -> converter found;
               Either res.pyVal contains a valid PyObject pointer,
               or a valid Python error has been set by the converter

*/

#ifdef __WINDOWS__
static void convert(hashEntry* hTable, const char* attr, char* recPtr,
                    conversionResult *res) {
    short index = strhash(attr);
    if ((res->f = hTable[index].conv) == NULL)
        return;

    res->pyVal = (*(res->f))(recPtr + hTable[index].offset);
    return;
}
#endif

#ifndef __WINDOWS__
static void convert(hashEntry* hTable, const char* attr, void* recPtr,
                    conversionResult *res) {
    short index = strhash(attr);
    if ((res->f = hTable[index].conv) == NULL)
        return;

    res->pyVal = (*(res->f))(recPtr + hTable[index].offset);
    return;
}
#endif

/*-------------------------------------------------------*/

staticforward PyTypeObject pFT_Library_Type;

typedef struct {
    PyObject_HEAD
    FT_Library lib;
} pFT_Library;

static PyObject* pFT_Library_new(PyObject* self, PyObject* args) {
    FT_Error err;
    pFT_Library *lib;
    FT_Library clib;

    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    err = FT_Init_FreeType(&clib);
    if (err)
        return pFT_Error(err);

    lib = PyObject_New(pFT_Library, &pFT_Library_Type);

    if (!lib) {
        FT_Done_FreeType(clib);
        return NULL;
    }

    lib->lib = clib;

    return (PyObject*) lib;
}

static void pFT_Library_del(pFT_Library* self) {
    FT_Error err;

    err = FT_Done_FreeType(self->lib);

    /* xxx how can we return an error from the destructor ???
    if (err)
        return pFT_Error(err);
    */

    PyObject_Del(self);
}

static PyMethodDef pFT_LibraryMethods[] = {
#if 0
    {"version", (PyCFunction) pFT_Library_version, METH_VARARGS,
     "version() --"
     "return the Freetype version. Return value is the tuple "
     "(major, minor, patchlevel)"
    },
#endif
    {NULL, NULL}
};

static PyObject* pFT_Library_getattr(pFT_Library* self, char* name) {
    return Py_FindMethod(pFT_LibraryMethods, (PyObject*) self, name);
}

static PyTypeObject pFT_Library_Type = {
    PyObject_HEAD_INIT(NULL)
    0,
    "Library",
    sizeof(pFT_Library),
    0,
    (destructor) pFT_Library_del, 	/* tp_dealloc */
    0, 					/* tp_print */
    (getattrfunc) pFT_Library_getattr,	/* tp_getattr */
    0,				/* tp_setattr */
    0,				/* tp_compare */
    0,				/* tp_repr */
    0,				/* tp_as_number */
    0,				/* tp_as_sequence */
    0,				/* tp_as_mapping */
    0, 				/* tp_hash */
};


/* -------------------------------------------------------------- */
staticforward PyTypeObject pFT_CharMap_Type;

typedef struct pFT_Face* pFT_Face_P;

typedef struct {
    PyObject_HEAD
    FT_CharMap charmap;
    pFT_Face_P face;
} pFT_CharMap;

staticforward PyTypeObject pFT_Face_Type;

typedef struct {
    PyObject_HEAD
    FT_Face face;
    pFT_Library *library;
    FT_Open_Args openargs;
    FT_StreamRec fStream;
    FT_Open_Args attachedOpenargs;
    FT_StreamRec attachedFStream;
} pFT_Face;

static unsigned long readfunction(FT_Stream stream,
                                  unsigned long offset,
                                  unsigned char *buffer,
                                  unsigned long count) {
    PyObject *pFile = (PyObject*) stream->descriptor.pointer;
    PyObject *pResult;
    unsigned long size;
    char *pBuffer;

    pResult = PyObject_CallMethod(pFile, "seek", "ii", offset, 0);
    if (pResult == 0)
        // xxx is there a "real" way to return an error?
        return 0;
    Py_DECREF(pResult);
    pResult = PyObject_CallMethod(pFile, "read", "i", count);

    if (pResult == 0)
        return 0;

    size = PyString_Size(pResult);
    pBuffer = PyString_AsString(pResult);

    memcpy(buffer, pBuffer, size);

    Py_DECREF(pResult);
    return size;
}

static PyObject *init_stream(PyObject *pStream, FT_StreamRec *fStream,
                             FT_Open_Args *openargs) {
    PyObject *pResult;
    FT_ULong streamsize;

    memset(fStream, 0, sizeof(FT_StreamRec));

    pResult = PyObject_CallMethod(pStream, "seek", "ii", 0, 2);
    if (pResult == NULL) {
      return NULL;
    }
    Py_DECREF(pResult);

    pResult = PyObject_CallMethod(pStream, "tell", "");
    if (pResult == NULL) {
      return NULL;
    }
    streamsize = PyInt_AsLong(pResult);
    Py_DECREF(pResult);

    pResult = PyObject_CallMethod(pStream, "seek", "ii", 0, 0);
    if (pResult == NULL)
        return NULL;
    Py_DECREF(pResult);

    fStream->read = readfunction;
    fStream->descriptor.pointer = pStream;
    Py_INCREF(pStream);
    fStream->size = streamsize;
    fStream->pos = 0;

    memset(openargs, 0, sizeof(FT_Open_Args));
    openargs->flags = FT_OPEN_STREAM;
    openargs->stream = fStream;

    return pResult;
}

/* Face(library, stream, index) */
static PyObject* pFT_Face_new(PyObject* self, PyObject* args) {
    FT_Error err;
    pFT_Face *pFace;
    FT_Face face;
    pFT_Library *pLibrary;
    PyObject *pStream;
    FT_Long index;


    if (!PyArg_ParseTuple(args, "O!Ol", &pFT_Library_Type, &pLibrary,
                          &pStream, &index))
        return NULL;

    pFace = PyObject_New(pFT_Face, &pFT_Face_Type);
    if (!pFace) {
        return NULL;
    }
    pFace->face = NULL;
    pFace->library = pLibrary;
    pFace->fStream.descriptor.pointer = NULL;
    pFace->attachedFStream.descriptor.pointer = NULL;
    Py_INCREF(pLibrary);
    if (NULL == init_stream(pStream, &pFace->fStream, &pFace->openargs)) {
        Py_DECREF(pFace);
        return NULL;
    }

    err = FT_Open_Face(pLibrary->lib, &pFace->openargs, index, &face);
    if (err)  {
        Py_DECREF(pFace);
        return pFT_Error(err);
    }

    pFace->face = face;

    return (PyObject*) pFace;
}

static void pFT_Face_del(pFT_Face* self) {
    if (self->face)
        FT_Done_Face(self->face);
    Py_DECREF(self->library);
    Py_XDECREF((PyObject*) self->fStream.descriptor.pointer);
    Py_XDECREF((PyObject*) self->attachedFStream.descriptor.pointer);
    PyObject_Del(self);
}

static PyObject *pFT_SetCharSize(pFT_Face *self, PyObject *args) {
    FT_F26Dot6 w, h;
    FT_UInt hr, vr;
    FT_Error error;
    if (!PyArg_ParseTuple(args, "iiii", &w, &h, &hr, &vr))
        return NULL;

    error = FT_Set_Char_Size(self->face, w, h, hr, vr);
    if (error)
        return pFT_Error(error);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *pFT_SetPixelSizes(pFT_Face *self, PyObject *args) {
    FT_UInt w, h;
    FT_Error error;
    if (!PyArg_ParseTuple(args, "ii", &w, &h))
        return NULL;

    error = FT_Set_Pixel_Sizes(self->face, w, h);
    if (error)
        return pFT_Error(error);

    Py_INCREF(Py_None);
    return Py_None;
}

/* setTransform(self, (xx, xy, yx, yy), (dx, dy))
   the first sequence is converted into an FT_Matrix,
   the second sequence into an FT_Vector
*/
static PyObject *pFT_SetTransform(pFT_Face *self, PyObject *args) {
    FT_Matrix matrix;
    FT_Vector vector;

    if (!PyArg_ParseTuple(args, "(iiii)(ii)",
         &matrix.xx, &matrix.xy, &matrix.yx, &matrix.yy,
         &vector.x, &vector.y)) {
        return NULL;
    }

    FT_Set_Transform(self->face, &matrix, &vector);

    Py_INCREF(Py_None);
    return Py_None;
}

/* getKerning(self, left, right, mode) */
static PyObject *pFT_GetKerning(pFT_Face *self, PyObject *args) {
    FT_UInt left, right, mode;
    FT_Error err;
    FT_Vector kerning;

    if (!PyArg_ParseTuple(args, "iii", &left, &right, &mode))
        return NULL;

    err = FT_Get_Kerning(self->face, left, right, mode, &kerning);
    if (err)
        return pFT_Error(err);

    return Py_BuildValue("(i,i)", kerning.x, kerning.y);
}

#ifndef FT_CONFIG_OPTION_NO_GLYPH_NAMES
/* getGlyphName(self, index) */
static PyObject *pFT_GetGlyphName(pFT_Face *self, PyObject *args) {
    FT_Error err;
    FT_UInt index;
    char name[100];

    if (!PyArg_ParseTuple(args, "i", &index))
        return NULL;

    err = FT_Get_Glyph_Name(self->face, index, name, 100);
    if (err)
        return pFT_Error(err);

    return Py_BuildValue("s", name);
}
#endif

/* getPostsriptName(self) */
static PyObject *pFT_GetPostscriptName(pFT_Face *self, PyObject *args) {
    if (!PyArg_ParseTuple(args, ""))
        return NULL;
    return Py_BuildValue("s", FT_Get_Postscript_Name(self->face));
}

/* getCharIndex(self, charcode) */
static PyObject *pFT_GetCharIndex(pFT_Face *self, PyObject *args) {
    FT_ULong index;
    FT_UInt glyphIndex;

    if (!PyArg_ParseTuple(args, "i", &index))
        return NULL;

    glyphIndex = FT_Get_Char_Index(self->face, index);
    if (!glyphIndex) {
        PyErr_SetString(ft2Error, "undefined character code");
        return NULL;
    }
    return Py_BuildValue("i", glyphIndex);

}

/* return a Python dict containing the mapping charCode -> glyphIndex */
/* xxx should we move this method to the charmap class ???
   would look reasonable. OTOH, we need to access methods from FT_Face in
   order to get the mapping.
*/
static PyObject *pFT_encodingVector(pFT_Face *self, PyObject* args) {
    PyObject *res, *pCharcode, *pGlyphIndex;
    FT_ULong charcode;
    FT_UInt glyphindex;

    if (!PyArg_ParseTuple(args, ""))
        return NULL;

    res = PyDict_New();
    if (res == NULL)
        return res;

    charcode = FT_Get_First_Char(self->face, &glyphindex);

    while(glyphindex) {
        if (NULL == (pCharcode = PyInt_FromLong(charcode))) {
            Py_DECREF(res);
            return NULL;
        }
        if (NULL == (pGlyphIndex = PyInt_FromLong(glyphindex))) {
            Py_DECREF(pCharcode);
            Py_DECREF(res);
            return NULL;
        }
        if (PyDict_SetItem(res, pCharcode, pGlyphIndex)) {
            Py_DECREF(res);
            Py_DECREF(pCharcode);
            Py_DECREF(pGlyphIndex);
            return NULL;
        }

        Py_DECREF(pCharcode);
        Py_DECREF(pGlyphIndex);

        charcode = FT_Get_Next_Char(self->face, charcode, &glyphindex);
    }

    return res;
}

static PyObject *pFT_setCharMap(pFT_Face *self, PyObject *args) {
    pFT_CharMap *charmap;
    FT_Error err;

    if (!PyArg_ParseTuple(args, "O!", &pFT_CharMap_Type, &charmap))
        return NULL;

    if ((pFT_Face*)charmap->face != self) {
        /* xxx we could avoid this error by replacing this method
           with something like "Charmap.selectThis()"
        */
        PyErr_SetString(ft2Error, "Charmap object does no refer to Face object");
        return NULL;
    }

    err = FT_Set_Charmap(self->face, charmap->charmap);
    if (err)
        return pFT_Error(err);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *pFT_get_Name_Index(pFT_Face *self, PyObject *args) {
    FT_String *name;

    if (!PyArg_ParseTuple(args, "s", &name))
        return NULL;

    return PyInt_FromLong(FT_Get_Name_Index(self->face, name));
}

static PyObject *pFT_Attach_Stream(pFT_Face *self, PyObject *args) {
    PyObject *pStream;
    FT_Error err;

    if (!PyArg_ParseTuple(args, "O", &pStream)) {
        return NULL;
    }

    if (NULL == init_stream(pStream, &self->attachedFStream,
                            &self->attachedOpenargs)) {
        return NULL;
    }

    err = FT_Attach_Stream(self->face, &self->attachedOpenargs);
    if (err)  {
        return pFT_Error(err);
    }

    Py_INCREF(Py_None);
    return Py_None;

}

static PyObject* pFT_GetMetrics(pFT_Face *self, PyObject *args) {
    if (!PyArg_ParseTuple(args, "")) {
        return NULL;
    }
    return Py_BuildValue("iiiiiiii",
             (int) self->face->size->metrics.x_ppem,
             (int) self->face->size->metrics.y_ppem,
             (int) self->face->size->metrics.x_scale,
             (int) self->face->size->metrics.y_scale,
             (int) self->face->size->metrics.ascender,
             (int) self->face->size->metrics.descender,
             (int) self->face->size->metrics.height,
             (int) self->face->size->metrics.max_advance);
}

/* xxx not implemented:
   FT_Load_Char -- let's base for now everything on glyphs
                   In the future, the Glyph() constructor may get
                   another parameter which allows to create a Glyph object
                   using both a char code and a glyph index.
   FT_Render_Glyph -- we use FT_Glyph_To_Bitmap in the Glyph class
   FT_Select_Charmap -- FT_Set_Charmap should be enough
   FT_Get_Name_Index -- not so important ...

   implemented elsewhere:
   FT_Load_Glyph is used in the Python Glyph object constructor
*/

static PyMethodDef pFT_FaceMethods[] = {
    {"setCharSize", (PyCFunction) pFT_SetCharSize, METH_VARARGS,
     "setCharSize(self, width, height, hres, vres) -- "
     "set the character dimensions. Values must be integer "
     "see FT_Set_Char_Size for details "
     "xxx allow float too "
     "return: None"
    },
    {"setPixelSizes", (PyCFunction) pFT_SetPixelSizes, METH_VARARGS,
     "setPixelSizes(self, pixel_width, pixel_height) -- "
     "set the character dimension. Values must be integer "
     "see FT_Set_Pixel_Sizes for details "
     "return: None"
    },
    {"setTransform", (PyCFunction) pFT_SetTransform, METH_VARARGS,
     "setTransform(self, (xx, xy, yx, yy), (dx, dy)) -- "
     "define the coordinate transformation for the face. "
     "xx, xy, yx, yy must be integers representing 16.16 floats; "
     "dx, dy must be integers representing FT_Pos values. "
     "these are either integers or 26.6 floats... xxx what is used here?? "
     "see FT_Set_Transform for details "
     "return: None"
    },
    {"getKerning", (PyCFunction) pFT_GetKerning, METH_VARARGS,
     "getKerning(self, left, right, mode) -- "
     "return the kerning vector for the glyph pair with indexes "
     "left, right. "
     "return: (kerning_x, kerning_y) "
    },
    {"getGlyphName", (PyCFunction) pFT_GetGlyphName, METH_VARARGS,
     "getGlyphName(self, index) -- "
     "return the glyph name "
    },
    {"getPostscriptName", (PyCFunction) pFT_GetPostscriptName, METH_VARARGS,
     "getPostscriptName(self) -- "
     "return the Postscript name of the font "
    },
    {"getCharIndex", (PyCFunction) pFT_GetCharIndex, METH_VARARGS,
     "getCharIndex(self, i) -- "
     "return the glyph index for character code i"
    },
    {"encodingVector", (PyCFunction) pFT_encodingVector, METH_VARARGS,
     "encodingVector(self) -- "
     "return the encoding vector as a Python dict for the selected charmap"
    },
    {"setCharMap", (PyCFunction) pFT_setCharMap, METH_VARARGS,
     "setCharMap(self, charmap) -- "
     "set the charmap. charmap must be of type CharMap and must have been "
     "created for this face object."
    },
    {"getNameIndex", (PyCFunction) pFT_get_Name_Index, METH_VARARGS,
    "getNameIndex(self, glyphName) -- "
    "return the glyph index of the glyph with the name glyphName or 0, "
    "if a glyph of this name does not exist in this face. "
    "As the Freetype 2 reference manual states, 'This function uses "
    "driver specific objects to do the translation.' The translation "
    "does not work for every font."
    },
    {"attach", (PyCFunction) pFT_Attach_Stream, METH_VARARGS,
     "attach(stream) -- "
     "attach a streamIO object to the face. The streamIO object should "
     "provide additional font information like metrics or kerning "
     "information as for example found in AFM files."
    },
    {"getMetrics", (PyCFunction) pFT_GetMetrics, METH_VARARGS,
     "getMetrics(self) -- "
     "get the metrics of the face. The return value is the tuple"
     "(x_ppem, y_ppem, x_scale, y_scale, ascender, descender, height, "
     "max_advance) as stored in FT_Face->size->metrics."
    },
    {NULL, NULL}
};

static hashEntry hFace[HASHTABLESIZE];

static void _initFaceAttr() {
    memset(hFace, 0, sizeof(hFace));
    ACCESSOR(hFace, FT_FaceRec, num_faces, FT_Long_conv)
    ACCESSOR(hFace, FT_FaceRec, face_index, FT_Long_conv)
    ACCESSOR(hFace, FT_FaceRec, face_flags, FT_Long_conv)
    ACCESSOR(hFace, FT_FaceRec, style_flags, FT_Long_conv)
    ACCESSOR(hFace, FT_FaceRec, num_glyphs, FT_Long_conv)
    ACCESSOR(hFace, FT_FaceRec, family_name, FT_String_conv)
    ACCESSOR(hFace, FT_FaceRec, style_name, FT_String_conv)
    /* access to FT_Bitmap_SizeP is too complicated for the simple
       converter function: The pointer may be 0, and in this case
       the converter function should return an AttributeError,
       and in order to do that, it needs the attribute name. Since
       this would be so far the only attribute with this requirement,
       we simply do not convert available_sizes here ;)
      ACCESSOR(hFace, FT_FaceRec, num_fixed_sizes, FT_Int_conv)
      ACCESSOR(hFace, FT_FaceRec, available_sizes, FT_Bitmap_SizeP_conv)
    */
    ACCESSOR(hFace, FT_FaceRec, num_charmaps, FT_Int_conv)
    ACCESSOR(hFace, FT_FaceRec, bbox, FT_BBox_conv)
    ACCESSOR(hFace, FT_FaceRec, units_per_EM, FT_UShort_conv)
    ACCESSOR(hFace, FT_FaceRec, ascender, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, descender, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, height, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, max_advance_width, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, max_advance_height, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, underline_position, FT_Short_conv)
    ACCESSOR(hFace, FT_FaceRec, underline_thickness, FT_Short_conv)
    /* xxx FT_Size_conv missing
    ACCESSOR(hFace, FT_FaceRec, size, FT_Size_conv)
    */


}

static PyObject* pFT_Face_getattr(pFT_Face* self, char* name) {
    conversionResult res;
    convert(hFace, name, self->face, &res);
    if (res.f)
        return res.pyVal;

    if (0 == strcmp(name, "available_sizes")) {
        /* return the avaiable sizes as a Python tuple */
        int i, imax = self->face->num_fixed_sizes;
        PyObject *sizes = PyTuple_New(imax);
        if (!sizes)
            return NULL;
        for (i = 0; i < imax; i++) {
            PyObject *n, *s = PyTuple_New(2);
            if (!s) {
                Py_DECREF(sizes);
                return NULL;
            }
            if (PyTuple_SetItem(sizes, i, s))
                goto error;
            if (NULL == (n = PyInt_FromLong(self->face->available_sizes[i].width)))
                goto error;
            if (PyTuple_SetItem(s, 0, n))
                goto error;
            if (NULL == (n = PyInt_FromLong(self->face->available_sizes[i].height)))
                goto error;
            if (PyTuple_SetItem(s, 1, n))
                goto error;
            continue;
            error:
                Py_DECREF(sizes);
                return NULL;
        }
        return sizes;
    }

    return Py_FindMethod(pFT_FaceMethods, (PyObject*) self, name);
}

static PyTypeObject pFT_Face_Type = {
    PyObject_HEAD_INIT(NULL)
    0,
    "Face",
    sizeof(pFT_Face),
    0,
    (destructor) pFT_Face_del, 		/* tp_dealloc */
    0,	 				/* tp_print */
    (getattrfunc) pFT_Face_getattr,	/* tp_getattr */
    0,				/* tp_setattr */
    0,				/* tp_compare */
    0,				/* tp_repr */
    0,				/* tp_as_number */
    0,				/* tp_as_sequence */
    0,				/* tp_as_mapping */
    0, 				/* tp_hash */
};

/*---------------------------------------------------------------*/

/* CharMap(f, i) -- return the charmap with index i of Face f)
   or none, if the index is out of range
*/
static PyObject* pFT_CharMap_new(PyObject *self, PyObject *args) {
    pFT_Face *face;
    pFT_CharMap *cm;
    FT_Int index;

    if (!PyArg_ParseTuple(args, "O!i", &pFT_Face_Type, &face, &index))
        return NULL;

    if (index >= face->face->num_charmaps || index < 0) {
        PyErr_SetString(ft2Error, "charmap index out pf range");
        return NULL;
    }

    cm = PyObject_New(pFT_CharMap, &pFT_CharMap_Type);
    if (cm == NULL)
        return NULL;

    cm->charmap = face->face->charmaps[index];
    Py_INCREF(face);
    cm->face = (pFT_Face_P) face;

    return (PyObject*) cm;
}

static void pFT_CharMap_del(pFT_CharMap* self) {
    Py_DECREF((pFT_Face*) self->face);
    PyObject_Del(self);
}

static hashEntry hCharMap[HASHTABLESIZE];

static void _initCharMapAttr() {
    memset(hCharMap, 0, sizeof(hCharMap));
    ACCESSOR(hCharMap, FT_CharMapRec, encoding, FT_Long_conv)
    ACCESSOR(hCharMap, FT_CharMapRec, platform_id, FT_UShort_conv)
    ACCESSOR(hCharMap, FT_CharMapRec, encoding_id, FT_UShort_conv)
    /* xxx add a special converter which returns the encoding as a string */
}

static PyObject* pFT_CharMap_getattr(pFT_CharMap* self, char* name) {
    conversionResult res;
    char senc[5] = "eeee";
    convert(hCharMap, name, self->charmap, &res);
    if (res.f)
        return res.pyVal;
    if (0 == strcmp(name, "encoding_as_string")) {
        senc[0] = self->charmap->encoding >> 24;
        senc[1] = self->charmap->encoding >> 16;
        senc[2] = self->charmap->encoding >> 8;
        senc[3] = self->charmap->encoding;
        return PyString_FromString(senc);
    }
    PyErr_SetString(PyExc_AttributeError, name);
    return NULL;
}

static PyTypeObject pFT_CharMap_Type = {
    PyObject_HEAD_INIT(NULL)
    0,
    "CharMap",
    sizeof(pFT_CharMap),
    0,
    (destructor) pFT_CharMap_del, 	/* tp_dealloc */
    0, 					/* tp_print */
    (getattrfunc) pFT_CharMap_getattr,	/* tp_getattr */
    0,				/* tp_setattr */
    0,				/* tp_compare */
    0,				/* tp_repr */
    0,				/* tp_as_number */
    0,				/* tp_as_sequence */
    0,				/* tp_as_mapping */
    0, 				/* tp_hash */
};


/*---------------------------------------------------------------*/
staticforward PyTypeObject pFT_Glyph_Type;

typedef struct {
    PyObject_HEAD
    FT_Glyph glyph;
    pFT_Face *face;
} pFT_Glyph;

static PyObject* pFT_Glyph_new(PyObject* self, PyObject* args) {
    FT_Error err;
    FT_UInt index;
    FT_Int32 flags;
    FT_Glyph glyph;
    pFT_Glyph *pGlyph;

    pFT_Face *pFace;

    if (!PyArg_ParseTuple(args, "O!ii", &pFT_Face_Type, &pFace,
                          &index, &flags))
        return NULL;

    err = FT_Load_Glyph(pFace->face, index, flags);
    if (err)
        return pFT_Error(err);
    err = FT_Get_Glyph(pFace->face->glyph, &glyph);
    if (err)
        return pFT_Error(err);

    pGlyph = PyObject_New(pFT_Glyph, &pFT_Glyph_Type);

    if (!pGlyph) {
        FT_Done_Glyph(glyph);
        return NULL;
    }

    pGlyph->glyph = glyph;
    glyph->format = FT_GLYPH_FORMAT_OUTLINE;
    /* although the Freetype docs state that glyph objects
       are "independent" of other Freetype obejcts, we get
       a segfault in FT_Done_glyph, if the library or the face
       object are deleted before the glyph object is deleted.

       So we'll reference the face object here
    */

    pGlyph->face = pFace;
    Py_INCREF(pFace);

    return (PyObject*) pGlyph;
}

static void pFT_Glyph_del(pFT_Glyph* self) {

    FT_Done_Glyph(self->glyph);
    Py_DECREF(self->face);
    PyObject_Del(self);
}

/* copy(self) */
static PyObject* pFT_Glyph_Copy(pFT_Glyph *self, PyObject *args) {
    FT_Error err;
    FT_Glyph newGlyph;
    pFT_Glyph *res;

    if (!PyArg_ParseTuple(args, "")) {
        return NULL;
    }

    err = FT_Glyph_Copy(self->glyph, &newGlyph);
    if (err)
        return pFT_Error(err);

    res = PyObject_New(pFT_Glyph, &pFT_Glyph_Type);
    if (!res) {
        FT_Done_Glyph(newGlyph);
        return NULL;
    }
    res->glyph = newGlyph;
    res->face = self->face;
    Py_INCREF(self->face);
    return (PyObject*) res;
}

/* transform(self, (xx, xy, yx, yy), (dx, dy)) */
static PyObject* pFT_Glyph_Transform(pFT_Glyph *self,  PyObject *args) {
    FT_Error err;
    FT_Matrix matrix;
    FT_Vector vector;

    if (!PyArg_ParseTuple(args, "(iiii)(ii)",
         &matrix.xx, &matrix.xy, &matrix.yx, &matrix.yy,
         &vector.x, &vector.y)) {
        return NULL;
    }

    err = FT_Glyph_Transform(self->glyph, &matrix, &vector);
    if (err)
        return pFT_Error(err);

    Py_INCREF(Py_None);
    return Py_None;
}

/* getCBox(self, mode) - returns (xmin, ymin, xmax, ymax) */
static PyObject * pFT_Glyph_Get_CBox(pFT_Glyph *self, PyObject *args) {
    FT_UInt bbox_mode;
    FT_BBox bbox;

    if (!PyArg_ParseTuple(args, "i", &bbox_mode)) {
        return NULL;
    }

    FT_Glyph_Get_CBox(self->glyph, bbox_mode, &bbox);
    return FT_BBox_conv(&bbox);
}


static PyMethodDef pFT_GlyphMethods[] = {
    {"copy", (PyCFunction) pFT_Glyph_Copy, METH_VARARGS,

     "copy(self) -- "
     "return a copy of this glyph object"
    },
    {"transform", (PyCFunction) pFT_Glyph_Transform, METH_VARARGS,
     "transform((xx, xy, yx, yy), (dx, dy)) -- "
     "transform the glyph image. Only possible for scalable formats "
     "xx, xy, yx, yy must be integers representing 16.16 floats; "
     "dx, dy must be integers representing FT_Pos values. "
     "these are either integers or 26.6 floats... xxx what is used here?? "
     "see FT_Set_Transform for details "
     "return: None"
    },
    {"getCBox", (PyCFunction) pFT_Glyph_Get_CBox, METH_VARARGS,
     "getCBox(self, mode) -- "
     "returns the bounding box data as (xmin, ymin, xmax, ymax) "
    },
    {NULL, NULL}
};

/* FT_Glyph has only one publicly available attribute: FT_Vector advance.
   So there is no need to set up a hash table of
   attribute names.

   While the derived classes FT_BitmapGlyph and FT_OutlineGlyph
   may have some of them, this is a bit difficult to represent
   with the current simple Python logic. Moreover, we extract a bitmap
   into it's own object type

   xxxx will this hold, if we also want to access data specific
   to certain font types (Truetype, Type 1 etc)? If so, we need
   to access the atrributes depending on the Freetype type of the glyph,
   and we'll need to setup different hash tables for each type.

*/

static PyObject* pFT_Glyph_getattr(pFT_Glyph* self, char* name) {
    if (0 == strcmp(name, "advance"))
        return FT_Vector_conv(&self->glyph->advance);

// A good place to implement outline extraction!
    if (0 == strcmp(name, "outline")){
	PyObject *contour, *p;
	int i, j, k;

	FT_OutlineGlyph glyph   = (FT_OutlineGlyph)self->glyph;
	FT_Outline *glyph_outline=&glyph->outline;
	PyObject *contours = PyTuple_New((int) (*glyph_outline).n_contours);

	for (i = j = 0; i < (int) (*glyph_outline).n_contours; i++) {
	contour = PyTuple_New((int) (*glyph_outline).contours[i] - j + 1);
		for (k = 0; j <= (int) (*glyph_outline).contours[i]; k++, j++) {
	// 	if (scaling)
	// 		p = Py_BuildValue("ffi",
	// 				(double)outline.points[j].x / 64,
	// 				(double)outline.points[j].y / 64,
	// 				outline.flags[j] & 1);
	// 	else
			p = Py_BuildValue("iii", (int)(*glyph_outline).points[j].x,
							(int)(*glyph_outline).points[j].y,
							(int)(*glyph_outline).tags[j]&1);
			PyTuple_SetItem(contour, k, p);
		}
	PyTuple_SetItem(contours, i, contour);
	}
        return contours;
	}

    return Py_FindMethod(pFT_GlyphMethods, (PyObject*) self, name);
}

static PyTypeObject pFT_Glyph_Type = {
    PyObject_HEAD_INIT(NULL)
    0,
    "Glyph",
    sizeof(pFT_Glyph),
    0,
    (destructor) pFT_Glyph_del, 	/* tp_dealloc */
    0, 					/* tp_print */
    (getattrfunc) pFT_Glyph_getattr,	/* tp_getattr */
    0,				/* tp_setattr */
    0,				/* tp_compare */
    0,				/* tp_repr */
    0,				/* tp_as_number */
    0,				/* tp_as_sequence */
    0,				/* tp_as_mapping */
    0, 				/* tp_hash */
};


/* -------------------------------------------------------------- */

staticforward PyTypeObject pFT_Bitmap_Type;

typedef struct {
    PyObject_HEAD
    FT_BitmapGlyph bitmap;
    pFT_Face *face;
} pFT_Bitmap;

/* Bitmap(glyph, mode, orig_x, orig_y) */
static PyObject* pFT_Bitmap_new(PyObject* self, PyObject* args) {
    FT_Error err;
    FT_Vector origin;
    FT_Render_Mode mode;
    FT_Glyph bitmap;

    pFT_Bitmap *res;
    pFT_Glyph *glyph;

    if (!PyArg_ParseTuple(args, "O!iii", &pFT_Glyph_Type, &glyph,
                          &mode, &origin.x, &origin.y))
        return NULL;

    err = FT_Glyph_Copy(glyph->glyph, &bitmap);
    if (err)
        return pFT_Error(err);

    err = FT_Glyph_To_Bitmap(&bitmap, mode, &origin, 1);
    if (err) {
        FT_Done_Glyph(bitmap);
        return pFT_Error(err);
    }

    res = PyObject_New(pFT_Bitmap, &pFT_Bitmap_Type);

    if (!res) {
        FT_Done_Glyph(bitmap);
        return NULL;
    }

    res->bitmap = (FT_BitmapGlyph) bitmap;
    res->face = glyph->face;
    Py_INCREF(res->face);

    return (PyObject*) res;
}

static void pFT_Bitmap_del(pFT_Bitmap* self) {

    FT_Done_Glyph((FT_Glyph) self->bitmap);
    Py_DECREF(self->face);

    PyObject_Del(self);
}

#if 0
  not needed
static PyMethodDef pFT_BitmapMethods[] = {
    {NULL, NULL}
};
#endif

static hashEntry hBitmap[HASHTABLESIZE];
static hashEntry hGlyphBitmap[HASHTABLESIZE];

static void _initBitmapAttr() {
    memset(hBitmap, 0, sizeof(hBitmap));
    /* just one publicly accessible field */
    ACCESSOR(hBitmap, FT_Bitmap, rows, int_conv)
    ACCESSOR(hBitmap, FT_Bitmap, width, int_conv)
    ACCESSOR(hBitmap, FT_Bitmap, num_grays, short_conv)
    ACCESSOR(hBitmap, FT_Bitmap, pixel_mode, char_as_int_conv)
    ACCESSOR(hBitmap, FT_Bitmap, palette_mode, char_as_int_conv)
    /* xxxxx palette access is missing */
    /* xxxxx FT_PIXEL_MODE_xxx and FT_PALETTE_MODE_xxx definitions
       are missing
    */

    memset(hGlyphBitmap, 0, sizeof(hBitmap));
    ACCESSOR(hGlyphBitmap, FT_BitmapGlyphRec, left, FT_Int_conv)
    ACCESSOR(hGlyphBitmap, FT_BitmapGlyphRec, top, FT_Int_conv)
}


static PyObject* pFT_Bitmap_getattr(pFT_Bitmap* self, char* name) {
    conversionResult res;
    FT_Bitmap bitmap;
    PyObject *pRes;
    int i, pitch, width, rows;
    char *dst, *src;

    convert(hBitmap, name, &self->bitmap->bitmap, &res);
    if (res.f)
        return res.pyVal;

    convert(hGlyphBitmap, name, self->bitmap, &res);
    if (res.f)
        return res.pyVal;

    if (0 == strcmp(name, "bitmap")) {
        bitmap = self->bitmap->bitmap;
        pRes = PyString_FromStringAndSize(NULL, bitmap.width * bitmap.rows);
        if (pRes == NULL)
            return NULL;

        dst = PyString_AsString(pRes);
        src = (char *)bitmap.buffer;
        pitch = bitmap.pitch;
        rows = bitmap.rows;
        width = bitmap.width;

        if (pitch < 0)
            src -= pitch * bitmap.rows;

        for (i = 0; i < bitmap.rows; i++) {
            memcpy(dst, src, bitmap.width);
            dst += bitmap.width;
            src += pitch;
        }

        return pRes;
    }
    PyErr_SetString(PyExc_AttributeError, name);
    return NULL;

}

static PyTypeObject pFT_Bitmap_Type = {
    PyObject_HEAD_INIT(NULL)
    0,
    "Bitmap",
    sizeof(pFT_Bitmap),
    0,
    (destructor) pFT_Bitmap_del, 	/* tp_dealloc */
    0, 					/* tp_print */
    (getattrfunc) pFT_Bitmap_getattr,	/* tp_getattr */
    0,				/* tp_setattr */
    0,				/* tp_compare */
    0,				/* tp_repr */
    0,				/* tp_as_number */
    0,				/* tp_as_sequence */
    0,				/* tp_as_mapping */
    0, 				/* tp_hash */
};


/* -------------------------------------------------------------- */


static PyMethodDef ft2_methods[] = {
    {"Library", pFT_Library_new, METH_VARARGS,
     "Library() -- Create a new FT2 library -- "
    },
    {"Face", pFT_Face_new, METH_VARARGS,
     "Face(library, file, index) -- Create a new font face object "
     "file is a stream containing the font data. "
     "The stream object must provide the methods read, seek and tell "
    },
    {"CharMap", pFT_CharMap_new, METH_VARARGS,
     "CharMap(face, i) -- create a CharMap object for face, "
     "using encoding i. This object must be used to select charmaps"
     "in face objects"
    },
    {"Glyph", pFT_Glyph_new, METH_VARARGS,
     "Glyph(face, index, options) -- "
     "Create a new Glyph object. "
    },
    {"Bitmap", pFT_Bitmap_new, METH_VARARGS,
     "Bitmap(glyph, mode, orig_x, orig_y) -- "
     "Create a new Bitmap object. "
    },
    {NULL, NULL, 0, NULL}
};


#define DEF_CONST(x) {x, #x}
static struct {
    FT_Int32 val;
    char *name;
} const_val[] = {
     DEF_CONST(FT_LOAD_NO_SCALE),
     DEF_CONST(FT_LOAD_NO_HINTING),
     DEF_CONST(FT_LOAD_RENDER),
     DEF_CONST(FT_LOAD_NO_BITMAP),
     DEF_CONST(FT_LOAD_VERTICAL_LAYOUT),
     DEF_CONST(FT_LOAD_FORCE_AUTOHINT),
     DEF_CONST(FT_LOAD_CROP_BITMAP),
     DEF_CONST(FT_LOAD_PEDANTIC),
     DEF_CONST(FT_LOAD_IGNORE_GLOBAL_ADVANCE_WIDTH),
     DEF_CONST(FT_LOAD_NO_RECURSE),
     DEF_CONST(FT_LOAD_IGNORE_TRANSFORM),
     DEF_CONST(FT_LOAD_MONOCHROME),
     DEF_CONST(FT_LOAD_LINEAR_DESIGN),

     DEF_CONST(FT_RENDER_MODE_NORMAL),
     DEF_CONST(FT_RENDER_MODE_LIGHT),
     DEF_CONST(FT_RENDER_MODE_MONO),
     DEF_CONST(FT_RENDER_MODE_LCD),
     DEF_CONST(FT_RENDER_MODE_LCD_V),

     DEF_CONST(FT_KERNING_DEFAULT),
     DEF_CONST(FT_KERNING_UNFITTED),
     DEF_CONST(FT_KERNING_UNSCALED),

     DEF_CONST(FT_ENCODING_NONE),
     DEF_CONST(FT_ENCODING_MS_SYMBOL),
     DEF_CONST(FT_ENCODING_UNICODE),
     DEF_CONST(FT_ENCODING_MS_SJIS),
     DEF_CONST(FT_ENCODING_MS_GB2312),
     DEF_CONST(FT_ENCODING_MS_BIG5),
     DEF_CONST(FT_ENCODING_MS_WANSUNG),
     DEF_CONST(FT_ENCODING_MS_JOHAB),
     DEF_CONST(FT_ENCODING_ADOBE_STANDARD),
     DEF_CONST(FT_ENCODING_ADOBE_EXPERT),
     DEF_CONST(FT_ENCODING_ADOBE_CUSTOM),
     DEF_CONST(FT_ENCODING_ADOBE_LATIN_1),
     DEF_CONST(FT_ENCODING_OLD_LATIN_2),
     DEF_CONST(FT_ENCODING_APPLE_ROMAN),

     DEF_CONST(FT_FACE_FLAG_SCALABLE),
     DEF_CONST(FT_FACE_FLAG_FIXED_SIZES),
     DEF_CONST(FT_FACE_FLAG_FIXED_WIDTH),
     DEF_CONST(FT_FACE_FLAG_SFNT),
     DEF_CONST(FT_FACE_FLAG_HORIZONTAL),
     DEF_CONST(FT_FACE_FLAG_VERTICAL),
     DEF_CONST(FT_FACE_FLAG_KERNING),
     DEF_CONST(FT_FACE_FLAG_FAST_GLYPHS),
     DEF_CONST(FT_FACE_FLAG_MULTIPLE_MASTERS),
     DEF_CONST(FT_FACE_FLAG_GLYPH_NAMES),
     DEF_CONST(FT_FACE_FLAG_EXTERNAL_STREAM),

     DEF_CONST(FT_STYLE_FLAG_ITALIC),
     DEF_CONST(FT_STYLE_FLAG_BOLD),

     DEF_CONST(ft_glyph_bbox_unscaled),
     DEF_CONST(ft_glyph_bbox_subpixels),
     DEF_CONST(ft_glyph_bbox_gridfit),
     DEF_CONST(ft_glyph_bbox_truncate),
     DEF_CONST(ft_glyph_bbox_pixels),
     {0, NULL}
};

static void init_constants(PyObject *d) {
    /* xxx the dict created here should be deallocated on module unload */
    int i = 0;
    PyObject *v;
    while (const_val[i].name) {
        v = PyInt_FromLong(const_val[i].val);
        PyDict_SetItemString(d, const_val[i].name, v);
        Py_DECREF(v);
        i++;
    }
}

DL_EXPORT(void)

initft2(void) {
    PyObject *m, *d;
    pFT_Library_Type.ob_type = &PyType_Type;
    pFT_Face_Type.ob_type = &PyType_Type;
    pFT_CharMap_Type.ob_type = &PyType_Type;
    pFT_Glyph_Type.ob_type = &PyType_Type;
    pFT_Bitmap_Type.ob_type = &PyType_Type;
    m = Py_InitModule("ft2", ft2_methods);
    d = PyModule_GetDict(m);
    ft2Error = PyErr_NewException("ft2.error", NULL, NULL);
    PyDict_SetItemString(d, "error", ft2Error);
    init_constants(d);
    _initFaceAttr();
    _initBitmapAttr();
    _initCharMapAttr();
}
