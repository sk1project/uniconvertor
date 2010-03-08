# Sketch - A Python-based interactive drawing program
# export_raster script
# Copyright (C) 1999, 2000, 2002, 2003 by Bernhard Herzog
# 6.12.2000 improved by Bernhard Reiter with Help form Bernhard
#    (used create_star.py by Tamito KAJIYAMA as an example to
#   build the dialog)
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

# Export Sketch drawings as raster images using ghostscript to render
# them
#
# This script adds the following to the Script menu:
#
# Export Raster         Renders the drawing on a white background
#
# You can add more with fixed parameters, if you need them frequently
# see the comments below, one example is enabled.
#
# Both commands prompt for a filename. The output file format is
# determined by the filename extension and should be something your PIL
# installation can handle. For the alpha version this should be PNG or
# some other format that can handle an alpha channel.
#

import os, tempfile

from sk1libs import imaging.Image, imaging.ImageChops

import app.Scripting
from app import _, PostScriptDevice

# for parameter dialogs
from app.UI.sketchdlg import SKModal
from Tkinter import *

class CreateRasterParametersDlg(SKModal):
	"Create Tk Dialog to ask for raster parameters."
	title = _("Choose Raster Parameters")

	def build_dlg(self):
		self.var_ppi = IntVar(self.top)
		self.var_ppi.set(72)
		label = Label(self.top, text=_("ppi"))
		label.grid(column=0, row=0, sticky=E)
		entry = Entry(self.top, width=15, textvariable=self.var_ppi)
		entry.grid(column=1, row=0)

		self.var_alpha = BooleanVar(self.top)
		self.var_alpha.set(1)
		label = Label(self.top, text=_("w. Transparency"))
		label.grid(column=0, row=1, sticky=E)
		entry = Checkbutton(self.top, variable=self.var_alpha)
		entry.grid(column=1, row=1)

		self.var_use_bbox = BooleanVar(self.top)
		self.var_use_bbox.set(0)
		label = Label(self.top, text=_("use BB information"))
		label.grid(column=0, row=2, sticky=E)
		entry = Checkbutton(self.top, variable=self.var_use_bbox)
		entry.grid(column=1, row=2)


		button = Button(self.top, text=_("OK"), command=self.ok)
		button.grid(column=0, row=3, sticky=W)
		button = Button(self.top, text=_("Cancel"), command=self.cancel)
		button.grid(column=1, row=3, sticky=E)

	def ok(self):
		self.close_dlg((self.var_ppi.get(),
						self.var_alpha.get(),self.var_use_bbox.get()))

def export_raster_more_interactive(context, alpha = 0, use_bbox = 0,
									render_ppi=72):
	"Get Parameter per dialog and run export_raster_interactive()"
	parms = CreateRasterParametersDlg(context.application.root).RunDialog()
	if parms is None:
		return
	else:
		render_ppi=parms[0]
		alpha=parms[1]
		use_bbox=parms[2]

		return export_raster_interactive(context,alpha,use_bbox,render_ppi)


def make_ps(document):
	file = tempfile.mktemp('.ps')
	device = PostScriptDevice(file, as_eps = 0, document = document)
	document.Draw(device)
	device.Close()
	return file


def render_ps(filename, resolution, width, height, orig_x = 0, orig_y = 0,
				prolog = '', antialias = '', gsdevice = 'ppmraw'):
	if prolog:
		prolog = '-c ' + '"' + prolog + '"'

	if antialias:
		antialias = ("-dTextAlphaBits=%d -dGraphicsAlphaBits=%d"
						% (antialias, antialias))
	else:
		antialias = ""

	orig_x = -orig_x
	orig_y = -orig_y

	temp = tempfile.mktemp()

	try:
		gs_cmd = ('gs -dNOPAUSE -g%(width)dx%(height)d -r%(resolution)d '
					'-sOutputFile=%(temp)s %(antialias)s '
					'-sDEVICE=%(gsdevice)s -q %(prolog)s '
					'-c %(orig_x)f %(orig_y)f translate '
					'-f%(filename)s -c quit')
		gs_cmd = gs_cmd % locals()

		os.system(gs_cmd)
		image = imaging.Image.open(temp)
		image.load()
		return image
	finally:
		try:
			os.unlink(temp)
		except:
			pass


