:: --------------------------------------------------------------------
::  Wrapper script to start a UniConvertor Tk frontend application
::
::  Copyright (C) 2010 Igor E. Novikov
::
::  This library is covered by GNU Library General Public License.
::  For more info see COPYRIGHTS file in uniconvw root directory.
:: ---------------------------------------------------------------------
@echo off

if "%~1"=="" (
   pyVM -c "from uniconvw import uniconvw_run; uniconvw_run();"
) else (
   pyVM -c "from uniconvw import uniconvw_run; uniconvw_run();" "%~1"
)