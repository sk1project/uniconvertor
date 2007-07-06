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


/*
 *	Draw bezier paths on X
 */

#include <math.h>
#include <Python.h>
#include <regionobject.h>
#include <gcobject.h>

#include "_sketchmodule.h"
#include "skrect.h"
#include "sktrafo.h"
#include "curvelow.h"
#include "curveobject.h"


/*
 *	drawing related funtions
 */

/* Return the maximum number of XPoints needed to represent the path.
 */
static int
estimate_number_of_points(SKCurveObject * self)
{
    int i, count = 0;
    CurveSegment * segment;
    
    segment = self->segments;
    for (i = 0; i < self->len; i++, segment++)
    {
	if (segment->type == CurveBezier)
	    /* BEZIER_FILL_LENGTH includes the start and endpoint of a segment.
	       The XPoint list contains internal nodes only once. */
	    count += BEZIER_FILL_LENGTH - 1;
	else
	    count += 1;
    }
    return count + 1; /* The start point must be included */
}

/* draw a poly bezier on a GC, applying the transformation trafo to each
 * point. Assume that the gc is set up as needed. This means that we can
 * only fill with the standard X fill capabilities, that is, no gradient
 * patterns, hatching etc.
 *
 * To achieve this, we need to construct a list of XPoints that holds
 * the entire curve approximated by line segments. To avoid the overhead
 * of malloc/free we define an array on the stack that is large enough
 * for most objects. Only if the estimated number of points is larger
 * than this array the required amount of memory is malloc'ed. This
 * array is quite large, which might cause problems on some systems.
 *
 * Another, related thing is that the estimated number of points is on
 * average about 40 (forty) times too large (at least for the pictures I
 * tested this with (imported with pstoedit)). Unfortunately, I see no
 * other efficient way to make the estimation more accurate while still
 * giving a correct upper bound for the number of points.
 *
 * As it turns out, on Linux at least malloc seems to be fast enough to
 * always malloc the array without a noticable (but measurable)
 * performance penalty
 */

#define ARRAY_LENGTH (BEZIER_FILL_LENGTH * 30)
/*#define ARRAY_LENGTH 1*/
PyObject *
SKCurve_PyDrawTransformed(SKCurveObject * self, PyObject * args)
{
    PyObject * trafo;
    int length, i, added;
    XPoint	* points;
    XPoint	point_array[ARRAY_LENGTH];
    CurveSegment * segment;
    SKCoord nx, ny, x1, y1, x2, y2, lastx, lasty;
    int		x[4], y[4];
    PyObject * fill, * line, *rect_or_none;
    PaxGCObject * gc_object;
    SKRectObject * clip_rect = NULL;
    int optimize_clip = 0;

    if (!PyArg_ParseTuple(args, "O!O!OOO", Pax_GCType, &gc_object,
			  &SKTrafoType, &trafo, &line, &fill, &rect_or_none))
	return NULL;

    if (rect_or_none == Py_None)
	clip_rect = NULL;
    else if (SKRect_Check(rect_or_none))
	clip_rect = (SKRectObject*)rect_or_none;
    else
    {
	PyErr_SetString(PyExc_TypeError, "Rect or None expected");
	return NULL;
    }

    optimize_clip = !PyObject_IsTrue(line);

    length = estimate_number_of_points(self);

    if (length <= 0)
    {
	/* should never happen */
	PyErr_SetString(PyExc_RuntimeError,
			"bezier_create_xpoint_list: estimeted length <= 0");
	return NULL;
    }

    if (length > ARRAY_LENGTH)
    {
	/* allocate the array, if not large enough */
	points = malloc(length * sizeof(XPoint));
	if (!points)
	{
	    PyErr_NoMemory();
	    return NULL;
	}
    }
    else
	points = point_array;

    /* the first point */
    segment = self->segments;
    SKTrafo_TransformXY(trafo, segment->x, segment->y, &lastx, &lasty);
    /* round to nearest int. Assumes that window coordinates are positive */
    points[0].x = rint(lastx);
    points[0].y = rint(lasty);
    length = 1;

    /* the rest */
    segment++;
    for (i = 1; i < self->len; i++, segment++)
    {
	int do_bezier = segment->type == CurveBezier;
	if (do_bezier && clip_rect && optimize_clip)
	{
	    /* check, whether part of the segment lies in the clip region */
	    /* XXX: this does not work correctly for very thick lines (lines
	       wider than a few pixels in window coordinates. Therefore we do
	       this only if optimize_clip is true. */
	    SKRectObject r;
	    r.left = r.right = segment[-1].x;
	    r.top = r.bottom = segment[-1].y;
	    SKRect_AddXY(&r, segment->x1, segment->y1);
	    SKRect_AddXY(&r, segment->x2, segment->y2);
	    SKRect_AddXY(&r, segment->x, segment->y);

	    if (r.left > clip_rect->right || r.right < clip_rect->left
		|| r.top < clip_rect->bottom || r.bottom > clip_rect->top)
		do_bezier = 0;
	}

	if (do_bezier)
	{
	    SKTrafo_TransformXY(trafo, segment->x1, segment->y1, &x1, &y1);
	    SKTrafo_TransformXY(trafo, segment->x2, segment->y2, &x2, &y2);
	    SKTrafo_TransformXY(trafo, segment->x, segment->y, &nx, &ny);
	    x[0] = rint(lastx);	y[0] = rint(lasty);
	    x[1] = rint(x1);	y[1] = rint(y1);
	    x[2] = rint(x2);    y[2] = rint(y2);
	    x[3] = rint(nx);    y[3] = rint(ny);
	    added = bezier_fill_points(points + length - 1, x, y);
	    length += added - 1;
	}
	else
	{
	    SKTrafo_TransformXY(trafo, segment->x, segment->y, &nx, &ny);
	    points[length].x = rint(nx);
	    points[length].y = rint(ny);
	    if (i >= self->len - 1
		|| abs(points[length].x - points[length - 1].x)
		|| abs(points[length].y - points[length - 1].y))
		length++;
	}

	lastx = nx;
	lasty = ny;
    }

    if (length > 1)
    {
	if (self->closed && PyObject_IsTrue(fill))
	{
	    XFillPolygon(gc_object->display, gc_object->drawable,
			 gc_object->gc,
			 points, length, Complex, CoordModeOrigin);
	}
	if (PyObject_IsTrue(line))
	{
	    XDrawLines(gc_object->display, gc_object->drawable,
		       gc_object->gc,
		       points, length, CoordModeOrigin);
	}
    }
#if 0
    else
    {
	fprintf(stderr, "DrawTransformed: length = 1\n");
    }
#endif
    
    if (points != point_array)
    {
	free(points);
    }
    Py_INCREF(Py_None);
    return Py_None;
}



