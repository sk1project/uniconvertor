# Sketch - A Python-based interactive drawing program
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

import os
from app import UI, Document, PostScriptDevice
import app.Scripting

def selection_as_document(document):
	# Get a copy of the currently selected objects as a group
	# If no object is selected the method returns None 
	selection = document.CopyForClipboard()

	if selection is not None:
		# create a new document
		seldoc = Document(create_layer = 1)
		# and insert the group
		seldoc.Insert(selection)
		# The group is now the selected object in the document. Ungroup
		# it.
		seldoc.UngroupSelected()
		return seldoc
	return None

def get_ps_filename(context):
	dir = context.document.meta.directory
	if not dir:
		dir = os.getcwd()
	name = context.document.meta.filename
	name, ext = os.path.splitext(name)
	name = name + '.eps'
	app = context.application
	filename = app.GetSaveFilename(title = "Save Selection As PostScript",
									filetypes = UI.skapp.psfiletypes,
									initialdir = dir,
									initialfile = name)
	return filename

def save_selection_as_ps(context):
	seldoc = selection_as_document(context.document)
	if seldoc is not None:
		filename = get_ps_filename(context)
		if filename:
			bbox = seldoc.BoundingRect(visible = 0, printable = 1)
			ps_dev = PostScriptDevice(filename, as_eps = 1,
										bounding_box = tuple(bbox),
										document = seldoc)
			seldoc.Draw(ps_dev)
			ps_dev.Close()

app.Scripting.AddFunction('save_selection_as_ps', 'Save Selection As EPS',
								save_selection_as_ps,
								script_type = app.Scripting.AdvancedScript)

