/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1997, 1998, 1999, 2000 by Bernhard Herzog
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

#define __NO_MATH_INLINES
#include <math.h>
#include <Python.h>
#include <structmember.h>

// #include <X11/Xlib.h>
// #include <X11/Xutil.h>

#include <Imaging.h>
// #include <imageobject.h>
// #include <regionobject.h>

#include "_sketchmodule.h"
#include "sktrafo.h"
#include "skcolor.h"

#ifndef PI
#define PI 3.14159265358979323846264338327
#endif

/* redefine the ImagingObject struct defined in _imagingmodule.c */
/* there should be a better way to do this... */
typedef struct {
    PyObject_HEAD
    Imaging image;
} ImagingObject;


// static void
// image_scale_rgb_16(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   int startx, int starty, int width, int height,
// 		   int dest_y, int dest_height, int flip_y,
// 		   int * origx, int * origy)
// {
//     long *red_bits = visual->red_bits;
//     long *green_bits = visual->green_bits;
//     long *blue_bits  = visual->blue_bits;
//     short * dest;
//     int x, y, lasty;
//     INT32 * src;
//     unsigned char * rgb;
// 
//     lasty = -1;
//     for (y = 0; y < height; y++)
//     {
// 	dest = (short*)(ximage->data + ximage->bytes_per_line * (y + starty))
// 	    +startx;
// 
// 	if (origy[y] != lasty)
// 	{
// 	    src = image->image32[origy[y]];
// 	    for (x = 0; x < width; x++, dest++)
// 	    {
// 		rgb = (unsigned char*)(src + origx[x]);
// 		*dest = red_bits[(int)rgb[0]]
// 		    | green_bits[(int)rgb[1]]
// 		    | blue_bits[(int)rgb[2]];
// 	    }
// 	    lasty = origy[y];
// 	}
// 	else
// 	{
// 	    memcpy(dest, ((char*)dest) - ximage->bytes_per_line,
// 		   width * sizeof(*dest));
// 	}
//     }
// }
// 
// static void
// image_scale_rgb_24(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   int startx, int starty, int width, int height,
// 		   int dest_y, int dest_height, int flip_y,
// 		   int * origx, int * origy)
// {
//     int red_index = visual->red_index;
//     int green_index = visual->green_index;
//     int blue_index = visual->blue_index;
//     unsigned char *dest;
//     int bpp = (ximage->bits_per_pixel + 7) / 8;
//     int x, y, lasty;
//     INT32 * src = NULL;
//     unsigned char * rgb;
// 
//     if (ximage->byte_order == MSBFirst)
//     {
// 	red_index = 3 - red_index;
// 	green_index = 3 - green_index;
// 	blue_index = 3 - blue_index;
//     }
// 
//     lasty = -1;
//     for (y = 0; y < height; y++)
//     {
// 	dest = (unsigned char*)(ximage->data
// 				+ ximage->bytes_per_line * (y + starty)
// 				+ bpp * startx);
// 
// 	if (origy[y] != lasty)
// 	{
// 	    src = image->image32[origy[y]];
// 	    for (x = 0; x < width; x++, dest += bpp)
// 	    {
// 		rgb= (unsigned char*)(src + origx[x]);
// 		dest[red_index] = rgb[0];
// 		dest[green_index] = rgb[1];
// 		dest[blue_index] = rgb[2];
// 	    }
// 	    lasty = origy[y];
// 	}
// 	else
// 	{
// 	    memcpy(dest, ((char*)dest) - ximage->bytes_per_line,
// 		   width * bpp);
// 	}
//     }
// }
// 
// static void
// image_scale_rgb_8(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		  int startx, int starty, int width, int height,
// 		  int dest_y, int dest_height, int flip_y,
// 		  int * origx, int * origy)
// {
//     int x, y;
//     INT32 * src;
//     long *colors = visual->pseudocolor_table;
//     SKDitherInfo *dither_red = visual->dither_red;
//     SKDitherInfo *dither_green = visual->dither_green;
//     SKDitherInfo *dither_blue = visual->dither_blue;
//     SKDitherInfo r, g, b;
//     unsigned char **dither_matrix;
//     unsigned char *matrix;
//     unsigned char *dest;
//     unsigned char * rgb;
// 
//     for (y = 0; y < height; y++)
//     {
// 	dither_matrix = visual->dither_matrix[(y + starty) & 0x7];
// 	dest = (unsigned char*)(ximage->data
// 				+ ximage->bytes_per_line * (y + starty)
// 				+ startx);
// 
// 	src = image->image32[origy[y]];
// 	for (x = 0; x < width; x++, dest++)
// 	{
// 	    rgb = (unsigned char*)(src + origx[x]);
// 	    r = dither_red[rgb[0]];
// 	    g = dither_green[rgb[1]];
// 	    b = dither_blue[rgb[2]];
// 
// 	    matrix = dither_matrix[x & 0x7];
// 	    *dest = colors[(r.c[matrix[r.s[1]]] +
// 			    g.c[matrix[g.s[1]]] +
// 			    b.c[matrix[b.s[1]]])];
// 	}
//     }
// }
// 
// static void
// image_scale_gray_16(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		    int startx, int starty, int width, int height,
// 		    int dest_y, int dest_height, int flip_y,
// 		    int * origx, int * origy)
// {
//     long *red_bits = visual->red_bits;
//     long *green_bits = visual->green_bits;
//     long *blue_bits  = visual->blue_bits;
//     short * dest;
//     int x, y, lasty, gray;
//     UINT8 * src;
// 
//     lasty = -1;
//     for (y = 0; y < height; y++)
//     {
// 	dest = (short*)(ximage->data + ximage->bytes_per_line * (y + starty))
// 	    +startx;
// 
// 	if (origy[y] != lasty)
// 	{
// 	    src = image->image8[origy[y]];
// 	    for (x = 0; x < width; x++, dest++)
// 	    {
// 		gray = src[origx[x]];
// 		*dest = red_bits[gray] | green_bits[gray] | blue_bits[gray];
// 	    }
// 	    lasty = origy[y];
// 	}
// 	else
// 	{
// 	    memcpy(dest, ((char*)dest) - ximage->bytes_per_line,
// 		   width * sizeof(*dest));
// 	}
//     }
// }
// 
// static void
// image_scale_gray_24(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		    int startx, int starty, int width, int height,
// 		    int dest_y, int dest_height, int flip_y,
// 		    int * origx, int * origy)
// {
//     int red_index = visual->red_index;
//     int green_index = visual->green_index;
//     int blue_index = visual->blue_index;
//     unsigned char *dest;
//     int bpp = (ximage->bits_per_pixel + 7) / 8;
//     int x, y, lasty;
//     UINT8 * src = NULL;
// 
//     if (ximage->byte_order == MSBFirst)
//     {
// 	red_index = 3 - red_index;
// 	green_index = 3 - green_index;
// 	blue_index = 3 - blue_index;
//     }
// 
//     lasty = -1;
//     for (y = 0; y < height; y++)
//     {
// 	dest = (unsigned char*)(ximage->data
// 				+ ximage->bytes_per_line * (y + starty)
// 				+ bpp * startx);
// 
// 	if (origy[y] != lasty)
// 	{
// 	    src = image->image8[origy[y]];
// 	    for (x = 0; x < width; x++, dest += bpp)
// 	    {
// 		dest[red_index] = dest[green_index] = dest[blue_index] \
// 		    = src[origx[x]];
// 	    }
// 	    lasty = origy[y];
// 	}
// 	else
// 	{
// 	    memcpy(dest, ((char*)dest) - ximage->bytes_per_line,
// 		   width * bpp);
// 	}
//     }
// }
// 
// static void
// image_scale_gray_8(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   int startx, int starty, int width, int height,
// 		   int dest_y, int dest_height, int flip_y,
// 		   int * origx, int * origy)
// {
//     int x, y;
//     UINT8 * src;
//     long *colors = visual->pseudocolor_table;
//     SKDitherInfo *dither_red = visual->dither_red;
//     SKDitherInfo *dither_green = visual->dither_green;
//     SKDitherInfo *dither_blue = visual->dither_blue;
//     SKDitherInfo r, g, b;
//     unsigned char **dither_matrix;
//     unsigned char *matrix;
//     unsigned char *dest;
//     int gray;
// 
//     for (y = 0; y < height; y++)
//     {
// 	dither_matrix = visual->dither_matrix[(y + starty) & 0x7];
// 	dest = (unsigned char*)(ximage->data
// 				+ ximage->bytes_per_line * (y + starty)
// 				+ startx);
// 	src = image->image8[origy[y]];
// 	for (x = 0; x < width; x++, dest++)
// 	{
// 	    gray = src[origx[x]];
// 	    r = dither_red[gray];
// 	    g = dither_green[gray];
// 	    b = dither_blue[gray];
// 
// 	    matrix = dither_matrix[x & 0x7];
// 	    *dest = colors[(r.c[matrix[r.s[1]]] +
// 			    g.c[matrix[g.s[1]]] +
// 			    b.c[matrix[b.s[1]]])];
// 	}
//     }
// }
// 
// static void
// scale_image(SKVisualObject * visual, Imaging image, XImage * ximage,
// 	    int dest_x, int dest_y, int dest_width, int dest_height,
// 	    int flip_x, int flip_y)
// {
//     int startx = dest_x, starty = dest_y;
//     int width = dest_width, height = dest_height;
//     int *origx, *origy;
//     int x, y;
// 
//     if (ximage->depth != 15 && ximage->depth != 16 && ximage->depth != 24
// 	&& ximage->depth != 8)
//     {
// 	fprintf(stderr, "cannot scale image: depth = %d, pixelsize = %d\n",
// 		ximage->depth, image->pixelsize);
// 	return;
//     }
// 
//     if (startx >= ximage->width || startx + dest_width <= 0)
// 	return;
//     if (startx < 0)
//     {
// 	width = width + startx;
// 	startx = 0;
//     }
// 
//     if (starty >= ximage->height || starty + dest_height <= 0)
// 	return;
//     if (starty < 0)
//     {
// 	height = height + starty;
// 	starty = 0;
//     }
// 
//     if (startx + width > ximage->width)
// 	width = ximage->width - startx;
//     if (starty + height > ximage->height)
// 	height = ximage->height - starty;
// 
//     origx = malloc((width + height) * sizeof(int));
//     if (!origx)
// 	return;
//     origy = origx + width;
// 
//     for (x = 0; x < width; x++)
//     {
// 	origx[x] = ((x + startx - dest_x) * image->xsize) / dest_width;
//     }
//     if (flip_x)
// 	for (x = 0; x < width; x++)
// 	    origx[x] = image->xsize - origx[x] - 1;
// 
//     for (y = 0; y < height; y++)
//     {
// 	origy[y] = ((y + starty - dest_y) * image->ysize) / dest_height;
//     }
//     if (flip_y)
// 	for (y = 0; y < height; y++)
// 	    origy[y] = image->ysize - origy[y] - 1;
// 
//     if (strncmp(image->mode, "RGB", 3) == 0)
//     {
// 	switch (ximage->depth)
// 	{
// 	case 32:
// 	case 24:
// 	    image_scale_rgb_24(visual, image, ximage, startx, starty,
// 			       width, height, dest_y, dest_height, flip_y,
// 			       origx, origy);
// 	    break;
// 	case 16:
// 	case 15:
// 	    image_scale_rgb_16(visual, image, ximage, startx, starty,
// 			       width, height, dest_y, dest_height, flip_y,
// 			       origx, origy);
// 	    break;
// 	case 8:
// 	    image_scale_rgb_8(visual, image, ximage, startx, starty,
// 			      width, height, dest_y, dest_height, flip_y,
// 			      origx, origy);
// 	    break;
// 	default:
// 	    fprintf(stderr, "sketch:scale_image:unsupported depth\n");
// 	}
//     }
//     else if (strcmp(image->mode, "L") == 0)
//     {
// 	switch (ximage->depth)
// 	{
// 	case 32:
// 	case 24:
// 	    image_scale_gray_24(visual, image, ximage, startx, starty,
// 				width, height, dest_y, dest_height, flip_y,
// 				origx, origy);
// 	    break;
// 	case 16:
// 	case 15:
// 	    image_scale_gray_16(visual, image, ximage, startx, starty,
// 				width, height, dest_y, dest_height, flip_y,
// 				origx, origy);
// 	    break;
// 	case 8:
// 	    image_scale_gray_8(visual, image, ximage, startx, starty,
// 			       width, height, dest_y, dest_height, flip_y,
// 			       origx, origy);
// 	    break;
// 	default:
// 	    fprintf(stderr, "sketch:scale_image:unsupported depth\n");
// 	}
//     }
// 
//     free(origx);
// }
// 
// PyObject *
// copy_image_to_ximage(PyObject * self, PyObject * args)
// {
//     ImagingObject * src;
//     PaxImageObject * dest;
//     SKVisualObject * visual;
//     int dest_x, dest_y, dest_width, dest_height;
// 
//     if (!PyArg_ParseTuple(args, "O!OO!iiii", &SKVisualType, &visual,
// 			  &src, Pax_ImageType, &dest,
// 			  &dest_x, &dest_y, &dest_width, &dest_height))
// 	return NULL;
// 
//     scale_image(visual, src->image, dest->ximage,
// 		dest_x, dest_y, abs(dest_width), abs(dest_height),
// 		dest_width < 0, dest_height < 0);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// 
// static void
// image_trafo_rgb_16(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   SKTrafoObject * trafo, int startx, int starty, int height,
// 		   int * minx, int * maxx)
// {
//     long *red_bits = visual->red_bits;
//     long *green_bits = visual->green_bits;
//     long *blue_bits  = visual->blue_bits;
//     short *dest;
//     int x, y, desty;
//     double sx, sy;
//     INT32 ** src = image->image32;
//     unsigned char * rgb;
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (short*)(ximage->data + desty * ximage->bytes_per_line)
// 	    + minx[y];
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest++, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    rgb = (unsigned char*)(src[(int)sy] + (int)sx);
// 	    *dest = red_bits[(int)rgb[0]]
// 		| green_bits[(int)rgb[1]]
// 		| blue_bits[(int)rgb[2]];
// 	}
//     }
// }
// 
// static void
// image_trafo_rgb_24(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   SKTrafoObject * trafo, int startx, int starty, int height,
// 		   int * minx, int * maxx)
// {
//     unsigned char *dest;
//     int bpp = (ximage->bits_per_pixel + 7) / 8;
//     int x, y, desty;
//     double sx, sy;
//     INT32 ** src = image->image32;
//     unsigned char * rgb;
//     int red_index = visual->red_index;
//     int green_index = visual->green_index;
//     int blue_index = visual->blue_index;
// 
//     if (ximage->byte_order == MSBFirst)
//     {
// 	red_index = 3 - red_index;
// 	green_index = 3 - green_index;
// 	blue_index = 3 - blue_index;
//     }
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (unsigned char*)(ximage->data
// 				+ desty * ximage->bytes_per_line
// 				+ bpp * minx[y]);
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest += bpp, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    rgb = (unsigned char*)(src[(int)sy] + (int)sx);
// 	    dest[red_index] = rgb[0];
// 	    dest[green_index] = rgb[1];
// 	    dest[blue_index] = rgb[2];
// 	}
//     }
// }
// 
// static void
// image_trafo_rgb_8(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		  SKTrafoObject * trafo, int startx, int starty, int height,
// 		  int * minx, int * maxx)
// {
//     int x, y, desty;
//     double sx, sy;
//     INT32 ** src = image->image32;
//     unsigned char * rgb;
//     long *colors = visual->pseudocolor_table;
//     SKDitherInfo *dither_red = visual->dither_red;
//     SKDitherInfo *dither_green = visual->dither_green;
//     SKDitherInfo *dither_blue = visual->dither_blue;
//     SKDitherInfo r, g, b;
//     unsigned char **dither_matrix;
//     unsigned char *matrix;
//     unsigned char *dest;
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	dither_matrix = visual->dither_matrix[y & 0x7];
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (unsigned char*)(ximage->data
// 				+ desty * ximage->bytes_per_line
// 				+ minx[y]);
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest++, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    rgb = (unsigned char*)(src[(int)sy] + (int)sx);
// 	    r = dither_red[rgb[0]];
// 	    g = dither_green[rgb[1]];
// 	    b = dither_blue[rgb[2]];
// 
// 	    matrix = dither_matrix[x & 0x7];
// 	    *dest = colors[r.c[matrix[r.s[1]]] + g.c[matrix[g.s[1]]]
// 			   + b.c[matrix[b.s[1]]]];
// 	}
//     }
// }
// 
// static void
// image_trafo_gray_16(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		    SKTrafoObject * trafo, int startx, int starty, int height,
// 		    int * minx, int * maxx)
// {
//     long *red_bits = visual->red_bits;
//     long *green_bits = visual->green_bits;
//     long *blue_bits  = visual->blue_bits;
//     short *dest;
//     int x, y, desty;
//     double sx, sy;
//     UINT8 ** src = image->image8;
//     int gray;
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (short*)(ximage->data + desty * ximage->bytes_per_line)
// 	    + minx[y];
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest++, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    gray = src[(int)sy][(int)sx];
// 	    *dest = red_bits[gray] | green_bits[gray] | blue_bits[gray];
// 	}
//     }
// }
// 
// static void
// image_trafo_gray_24(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		    SKTrafoObject * trafo, int startx, int starty, int height,
// 		    int * minx, int * maxx)
// {
//     unsigned char *dest;
//     int bpp = (ximage->bits_per_pixel + 7) / 8;
//     int x, y, desty;
//     double sx, sy;
//     UINT8 ** src = image->image8;
//     int red_index = visual->red_index;
//     int green_index = visual->green_index;
//     int blue_index = visual->blue_index;
// 
//     if (ximage->byte_order == MSBFirst)
//     {
// 	red_index = 3 - red_index;
// 	green_index = 3 - green_index;
// 	blue_index = 3 - blue_index;
//     }
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (unsigned char*)(ximage->data
// 				+ desty * ximage->bytes_per_line
// 				+ bpp * minx[y]);
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest += bpp, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    dest[red_index] = dest[green_index] = dest[blue_index] \
// 		= src[(int)sy][(int)sx];
// 	}
//     }
// }
// 
// static void
// image_trafo_gray_8(SKVisualObject * visual, Imaging image, XImage * ximage,
// 		   SKTrafoObject * trafo, int startx, int starty, int height,
// 		   int * minx, int * maxx)
// {
//     int x, y, desty;
//     double sx, sy;
//     UINT8 ** src = image->image8;
//     int gray;
//     long *colors = visual->pseudocolor_table;
//     SKDitherInfo *dither_red = visual->dither_red;
//     SKDitherInfo *dither_green = visual->dither_green;
//     SKDitherInfo *dither_blue = visual->dither_blue;
//     SKDitherInfo r, g, b;
//     unsigned char **dither_matrix;
//     unsigned char *matrix;
//     unsigned char *dest;
// 
//     for (y = 0; y < height; y++)
//     {
// 	if (minx[y] == -1)
// 	    continue;
// 	dither_matrix = visual->dither_matrix[y & 0x7];
// 	desty = starty + y;
// 	sx = trafo->m11 * minx[y] + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * minx[y] + trafo->m22 * desty + trafo->v2;
// 
// 	dest = (unsigned char*)(ximage->data
// 				+ desty * ximage->bytes_per_line
// 				+ minx[y]);
// 	for (x = minx[y]; x <= maxx[y];
// 	     x++, dest++, sx += trafo->m11, sy += trafo->m21)
// 	{
// 	    gray = src[(int)sy][(int)sx];
// 	    r = dither_red[gray];
// 	    g = dither_green[gray];
// 	    b = dither_blue[gray];
// 
// 	    matrix = dither_matrix[x & 0x7];
// 	    *dest = colors[r.c[matrix[r.s[1]]] + g.c[matrix[g.s[1]]]
// 			   + b.c[matrix[b.s[1]]]];
// 	}
//     }
// }
// 
// static void
// make_region(SKTrafoObject * trafo, int xsize, int ysize,
// 	    int startx, int starty, int width, int height,
// 	    int * pminx, int * pmaxx, Region region)
// {
//     XRectangle rect;
//     double sx, sy;
//     int y, desty;
//     int minx, maxx;
//     double minxx, minxy, maxxx, maxxy;
// 
//     rect.height = 1;
// 
//     for (y = 0; y < height; y++)
//     {
// 	pminx[y] = -1;
// 	desty = starty + y;
// 	sx = trafo->m11 * startx + trafo->m12 * desty + trafo->v1;
// 	sy = trafo->m21 * startx + trafo->m22 * desty + trafo->v2;
// 
// 	if (trafo->m11 > 0)
// 	{
// 	    if (sx < 0)
// 		minxx = ceil(- sx / trafo->m11);
// 	    else
// 		minxx = 0;
// 
// 	    if (sx < xsize)
// 	    {
// 		maxxx = floor((xsize - sx) / trafo->m11);
// 	    }
// 	    else
// 	    {
// 		continue;
// 	    }
// 	}
// 	else if (trafo->m11 < 0)
// 	{
// 	    if (sx < 0)
// 		continue;
// 	    else
// 		maxxx = floor(-sx / trafo->m11);
// 	    if (sx > xsize)
// 		minxx = ceil((xsize - sx) / trafo->m11);
// 	    else
// 		minxx = 0;
// 	}
// 	else
// 	{
// 	    if (sx < 0 || sx > xsize)
// 		continue;
// 	    minxx = 0;
// 	    maxxx = width;
// 	}
// 
// 	if (trafo->m21 > 0)
// 	{
// 	    if (sy < 0)
// 		minxy = ceil(- sy / trafo->m21);
// 	    else
// 		minxy = 0;
// 
// 	    if (sy < ysize)
// 	    {
// 		maxxy = floor((ysize - sy) / trafo->m21);
// 	    }
// 	    else
// 		continue;
// 	}
// 	else if (trafo->m21 < 0)
// 	{
// 	    if (sy < 0)
// 		continue;
// 	    else
// 		maxxy = floor(-sy / trafo->m21);
// 	    if (sy > ysize)
// 		minxy = ceil((ysize - sy) / trafo->m21);
// 	    else
// 		minxy = 0;
// 	}
// 	else
// 	{
// 	    if (sy < 0 || sy > ysize)
// 		continue;
// 	    minxy = 0;
// 	    maxxy = width;
// 	}
// 	minx = minxx > minxy ? minxx : minxy;
// 
// 	maxx = maxxx < maxxy ? maxxx : maxxy;
// 	if (maxx >= width)
// 	    maxx = width - 1;
// 	if (maxx < minx)
// 	    continue;
// 	maxx += startx;
// 	minx += startx;
// 
// 	pminx[y] = minx; pmaxx[y] = maxx;
// 
// 	rect.x = minx; rect.y = desty; rect.width = maxx - minx + 1;
// 	XUnionRectWithRegion(&rect, region, region);
//     }
// }
// 
// static PyObject *
// transform_image(SKVisualObject * visual, SKTrafoObject * trafo,
// 		Imaging image, XImage * ximage, int dest_x, int dest_y,
// 		int dest_width, int dest_height, Region region)
// {
//     int startx = dest_x, starty = dest_y;
//     int width = dest_width, height = dest_height;
//     int *minx, *maxx;
// 
//     if (ximage->depth != 15 && ximage->depth != 16 && ximage->depth != 24
// 	&& ximage->depth != 8)
//     {
// 	fprintf(stderr, "cannot copy image: depth = %d, pixelsize = %d\n",
// 		ximage->depth, image->pixelsize);
// 	Py_INCREF(Py_None);
// 	return Py_None;
//     }
// 
//     if (startx >= ximage->width || startx + dest_width <= 0)
//     {
// 	Py_INCREF(Py_None);
// 	return Py_None;
//     }
//     if (startx < 0)
//     {
// 	width = width + startx;
// 	startx = 0;
//     }
// 
//     if (starty >= ximage->height || starty + dest_height <= 0)
//     {
// 	Py_INCREF(Py_None);
// 	return Py_None;
//     }
//     if (starty < 0)
//     {
// 	height = height + starty;
// 	starty = 0;
//     }
// 
//     if (startx + width > ximage->width)
// 	width = ximage->width - startx;
//     if (starty + height > ximage->height)
// 	height = ximage->height - starty;
// 
//     minx = malloc(2 * height * sizeof(int));
//     if (!minx)
// 	return PyErr_NoMemory();
//     maxx = minx + height;
//     make_region(trafo, image->xsize, image->ysize, startx, starty,
// 		width, height, minx, maxx, region);
// 
//     if (strncmp(image->mode, "RGB", 3) == 0)
//     {
// 	switch (ximage->depth)
// 	{
// 	case 32:
// 	case 24:
// 	    image_trafo_rgb_24(visual, image, ximage, trafo,
// 			       startx, starty, height, minx, maxx);
// 	    break;
// 	case 16:
// 	case 15:
// 	    image_trafo_rgb_16(visual, image, ximage, trafo,
// 			       startx, starty, height, minx, maxx);
// 	    break;
// 	case 8:
// 	    image_trafo_rgb_8(visual, image, ximage, trafo,
// 			      startx, starty, height, minx, maxx);
// 	    break;
// 	default:
// 	    fprintf(stderr, "sketch:transform_image:unsupported depth\n");
// 	}
//     }
//     else if (strcmp(image->mode, "L") == 0)
//     {
// 	switch (ximage->depth)
// 	{
// 	case 32:
// 	case 24:
// 	    image_trafo_gray_24(visual, image, ximage, trafo,
// 				startx, starty, height, minx, maxx);
// 	    break;
// 	case 16:
// 	case 15:
// 	    image_trafo_gray_16(visual, image, ximage, trafo,
// 				startx, starty, height, minx, maxx);
// 	    break;
// 	case 8:
// 	    image_trafo_gray_8(visual, image, ximage, trafo,
// 			       startx, starty, height, minx, maxx);
// 	    break;
// 	default:
// 	    fprintf(stderr, "sketch:transform_image:unsupported depth\n");
// 	}
//     }
// 
//     free(minx);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// 
// PyObject *
// transform_to_ximage(PyObject * self, PyObject * args)
// {
//     SKVisualObject * visual;
//     ImagingObject * src;
//     PaxImageObject * dest;
//     SKTrafoObject * trafo;
//     PaxRegionObject * region;
//     int dest_x, dest_y, dest_width, dest_height;
// 
//     if (!PyArg_ParseTuple(args, "O!O!OO!iiiiO",	 &SKVisualType, &visual,
// 			  &SKTrafoType, &trafo, &src, Pax_ImageType, &dest,
// 			  &dest_x, &dest_y, &dest_width, &dest_height,
// 			  &region))
// 	return NULL;
// 
//     return transform_image(visual, trafo, src->image, dest->ximage,
// 			   dest_x, dest_y, dest_width, dest_height,
// 			   region->region);
// }
// 
// PyObject *
// fill_rgb_xy(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, width, height;
//     int xidx, yidx, otheridx, othercolor;
//     double color[3];
//     unsigned char *dest;
// 
//     if (!PyArg_ParseTuple(args, "Oii(ddd)", &image, &xidx, &yidx,
// 			  &color[0], &color[1], &color[2]))
// 	return NULL;
// 
//     if (xidx < 0 || xidx > 2 || yidx < 0 || yidx > 2 || xidx == yidx)
// 	return PyErr_Format(PyExc_ValueError,
// 			    "xidx and yidx must be different "
// 			    "and in the range [0..2] (x:%d, y:%d)",
// 			    xidx, yidx);
// 
//     otheridx = 3 - xidx - yidx;
//     othercolor = 255 * color[otheridx];
//     width = image->image->xsize - 1;
//     height = image->image->ysize - 1;
//     for (y = 0; y <= height; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y]);
// 	for (x = 0; x <= width; x++, dest += 4)
// 	{
// 	    dest[xidx] = (255 * x) / width;
// 	    dest[yidx] = (255 * (height - y)) / height;
// 	    dest[otheridx] = othercolor;
// 	}
//     }
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// PyObject *
// fill_rgb_z(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, width, height;
//     int idx, idx1, idx2, val1, val2;
//     double r, g, b;
//     unsigned char *dest;
// 
// 
//     if (!PyArg_ParseTuple(args, "Oi(ddd)", &image, &idx, &r, &g, &b))
// 	return NULL;
// 
//     switch (idx)
//     {
//     case 0:
// 	idx1 = 1; val1 = 255 * g;
// 	idx2 = 2; val2 = 255 * b;
// 	break;
//     case 1:
// 	idx1 = 0; val1 = 255 * r;
// 	idx2 = 2; val2 = 255 * b;
// 	break;
//     case 2:
// 	idx1 = 0; val1 = 255 * r;
// 	idx2 = 1; val2 = 255 * g;
// 	break;
//     default:
// 	PyErr_SetString(PyExc_ValueError, "idx must 0, 1 or 2");
// 	return NULL;
//     }
// 
//     width = image->image->xsize - 1;
//     height = image->image->ysize - 1;
//     for (y = 0; y <= height; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y]);
// 	for (x = 0; x <= width; x++, dest += 4)
// 	{
// 	    dest[idx1] = val1;
// 	    dest[idx2] = val2;
// 	    dest[idx] = (255 * (height - y)) / height;
// 	}
//     }
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// 
// static void
// hsv_to_rgb(double h, double s, double v, unsigned char * rgb)
// {
//     if (s == 0.0)
//     {
// 	rgb[0] = rgb[1] = rgb[2] = 255 * v;
//     }
//     else
//     {
// 	double p, q, t, f;
// 	int i;
// 
// 	h *= 6;
// 	i = (int)h;
// 	f = h - i;
// 	p = v * (1.0 - s);
// 	q = v * (1.0 - s * f);
// 	t = v * (1.0 - s * (1.0 - f));
// 	switch (i)
// 	{
// 	case 0:
// 	case 6:
// 	    rgb[0] = 255 * v; rgb[1] = 255 * t; rgb[2] = 255 * p; break;
// 	case 1:
// 	    rgb[0] = 255 * q; rgb[1] = 255 * v; rgb[2] = 255 * p; break;
// 	case 2:
// 	    rgb[0] = 255 * p; rgb[1] = 255 * v; rgb[2] = 255 * t; break;
// 	case 3:
// 	    rgb[0] = 255 * p; rgb[1] = 255 * q; rgb[2] = 255 * v; break;
// 	case 4:
// 	    rgb[0] = 255 * t; rgb[1] = 255 * p; rgb[2] = 255 * v; break;
// 	case 5:
// 	    rgb[0] = 255 * v; rgb[1] = 255 * p; rgb[2] = 255 * q; break;
// 	}
//     }
// }
// 
// PyObject *
// fill_hsv_xy(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, width, height;
//     int xidx, yidx;
//     double color[3];
//     unsigned char *dest;
// 
//     if (!PyArg_ParseTuple(args, "Oii(ddd)", &image, &xidx, &yidx,
// 			  &color[0], &color[1], &color[2]))
// 	return NULL;
// 
//     if (xidx < 0 || xidx > 2 || yidx < 0 || yidx > 2 || xidx == yidx)
// 	return PyErr_Format(PyExc_ValueError,
// 			    "xidx and yidx must be different and in the range "
// 			    "[0..2] (x:%d, y:%d)",
// 			    xidx, yidx);
// 
//     width = image->image->xsize - 1;
//     height = image->image->ysize - 1;
//     for (y = 0; y <= height; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y]);
// 	for (x = 0; x <= width; x++, dest += 4)
// 	{
// 	    color[xidx] = (double)x / width;
// 	    color[yidx] = (double)(height - y) / height;
// 	    hsv_to_rgb(color[0], color[1], color[2], dest);
// 	}
//     }
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// 
// PyObject *
// fill_hsv_z(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, width, height;
//     int idx;
//     double hsv[3];
//     unsigned char *dest;
// 
// 
//     if (!PyArg_ParseTuple(args, "Oi(ddd)", &image, &idx,
// 			  &hsv[0], &hsv[1], &hsv[2]))
// 	return NULL;
// 
//     if (idx < 0 || idx > 2)
//     {
// 	PyErr_SetString(PyExc_ValueError, "idx must be in the range [0,2]");
// 	return NULL;
//     }
// 
//     width = image->image->xsize - 1;
//     height = image->image->ysize - 1;
//     for (y = 0; y <= height; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y]);
// 	for (x = 0; x <= width; x++, dest += 4)
// 	{
// 	    hsv[idx] = (double)(height - y) / height;
// 	    hsv_to_rgb(hsv[0], hsv[1], hsv[2], dest);
// 	}
//     }
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// /*
//  *
//  */
// 
// static void
// fill_transformed_tile_gray(ImagingObject * image, ImagingObject * tile,
// 			   SKTrafoObject * trafo)
// {
//     int x, y, width, height, itx, ity;
//     int tile_width, tile_height;
//     double tx, ty, dx, dy;
//     UINT8 *dest, **src;
// 
//     width = image->image->xsize;
//     height = image->image->ysize;
//     tile_width = tile->image->xsize;
//     tile_height = tile->image->ysize;
//     src = tile->image->image8;
//     dx = trafo->m11; dy = trafo->m21;
//     for (y = 0; y < height; y++)
//     {
// 	dest = (UINT8*)(image->image->image32[y]);
// 	tx = y * trafo->m12 + trafo->v1;
// 	ty = y * trafo->m22 + trafo->v2;
// 	for (x = 0; x < width; x++, dest += 4, tx += dx, ty += dy)
// 	{
// 	    itx = ((int)tx) % tile_width;
// 	    if (itx < 0)
// 		itx += tile_width;
// 	    ity = ((int)ty) % tile_height;
// 	    if (ity < 0)
// 		ity += tile_height;
// 	    dest[0] = dest[1] = dest[2] = src[ity][itx];
// 	}
//     }
// }
// 
// static void
// fill_transformed_tile_rgb(ImagingObject * image, ImagingObject * tile,
// 			  SKTrafoObject * trafo)
// {
//     int x, y, width, height, itx, ity;
//     int tile_width, tile_height;
//     double tx, ty, dx, dy;
//     INT32 *dest, **src;
// 
//     width = image->image->xsize;
//     height = image->image->ysize;
//     tile_width = tile->image->xsize;
//     tile_height = tile->image->ysize;
//     src = tile->image->image32;
//     dx = trafo->m11; dy = trafo->m21;
//     for (y = 0; y < height; y++)
//     {
// 	dest = image->image->image32[y];
// 	tx = y * trafo->m12 + trafo->v1;
// 	ty = y * trafo->m22 + trafo->v2;
// 	for (x = 0; x < width; x++, dest++, tx += dx, ty += dy)
// 	{
// 	    itx = ((int)tx) % tile_width;
// 	    if (itx < 0)
// 		itx += tile_width;
// 	    ity = ((int)ty) % tile_height;
// 	    if (ity < 0)
// 		ity += tile_height;
// 	    *dest = src[ity][itx];
// 	}
//     }
// }
// 	
// 				  
// 
// PyObject *
// fill_transformed_tile(PyObject * self, PyObject * args)
// {
//     ImagingObject * image, *tile;
//     SKTrafoObject * trafo;
//     
// 
//     if (!PyArg_ParseTuple(args, "OOO!", &image, &tile, &SKTrafoType, &trafo))
// 	return NULL;
// 
//     if (strncmp(tile->image->mode, "RGB", 3) == 0)
//     {
// 	fill_transformed_tile_rgb(image, tile, trafo);
//     }
//     else if (strcmp(tile->image->mode, "L") == 0)
//     {
// 	fill_transformed_tile_gray(image, tile, trafo);
//     }
//     else
// 	return PyErr_Format(PyExc_TypeError,
// 			    "Images of mode %s cannot be used as tiles",
// 			    tile->image->mode);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// #define POS_FACTOR 65536
// typedef struct {
//     unsigned int pos;
//     int r, g, b;
// } GradientEntry;
// typedef GradientEntry * Gradient;
// 
// static int
// convert_color(PyObject * object, GradientEntry * entry)
// {
//     if (PyTuple_Check(object))
//     {
// 	double red, green, blue;
// 	if (!PyArg_ParseTuple(object, "ddd", &red, &green, &blue))
// 	    return 0;
// 	entry->r = 255 * red;
// 	entry->g = 255 * green;
// 	entry->b = 255 * blue;
//     }
//     else if (SKColor_Check(object))
//     {
// 	entry->r = 255 * ((SKColorObject*)object)->red;
// 	entry->g = 255 * ((SKColorObject*)object)->green;
// 	entry->b = 255 * ((SKColorObject*)object)->blue;
//     }
//     else
//     {
// 	PyErr_SetString(PyExc_TypeError,
// 		    "color spec must be tuple of floats or color object");
// 	return 0;
//     }
//     return 1;
// }
// 	
// static Gradient
// gradient_from_list(PyObject * list)
// {
//     int idx, length;
//     Gradient gradient;
// 
//     length = PySequence_Length(list);
//     if (length < 2)
//     {
// 	PyErr_SetString(PyExc_TypeError, "gradient list too short");
// 	return NULL;
//     }
//     
//     gradient = malloc(length * sizeof(GradientEntry));
//     if (!gradient)
//     {
// 	PyErr_NoMemory();
// 	return NULL;
//     }
// 
//     for (idx = 0; idx < length; idx++)
//     {
// 	int result;
// 	double pos;
// 	PyObject * item = PySequence_GetItem(list, idx);
// 	result = PyArg_ParseTuple(item, "dO&:"
// 				  "Gradient Element must be a tuple of "
// 				  "a float and a color", &pos,
// 				  convert_color, &(gradient[idx]));
// 	gradient[idx].pos = POS_FACTOR * pos;
// 	Py_DECREF(item);
// 	if (!result)
// 	    goto fail;
//     }
// 
//     return gradient;
// 
//  fail:
//     free(gradient);
//     return NULL;
// }
// 
// void
// store_gradient_color(Gradient gradient, int length, double t,
// 		     unsigned char *dest)
// {
//     GradientEntry * entry = gradient;
//     unsigned int it = (t < 0) ? 0 : POS_FACTOR *  t;
// 
//     if (it <= 0 || it >= POS_FACTOR)
//     {
// 	if (it <= 0)
// 	    entry = gradient;
// 	else
// 	    entry = gradient + length - 1;
// 	dest[0] = entry->r;
// 	dest[1] = entry->g;
// 	dest[2] = entry->b;
//     }
//     else
//     {
// 	int min = 0, max = length - 1, idx = (max + min) / 2;
// 	unsigned int tt;
// 	while (max - min != 1)
// 	{
// 	    if (gradient[idx].pos < it)
// 		min = idx;
// 	    else
// 		max = idx;
// 	    idx = (max + min) / 2;
// 	}
// 	entry = gradient + min;
// 	tt = (POS_FACTOR * (it - entry->pos)) / (entry[1].pos - entry->pos);
// 	dest[0] = entry->r + (tt * (entry[1].r - entry->r)) / POS_FACTOR;
// 	dest[1] = entry->g + (tt * (entry[1].g - entry->g)) / POS_FACTOR;
// 	dest[2] = entry->b + (tt * (entry[1].b - entry->b)) / POS_FACTOR;
//     }
// }
// 
// #define free_gradient(gradient) free(gradient)
// 
// 
// static void
// horizontal_axial_gradient(ImagingObject * image, Gradient gradient, int length,
// 			  int x0, int x1)
// {
//     unsigned char *dest;
//     int maxx, height, x, y;
//     double factor = 1.0 / (x1 - x0);
// 
//     maxx = image->image->xsize - x0;
//     height = image->image->ysize;
// 
//     dest = (unsigned char*)(image->image->image32[0]);
//     for (x = -x0; x < maxx; x++, dest += 4)
//     {
// 	store_gradient_color(gradient, length, factor * x, dest);
//     }
// 
//     for (y = 1; y < height; y++)
//     {
// 	memcpy(image->image->image32[y], image->image->image32[0],
// 	       4 * image->image->xsize);
//     }
// }    
// 
// static void
// vertical_axial_gradient(ImagingObject * image, Gradient gradient, int length,
// 			int y0, int y1)
// {
//     INT32 *dest;
//     int height, width, x, y;
//     double factor = 1.0 / (y1 - y0);
// 
//     width = image->image->xsize;
//     height = image->image->ysize;
//     for (y = 0; y < height; y++)
//     {
// 	dest = image->image->image32[y];
// 	store_gradient_color(gradient, length, factor * (y - y0),
// 			     (unsigned char*)dest);
// 	for (x = 1; x < width; x++)
// 	{
// 	    dest[x] = dest[0];
// 	}
//     }
// }    
// 
// 
// #define ANGLE_EPSILON 0.01
// PyObject *
// fill_axial_gradient(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, maxx, maxy;
//     double x0, y0, x1, y1, dx, dy, angle;
//     int length;
//     unsigned char *dest;
//     PyObject * list;
//     Gradient gradient;
// 
//     if (!PyArg_ParseTuple(args, "OOdddd", &image, &list, &x0, &y0, &x1, &y1))
// 	return NULL;
// 
//     if (!PySequence_Check(list))
//     {
// 	PyErr_SetString(PyExc_TypeError,
// 			"gradient argument must be a sequence");
// 	return NULL;
//     }
// 
//     if (x0 == x1 && y0 == y1)
//     {
// 	Py_INCREF(Py_None);
// 	return Py_None;
//     }
// 
//     length = PySequence_Length(list);
//     gradient = gradient_from_list(list);
//     if (!gradient)
// 	return NULL;
// 
//     dx = x1 - x0; dy = y1 - y0;
//     angle = atan2(dy, dx);
// 
//     if (fabs(angle) < ANGLE_EPSILON || fabs(fabs(angle) - PI) < ANGLE_EPSILON)
//     {
// 	horizontal_axial_gradient(image, gradient, length,
// 				  (int)(rint(x0)), (int)(rint(x1)));
//     }
//     else if (fabs(angle - PI/2) < ANGLE_EPSILON
// 	     || fabs(angle + PI/2) < ANGLE_EPSILON)
//     {
// 	vertical_axial_gradient(image, gradient, length,
// 				(int)(rint(y0)), (int)(rint(y1)));
//     }
//     else
//     {
// 	double t, dt;
// 	double lensqr = hypot(dx, dy) ; /*(double)dx * dx +  (double)dy * dy;*/
// 	lensqr *= lensqr;
// 	dt = dx / lensqr;
// 	
// 	maxx = image->image->xsize;
// 	maxy = image->image->ysize;
// 	for (y = 0; y < maxy; y++)
// 	{
// 	    dest = (unsigned char*)(image->image->image32[y]);
// 	    t = (dx * -x0 + dy * (y - y0)) / lensqr;
// 	    for (x = 0; x < maxx; x++, dest += 4, t += dt)
// 	    {
// 		store_gradient_color(gradient, length, t, dest);
// 	    }
// 	}
//     }
//     free_gradient(gradient);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// #if 0
// PyObject *
// fill_axial_gradient(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, maxx, maxy, dx, dy;
//     int x0, y0, x1, y1;
//     int length;
//     unsigned char *dest;
//     PyObject * list;
//     Gradient gradient;
// 
//     if (!PyArg_ParseTuple(args, "OOiiii", &image, &list, &x0, &y0, &x1, &y1))
// 	return NULL;
// 
//     if (!PySequence_Check(list))
//     {
// 	PyErr_SetString(PyExc_TypeError,
// 			"gradient argument must be a sequence");
// 	return NULL;
//     }
// 
//     if (x0 == x1 && y0 == y1)
//     {
// 	Py_INCREF(Py_None);
// 	return Py_None;
//     }
// 
//     length = PySequence_Length(list);
//     gradient = gradient_from_list(list);
//     if (!gradient)
// 	return NULL;
// 
//     dx = x1 - x0; dy = y1 - y0;
// 
//     if (dy == 0)
//     {
// 	horizontal_axial_gradient(image, gradient, length, x0, x1);
//     }
//     else if (dx == 0)
//     {
// 	vertical_axial_gradient(image, gradient, length, y0, y1);
//     }
//     else
//     {
// 	double t, dt;
// 	double lensqr = hypot(dx, dy) ; /*(double)dx * dx +  (double)dy * dy;*/
// 	lensqr *= lensqr;
// 	dt = dx / lensqr;
// 	
// 	maxx = image->image->xsize - x0;
// 	maxy = image->image->ysize - y0;
// 	for (y = -y0; y < maxy; y++)
// 	{
// 	    dest = (unsigned char*)(image->image->image32[y + y0]);
// 	    t = (dx * -x0 + dy * y) / lensqr;
// 	    for (x = -x0; x < maxx; x++, dest += 4, t += dt)
// 	    {
// 		store_gradient_color(gradient, length, t, dest);
// 	    }
// 	}
//     }
//     free_gradient(gradient);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// #endif
// 
// PyObject *
// fill_radial_gradient(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, maxx, maxy;
//     int cx, cy, r0, r1;
//     double factor;
//     int length;
//     unsigned char *dest;
//     PyObject * list;
//     Gradient gradient;
// 
//     if (!PyArg_ParseTuple(args, "OOiiii", &image, &list, &cx, &cy, &r0, &r1))
// 	return NULL;
// 
//     if (!PySequence_Check(list))
//     {
// 	PyErr_SetString(PyExc_TypeError,
// 			"gradient argument must be a sequence");
// 	return NULL;
//     }
// 
//     length = PySequence_Length(list);
//     gradient = gradient_from_list(list);
//     if (!gradient)
// 	return NULL;
// 
//     factor = 1.0 / (r1 - r0);
//     maxx = image->image->xsize - cx;
//     maxy = image->image->ysize - cy;
//     for (y = -cy; y < maxy; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y + cy]);
// 	for (x = -cx; x < maxx; x++, dest += 4)
// 	{
// 	    store_gradient_color(gradient, length, factor * (hypot(x, y) - r0),
// 				 dest);
// 	}
//     }
//     
//     free_gradient(gradient);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 
// PyObject *
// fill_conical_gradient(PyObject * self, PyObject * args)
// {
//     ImagingObject * image;
//     int x, y, maxx, maxy;
//     int cx, cy;
//     double angle, t;
//     int length;
//     unsigned char *dest;
//     PyObject * list;
//     Gradient gradient;
// 
//     if (!PyArg_ParseTuple(args, "OOiid", &image, &list, &cx, &cy, &angle))
// 	return NULL;
// 
//     if (!PySequence_Check(list))
//     {
// 	PyErr_SetString(PyExc_TypeError,
// 			"gradient argument must be a sequence");
// 	return NULL;
//     }
// 
//     length = PySequence_Length(list);
//     gradient = gradient_from_list(list);
//     if (!gradient)
// 	return NULL;
// 
//     angle = fmod(angle, 2 * PI);
//     if (angle < -PI)
// 	angle += 2 * PI;
//     else if (angle > PI)
// 	angle -= 2 * PI;
//     
//     maxx = image->image->xsize - cx;
//     maxy = image->image->ysize - cy;
//     for (y = -cy; y < maxy; y++)
//     {
// 	dest = (unsigned char*)(image->image->image32[y + cy]);
// 	for (x = -cx; x < maxx; x++, dest += 4)
// 	{
// 	    if (x || y)
// 	    {
// 		t = atan2(y, x) - angle;
// 		if (t < -PI)
// 		    t += 2 * PI;
// 		else if (t > PI)
// 		    t -= 2 * PI;
// 		t = fabs(t / PI);
// 	    }
// 	    else
// 		t = 0;
// 	    store_gradient_color(gradient, length, t, dest);
// 	}
//     }
//     
//     free_gradient(gradient);
// 
//     Py_INCREF(Py_None);
//     return Py_None;
// }
// 

static char * hexdigit = "0123456789ABCDEF";

static void
write_ps_hex_rgb(FILE * out, int width, int height, char ** data,
		 int line_length, char * prefix)
{
    int x, y;
    char * line;
    int written = 0;

    for (y = 0; y < height; y++)
    {
	line = data[y];

	for (x = 0; x < width; x++)
	{
	    if (x % 4 == 3)
		continue;

	    if (written == 0 && prefix)
	    {
		fputs(prefix, out);
	    }
	    putc(hexdigit[(int)(line[x] >> 4) & 0x0F], out);
	    putc(hexdigit[(int)(line[x] & 0x0F)], out);
	    written += 2;

	    if (written > line_length)
	    {
		putc('\n', out);
		written = 0;
	    }
	}
    }

    if (written)
	putc('\n', out);
}

static void
write_ps_hex_gray(FILE * out, int width, int height, char ** data,
		  int line_length, char * prefix)
{
    int x, y;
    char * line;
    int written = 0;

    for (y = 0; y < height; y++)
    {
	line = data[y];

	for (x = 0; x < width; x++)
	{
	    if (written == 0 && prefix)
	    {
		fputs(prefix, out);
	    }
	    putc(hexdigit[(int)(line[x] >> 4) & 0x0F], out);
	    putc(hexdigit[(int)(line[x] & 0x0F)], out);
	    written += 2;

	    if (written > line_length)
	    {
		putc('\n', out);
		written = 0;
	    }
	}
    }

    if (written)
	putc('\n', out);
}


PyObject *
skimage_write_ps_hex(PyObject * self, PyObject * args)
{
    PyObject * pyfile;
    ImagingObject * imobj;
    int line_length = 80;
    char * prefix = NULL;

    if (!PyArg_ParseTuple(args, "OO!|is", &imobj, &PyFile_Type, &pyfile,
			  &line_length, &prefix))
	return NULL;

    
    line_length = line_length - 2;
    if (line_length < 0)
	line_length = 0;
    if (imobj->image->pixelsize == 4)
	write_ps_hex_rgb(PyFile_AsFile(pyfile), imobj->image->linesize,
			 imobj->image->ysize, imobj->image->image,
			 line_length, prefix);
    else if (imobj->image->pixelsize == 1)
	write_ps_hex_gray(PyFile_AsFile(pyfile), imobj->image->linesize,
			  imobj->image->ysize, imobj->image->image,
			  line_length, prefix);

    Py_INCREF(Py_None);
    return Py_None;
}