static int
curve_add_transformed_points(SKCurveObject * self, XPoint * points,
			     PyObject * trafo, SKRectObject * clip_rect,
			     int optimize_clip)
{
    int length, i, added;
    CurveSegment *segment;
    SKCoord nx, ny, x1, y1, x2, y2, lastx, lasty;
    int x[4], y[4];

    /* the first point */
    segment = self->segments;
    SKTrafo_TransformXY(trafo, segment->x, segment->y, &lastx, &lasty);
    /* round to nearest int. Assumes that window coordinates are positive */
    points[0].x = rint(lastx);
    points[0].y = rint(lasty);
    length = 1;

    /* the rest */
    segment++;
    for (i = 1; i < self->len; i++, segment++)
    {
	int do_bezier = segment->type == CurveBezier;
	if (do_bezier && clip_rect && optimize_clip)
	{
	    /* check, whether part of the segment lies in the clip region */
	    /* XXX: this does not work correctly for very thick lines (lines
	       wider than a few pixels in window coordinates */
	    SKRectObject r;
	    r.left = r.right = segment[-1].x;
	    r.top = r.bottom = segment[-1].y;
	    SKRect_AddXY(&r, segment->x1, segment->y1);
	    SKRect_AddXY(&r, segment->x2, segment->y2);
	    SKRect_AddXY(&r, segment->x, segment->y);

	    if (r.left > clip_rect->right || r.right < clip_rect->left
		|| r.top < clip_rect->bottom || r.bottom > clip_rect->top)
		do_bezier = 0;
	}

	if (do_bezier)
	{
	    SKTrafo_TransformXY(trafo, segment->x1, segment->y1, &x1, &y1);
	    SKTrafo_TransformXY(trafo, segment->x2, segment->y2, &x2, &y2);
	    SKTrafo_TransformXY(trafo, segment->x, segment->y, &nx, &ny);
	    x[0] = rint(lastx);	y[0] = rint(lasty);
	    x[1] = rint(x1);	y[1] = rint(y1);
	    x[2] = rint(x2);	y[2] = rint(y2);
	    x[3] = rint(nx);	y[3] = rint(ny);
	    added = bezier_fill_points(points + length - 1, x, y);
	    length += added - 1;
	}
	else
	{
	    SKTrafo_TransformXY(trafo, segment->x, segment->y, &nx, &ny);
	    points[length].x = rint(nx);
	    points[length].y = rint(ny);
	    if (i >= self->len - 1
		|| abs(points[length].x - points[length - 1].x)
		|| abs(points[length].y - points[length - 1].y))
		length++;
	}

	lastx = nx;
	lasty = ny;
    }

    return length;
}

