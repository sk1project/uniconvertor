#!/bin/sh

#To build UniConvertor python devel package should be installed.
#To run UniConvertor you need Python, Python Image Library
#and pylcms (optional for color managment).

# ---------------------------------------------------------------------------
# Check subroutine
# ---------------------------------------------------------------------------
check() {
if [ $? -ne 0 ]
then
	echo ""
	echo "======================================"
	echo " WARINIG!: "$CURRENT_STEP" "$OPERATION" is FAILED"
	echo " Try finding reason in stack trace."
	echo "======================================"
	exit
fi
}

echo
echo ---------------------------------------------------------------------------
echo UniConvertor build starts...
echo ---------------------------------------------------------------------------
echo

# ---------------------------------------------------------------------------
# INSTALLATION PATH
# ---------------------------------------------------------------------------

INSTALL_PATH=/usr/local

# ---------------------------------------------------------------------------
# ENVIROMENT VARIABLES
# ---------------------------------------------------------------------------

EPREFIX=$INSTALL_PATH/lib/UniConvertor
PREFIX=$EPREFIX

# ---------------------------------------------------------------------------
# Prepare UniConvertor installation
# ---------------------------------------------------------------------------
echo "Clearing possible previous UniConvertor installation..."
rm -rf $PREFIX

echo "Copying UniConvertor installation..."
cp -r src $PREFIX
rm -rf $PREFIX/modules; rm -rf $PREFIX/app/modules

echo "Removing .svn folders..."
for i in `find $EPREFIX |grep .svn`
do
	rm -rf $i
done


echo "Copying modules source code..."
rm -rf build;cp -r src/modules build
rm -rf modules;mkdir modules

echo "Removing .svn folders..."
for i in `find build |grep .svn`
do
	rm -rf $i
done


# ---------------------------------------------------------------------------
# MODULES BUILD
# ---------------------------------------------------------------------------
cd build

echo
echo ---------------------------------------------------------------------------
echo Filter module build
echo ---------------------------------------------------------------------------
echo
CURRENT_STEP="Filter module"
cd Filter

ls
OPERATION="make -f"
make -f Makefile.pre.in Makefile VERSION=2.4 installdir=/usr
check
OPERATION="make"
make
check
#------------install-------------
cp streamfilter.so ../../modules/streamfilter.so


echo
echo ---------------------------------------------------------------------------
echo Objects Modules
echo ---------------------------------------------------------------------------
echo
CURRENT_STEP="Modules"

cd ../Modules

OPERATION="make -f"
make -f Makefile.pre.in Makefile VERSION=2.4 installdir=/usr
check
OPERATION="make"
make
check

#------------install-------------
cp _sketchmodule.so ../../modules/_sketchmodule.so
cp skreadmodule.so ../../modules/skreadmodule.so
cp _type1module.so ../../modules/_type1module.so
cp pstokenize.so ../../modules/pstokenize.so

cd ..;cd ..
mv modules $PREFIX/app/modules;rm -rf build

START=$PREFIX/uniconvertor.py
chmod +x $START
ln -s $START $INSTALL_PATH/bin/uniconv

echo
echo ---------------------------------------------------------------------------
echo UniConvertor build and installation are completed! 
echo To launch UniConvertor use "<uniconv> command"
echo  or $PREFIX/uniconvertor.py script
echo ---------------------------------------------------------------------------
