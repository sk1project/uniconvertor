/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Library General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Library General Public License for more details.
 *
 * You should have received a copy of the GNU Library General Public
 * License along with this library; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */


#include <math.h>
#include <float.h>
#include <Python.h>

#include "skpoint.h"
#include "skrect.h"
#include "sktrafo.h"
#include "skfm.h"
#include "curvefunc.h"
#include "curveobject.h"
// #include "curvedraw.h"
#include "skimage.h"
#include "skcolor.h"
#include "skaux.h"
#include "_sketchmodule.h"

// #include <pixmapobject.h>


static PyMethodDef curve_functions[] = {

    /* Point functions */
    {"Point",			SKPoint_PyPoint,		1},
    {"Polar",			SKPoint_PyPolar,		1},
    {"points_allocated",	skpoint_allocated,		1},

    /* Rect functions */
    {"Rect",			skrect_skrect,			1},
    {"UnionRects",		skrect_unionrects,		1},
    {"PointsToRect",		skrect_PointsToRect,		1},
    {"IntersectRects",		skrect_intersect,		1},
    {"rects_allocated",		skrect_allocated,		1},

    /* Trafo functions */
    {"Trafo",			sktrafo_sktrafo,		1},
    {"Scale",			sktrafo_scale,			1},
    {"Translation",		sktrafo_translation,		1},
    {"Rotation",		sktrafo_rotation,		1},
    {"trafos_allocted",		sktrafo_allocated,		1},
    
    /* FontMetric functions */
    {"CreateFontMetric",	SKFM_PyCreateMetric,		1},
    
    /* Curve functions */
//     {"draw_multipath",		SKCurve_PyDrawMultipath,	1},
    {"test_transformed",	SKCurve_PyTestTransformed,	1},
    {"blend_paths",		SKCurve_PyBlendPaths,		1},
//     {"multicurve_region",	SKCurve_PyMultipathRegion,	1},
    {"CreatePath",		SKCurve_PyCreatePath,		1},
    {"approx_arc",		SKCurve_PyApproxArc,		1},
    {"RectanglePath",		SKCurve_PyRectanglePath,	1},
    {"RoundedRectanglePath",	SKCurve_PyRoundedRectanglePath,	1},
    {"num_allocated",		_SKCurve_NumAllocated,		1},

    /* image functions */
//     {"copy_image_to_ximage",	copy_image_to_ximage,		1},
//     {"transform_to_ximage",	transform_to_ximage,		1},
//     {"fill_rgb_xy",		fill_rgb_xy,			1},
//     {"fill_rgb_z",		fill_rgb_z,			1},
//     {"fill_hsv_xy",		fill_hsv_xy,			1},
//     {"fill_hsv_z",		fill_hsv_z,			1},
//     {"fill_axial_gradient",	fill_axial_gradient,		1},
//     {"fill_radial_gradient",	fill_radial_gradient,		1},
//     {"fill_conical_gradient",	fill_conical_gradient,		1},
//     {"fill_transformed_tile",	fill_transformed_tile,		1},
    {"write_ps_hex",		skimage_write_ps_hex,		1},

    /* color functions */
    {"RGBColor",		skcolor_rgbcolor,		1},
    {"colors_allocated",	skcolor_num_allocated,		1},
//     {"XVisual",			skcolor_xvisual,		1},

    /* skaux */
    {"DrawBezier",		SKAux_DrawBezier,		1},
//     {"GetPixel",		SKAux_GetPixel,			1},
//     {"DrawGrid",		SKAux_DrawGrid,			1},
    {"TransformRectangle",	SKAux_TransformRectangle,	1},
    {"IdIndex",			SKAux_IdIndex,			1},
    {"xlfd_char_range",		xlfd_char_range,		1},
    {"SKCache",			SKCache_PyCreate,		1},
    
    /* */
    {NULL,		NULL} 
};

/*
 */

// PyObject * Pax_GCType = NULL;
// PyObject * Pax_ImageType = NULL;
// Pax_Functions * pax_functions = NULL;

/*
 *	Init module
 */
static void
add_int(PyObject * dict, int i, char * name)
{
    PyObject *v;
    
    v = Py_BuildValue("i", i);
    if (v)
    {
	PyDict_SetItemString(dict, name, v);
	Py_DECREF(v);
    }
}

void
init_sketch()
{
    PyObject * d, *m, *r, *pax;

    m = Py_InitModule("_sketch", curve_functions);
    d = PyModule_GetDict(m);

   
    /* Rect specific initialization */
    /* The InfinityRect is initialized with FLT_MAX instead of HUGE_VAL
       now (Sketch 0.5.4), because of problems with HUGE_VAL on Alpha
       Linux. */
    r = SKRect_FromDouble(-FLT_MAX, -FLT_MAX, FLT_MAX, FLT_MAX);
    if (r)
    {
	PyDict_SetItemString(d, "InfinityRect", r);
	SKRect_InfinityRect = (SKRectObject*)r;
    }
    
    r = SKRect_FromDouble(0.0, 0.0, 0.0, 0.0);
    if (r)
    {
	PyDict_SetItemString(d, "EmptyRect", r);
	SKRect_EmptyRect = (SKRectObject*)r;
    }

    /* Trafo specific initialization */
    SKTrafo_ExcSingular = PyErr_NewException("_sketch.SingularMatrix",
					     PyExc_ArithmeticError, NULL);
    if (SKTrafo_ExcSingular)
    {
	PyDict_SetItemString(d, "SingularMatrix", SKTrafo_ExcSingular);
    }

    /* Sketch type objects */
    PyDict_SetItemString(d, "RectType", (PyObject*)&SKRectType);
    PyDict_SetItemString(d, "PointType", (PyObject*)&SKPointType);
    PyDict_SetItemString(d, "TrafoType", (PyObject*)&SKTrafoType);
    PyDict_SetItemString(d, "CurveType", (PyObject*)&SKCurveType);
//     PyDict_SetItemString(d, "ColorType", (PyObject*)&SKColorType);

    /* Curve specific initialization */
#define ADD_INT(name) add_int(d, name, #name)
#define ADD_INT2(i, name) add_int(d, i, name)
    ADD_INT(ContAngle);
    ADD_INT(ContSmooth);
    ADD_INT(ContSymmetrical);
    ADD_INT2(CurveBezier, "Bezier");
    ADD_INT2(CurveLine, "Line");
    ADD_INT(SelNone);
    ADD_INT(SelNodes);
    ADD_INT(SelSegmentFirst);
    ADD_INT(SelSegmentLast);

    _SKCurve_InitCurveObject();

    /* import some objects from pax */
//     pax = PyImport_ImportModule("pax");
//     if (pax)
//     {
// 	Pax_GCType = PyObject_GetAttrString(pax, "PaxGCType");
// 	if (!Pax_GCType)
// 	    return;
// 	Pax_ImageType = PyObject_GetAttrString(pax, "PaxImageType");
// 	if (!Pax_ImageType)
// 	    return;
// 	r = PyObject_GetAttrString(pax, "Pax_Functions");
// 	if (!r)
// 	    return;
// 	pax_functions = (Pax_Functions*)PyCObject_AsVoidPtr(r);
// 	Py_DECREF(r);
//     }
}
