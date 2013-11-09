@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat

REM We are assuming the appdir is two levels above this file.
REM If the structure of APPDIR changes, a smiliar change in this file will also be required
set APPDIR=%~dp0..\..
set WEBDIR=%APPDIR%\..\website
set PHUNGSUKDIR=%APPDIR%\..\phungsuk_jibabo\detect_change_app
set RELATIVEPATH=\Myscripts\bin\alias.txt


doskey /MACROFILE=%APPDIR%%RELATIVEPATH%
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%PYTHONPATH%;%APPDIR%\myscripts\PythonModules

pushd %APPDIR%\myscripts
