# -*- coding: utf-8 -*-
#
#	Copyright (C) 2011 by Igor E. Novikov
#	
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#	
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#	
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.

from uc2 import _

#Formats enumeration

ALL_FORMATS = 0

SKX = 1
SK1 = 2
SK = 3

SVG = 5
SVGZ = 6
ODG = 7
ORA = 8
XCF = 9
SLA = 10
FIG = 11


CDR = 50
CDT = 51
CDRZ = 52
CDTZ = 53
CMX = 54
CCX = 55
CDRX = 56

XAR = 66

AI_PS = 70
AI_PDF = 71
PS = 72
EPS = 73
PDF = 74
PSD = 75

CGM = 100
WMF = 101
EMF = 102
XPS = 103
VSD = 104

PLT = 110
HPGL = 111
DXF = 120
DWG = 121

FORMAT_DESCRIPTION = {
ALL_FORMATS : _("All supported formats"),
SKX : _("SKX graphics /sK1 ver.1.0 and Skencil 2.0/"),
SK1 : _("sK1 graphics /ver.0.9 and older/"),
SK : _("Sketch/Skencil files"),
SVG : _("Scalable Vector Graphics files"),
SVGZ : _("Compressed Scalable Vector Graphics files"),
ODG : _("Open Document Drawing files"),
ORA : _("Open Raster Format files"),
XCF : _("GIMP files"),
SLA : _("Scribus documents"),
CDR : _("CorelDRAW Graphics files /7-X3 ver./"),
CDT : _("CorelDRAW Templates files /7-X3 ver./"),
CDRZ : _("CorelDRAW Graphics files /X4-X5 ver./"),
CDTZ : _("CorelDRAW Templates files /X4-X5 ver./"),
CMX : _("CorelDRAW Presentation Exchange files"),
CCX : _("CorelDRAW Compressed Exchange files /CDRX format/"),
CDRX : _("CorelDRAW Compressed Exchange files /CDRX format/"),
XAR : _("Xara graphics files"),
FIG : _("XFig files"),
AI_PS : _("Adobe Illustrator files"),
AI_PDF : _("Adobe Illustrator files"),
PS : _("PostScript files"),
EPS : _("Encapsulated PostScript files"),
PDF : _("Portable Document Format"),
PSD : _("Adobe Photoshop files"),
CGM : _("Computer Graphics Metafile files"),
WMF : _("Windows Metafile files"),
EMF : _("Windows Enhanced Metafile files"),
XPS : _("XML Paper Specification"),
VSD : _("Visio Drawing"),
PLT : _("HPGL cutting plotter files"),
HPGL : _("HPGL plotter files"),
DXF : _("AutoCAD DXF files"),
DWG : _("AutoCAD DWG files"),
}

FORMAT_EXTENSION = {
ALL_FORMATS : '',
SKX : 'skx', SK1 : 'sk1', SK : 'sk',
SVG : 'svg', SVGZ : 'svgz', ODG : 'odg', ORA : 'ora', XCF : 'xcf', SLA : 'sla', FIG : 'fig',
CDR : 'cdr', CDT : 'cdt', CDRZ : 'cdr', CDTZ : 'cdt', CMX : 'cmx', CCX : 'ccx', CDRX : 'cdr',
XAR : 'xar',
AI_PS : 'ai', AI_PDF : 'ai', PS : 'ps', EPS : 'eps', PDF : 'pdf', PSD : 'psd',
CGM : 'cgm', WMF : 'wmf', EMF : 'emf', XPS : 'xps', VSD : 'vsd',
PLT : 'plt', HPGL : 'hgl', DXF : 'dxf', DWG : 'dwg',
}

LOADER_FORMATS = [SKX, SK1, SK]

SAVER_FORMATS = [SKX, SK1, SK]

from skx import SKX_Loader, SKX_Saver
from sk1 import SK1_Loader, SK1_Saver
from sk import SK_Loader, SK_Saver


LOADERS = {
SKX : SKX_Loader, SK1 : SK1_Loader, SK : SK_Loader,
SVG : None, SVGZ : None, ORA : None, XCF : None, SLA : None, FIG : None,
CDR : None, CDT : None, CDRZ : None, CDTZ : None, CMX : None, CCX : None, CDRX : None,
XAR : None,
AI_PS : None, AI_PDF : None, PS : None, EPS : None, PDF : None, PSD : None,
CGM : None, WMF : None, EMF : None, XPS : None, VSD : None,
PLT : None, HPGL : None, DXF : None, DWG : None,
		}

SAVERS = {
SKX : SKX_Saver, SK1 : SK1_Saver, SK : SK_Saver,
SVG : None, SVGZ : None, ORA : None, XCF : None, SLA : None, FIG : None,
CDR : None, CDT : None, CDRZ : None, CDTZ : None, CMX : None, CCX : None, CDRX : None,
XAR : None,
AI_PS : None, AI_PDF : None, PS : None, EPS : None, PDF : None, PSD : None,
CGM : None, WMF : None, EMF : None, XPS : None, VSD : None,
PLT : None, HPGL : None, DXF : None, DWG : None,
}
