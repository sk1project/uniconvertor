#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2007 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

'''
USAGE: uniconv [INPUT FILE] [OUTPUT FILE]

Converts one vector graphics format to another using sK1 engine.
sK1 Team (http://sk1project.org), copyright (C) 2007 by Igor E. Novikov, Valek Filippov

 Allowed input formats:
     AI  - Adobe Illustrator files (postscript based)
     CDR - CorelDRAW Graphics files (7-X3,X4 versions)
     CDT - CorelDRAW templates files (7-X3 versions)
     CCX - Corel Compressed Exchange files
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

Example: uniconv drawing.cdr drawing.svg\n
'''

import sys, os, string

_pkgdir = __path__[0]
app_dir = os.path.join(_pkgdir, 'app')
app_ver = string.strip(open(os.path.join(app_dir, 'VERSION')).read())

if len(sys.argv)<2 or sys.argv[1]=='--help':
	print '\nUniConvertor',app_ver
	print __doc__
	sys.exit(0)
if not os.path.isfile(sys.argv[1]):
	print '\nERROR: %s file is not found!' % sys.argv[1]
	print '\nUniConvertor',app_ver
	print __doc__
	sys.exit(1)
if len(sys.argv) != 3:
	print '\nERROR: incorrect arguments!'
	print '\nUniConvertor',app_ver
	print __doc__
	sys.exit(1)


sys.path.insert(1, _pkgdir)

from app.io import load
from app.plugins import plugins
import app

app.init_lib()

doc = load.load_drawing(sys.argv[1])
extension = os.path.splitext(sys.argv[2])[1]
plugins.load_plugin_configuration()
fileformat = plugins.guess_export_plugin(extension)
if fileformat:
	saver = plugins.find_export_plugin(fileformat)
	saver(doc, sys.argv[2])
else:
	sys.stderr.write('ERROR: unrecognized extension %s\n' % extension)
	sys.exit(1)
doc.Destroy()
sys.exit(0)
