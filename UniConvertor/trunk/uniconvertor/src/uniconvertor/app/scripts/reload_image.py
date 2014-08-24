# Sketch - A Python-based interactive drawing program
# Copyright (C) 2002 by Bernhard Herzog
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

"""User Script that reloads the image data of an external image or
updates the preview of an EPS file.
"""

import app
from app import _
import app.Scripting
from app.Graphics import external, eps


def reload_image(context):
	image = context.document.CurrentObject()
	if image is not None and isinstance(image, external.ExternalGraphics):
		# Don't try this at home :) It pokes around in the internals of
		# Sketch!

		olddata = image.data
		filename = olddata.Filename()
		oldrect = image.bounding_rect

		# first, remove the old object from the cache.
		if olddata.stored_in_cache \
			and external.instance_cache.has_key(filename):
			del external.instance_cache[filename]
			olddata.stored_in_cache = 0

		# now we can load the data again the normal way because it's not
		# in the cache anymore.
		if image.is_Eps:
			data = eps.load_eps(filename)
		else:
			data = app.load_image(filename)

		# replace the old data object with the new one. Normally we
		# would have to handle the undo info returned. Here we just
		# discard it so that the reload won't be in the history.
		image.SetData(data)

		# some house keeping tasks that are necessary because the sort
		# of thing we're doing here, i.e. modifying an object without
		# undo information etc., wasn't anticipated:
		
		# to make sure that the bboxes get recomputed etc, call the
		# _changed method. SetData should probably do that
		# automatically, but currently it doesn't
		image._changed()

		# make sure the object itself is properly redrawn
		context.document.AddClearRect(oldrect)
		context.document.AddClearRect(image.bounding_rect)
		
		# make sure the selection's idea of the bounding rect is updated
		# too and have the canvas update the handles
		context.document.selection.ResetRectangle()
		context.main_window.canvas.update_handles()


		
app.Scripting.AddFunction('reload_image', _("Reload Image"),
								reload_image,
								script_type = app.Scripting.AdvancedScript)
