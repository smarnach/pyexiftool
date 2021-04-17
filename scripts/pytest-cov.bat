@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo PyTest Coverage Script
echo;
echo pip's PyTest version
python -m pip show pytest | findstr /l /c:"Version:"
echo ______________________


python.exe -m pytest -v --cov --cov-report term-missing

popd