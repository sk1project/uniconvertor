#!/usr/bin/env python
#
# Setup script for UniConvertor 1.x
#
# Copyright (C) 2007-2014 Igor E. Novikov
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA
#

"""
Usage: 
--------------------------------------------------------------------------
 to build package:   python setup.py build
 to install package:   python setup.py install
--------------------------------------------------------------------------
 to create source distribution:   python setup.py sdist
--------------------------------------------------------------------------
 to create binary RPM distribution:  python setup.py bdist_rpm
--------------------------------------------------------------------------
 to create binary DEB distribution:  python setup.py bdist_deb
--------------------------------------------------------------------------
 to force compiling against LCMS2 use flag --lcms2 
 to force compiling against LCMS1 use flag --lcms1 
 By default build script tries to detect lcms2.h to choise LCMS version
--------------------------------------------------------------------------
 Help on available distribution formats: --help-formats
"""

import os, sys

import libutils
from libutils import make_source_list, DEB_Builder


############################################################
#
# Flags
#
############################################################
UPDATE_MODULES = False
DEB_PACKAGE = False
CLEAR_BUILD = False
LCMS2 = False

############################################################
#
# Package description
#
############################################################
NAME = 'uniconvertor'
VERSION = '1.2.0pre1'
DESCRIPTION = 'Universal vector graphics translator'
AUTHOR = 'Igor E. Novikov'
AUTHOR_EMAIL = 'igor.e.novikov@gmail.com'
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL
LICENSE = 'LGPL v2'
URL = 'http://sk1project.org'
DOWNLOAD_URL = URL
CLASSIFIERS = [
'Development Status :: 6 - Mature',
'Environment :: Console',
'Intended Audience :: End Users/Desktop',
'License :: OSI Approved :: LGPL v2',
'Operating System :: POSIX',
'Operating System :: MacOS :: MacOS X',
'Operating System :: Microsoft :: Windows',
'Programming Language :: Python',
'Programming Language :: C',
"Topic :: Multimedia :: Graphics :: Graphics Conversion",
]
LONG_DESCRIPTION = '''
UniConvertor is a multiplatform universal vector graphics translator.
Uses sK1 model to convert one format to another. 

sK1 Project (http://sk1project.org),
Copyright (C) 2007-2014 by Igor E. Novikov
--------------------------------------------------------------------------------
Supported input formats:  
 CDR, CDT, CCX, CDRX, CMX, AI, PS, EPS, CGM, WMF, XFIG, SVG, SK, SK1, 
 AFF, PLT, DXF, DST, PES, EXP, PCS
--------------------------------------------------------------------------------
Supported output formats: 
 AI, SVG, SK, SK1, CGM, WMF, PDF, PS, PLT    
--------------------------------------------------------------------------------
'''
LONG_DEB_DESCRIPTION = ''' .
 UniConvertor is a multiplatform universal vector graphics translator.
 Uses sK1 model to convert one format to another. 
 . 
 sK1 Project (http://sk1project.org),
 Copyright (C) 2007-2014 by Igor E. Novikov 
 .
 Supported input formats:  
 CDR, CDT, CCX, CDRX, CMX, AI, PS, EPS, CGM, WMF, XFIG, SVG, SK, SK1, 
 AFF, PLT, DXF, DST, PES, EXP, PCS
 .
 Supported output formats: 
 AI, SVG, SK, SK1, CGM, WMF, PDF, PS, PLT
 .
'''

############################################################
#
# Build data
#
############################################################
src_path = 'src'
pkg_path = os.path.join(src_path, 'uniconvertor')
include_path = '/usr/include'
modules = []
scripts = ['src/script/uniconvertor', ]
deb_scripts = ['debian/postinst', 'debian/postrm']
data_files = []
deb_depends = 'libfreetype6, python (>=2.4), python (<<3.0), python-imaging'
deb_depends += ', python-reportlab'

if os.path.isfile(os.path.join(include_path, 'lcms2.h')): LCMS2 = True

package_data = {
'uniconvertor':libutils.get_resources(pkg_path, pkg_path + '/share'),
'uniconvertor.cms': ['profiles/*.*'],
'uniconvertor.ft2engine': ['fallback_fonts/*.*'],
'uniconvertor.app': ['VERSION', ],
'uniconvertor.app.modules': ['descr.txt', ],
'uniconvertor.filters': ['import/*.py', 'export/*.py',
						'parsing/*.py', 'preview/*.py'],
}

############################################################
#
# Main build procedure
#
############################################################

if len(sys.argv) == 1:
	print 'Please specify build options!'
	print __doc__
	sys.exit(0)

if len(sys.argv) > 1:
	if sys.argv[1] == 'bdist_rpm':
		CLEAR_BUILD = True

	if sys.argv[1] == 'build_update':
		UPDATE_MODULES = True
		CLEAR_BUILD = True
		sys.argv[1] = 'build'

	if sys.argv[1] == 'bdist_deb':
		DEB_PACKAGE = True
		CLEAR_BUILD = True
		sys.argv[1] = 'build'

	if len(sys.argv) > 2 and '--lcms2' in sys.argv:
		LCMS2 = True
		sys.argv.remove('--lcms2')

	if len(sys.argv) > 2 and '--lcms1' in sys.argv:
		LCMS2 = False
		sys.argv.remove('--lcms1')


