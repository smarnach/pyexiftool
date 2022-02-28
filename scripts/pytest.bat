@echo off

pushd %~dp0..

echo ______________________
echo *** PyExifTool automation ***
echo PyTest Coverage Script
echo;
echo pip's PyTest version
python.exe -m pip show pytest | findstr /l /c:"Version:"
echo pip's PyTest-cov version
python.exe -m pip show pytest-cov | findstr /l /c:"Version:"
echo ______________________

REM added the --cov= so that it doesn't try to test coverage on the virtualenv directory
REM add -s to print out stuff from pytest class (don't capture output) -- https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html#setting-capturing-methods-or-disabling-capturing
python.exe -m pytest -v --cov-config=%~dp0windows.coveragerc --cov=exiftool --cov-report term-missing tests/

popd
