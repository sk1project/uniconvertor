#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2007-2009 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

'''
USAGE: uniconvertor [OPTIONS] [INPUT FILE] [OUTPUT FILE]

Converts one vector graphics format to another using sK1 engine.
sK1 Team (http://sk1project.org), copyright (C) 2007-2009 by Igor E. Novikov

 Allowed input formats:
	 AI  - Adobe Illustrator files (postscript based)
     CDR - CorelDRAW Graphics files (7-X3,X4 versions)
     CDT - CorelDRAW templates files (7-X3,X4 versions)
     CCX - Corel Compressed Exchange files
     CMX - Corel Presentation Exchange files (CMX1 format)
     SVG - Scalable Vector Graphics files
     FIG - XFig files
     CGM - Computer Graphics Metafile files
     AFF - Draw files
     WMF - Windows Metafile files
     SK  - Sketch/Skencil files
     SK1 - sK1 vector graphics files
     PLT - HPGL for cutting plotter files
     DXF - Autocad Drawing Exchange Format
     DST - Design format (Tajima)
     PES - Embroidery file format (Brother)
     EXP - Embroidery file format (Melco)
     PCS - Design format (Pfaff home)
     

 Allowed output formats:
     AI  - Adobe Illustrator files (postscript based)
     SVG - Scalable Vector Graphics files
     CGM - Computer Graphics Metafile files
     WMF - Windows Metafile files
     SK  - Sketch/Skencil files
     SK1 - sK1 vector graphics files
     PDF - Portable Document Format
     PS  - PostScript
     PLT - HPGL for cutting plotter files

Example: uniconvertor drawing.cdr drawing.svg\n

'''

import sys, os, string

def init_uniconv():
	_pkgdir = __path__[0]
	app_dir = os.path.join(_pkgdir, 'app')
	sys.path.insert(1, _pkgdir)

def uniconv_run():	
	_pkgdir = __path__[0]
	app_dir = os.path.join(_pkgdir, 'app')
	app_ver = string.strip(open(os.path.join(app_dir, 'VERSION')).read())

	if len(sys.argv)<3 or sys.argv[1]=='--help':
		print '\nUniConvertor',app_ver
		print __doc__
		sys.exit(0)
		
	options=[]
	input_file=sys.argv[-2]
	output_file=sys.argv[-1]
	
	if len(sys.argv)>3:
		options=sys.argv[1:-2]
		
	if not os.path.isfile(input_file):
		print '\nERROR: %s file is not found!' % input_file
		print '\nUniConvertor',app_ver
		print __doc__
		sys.exit(1)
	
	sys.path.insert(1, _pkgdir)
	
	from app.io import load
	from sk1libs import filters
	import app
	
	app.init_lib()
	
	filters.load_plugin_configuration()
	
	if len(options) and options[0]=='-parse':
		load.parse_drawing(input_file, output_file)
		sys.exit(0)
	else:
		doc = load.load_drawing(input_file)
		extension = os.path.splitext(output_file)[1]
		fileformat = filters.guess_export_plugin(extension)
		if fileformat:
			saver = filters.find_export_plugin(fileformat)
			saver(doc, output_file)
		else:
			sys.stderr.write('ERROR: unrecognized extension %s\n' % extension)
			sys.exit(1)
		doc.Destroy()
	
	sys.exit(0)
