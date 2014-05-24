@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat

set XDATDOCSDIR="%APPDIR%"\ODATDOCS
set PMTAPPDIR=%APPDIR%\pmtsdat
set PYTHONPATH=%PYTHONPATH%;%XDATDOCSDIR%\myscripts\PythonModules
set RELATIVEPATH=Myscripts\bin\alias.txt
set TCL_LIBRARY=b:\Python27\tcl\tcl8.5\
doskey /MACROFILE=%XDATDOCSDIR%\%RELATIVEPATH%
set PYTHONDONTWRITEBYTECODE=1


pushd %XDATDOCSDIR%\myscripts
