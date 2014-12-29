@REM set GOROOT=c:\go
set GOBIN=$GOROOT\bin
set PATH=%PATH%;$GOBIN
set GOARCH=386
set GOOS=windows
echo off
8g %1.go
8l -o %1.exe %1.8
%1
