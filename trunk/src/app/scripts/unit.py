#
#  unit.py - a module for unit conversion
#            Tamito KAJIYAMA <26 March 2000>
# Copyright (C) 2000 by Tamito KAJIYAMA
# Copyright (C) 2000 by Bernhard Herzog
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

import re
import string
from app.Lib.units import unit_dict

def convert(s):
	"Convert S (representing a value and unit) into a value in point."
	match = re.search('[^0-9]+$', s)
	if match:
		value, unit = s[:match.start()], s[match.start():]
		value = string.atof(value)
		unit = string.strip(unit)
		if unit_dict.has_key(unit):
			value = value * unit_dict[unit]
		elif unit:
			raise ValueError, "unsupported unit: " + unit
	else:
		value = string.atof(s)
	return value
