@echo off
title examshell
where py >/dev/null 2>nul
if %errorlevel%==0 (
    py -3 "%~dp0examshell.py" %*
    exit /b
)
where python >/dev/null 2>nul
if %errorlevel%==0 (
    python "%~dp0examshell.py" %*
    exit /b
)
echo [examshell] Python 3 was not found.
echo Install it from https://www.python.org/downloads/  or run:  winget install Python.Python.3.12
pause
