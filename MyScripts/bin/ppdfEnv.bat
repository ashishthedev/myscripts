@echo off

REM Entry point where the whole dev environment is set
REM Place the following line into the cmd promt shortcut and point to this setenv.bat
REM D:\Windows\system32\cmd.exe /k E:\Dev\WorkSpace\setenv.bat

::This environment is specific to Google App Engine
SET "VIRTUAL_ENV=b:\ppdf"
call setenv.bat
call %VIRTUAL_ENV%\Scripts\activate.bat
set "PYTHONPATH=%PYTHONPATH%; %VIRTUAL_ENV%\Lib\site-packages\wkhtmltopdf"
pushd %VIRTUAL_ENV%
