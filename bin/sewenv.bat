@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat



set XDATDOCSDIR=%APPDIR%\SEWDocs\sewpulse
set RELATIVEPATH=code\bin\alias.txt

doskey /MACROFILE="%XDATDOCSDIR%\%RELATIVEPATH%"
set PYTHONDONTWRITEBYTECODE=1
set PYTHONPATH=%XDATDOCSDIR%\code\
set GOPATH=%APPDIR%\goscripts

pushd %XDATDOCSDIR%

