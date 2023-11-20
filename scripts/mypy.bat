@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo MyPy Static Analysis Script
echo;
echo pip's MyPy version
python.exe -m pip show mypy | findstr /l /c:"Version:"
echo ______________________

python.exe -m mypy --config-file mypy.ini --strict exiftool/


popd
