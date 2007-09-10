#ifndef CURVE_LOW_H
#define CURVE_LOW_H

#include "X11/Xlib.h"

#define BEZIER_DEPTH 5
#define BEZIER_NUM_STEPS ((2 << (BEZIER_DEPTH + 1)) + 1)
#define BEZIER_FILL_LENGTH (BEZIER_NUM_STEPS + 1)

int bezier_fill_points(XPoint * points, int * x, int * y);

int bezier_hit_segment(int * x, int * y, int px, int py);
int bezier_hit_line(int sx, int sy, int ex, int ey, int px, int py);


void bezier_point_at(double *x, double *y, double t,
		     double * result_x, double * result_y);
void bezier_tangent_at(double *x, double *y, double t,
		       double * result_x, double * result_y);

extern int bezier_basis[4][4];

#endif
