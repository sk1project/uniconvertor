:: --------------------------------------------------------------------
::  Wrapper script to start a UniConvertor application once it is installed
::
::  Copyright (C) 2007-2010 Igor E. Novikov
::
::  This library is covered by GNU Library General Public License.
::  For more info see COPYRIGHTS file in uniconvertor root directory.
:: ---------------------------------------------------------------------
@echo off

if "%~3"=="" (
   pyVM -c "from uniconvertor import uniconv_run; uniconv_run();" "%~1" "%~2"
) else (
   pyVM -c "from uniconvertor import uniconv_run; uniconv_run();" "%~1" "%~2" "%~3"
)
