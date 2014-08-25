#!/usr/bin/env python
#
# Setup script for UniConvertor
#
# Copyright (C) 2007-2010 Igor E. Novikov
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
# Usage:
# --------------------------------------------------------------------------
#  to build package:   python setup.py build
#  to install package:   python setup.py install
# --------------------------------------------------------------------------
#  to create source distribution:   python setup.py sdist
# --------------------------------------------------------------------------
#  to create binary RPM distribution:  python setup.py bdist_rpm
# --------------------------------------------------------------------------
#  to create binary DEB package:  python setup.py bdist_deb
# --------------------------------------------------------------------------
#  to create Win32 distribution:   python setup.py bdist_wininst
# --------------------------------------------------------------------------
#  help on available distribution formats: python setup.py bdist --help-formats
#

from distutils.core import setup, Extension
import sys, os


COPY = True
DEBIAN = False
VERSION = '1.1.6pre'

########################
#
# Main build procedure
#
########################

if __name__ == "__main__":

	if len(sys.argv) > 1 and sys.argv[1] == 'build&copy':
		COPY = True
		sys.argv[1] = 'build'

	if len(sys.argv) > 1 and sys.argv[1] == 'bdist_deb':
		DEBIAN = True
		sys.argv[1] = 'build'


	src = 'src/uniconvertor/'

	filter_src = src + 'modules/filter/'
	filter_module = Extension('uniconvertor.app.modules.streamfilter',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '1')],
			sources=[filter_src + 'streamfilter.c', filter_src + 'filterobj.c', filter_src + 'linefilter.c',
					filter_src + 'subfilefilter.c', filter_src + 'base64filter.c', filter_src + 'nullfilter.c',
					filter_src + 'stringfilter.c', filter_src + 'binfile.c', filter_src + 'hexfilter.c'])

 	type1mod_src = src + 'modules/type1mod/'
	type1mod_module = Extension('uniconvertor.app.modules._type1',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '1')],
			sources=[type1mod_src + '_type1module.c'])

 	skread_src = src + 'modules/skread/'
	skread_module = Extension('uniconvertor.app.modules.skread',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '1')],
			sources=[skread_src + 'skreadmodule.c'])

 	pstokenize_src = src + 'modules/pstokenize/'
	pstokenize_module = Extension('uniconvertor.app.modules.pstokenize',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '1')],
			sources=[pstokenize_src + 'pstokenize.c', pstokenize_src + 'pschartab.c'])

 	skmod_src = src + 'modules/skmod/'
	skmod_module = Extension('uniconvertor.app.modules._sketch',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '1')],
			sources=[skmod_src + '_sketchmodule.c', skmod_src + 'skpoint.c', skmod_src + 'skcolor.c',
					skmod_src + 'sktrafo.c', skmod_src + 'skrect.c', skmod_src + 'skfm.c',
					skmod_src + 'curvefunc.c', skmod_src + 'curveobject.c', skmod_src + 'curvelow.c',
					skmod_src + 'curvemisc.c', skmod_src + 'skaux.c', skmod_src + 'skimage.c', ])

 	ft2_src = src + 'ft2engine/'
	ft2_module = Extension('uniconvertor.ft2engine.ft2',
			define_macros=[('MAJOR_VERSION', '1'),
						('MINOR_VERSION', '0')],
			sources=[ft2_src + 'ft2module.c'],
			include_dirs=['/usr/include/freetype2'],
			libraries=['freetype'],
			extra_compile_args=["-Wall"])

	setup (name='uniconvertor',
			version=VERSION,
			description='Universal vector graphics translator',
			author='Igor E. Novikov',
			author_email='igor.e.novikov@gmail.com',
			maintainer='Igor E. Novikov',
			maintainer_email='igor.e.novikov@gmail.com',
			license='LGPL v2, GPL v2 (some packages)',
			url='http://sk1project.org',
			download_url='http://sk1project.org/modules.php?name=Products&product=uniconvertor',
			long_description='''
UniConvertor is a multiplatform universal vector graphics translator.
It uses sK1 engine to convert one format to another.

sK1 Team (http://sk1project.org),
Copyright (C) 2007-2010 by Igor E. Novikov
------------------------------------------------------------------------------------

Import filters: 
    * CorelDRAW ver.7-X3,X4 (CDR/CDT/CCX/CDRX/CMX)
    * Adobe Illustrator up to 9 ver. (AI postscript based)
    * Postscript (PS)
    * Encapsulated Postscript (EPS)
    * Computer Graphics Metafile (CGM)
    * Windows Metafile (WMF)
    * XFIG
    * Scalable Vector Graphics (SVG)
    * Skencil/Sketch/sK1 (SK and SK1)
    * Acorn Draw (AFF)
    * HPGL for cutting plotter files (PLT)
    * Autocad Drawing Exchange Format (DXF)
    * Design format (Tajima) (DST)
    * Embroidery file format (Brother) (PES)
    * Embroidery file format (Melco) (EXP)
    * Design format (Pfaff home) (PCS)
------------------------------------------------------------------------------------

Export filters: 
    * AI - Postscript based Adobe Illustrator 5.0 format
    * SVG - Scalable Vector Graphics
    * SK - Sketch/Skencil format
    * SK1 - sK1 format
    * CGM - Computer Graphics Metafile
    * WMF - Windows Metafile
    * PDF - Portable Document Format
    * PS  - PostScript
    * PLT - HPGL for cutting plotter files
    
------------------------------------------------------------------------------------
			''',
		classifiers=[
			'Development Status :: 6 - Mature',
			'Environment :: Console',
			'Intended Audience :: End Users/Desktop',
			'License :: OSI Approved :: LGPL v2',
			'License :: OSI Approved :: GPL v2',
			'Operating System :: POSIX',
			'Operating System :: MacOS :: MacOS X',
			'Programming Language :: Python',
			'Programming Language :: C',
			"Topic :: Multimedia :: Graphics :: Graphics Conversion",
			],

			packages=['uniconvertor',
				'uniconvertor.app',
				'uniconvertor.app.Graphics',
				'uniconvertor.app.Lib',
				'uniconvertor.app.Scripting',
				'uniconvertor.app.conf',
				'uniconvertor.app.events',
				'uniconvertor.app.io',
				'uniconvertor.app.managers',
				'uniconvertor.app.modules',
				'uniconvertor.app.scripts',
				'uniconvertor.app.utils',
				'uniconvertor.utils',
				'uniconvertor.ft2engine',
			],

			package_dir={'uniconvertor': 'src/uniconvertor',
			'uniconvertor.app': src + 'app',
			'uniconvertor.app.modules': src + 'app/modules',
#			'uniconvertor.utils': src + 'utils',
#			'uniconvertor.ft2engine': src + 'ft2engine',
			},

			package_data={'uniconvertor.app': ['VERSION'],
			'uniconvertor': ['share/icc/*.*', 'share/fonts/*.*', 'share/ps_templates/*.*'],
			'uniconvertor.app.modules': ['descr.txt', ],
			'uniconvertor.ft2engine': ['fallback_fonts/*.*'],
			},

			scripts=['src/script/uniconvertor'],

			ext_modules=[filter_module, type1mod_module, skread_module, pstokenize_module, skmod_module,
						ft2_module, ])


