# UniConvertor 2.0

[![Build Status](https://app.travis-ci.com/sk1project/uniconvertor.svg?branch=master)](https://app.travis-ci.com/sk1project/uniconvertor) ![platform](https://img.shields.io/badge/platform-Linux-blue.svg) ![platform](https://img.shields.io/badge/platform-Windows-blue.svg) ![platform](https://img.shields.io/badge/platform-Mac-blue.svg) [![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

<center>

![UniConvertor 2.0](./docs/images/uc2_0.png "UniConvertor 2.0")

</center>

UniConvertor 2.0 is a cross-platform universal vector graphics translator.
Uses sK1 2.0 model to convert one format to another. 

sK1 Project (https://sk1project.net)

### How to install: 

---

* to build package:   `python setup.py build`
* to install package:   `python setup.py install`
* to remove installation: `python setup.py uninstall`

---

* to create source distribution:   `python setup.py sdist`

---

* to create binary RPM distribution:  `python setup.py bdist_rpm`
* to create binary DEB distribution:  `python setup.py bdist_deb`

---

* help on available distribution formats: `python setup.py bdist --help-formats`

---


## DETAILS

If you wish testing UniConvertor 2.0 you have two installation ways. 
First option is a distutils install with commands:
```
python setup.py build
python setup.py install
```

But this way is not recommended. The most preferred option is a package 
installation (deb or rpm). You can create package using command:
```
python setup.py bdist_deb (for Ubuntu|Mint|Debian etc.)
python setup.py bdist_rpm (for Fedora|OpenSuse|Mageia etc.)
```

By installing the package you have full control over all the installed files 
and can easily remove them from the system (it's important for application
preview).

### Dependencies

Please note that application uses Python 2.x version. So Python interpreter
and python based dependencies should be for 2.x, but not 3.x

For successful build either distutils or deb|rpm package you need installing
some development packages. We describe dev-packages for Ubuntu|Debian, but for
other distros they have similar names. So, you need:
```
git
curl
libcairo2-dev
liblcms2-dev
libmagickwand-dev
libpango1.0-dev
python-dev
python-cairo-dev
```

To run application you need installing also:
```
python-pil 
python-reportlab
python-cairo
```
