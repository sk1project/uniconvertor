/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1998 by Bernhard Herzog
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


#ifndef SKCOLOR_H
#define SKCOLOR_H


typedef struct {
    PyObject_HEAD
    float		red;
    float		green;
    float		blue;
} SKColorObject;

extern PyTypeObject SKColorType;
#define SKColor_Check(v)		((v)->ob_type == &SKColorType)

PyObject * SKColor_FromRGB(double red, double green, double blue);

#include <X11/Xlib.h>
#include <X11/Xutil.h>

struct SKVisualObject_s;

typedef union
{
    unsigned short s[2];
    unsigned char c[4];
}  SKDitherInfo;


typedef PyObject * (*SKVisual_GetPixel)(struct SKVisualObject_s * self,
					SKColorObject * color);
typedef void (*SKVisual_FreeExtra)(struct SKVisualObject_s * self);

typedef struct SKVisualObject_s {
    PyObject_HEAD
    Display * display;
    XVisualInfo * visualinfo;
        
    SKVisual_GetPixel	get_pixel;
    SKVisual_FreeExtra	free_extra;

    double gamma;
    double gamma_inv;	/* 1 / gamma */

    /* XXX: the data for different visual types should be a union (?) */
    
    /* true color */
    long red_bits[256];
    long green_bits[256];
    long blue_bits[256];
    int red_index;
    int green_index;
    int blue_index;

    /* pseudo color */
    int shades_r;
    int shades_g;
    int shades_b;
    int shades_gray;
    int cube_size;
    long pseudocolor_table[256];
    SKDitherInfo * dither_red;
    SKDitherInfo * dither_green;
    SKDitherInfo * dither_blue;
    SKDitherInfo * dither_gray;
    unsigned char ***dither_matrix;
    XImage * tile;
    GC	tilegc;
} SKVisualObject;

extern PyTypeObject SKVisualType;
#define SKVisual_Check(v)		((v)->ob_type == &SKVisualType)

/* in skdither.c */
void skvisual_init_dither(SKVisualObject * self);

/* Python functions */

PyObject * skcolor_xvisual(PyObject * self, PyObject * args);
PyObject * skcolor_rgbcolor(PyObject * self, PyObject * args);
PyObject * skcolor_num_allocated(PyObject * self, PyObject * args);




#endif /* SKCOLOR_H */
