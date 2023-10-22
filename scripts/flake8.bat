@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo Flake8 Script
echo;
echo pip's flake8 version
python.exe -m pip show flake8 | findstr /l /c:"Version:"
echo pip's flake8 pep8-naming plugin version
python.exe -m pip show pep8-naming | findstr /l /c:"Version:"
echo flake8 version
python.exe -m flake8 --version
echo ______________________

REM python.exe -m flake8 -v --config "%~dp0flake8.ini" "exiftool" "tests"

python.exe -m flake8 -v --config "%~dp0flake8.ini" --output-file "%~dp0~flake8_report.txt" "exiftool" "tests"

popd
