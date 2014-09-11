@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat



set XDATDOCSDIR=%APPDIR%\trackerdir\GZBDocs
set UBEROBSERVERDIR=%APPDIR%\trackerdir\observer
set RELATIVEPATH=code\bin\alias.txt
set TCL_LIBRARY=b:\Python27\tcl\tcl8.5\

doskey /MACROFILE="%XDATDOCSDIR%\%RELATIVEPATH%"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%XDATDOCSDIR%\code\

pushd %XDATDOCSDIR%\code
