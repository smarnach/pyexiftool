@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo Python Built-in Unittest Script
echo ______________________


python -m unittest -v

popd

