@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat



REM Environment variables should not have quotes. The final path should have.
set WEBDIR=%APPDIR%\website
set LEANDIR=%APPDIR%\leantricks
set PMTAPPDIR=%APPDIR%\pmtsdat
set XDATDOCSDIR=%APPDIR%\SDATDocs
set PHUNGSUKDIR="%APPDIR%"\phungsuk_jibabo\detect_change_app
set RELATIVEPATH=code\bin\alias.txt
set TCL_LIBRARY=b:\Python27\tcl\tcl8.5\
REM set GOPATH=%APPDIR%\goscripts

doskey /MACROFILE="%XDATDOCSDIR%\%RELATIVEPATH%"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=e:\gaeSDK\;%XDATDOCSDIR%\code\;

pushd %XDATDOCSDIR%\code\whopaid

set PATH=%PATH%;B:\Exercism\


@echo ___________________________________________
@echo                   SDAT                     
@echo ___________________________________________
@echo.
@echo.
