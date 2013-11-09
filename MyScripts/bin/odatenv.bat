@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat

set APPDIR=%~dp0..\..\..\ODATDOCS
doskey /MACROFILE=%APPDIR%\Myscripts\bin\alias.txt
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%PYTHONPATH%;%APPDIR%\myscripts\PythonModules

pushd %APPDIR%\myscripts
