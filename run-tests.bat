@echo off
pushd "%~dp0"
python -m pytest %*
set "test_exit=%ERRORLEVEL%"
popd
exit /b %test_exit%
