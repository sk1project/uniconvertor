#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.
'''
Gtk frontend for UniConvertor.
Converts one vector graphics format to another using sK1 engine.
sK1 Team (http://sk1project.org), copyright (C) 2010 by Igor E. Novikov

USAGE: uniconvw [INPUT FILE]

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

Example: uniconvw drawing.cdr\n

'''

from sk1libs.utils import system
import os, sys, string

OPTIONS=[
('AI - Postscript based Adobe Illustrator 5.0 format', 'ai'),
('SVG - Scalable Vector Graphics', 'svg'),
('SK - Sketch/Skencil format', 'sk'),
('SK1 - sK1 format', 'sk1'),
('CGM - Computer Graphics Metafile', 'cgm'),
('WMF - Windows Metafile', 'wmf'),
('PDF - Portable Document Format', 'pdf'),
('PS  - PostScript', 'ps'),
('PLT - HPGL for cutting plotter files', 'plt'),
]

IMPORTFILETYPES=[
('CorelDRAW Graphics files (7-X4 ver.) - *.cdr','*.cdr'),
('CorelDRAW Templates files (7-X4 ver.) - *.cdt','*.cdt'),
('CorelDRAW Presentation Exchange files - *.cmx','*.cmx'),
('CorelDRAW Compressed Exchange files (CDRX format) - *.ccx','*.ccx'),
('Adobe Illustrator files (up to ver. 9.0) - *.ai','*.ai'),
('Encapsulated PostScript files - *.eps','*.eps'),
('sK1 vector graphics files - *.sk1','*.sk1'),
('Sketch\Skencil files - *.sk','*.sk'),
('PostScript files - *.ps','*.ps'),
('Computer Graphics Metafile files - *.cgm','*.cgm'),
('Scalable Vector Graphics files - *.svg','*.svg'),
('Windows Metafile files - *.wmf','*.wmf'),
('HPGL cutting plotter files - *.plt','*.plt'),
('AutoCAD DXF files - *.dxf','*.dxf'),
('XFig files - *.fig','*.fig'),
('Acorn Draw files - *.aff','*.aff'),
]

def uniconvw_run():	
	file=None
	_pkgdir = __path__[0]
	
	app_ver = string.strip(open(os.path.join(_pkgdir, 'VERSION')).read())
#	 or not os.path.isfile(sys.argv[1])
	if len(sys.argv)>2:
		print 'Incorrect argument!\n\n'
		print '\nuniconvw',app_ver
		print __doc__
		sys.exit(1)
		
	if len(sys.argv)==2 and sys.argv[1]=='--help':
		print '\nuniconvw',app_ver
		print __doc__
		sys.exit(0)
		
	dir=os.path.join(_pkgdir, 'resources')
	
	if system.get_os_family()==system.MACOSX:	
		pass	
	elif system.get_os_family()==system.WINDOWS:
		pass
	
	else:	
		from uc_gtk import UniConvw
		if len(sys.argv)>1 and os.path.isfile(sys.argv[1]): file=sys.argv[1]
		icon=os.path.join(dir,'uniconvw_icon_32.png')
		application = UniConvw(icon,OPTIONS,IMPORTFILETYPES, file=file)
		application.main()