/*
 * Draw a multipath bezier on a gc.
 *
 * The multipath bezier is represented by a tuple of SKCurveObject objects.
 * The callback functions fill_func and line_func allow arbitrary fill
 * patterns.
 *
 */

PyObject *
SKCurve_PyDrawMultipath(PyObject* self, PyObject * args)
{
    PyObject * trafo;
    int length, i, added, filled;
    XPoint * points = NULL;
    int *start_idx = NULL, *lengths = NULL;
    PyObject *fill_func, *line_func, *push_clip, *pop_clip, *set_clip;
    PyObject *rect_or_none, *paths;
    SKCurveObject *path;
    PaxGCObject * gc_object;
    SKRectObject * clip_rect = NULL;
    XPoint start;
    PaxRegionObject * oregion = NULL;
    int is_proc_fill = 0, do_clip = 0;

    if (!PyArg_ParseTuple(args, "O!O!OOOOOOO!Oii", Pax_GCType, &gc_object,
			  &SKTrafoType, &trafo,
			  &line_func, &fill_func, &push_clip, &pop_clip,
			  &set_clip, &rect_or_none,
			  &PyTuple_Type, &paths, &oregion, &is_proc_fill,
			  &do_clip))
	return NULL;

    if (rect_or_none == Py_None)
	clip_rect = NULL;
    else if (SKRect_Check(rect_or_none))
	clip_rect = (SKRectObject*)rect_or_none;
    else
    {
	PyErr_SetString(PyExc_TypeError,
			"8th parameter must None or an SKRectObject");
	return NULL;
    }

    if (!PyObject_IsTrue((PyObject*)oregion))
	oregion = NULL;

    filled = PyObject_IsTrue(fill_func) || do_clip;

    length = 0;
    for (i = 0; i < PyTuple_Size(paths); i++)
    {
	path = (SKCurveObject*)PyTuple_GetItem(paths, i);
	if (!SKCurve_Check(path))
	{
	    PyErr_SetString(PyExc_TypeError,
			    "paths must be a tuple of bezier path objects");
	    return NULL;
	}
	length += estimate_number_of_points(path);
    }
    /* additional points to close the paths: */
    if (filled)
	length += 2 * PyTuple_Size(paths);

    if (length <= 0)
    {
	/* can theoretically happen if there is only one path with no segments.
	 * Such paths should have been automatically removed from the drawing.
	 */
	Py_INCREF(Py_None);
	return Py_None;
    }

    points = malloc(length * sizeof(XPoint));
    start_idx = malloc(PyTuple_Size(paths) * sizeof(int));
    lengths = malloc(PyTuple_Size(paths) * sizeof(int));
    if (!points || !start_idx || !lengths)
    {
	PyErr_NoMemory();
	goto fail;
    }

    length = 0;
    for (i = 0; i < PyTuple_Size(paths); i++)
    {
	start_idx[i] = length;
	path = (SKCurveObject*)PyTuple_GetItem(paths, i);
	added = curve_add_transformed_points(path, points + length, trafo,
					     clip_rect,
					     !PyObject_IsTrue(line_func));
	if (!added)
	    goto fail;
	lengths[i] = added;

	if (filled)
	{
	    if (!path->closed)
	    {
		points[length + added] = points[length];
		added++;
	    }
	    if (i == 0)
	    {
		start = points[0];
	    }
	    else
	    {
		points[length + added] = start;
		added++;
	    }
	}
	length += added;
    }

    if (length > 1)
    {
	if (filled)
	{
	    Region region = XPolygonRegion(points, length, EvenOddRule);
	    XUnionRegion(oregion->region, region, oregion->region);
	    XDestroyRegion(region);
	    
	    if (is_proc_fill)
	    {
		PyObject * result;

		if (!do_clip)
		{
		    result = PyObject_CallObject(push_clip, NULL);
		    if (!result)
			goto fail;
		    Py_DECREF(result);
		}
		result = PyObject_CallFunction(set_clip, "(O)", oregion);
		if (!result)
		    goto fail;
		Py_DECREF(result);
		result = PyObject_CallObject(fill_func, NULL);
		if (!result)
		    goto fail;
		Py_DECREF(result);
		if (!do_clip)
		{
		    result = PyObject_CallObject(pop_clip, NULL);
		    if (!result)
			goto fail;
		    Py_DECREF(result);
		}
	    }
	    else /* !is_proc_fill */
	    {
		if (PyObject_IsTrue(fill_func))
		{
		    PyObject * result = PyObject_CallObject(fill_func, NULL);
		    if (!result)
			goto fail;
		    Py_DECREF(result);
		    XFillPolygon(gc_object->display, gc_object->drawable,
				 gc_object->gc,
				 points, length, Complex, CoordModeOrigin);
		}

		if (do_clip)
		{
		    PyObject * result = PyObject_CallFunction(set_clip, "(O)",
							      oregion);
		    if (!result)
			goto fail;
		    Py_DECREF(result);
		}
	    }
	} /* if (filled) */

	if (PyObject_IsTrue(line_func))
	{
	    PyObject * result = PyObject_CallObject(line_func, NULL);
	    if (!result)
		goto fail;
	    Py_DECREF(result);
	    for (i = 0; i < PyTuple_Size(paths); i++)
	    {
		XDrawLines(gc_object->display, gc_object->drawable,
			   gc_object->gc,
			   points + start_idx[i], lengths[i], CoordModeOrigin);
	    }
	}
    }

    free(points);
    free(lengths);
    free(start_idx);

    Py_INCREF(Py_None);
    return Py_None;

fail:
    free(points);
    free(lengths);
    free(start_idx);
    return NULL;

}

