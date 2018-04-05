UniConvertor is a multiplatform universal vector graphics translator.
Uses sK1 model to convert one format to another. 

THIS REPOSITORY CONTAINS OLD UNICONVERTOR 1.x BRANCH.
Actual UniConvertor 2.0 is under active development and the source
code is placed in sk1project/sk1-wx repository (together with sK1 2.0).

sK1 Project (http://sk1project.net),
Copyright (C) 2007-2013 by Igor E. Novikov

You can find lcms at https://github.com/mm2/Little-CMS.git

How to install: 
--------------------------------------------------------------------------
 to build package:   python setup.py build [build_ext -n -I <lcms include path> -L <lcms lib path>]
 to install package:   python setup.py install
--------------------------------------------------------------------------
 to create source distribution:   python setup.py sdist
--------------------------------------------------------------------------
 to create binary RPM distribution:  python setup.py bdist_rpm [build_ext -n -I <lcms include path> -L <lcms lib path>]
--------------------------------------------------------------------------
 to create binary DEB distribution:  python setup.py bdist_deb [build_ext -n -I <lcms include path> -L <lcms lib path>]
--------------------------------------------------------------------------
 to create binary wheel distribution:  python setup.py bdist_wheel [build_ext -n -I <lcms include path> -L <lcms lib path>]
--------------------------------------------------------------------------

help on available distribution formats: python setup.py bdist --help-formats


DETAILS

If you wish testing UniConvertor you have two installation ways. 
First option is a distutils install with commands:

python setup.py build [build_ext -n -I <lcms include path> -L <lcms lib path>]
python setup.py install

Application will be installed into /usr/local/lib/python2.x/site-packages
Also uniconvertor script will be in /usr/local/bin
But this way is not recommended. The most preferred option is a package 
installation (deb or rpm). You can create package using command:

python setup.py bdist_deb (for Ubuntu|Mint|Debian etc.)
python setup.py bdist_rpm (for Fedora|OpenSuse|Mandriva etc.)

By installing the package you have full control over all the installed files 
and can easily remove them from the system (it's important for application
preview).

For successful build either distutils or deb|rpm package you need installing
some development packages. We describe dev-packages for Ubuntu|Debian, but for
other distros they have similar names. So, you need:

libfreetype6-dev
python-dev
liblcms1-dev (or liblcms2-dev)

To run application you need installing also:

python-imaging 
python-reportlab
