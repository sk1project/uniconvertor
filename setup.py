#!/usr/bin/python2
#
#   Setup script for UniConvertor 2.x
#
# 	Copyright (C) 2013-2018 by Ihor E. Novikov
#
# 	This program is free software: you can redistribute it and/or modify
# 	it under the terms of the GNU Affero General Public License
# 	as published by the Free Software Foundation, either version 3
# 	of the License, or (at your option) any later version.
#
# 	This program is distributed in the hope that it will be useful,
# 	but WITHOUT ANY WARRANTY; without even the implied warranty of
# 	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# 	GNU General Public License for more details.
#
# 	You should have received a copy of the GNU Affero General Public License
# 	along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Usage:
--------------------------------------------------------------------------
 to build package:       python setup.py build
 to install package:     python setup.py install
 to remove installation: python setup.py uninstall
--------------------------------------------------------------------------
 to create source distribution:   python setup.py sdist
--------------------------------------------------------------------------
 to create binary RPM distribution:  python setup.py bdist_rpm
--------------------------------------------------------------------------
 to create binary DEB distribution:  python setup.py bdist_deb
--------------------------------------------------------------------------.
 Help on available distribution formats: --help-formats
"""

import datetime
import os
import shutil
import sys
from distutils.core import setup

############################################################
# Subprojects resolving

CLEAR_UTILS = False

if not os.path.exists('./utils'):
    if os.path.exists('../build-utils/src/utils'):
        os.system('ln -s ../build-utils/src/utils utils')
    else:
        if not os.path.exists('./subproj/build-utils/src/utils'):
            os.makedirs('./subproj')
            os.system('cd subproj && git clone https://github.com/sk1project/build-utils && cd ..')
        os.system('ln -s ./subproj/build-utils/src/utils utils')
    CLEAR_UTILS = True

############################################################

import utils.deb
import utils.rpm
from utils import build

from utils import dependencies
from utils.native_mods import make_modules

sys.path.insert(1, os.path.abspath('./src'))

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))

from uc2 import uc2const

############################################################
# Flags
############################################################
UPDATE_MODULES = False
DEB_PACKAGE = False
RPM_PACKAGE = False
CLEAR_BUILD = False

############################################################
# Package description
############################################################
NAME = 'uniconvertor'
VERSION = uc2const.VERSION + uc2const.REVISION
DESCRIPTION = 'Universal vector graphics translator'
AUTHOR = 'Ihor E. Novikov'
AUTHOR_EMAIL = 'sk1.project.org@gmail.com'
MAINTAINER = AUTHOR
MAINTAINER_EMAIL = AUTHOR_EMAIL
LICENSE = 'GPL v3'
URL = 'https://sk1project.net'
DOWNLOAD_URL = URL
CLASSIFIERS = [
    'Development Status :: 6 - Mature',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'License :: OSI Approved :: LGPL v2',
    'License :: OSI Approved :: GPL v3',
    'Operating System :: POSIX',
    'Operating System :: MacOS :: MacOS X',
    'Operating System :: Microsoft :: Windows',
    'Programming Language :: Python',
    'Programming Language :: C',
    "Topic :: Multimedia :: Graphics :: Graphics Conversion",
]
loaders = uc2const.MODEL_LOADERS + uc2const.PALETTE_LOADERS + \
          uc2const.BITMAP_LOADERS
savers = uc2const.MODEL_SAVERS + uc2const.PALETTE_SAVERS + \
         uc2const.BITMAP_SAVERS
year = str(datetime.date.today().year)

LONG_DESCRIPTION = '''
UniConvertor is a multiplatform universal vector graphics translator.
Uses SK2 model to convert one format to another. 

sK1 Project (https://sk1project.net),
Copyright (C) 2007-%s sK1 Project Team
--------------------------------------------------------------------------------
Supported input formats:  
  %s
--------------------------------------------------------------------------------
Supported output formats: 
  %s
--------------------------------------------------------------------------------
''' % (year,
       '\n  '.join([uc2const.FORMAT_DESCRIPTION[item] for item in loaders]),
       '\n  '.join([uc2const.FORMAT_DESCRIPTION[item] for item in savers]))

LONG_DEB_DESCRIPTION = ''' UniConvertor is a multiplatform universal vector graphics translator.
 Uses SK2 model to convert one format to another. 
 . 
 sK1 Project (https://sk1project.net),
 Copyright (C) 2007-%s sK1 Project Team 
 .
 ##############################################
 .
 Supported input formats:
 .
 %s
 .
 ##############################################
 .
 Supported output formats:
 .
 %s
 .
 ##############################################  
''' % (year,
       '  '.join([uc2const.FORMAT_DESCRIPTION[item] for item in loaders]),
       '  '.join([uc2const.FORMAT_DESCRIPTION[item] for item in savers]))

############################################################
# Build data
############################################################
install_path = '/usr/lib/%s-%s' % (NAME, VERSION)
os.environ["APP_INSTALL_PATH"] = "%s" % (install_path,)
src_path = 'src'
include_path = '/usr/include'
modules = []
scripts = ['src/script/uniconvertor', 'src/script/uc2']
deb_scripts = []
data_files = [
    (install_path, ['LICENSE', ]),
]

############################################################
deb_depends = ''
rpm_depends = ''
############################################################

package_data = {}

# Preparing start script
src_script = 'src/script/uniconvertor.tmpl'
dst_script = 'src/script/uniconvertor'
fileptr = open(src_script, 'r')
fileptr2 = open(dst_script, 'w')
while True:
    line = fileptr.readline()
    if line == '':
        break
    if '$APP_INSTALL_PATH' in line:
        line = line.replace('$APP_INSTALL_PATH', install_path)
    fileptr2.write(line)
fileptr.close()
fileptr2.close()
shutil.copy(dst_script, 'src/script/uc2')

############################################################
# Main build procedure
############################################################

if len(sys.argv) == 1:
    sys.argv.append('build_update')

if len(sys.argv) > 1:

    if sys.argv[1] == 'bdist_rpm':
        CLEAR_BUILD = True
        RPM_PACKAGE = True
        sys.argv[1] = 'sdist'
        rpm_depends = dependencies.get_uc2_rpm_depend()

    if sys.argv[1] == 'build_update':
        UPDATE_MODULES = True
        CLEAR_BUILD = True
        sys.argv[1] = 'build'

    if sys.argv[1] == 'bdist_deb':
        DEB_PACKAGE = True
        CLEAR_BUILD = True
        sys.argv[1] = 'build'
        deb_depends = dependencies.get_uc2_deb_depend()

    if sys.argv[1] == 'uninstall':
        if os.path.isdir(install_path):
            # removing UC2 folder
            print('REMOVE: ' + install_path)
            os.system('rm -rf ' + install_path)
            # removing scripts
            for item in scripts:
                filename = os.path.basename(item)
                print('REMOVE: /usr/bin/' + filename)
                os.system('rm -rf /usr/bin/' + filename)
            # removing data files
            for item in data_files:
                location = item[0]
                file_list = item[1]
                for file_item in file_list:
                    filename = os.path.basename(file_item)
                    filepath = os.path.join(location, filename)
                    if not os.path.isfile(filepath):
                        continue
                    print('REMOVE: ' + filepath)
                    os.system('rm -rf ' + filepath)
            print('Desktop database update: ', end=' ')
            os.system('update-desktop-database')
            print('DONE!')
        else:
            print('UniConvertor installation is not found!')
        sys.exit(0)

# Preparing setup.cfg
############################################################

with open('setup.cfg.in', 'r') as fileptr:
    content = fileptr.read()
    if rpm_depends:
        content += '\nrequires = ' + rpm_depends

with open('setup.cfg', 'w') as fileptr:
    fileptr.write(content)

############################################################
# Native extensions
############################################################

modules += make_modules(src_path, include_path)

############################################################
# Setup routine
############################################################

setup(
    name=NAME,
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
    packages=build.get_source_structure('src/uc2') + ['uc2'],
    package_dir={'uc2': 'src/uc2'},
    package_data=package_data,
    # install_requires=[line.strip() for line in open('requirements.txt', 'r').readlines()],
    data_files=data_files,
    scripts=scripts,
    ext_modules=modules)

############################################################
# .py source compiling
############################################################
if not UPDATE_MODULES:
    build.compile_sources()

############################################################
# This section for developing purpose only
# Command 'python setup.py build_update' allows
# automating build and copying of native extensions
# into package directory
############################################################
if UPDATE_MODULES:
    build.copy_modules(modules)

############################################################
# Implementation of bdist_deb command
############################################################
if DEB_PACKAGE:
    utils.deb.DebBuilder(
        name=NAME,
        version=VERSION,
        maintainer='%s <%s>' % (AUTHOR, AUTHOR_EMAIL),
        depends=deb_depends,
        homepage=URL,
        description=DESCRIPTION,
        long_description=LONG_DEB_DESCRIPTION,
        section='graphics',
        package_dirs=build.get_package_dirs('src/uc2'),
        package_data=package_data,
        scripts=scripts,
        data_files=data_files,
        deb_scripts=deb_scripts,
        dst=install_path)

############################################################
# Implementation of bdist_rpm command
############################################################
if RPM_PACKAGE:
    utils.rpm.RpmBuilder(
        name=NAME,
        version=VERSION,
        release='0',
        arch='',
        maintainer='%s <%s>' % (AUTHOR, AUTHOR_EMAIL),
        summary=DESCRIPTION,
        description=LONG_DESCRIPTION,
        license=LICENSE,
        url=URL,
        depends=rpm_depends.split(' '),
        build_script='setup.py',
        scripts=scripts,
        install_path=install_path,
        data_files=data_files, )

os.chdir(CURRENT_PATH)

if CLEAR_BUILD:
    build.clear_build()

FOR_CLEAR = ['MANIFEST', 'setup.cfg'] + scripts
if CLEAR_UTILS:
    FOR_CLEAR += ['utils']
for item in FOR_CLEAR:
    if os.path.lexists(item):
        os.remove(item)
