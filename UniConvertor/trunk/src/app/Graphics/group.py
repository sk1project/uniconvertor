# Sketch - A Python-based interactive drawing program
# Copyright (C) 1997, 1998 by Bernhard Herzog
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

from app.events.warn import warn_tb, INTERNAL
from app import _

from compound import EditableCompound
from blend import Blend, MismatchError

class Group(EditableCompound):

    is_Group = 1

    def Info(self):
	return _("Group with %d objects") % len(self.objects)

    def Blend(self, other, frac1, frac2):
	try:
	    objs = self.objects
	    oobjs = other.objects
	    blended = []
	    for i in range(min(len(objs), len(oobjs))):
		blended.append(Blend(objs[i], oobjs[i], frac1, frac2))
	    return Group(blended)
	except:
	    warn_tb(INTERNAL)
	    raise MismatchError

    Ungroup = EditableCompound.GetObjects

    def SaveToFile(self, file):
	file.BeginGroup()
	for obj in self.objects:
	    obj.SaveToFile(file)
	file.EndGroup()
