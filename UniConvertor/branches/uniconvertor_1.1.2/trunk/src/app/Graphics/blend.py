# -*- coding: utf-8 -*-

# Copyright (C) 2003-2006 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.


#
#	blend function
#

from app import Trafo, SketchError, _sketch

class MismatchError(SketchError):
	pass

def Blend(obj1, obj2, frac1, frac2 = None):
	if frac2 is None:
		frac2 = 1.0 - frac1
	try:
		return obj1.Blend(obj2, frac1, frac2)
	except MismatchError:
		pass
	try:
		return obj2.Blend(obj1, frac2, frac1)
	except MismatchError:
		pass
	try:
		from bezier import PolyBezier
		if not isinstance(obj1,PolyBezier) and not isinstance(obj2,PolyBezier)\
			and obj1.is_curve and obj2.is_curve:
			paths = BlendPaths(obj1.Paths(), obj2.Paths(), frac1, frac2)
			properties = Blend(obj1.Properties(), obj2.Properties(), frac1, frac2)
			return PolyBezier(paths = paths, properties = properties)
	except AttributeError, value:
		if str(value) != 'is_curve':
			raise
	
	return obj1.Duplicate()


def BlendTrafo(t1, t2, frac1, frac2):
	return Trafo(frac1 * t1.m11 + frac2 * t2.m11,
					frac1 * t1.m21 + frac2 * t2.m21,
					frac1 * t1.m12 + frac2 * t2.m12,
					frac1 * t1.m22 + frac2 * t2.m22,
					frac1 * t1.v1  + frac2 * t2.v1,
					frac1 * t1.v2  + frac2 * t2.v2)

def BlendPaths(paths1, paths2, frac1, frac2):
		length = min((len(paths1), len(paths2)))
		paths = [None] * length
		blend_paths = _sketch.blend_paths
		for i in range(length):
			paths[i] = blend_paths(paths1[i], paths2[i], frac1, frac2)
		return tuple(paths)
