@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat

REM We are assuming the appdir is two levels above this file.
REM If the structure of APPDIR changes, a smiliar change in this file will also be required
REM set APPDIR="C:\Users\Ichigo\Google Drive\Appdir"


REM Environment variables should not have quotes. The final path should have.
set WEBDIR=%APPDIR%\website
set LEANDIR=%APPDIR%\leantricks
set PMTAPPDIR=%APPDIR%\pmtsdat
set XDATDOCSDIR=%APPDIR%\SDATDocs
set PHUNGSUKDIR="%APPDIR%"\phungsuk_jibabo\detect_change_app
set RELATIVEPATH=Myscripts\bin\alias.txt
set TCL_LIBRARY=b:\Python27\tcl\tcl8.5\
set GOPATH=%APPDIR%\goscripts

doskey /MACROFILE="%XDATDOCSDIR%\%RELATIVEPATH%"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%XDATDOCSDIR%\myscripts\PythonModules\

pushd %XDATDOCSDIR%\myscripts