def export_raster(context, filename, resolution, use_bbox, format = None,
					antialias = None):
	# instead of the page size one could also use the bounding box
	# (returned by the BoundingRect method).
	if use_bbox:
		left, bottom, right, top = context.document.BoundingRect()
		width = right - left
		height = top - bottom
		x = left; y = bottom
	else:
		width, height = context.document.PageSize()
		x = y = 0
	width = round(width * resolution / 72.0)
	height = round(height * resolution / 72.0)

	temp = make_ps(context.document)
	try:
		image = render_ps(temp, resolution, width, height,
							orig_x = x, orig_y = y, antialias = antialias)
	finally:
		os.unlink(temp)
	image.save(filename, format = format)


alpha_prolog = "/setrgbcolor {pop pop pop 0 0 0 setrgbcolor} bind def \
/setgray { pop 0 setgray} bind def \
/setcmykcolor { pop pop pop pop 0 0 0 1.0 setcmykcolor} bind def "

def export_alpha(context, filename, resolution, use_bbox = 0):
	if use_bbox:
		left, bottom, right, top = context.document.BoundingRect()
		width = right - left
		height = top - bottom
		x = left; y = bottom
	else:
		width, height = context.document.PageSize()
		x = y = 0

	ps = make_ps(context.document)

	width = round(width * resolution / 72.0)
	height = round(height * resolution / 72.0)
	rgb = render_ps(ps, resolution, width, height,
					orig_x = x, orig_y = y, antialias = 2)
	alpha = render_ps(ps, resolution, width, height,
						orig_x = x, orig_y = y, antialias = 2,
						prolog = alpha_prolog, gsdevice = 'pgmraw')

	alpha = imaging.ImageChops.invert(alpha)

	rgb = rgb.convert('RGBA')
	rgb.putalpha(alpha)
	rgb.save(filename)



filelist = [(_("Portable Pixmap"), '.ppm'),
			(_("Portable Graymap"), '.pgm'),
			(_("Jpeg"),   '.jpg'),
			(_("Portable Network Graphics"), '.png')]

def export_raster_interactive(context, alpha = 0, use_bbox = 0, render_ppi=72):
	# popup a filedialog and export the document

	doc = context.document

	# construct the tk filetypes list
	extensions = {}
	for text, ext in filelist:
		extensions[ext] = 1

	# determine a default filename
	basename = os.path.splitext(doc.meta.filename)[0]
	if alpha:
		default_ext = '.png'
		# shift png up in filetypes so it is displayed accordingly
		filetypes=tuple(filelist[-1:]+filelist[1:-1])
	else:
		default_ext = '.ppm'
		filetypes=tuple(filelist)

	filename = context.application.GetSaveFilename(
		title = _("Export Raster"),
		filetypes = filetypes,
		initialdir = doc.meta.directory,
		initialfile = basename + default_ext)
	if filename:
		ext = os.path.splitext(filename)[1]
		if extensions.has_key(ext):
			if alpha:
				export_alpha(context, filename, render_ppi, use_bbox)
			else:
				export_raster(context, filename, render_ppi, use_bbox)
		else:
			message = _("unknown extension %s") % ext
			context.application.MessageBox(title = _("Export Raster"),
											message = message)




app.Scripting.AddFunction('export_raster', _("Export Raster"),
								export_raster_more_interactive,
								script_type = app.Scripting.AdvancedScript)
#app.Scripting.AddFunction('export_raster', 'Export Raster Alpha (Default)',
#                             export_raster_interactive, args = (1,0),
#                             script_type = app.Scripting.AdvancedScript)
app.Scripting.AddFunction('export_raster',
								_("Export Raster Alpha (100ppi)"),
								export_raster_interactive, args = (1,0,100),
								script_type = app.Scripting.AdvancedScript)
#app.Scripting.AddFunction('export_raster', 'Export Raster Alpha (120ppi)',
#                             export_raster_interactive, args = (1,0,120),
#                             script_type = app.Scripting.AdvancedScript)
