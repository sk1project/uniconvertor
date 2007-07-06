/* Sketch - A Python-based interactive drawing program
 * Copyright (C) 1997, 1998 by Bernhard Herzog
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
 *
 * This file is based on code from GTK which was distributed under the
 * GNU Library General Public License and came with the following
 * notice:
 *
 * GTK - The GIMP Toolkit
 * Copyright (C) 1995-1997 Peter Mattis, Spencer Kimball and Josh MacDonald
 */

#include <Python.h>
#include "skcolor.h"

/* initialize dither info. Assumes PseudoColor visual */

void
skvisual_init_dither(SKVisualObject * self)
{
    int i, j, k;
    unsigned char low_shade, high_shade;
    unsigned short index;
    long red_mult, green_mult;
    double red_matrix_width;
    double green_matrix_width;
    double blue_matrix_width;
    double gray_matrix_width;
    double red_colors_per_shade;
    double green_colors_per_shade;
    double blue_colors_per_shade;
    double gray_colors_per_shade;
    int shades_r, shades_g, shades_b, shades_gray;
    SKDitherInfo *red_ordered_dither;
    SKDitherInfo *green_ordered_dither;
    SKDitherInfo *blue_ordered_dither;
    SKDitherInfo *gray_ordered_dither;
    unsigned char ***dither_matrix;
    unsigned char DM[8][8] =
    {
	{ 0,  32, 8,  40, 2,  34, 10, 42 },
	{ 48, 16, 56, 24, 50, 18, 58, 26 },
	{ 12, 44, 4,  36, 14, 46, 6,  38 },
	{ 60, 28, 52, 20, 62, 30, 54, 22 },
	{ 3,  35, 11, 43, 1,  33, 9,  41 },
	{ 51, 19, 59, 27, 49, 17, 57, 25 },
	{ 15, 47, 7,  39, 13, 45, 5,  37 },
	{ 63, 31, 55, 23, 61, 29, 53, 21 }
    };

  
    shades_r = self->shades_r;
    shades_g = self->shades_g;
    shades_b = self->shades_b;
    shades_gray = self->shades_gray;

    red_mult = shades_g * shades_b;
    green_mult = shades_b;

    red_colors_per_shade = 255.0 / (shades_r - 1);
    red_matrix_width = red_colors_per_shade / 64;

    green_colors_per_shade = 255.0 / (shades_g - 1);
    green_matrix_width = green_colors_per_shade / 64;

    blue_colors_per_shade = 255.0 / (shades_b - 1);
    blue_matrix_width = blue_colors_per_shade / 64;

    gray_colors_per_shade = 255.0 / (shades_gray - 1);
    gray_matrix_width = gray_colors_per_shade / 64;

    /*  alloc the ordered dither arrays for accelerated dithering  */

    self->dither_red  = PyMem_NEW(SKDitherInfo, 256);
    self->dither_green= PyMem_NEW(SKDitherInfo, 256);
    self->dither_blue = PyMem_NEW(SKDitherInfo, 256);
    self->dither_gray = PyMem_NEW(SKDitherInfo, 256);

    red_ordered_dither  = self->dither_red;
    green_ordered_dither= self->dither_green;
    blue_ordered_dither = self->dither_blue;
    gray_ordered_dither = self->dither_gray;

    dither_matrix = PyMem_NEW(unsigned char**, 8);
    for (i = 0; i < 8; i++)
    {
	dither_matrix[i] = PyMem_NEW(unsigned char*, 8);
	for (j = 0; j < 8; j++)
	    dither_matrix[i][j] = PyMem_NEW(unsigned char, 65);
    }

    self->dither_matrix = dither_matrix;

    /*  setup the ordered_dither_matrices  */
    for (i = 0; i < 8; i++)
	for (j = 0; j < 8; j++)
	    for (k = 0; k <= 64; k++)
		dither_matrix[i][j][k] = (DM[i][j] < k) ? 1 : 0;

    /* setup arrays containing three bytes of information for red, green
     * and blue
     *
     *  the arrays contain :
     *    1st byte:    low end shade value
     *    2nd byte:    high end shade value
     *    3rd & 4th bytes:    ordered dither matrix index
     */

    for (i = 0; i < 256; i++)
    {

	/*  setup the red information  */
	low_shade = (unsigned char) (i / red_colors_per_shade);
	if (low_shade == (shades_r - 1))
	    low_shade--;
	high_shade = low_shade + 1;

	index = (unsigned short)
	    (((double) i - low_shade * red_colors_per_shade) /
	     red_matrix_width);

	low_shade *= red_mult;
	high_shade *= red_mult;

	red_ordered_dither[i].s[1] = index;
	red_ordered_dither[i].c[0] = low_shade;
	red_ordered_dither[i].c[1] = high_shade;

	/*  setup the green information  */
	low_shade = (unsigned char) (i / green_colors_per_shade);
	if (low_shade == (shades_g - 1))
	    low_shade--;
	high_shade = low_shade + 1;

	index = (unsigned short)
	    (((double) i - low_shade * green_colors_per_shade) /
	     green_matrix_width);

	low_shade *= green_mult;
	high_shade *= green_mult;

	green_ordered_dither[i].s[1] = index;
	green_ordered_dither[i].c[0] = low_shade;
	green_ordered_dither[i].c[1] = high_shade;

	/*  setup the blue information  */
	low_shade = (unsigned char) (i / blue_colors_per_shade);
	if (low_shade == (shades_b - 1))
	    low_shade--;
	high_shade = low_shade + 1;

	index = (unsigned short)
	    (((double) i - low_shade * blue_colors_per_shade) /
	     blue_matrix_width);

	blue_ordered_dither[i].s[1] = index;
	blue_ordered_dither[i].c[0] = low_shade;
	blue_ordered_dither[i].c[1] = high_shade;

	/*  setup the gray information */
	low_shade = (unsigned char) (i / gray_colors_per_shade);
	if (low_shade == (shades_gray - 1))
	    low_shade--;
	high_shade = low_shade + 1;

	index = (unsigned short)
	    (((double) i - low_shade * gray_colors_per_shade) /
	     gray_matrix_width);

	gray_ordered_dither[i].s[1] = index;
	gray_ordered_dither[i].c[0] = self->cube_size + low_shade;
	gray_ordered_dither[i].c[1] = self->cube_size + high_shade;
    }
}
