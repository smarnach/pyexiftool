@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo Python Built-in Unittest Script
echo ______________________

python.exe -m unittest -v

popd
