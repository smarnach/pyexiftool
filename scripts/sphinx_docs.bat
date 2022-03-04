@echo off

REM script takes ONE optional parameter, which is the path to the Graphviz dot.exe
REM it is only used if dot.exe does not exist on your PATH

setlocal

pushd %~dp0..\docs

echo ______________________
echo *** PyExifTool automation ***
echo Generate Sphinx Docs
echo;
call :PIP_SHOW_VER packaging
call :PIP_SHOW_VER sphinx
call :PIP_SHOW_VER sphinx-autoapi
call :PIP_SHOW_VER sphinx-rtd-theme
call :PIP_SHOW_VER sphinx-autodoc-typehints
echo ______________________

REM add some opts, -v = more verbose
SET SPHINXOPTS=-v

echo;
echo ** Searching for Graphviz's dot **
SET INPUT_DOT=dot.exe
where dot.exe 2>nul
IF NOT ERRORLEVEL 1 (
	REM no need to set more opts
	goto FOUND_DOT
)


REM check %1 to see if a path to dot.exe was provided
SET INPUT_DOT=%~1
IF EXIST "%INPUT_DOT%" (
	SET SPHINXOPTS=%SPHINXOPTS% -D graphviz_dot="%INPUT_DOT%"
	goto FOUND_DOT
)

echo Graphviz's dot.exe was not found.  Either have it on your PATH, or specify with %%1

REM docs still generate without it, but all the graphics are missing, and so it sort of fails silently!

exit /b 1

:FOUND_DOT

echo;
echo ** Graphviz dot.exe version **
%INPUT_DOT% -V


echo;
echo ** Clean build **
call make.bat clean

echo;
echo ** Build HTML **
echo ___________________________________________________________________
call make.bat html

echo ___________________________________________________________________
echo MAKE SURE TO CHECK FOR ANY ERRORS ABOVE!!! Sphinx fails silently!

popd

exit /b %errorlevel%


REM -------------------------------------------
:PIP_SHOW_VER

echo pip's %1 version
python.exe -m pip show %1 | findstr /l /c:"Version:"

exit /b 0