from distutils.core import setup, Extension

macros = [('MAJOR_VERSION', '1'), ('MINOR_VERSION', '0')]

filter_src = os.path.join(src_path, 'uniconvertor', 'modules', 'filter')
files = ['streamfilter.c', 'filterobj.c', 'linefilter.c',
		'subfilefilter.c', 'base64filter.c', 'nullfilter.c',
		'stringfilter.c', 'binfile.c', 'hexfilter.c']
files = make_source_list(filter_src, files)
filter_module = Extension('uniconvertor.app.modules.streamfilter',
		define_macros=macros, sources=files)
modules.append(filter_module)

type1mod_src = os.path.join(src_path, 'uniconvertor', 'modules', 'type1mod')
files = make_source_list(type1mod_src, ['_type1module.c', ])
type1mod_module = Extension('uniconvertor.app.modules._type1',
		define_macros=macros, sources=files)
modules.append(type1mod_module)

skread_src = os.path.join(src_path, 'uniconvertor', 'modules', 'skread')
files = make_source_list(skread_src, ['skreadmodule.c', ])
skread_module = Extension('uniconvertor.app.modules.skread',
		define_macros=macros, sources=files)
modules.append(skread_module)

pstokenize_src = os.path.join(src_path, 'uniconvertor', 'modules', 'pstokenize')
files = make_source_list(pstokenize_src, ['pstokenize.c', 'pschartab.c'])
pstokenize_module = Extension('uniconvertor.app.modules.pstokenize',
		define_macros=macros, sources=files)
modules.append(pstokenize_module)

skmod_src = os.path.join(src_path, 'uniconvertor', 'modules', 'skmod')
files = ['_sketchmodule.c', 'skpoint.c', 'skcolor.c', 'sktrafo.c', 'skrect.c',
		'skfm.c', 'curvefunc.c', 'curveobject.c', 'curvelow.c', 'curvemisc.c',
		'skaux.c', 'skimage.c', ]
files = make_source_list(skmod_src, files)
skmod_module = Extension('uniconvertor.app.modules._sketch',
		define_macros=macros, sources=files)
modules.append(skmod_module)

cms_src = os.path.join(src_path, 'uniconvertor', 'cms')
libs = ['lcms2', ]
if LCMS2:
 	files = make_source_list(cms_src, ['_cms2.c', ])
	deb_depends = 'liblcms2, ' + deb_depends
else:
 	files = make_source_list(cms_src, ['_cms.c', ])
	deb_depends = 'liblcms1, ' + deb_depends
	libs = ['lcms', ]

cms_module = Extension('uniconvertor.cms._cms',
		define_macros=macros, sources=files,
		libraries=libs, extra_compile_args=["-Wall"])
modules.append(cms_module)

ft2_src = os.path.join(src_path, 'uniconvertor', 'ft2engine')
files = make_source_list(ft2_src, ['ft2module.c', ])
ft2_module = Extension('uniconvertor.ft2engine.ft2',
		define_macros=macros, sources=files,
		include_dirs=['/usr/include/freetype2'], libraries=['freetype'],
		extra_compile_args=["-Wall"])
modules.append(ft2_module)

setup(name=NAME,
	version=VERSION,
	description=DESCRIPTION,
	author=AUTHOR,
	author_email=AUTHOR_EMAIL,
	maintainer=MAINTAINER,
	maintainer_email=MAINTAINER_EMAIL,
	license=LICENSE,
	url=URL,
	download_url=DOWNLOAD_URL,
	long_description=LONG_DESCRIPTION,
	classifiers=CLASSIFIERS,
	packages=libutils.get_source_structure(),
	package_dir=libutils.get_package_dirs(),
	package_data=package_data,
	data_files=data_files,
	scripts=scripts,
	ext_modules=modules)

#################################################
# .py source compiling
#################################################
libutils.compile_sources()


##############################################
# This section for developing purpose only
# Command 'python setup.py build_update' allows
# automating build and native extension copying
# into package directory
##############################################
if UPDATE_MODULES: libutils.copy_modules(modules)


#################################################
# Implementation of bdist_deb command
#################################################
if DEB_PACKAGE:
	bld = DEB_Builder(name=NAME,
					version=VERSION,
					maintainer='%s <%s>' % (AUTHOR, AUTHOR_EMAIL),
					depends=deb_depends,
					homepage=URL,
					description=DESCRIPTION,
					long_description=LONG_DEB_DESCRIPTION,
					package_dirs=libutils.get_package_dirs(),
					package_data=package_data,
					scripts=scripts,
					data_files=data_files,
					deb_scripts=deb_scripts)
	bld.build()

if CLEAR_BUILD: libutils.clear_build()

