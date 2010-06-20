#!/usr/bin/env python
#
# Setup script for uniconw
#
# Copyright (C) 2010 Igor E. Novikov
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


COPY=False
DEBIAN=False
VERSION='1.0'

########################
#
# Main build procedure
#
########################

if __name__ == "__main__":
		
	if len(sys.argv)>1 and sys.argv[1]=='bdist_deb':
		DEBIAN=True
		sys.argv[1]='build'
		
	setup (name = 'uniconvw',
			version = VERSION,
			description = 'Frontend for UniConvertor vector graphics translator',
			author = 'Igor E. Novikov',
			author_email = 'igor.e.novikov@gmail.com',
			maintainer = 'Igor E. Novikov',
			maintainer_email = 'igor.e.novikov@gmail.com',
			license = 'LGPL v2',
			url = 'http://sk1project.org',
			download_url = 'http://sk1project.org/modules.php?name=Products&product=uniconvertor',
			long_description = '''
uniconvw is a Gtk frontend for UniConvertor. 
UniConvertor is used as a backend library to convert one format to another.
sK1 Team, copyright (C) 2010 by Igor E. Novikov
			''',
		classifiers=[
			'Development Status :: 5 - Stable',
			'Environment :: Desktop',
			'Intended Audience :: End Users/Desktop',
			'License :: OSI Approved :: LGPL v2',
			'License :: OSI Approved :: GPL v2',
			'Operating System :: POSIX',
			'Operating System :: MacOS :: MacOS X',
			'Programming Language :: Python',
			'Programming Language :: C',
			"Topic :: Multimedia :: Graphics :: Graphics Conversion",
			],

			packages = ['uniconvw',
				'uniconvw.uc_gtk',
#				'uniconvw.uc_win',
#				'uniconvw.uc_macosx',
				'uniconvw.resources'
			],
			
			package_dir = {'uniconvw': 'src',
			'uniconvw.resources': 'src/resources',
			},
			
			package_data={'uniconvw.resources': ['*.*'],		
			'uniconvw': ['GNU_GPL_v2', 'GNU_LGPL_v2', 'COPYRIGHTS', 'VERSION'], 
			},


			scripts=['src/uniconvw'],
			
			data_files=[
					('/usr/share/applications',['src/uniconvw.desktop',]),
					('/usr/share/pixmaps',['src/uniconvw.png','src/uniconvw.xpm',]),
					],
			)
			
#################################################
# Implementation of bdist_deb command
#################################################
if DEBIAN:
	print '\nDEBIAN PACKAGE BUILD'
	print '===================='
	import shutil, string, platform
	version=(string.split(sys.version)[0])[0:3]
	
	arch,bin = platform.architecture()
	if arch=='64bit':
		arch='amd64'
	else:
		arch='i386'
		
	target='build/deb-root/usr/lib/python'+version+'/dist-packages'
	
	if os.path.lexists(os.path.join('build','deb-root')):
		os.system('rm -rf build/deb-root')
	os.makedirs(os.path.join('build','deb-root','DEBIAN'))
	
	os.system("cat DEBIAN/control |sed 's/<PLATFORM>/"+arch+"/g'|sed 's/<VERSION>/"+VERSION+"/g'> build/deb-root/DEBIAN/control")	

	os.makedirs(target)
	os.makedirs('build/deb-root/usr/bin')
	os.makedirs('build/deb-root/usr/share/applications')
	os.makedirs('build/deb-root/usr/share/pixmaps')
	
	os.system('cp -R build/lib/uniconvw '+target)
	os.system('cp src/uniconvw.desktop build/deb-root/usr/share/applications')
	os.system('cp src/uniconvw.png build/deb-root/usr/share/pixmaps')	
	os.system('cp src/uniconvw.xpm build/deb-root/usr/share/pixmaps')
	os.system('cp src/uniconvw build/deb-root/usr/bin')
	os.system('chmod +x build/deb-root/usr/bin/uniconvw')
		
	if os.path.lexists('dist'):	
		os.system('rm -rf dist/*.deb')
	else:
		os.makedirs('dist')
	
	os.system('dpkg --build build/deb-root/ dist/python-uniconvw-'+VERSION+'_'+arch+'.deb')	
	