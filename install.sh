#!/bin/sh

#The following devel packages should be installed:
# python
# python-imaging

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

myEPREFIX=

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

sed 's/_MY_INSTALL_DIR_/'"$myEPREFIX"'/g' Makefile.pre.in |sed 's/_MY_INSTALL_PREFIX_/'"$myEPREFIX"'/g'> Makefile.pre; rm -f Makefile.pre.in;mv Makefile.pre Makefile.pre.in

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

myIMAGING_HEADER=`echo $RE_PREFIX/include/PIL|sed 's/\//\\\ \//g'|sed 's/ \//\//g'`

sed 's/_MY_TCL_HEADERS_/'"$myTCL_HEADERS"'/g' Setup.in |sed 's/_MY_TCL_LIBS_/'"$myTCL_LIBS"'/g' |sed 's/_MY_IMAGING_HEADER_/'"$myIMAGING_HEADER"'/g' > Setup.in.pre; rm -f Setup.in; mv Setup.in.pre Setup.in

# cat ../../patches/Modules/Setup.config > Setup.config

sed 's/_MY_INSTALL_DIR_/'"$myEPREFIX"'/g' Makefile.pre.in |sed 's/_MY_INSTALL_PREFIX_/'"$myEPREFIX"'/g'> Makefile.pre; rm -f Makefile.pre.in;mv Makefile.pre Makefile.pre.in

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
echo UniConvertor buildand installation are completed! 
echo To launch UniConvertor use "<uniconv> command"
echo  or $PREFIX/uniconvertor.py script
echo ---------------------------------------------------------------------------
