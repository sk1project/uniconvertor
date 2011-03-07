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

SKX = 0
SK1 = 1
SK = 2

SVG = 5
SVGZ = 6
ORA = 7
XCF = 8
SLA = 9
FIG = 10

CDR = 50
CDT = 51
CDRZ = 52
CMX = 53
CCX = 54
CDRX = 55

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
SKX : _("sK1 graphics (ver.1.0 and newer)"),
SK1 : _("sK1 graphics (ver.0.9 and older)"),
SK : _("Sketch\Skencil files"),
SVG : _("Scalable Vector Graphics files"),
SVGZ : _("Compressed Scalable Vector Graphics files"),
ORA : _("Open Raster Format files"),
XCF : _("GIMP files"),
SLA : _("Scribus documents"),
CDR : _("CorelDRAW Graphics files (7-X3 ver.)"),
CDT : _("CorelDRAW Templates files (7-X3 ver.)"),
CDRZ : _("CorelDRAW Graphics files (X4-X5 ver.)"),
CDTZ : _("CorelDRAW Templates files (X4-X5 ver.)"),
CMX : _("CorelDRAW Presentation Exchange files"),
CCX : _("CorelDRAW Compressed Exchange files (CDRX format)"),
CDRX : _("CorelDRAW Compressed Exchange files (CDRX format)"),
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
SKX : ("skx",), SK1 : ("sk1",), SK : ("sk",),
SVG : ("svg",), SVGZ : ("svgz",), ORA : ("ora",), XCF : ("xcf",), SLA : ("sla",),FIG : ("fig",),
CDR : ("cdr",), CDT : ("cdt",), CDRZ : ("cdr",), CMX : ("cmx",), CCX : ("ccx",), CDRX : ("cdr",),
XAR : ("xar",),
AI_PS : ("ai",), AI_PDF : ("ai",), PS : ("ps",), EPS : ("eps",), PDF : ("pdf",), PSD : ("psd",),
CGM : ("cgm",), WMF : ("wmf",), EMF : ("emf",), XPS : ("xps",), VSD : ("vsd",),
PLT : ("plt",), HPGL : ("hgl",), DXF : ("dxf",), DWG : ("dwg",),
}

LOADER_FORMATS = [SKX, SK1, SK]

SAVER_FORMATS = [SKX, SK1, SK]
