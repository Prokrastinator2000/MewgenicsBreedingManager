@echo off
setlocal
cd /d "%~dp0"

REM Pick a Python launcher. The app targets Python 3.14, so try the
REM version-pinned launcher first, then any py -3, then plain python.
set "PY="
py -3.14 -c "import sys" >nul 2>&1 && set "PY=py -3.14"
if not defined PY (
    py -3 -c "import sys" >nul 2>&1 && set "PY=py -3"
)
if not defined PY (
    python -c "import sys" >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo No usable Python interpreter found.
    echo Install Python 3.14 from https://www.python.org/downloads/ and retry.
    pause
    endlocal & exit /b 1
)

echo Using interpreter: %PY%

REM Install dependencies if PySide6 is not available for this interpreter.
%PY% -c "import PySide6" >nul 2>&1 || (
    echo Installing dependencies...
    %PY% -m pip install -r requirements.txt
)

%PY% src\mewgenics_manager.py
set "EXITCODE=%ERRORLEVEL%"
endlocal & exit /b %EXITCODE%
