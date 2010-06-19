#! /usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2010 by Igor E. Novikov
#
# This library is covered by GNU Library General Public License.
# For more info see COPYRIGHTS file in root directory.

from sk1libs.utils import system

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
("All Files",'*'),
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
	if system.get_os_family()==system.MACOSX:	
		pass	
	elif system.get_os_family()==system.WINDOWS:
		pass
	
	else:	
		from uc_gtk import UniConvw
		
		application = UniConvw(OPTIONS,IMPORTFILETYPES)
		application.main()