#################################################
# .py source compiling
#################################################
if sys.argv[1] == 'build':
	import compileall
	compileall.compile_dir('build/')

##############################################
# This section for developing purpose only
# Command 'python setup.py build&copy' allows
# automating build and native extension copying
# into package directory
##############################################

if COPY:
	import shutil, string, platform
	version = (string.split(sys.version)[0])[0:3]

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/app/modules/pstokenize.so', src + 'app/modules/')
	print '\n pstokenize.so has been copied to src/ directory'

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/app/modules/_sketch.so', src + 'app/modules/')
	print '\n _sketchmodule.so has been copied to src/ directory'

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/app/modules/skread.so', src + 'app/modules/')
	print '\n skreadmodule.so has been copied to src/ directory'

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/app/modules/streamfilter.so', src + 'app/modules/')
	print '\n streamfilter.so has been copied to src/ directory'

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/app/modules/_type1.so', src + 'app/modules/')
	print '\n _type1module.so has been copied to src/ directory'

	shutil.copy('build/lib.linux-' + platform.machine() + '-' + version +
			'/uniconvertor/ft2engine/ft2.so', src + 'ft2engine/')
	print '\n ft2.so has been copied to src/ directory'

	os.system('rm -rf build')

#################################################
# Implementation of bdist_deb command
#################################################
if DEBIAN:
	print '\nDEBIAN PACKAGE BUILD'
	print '===================='
	import shutil, string, platform
	version = (string.split(sys.version)[0])[0:3]

	arch, bin = platform.architecture()
	if arch == '64bit':
		arch = 'amd64'
	else:
		arch = 'i386'

	target = 'build/deb-root/usr/lib/python' + version + '/dist-packages'

	if os.path.lexists(os.path.join('build', 'deb-root')):
		os.system('rm -rf build/deb-root')
	os.makedirs(os.path.join('build', 'deb-root', 'DEBIAN'))

	os.system("cat DEBIAN/control |sed 's/<PLATFORM>/" + arch + "/g'|sed 's/<VERSION>/" + VERSION + "/g'> build/deb-root/DEBIAN/control")

	os.makedirs(target)
	os.makedirs('build/deb-root/usr/bin')
	os.system('cp -R build/lib.linux-' + platform.machine() + '-' + version + '/uniconvertor ' + target)
	os.system('cp src/uniconvertor build/deb-root/usr/bin')
	os.system('chmod +x build/deb-root/usr/bin/uniconvertor')

	if os.path.lexists('dist'):
		os.system('rm -rf dist/*.deb')
	else:
		os.makedirs('dist')

	os.system('dpkg --build build/deb-root/ dist/python-uniconvertor-' + VERSION + '_' + arch + '.deb')