/*
 *
 */

PyObject *
SKCurve_PyMultipathRegion(PyObject* self, PyObject * args)
{
    PyObject * trafo;
    int length, i, added;
    XPoint	* points = NULL;
    PyObject	*rect_or_none, *paths;
    SKCurveObject *path;
    SKRectObject * clip_rect = NULL;
    PaxRegionObject * oregion = NULL;
    XPoint start;

    if (!PyArg_ParseTuple(args, "O!O!OO", &SKTrafoType, &trafo,
			  &PyTuple_Type, &paths, &rect_or_none, &oregion))
	return NULL;

    if (rect_or_none == Py_None)
	clip_rect = NULL;
    else if (SKRect_Check(rect_or_none))
	clip_rect = (SKRectObject*)rect_or_none;
    else
    {
	PyErr_SetString(PyExc_TypeError,
			"3rd parameter must None or an SKRectObject");
	return NULL;
    }

    length = 0;
    for (i = 0; i < PyTuple_Size(paths); i++)
    {
	path = (SKCurveObject*)PyTuple_GetItem(paths, i);
	if (!SKCurve_Check(path))
	{
	    PyErr_SetString(PyExc_TypeError,
			    "paths must be a tuple of bezier path objects");
	    return NULL;
	}
	length += estimate_number_of_points(path);
    }
    /* additional points needed to close the paths: */
    length += 2 * PyTuple_Size(paths);

#if 0
    if (length <= 0)
    {
	/* can theoretically happen if there is only one path with no segments.
	 * Such paths should have been automatically removed from the drawing.
	 */
	Py_INCREF(Py_None);
	return Py_None;
    }
#endif

    points = malloc(length * sizeof(XPoint));
    if (!points)
    {
	PyErr_NoMemory();
	goto fail;
    }

    length = 0;
    for (i = 0; i < PyTuple_Size(paths); i++)
    {
	path = (SKCurveObject*)PyTuple_GetItem(paths, i);
	added = curve_add_transformed_points(path, points + length, trafo,
					    clip_rect, 1);
	if (!added)
	    goto fail;

	if (!path->closed)
	{
	    points[length + added] = points[length];
	    added++;
	}
	if (i == 0)
	{
	    start = points[0];
	}
	else
	{
	    points[length + added] = start;
	    added++;
	}
	length += added;
    }

    if (length > 1)
    {
	Region region = XPolygonRegion(points, length, EvenOddRule);
	XUnionRegion(oregion->region, region, oregion->region);
	XDestroyRegion(region);
    }
    
    free(points);

    Py_INCREF(Py_None);
    return Py_None;

fail:
    free(points);
    return NULL;

}
