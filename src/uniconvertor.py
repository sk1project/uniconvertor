#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor E. Novikov
# Copyright (C) 1997, 1998, 1999, 2000, 2002, 2006 by Bernhard Herzog
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in sK1 root directory.

'''
USAGE: uniconvertor.sh [INPUT FILE] [OUTPUT FILE]

Converts one vector graphics format to another using sK1 engine.

 Allowed input formats:
     AI  - Adobe Illustrator files (postscript based)
     CDR - CorelDRAW Graphics files (7-X3 versions)
     CMX - Corel Presentation Exchange files (CMX1 format)
     SVG - Scalable Vector Graphics files
     FIG - XFig files
     CGM - Computer Graphics Metafile files
     AFF - Draw files
     WMF - Windows Metafile files
     SK  - Sketch/Skencil files
     SK1 - sK1 vector graphics files

 Allowed output formats:
     AI  - Adobe Illustrator files (postscript based)
     SVG - Scalable Vector Graphics files
     CGM - Computer Graphics Metafile files
     WMF - Windows Metafile files
     SK  - Sketch/Skencil files
     SK1 - sK1 vector graphics files

Example: uniconvertor.sh drawing.cdr drawing.svg\n
'''


import sys, os

if sys.argv[1]=='--help':
	print __doc__
	sys.exit(0)
if not os.path.isfile(sys.argv[1]):
	print '\nERROR: %s file is not found!\n' % sys.argv[1]
	sys.exit(1)
if len(sys.argv) != 3:
	print '\nERROR: incorrect arguments!\n'
	print __doc__
	sys.exit(1)

from app.io import load
from app.plugins import plugins
import app

app.init_lib()

doc = load.load_drawing(sys.argv[1])
extension = os.path.splitext(sys.argv[2])[1]
fileformat = plugins.guess_export_plugin(extension)
if fileformat:
	saver = plugins.find_export_plugin(fileformat)
	saver(doc, sys.argv[2])
else:
	sys.stderr.write('ERROR: unrecognized extension %s\n' % extension)
	sys.exit(1)
doc.Destroy()
sys.exit(0)