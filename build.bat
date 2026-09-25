@echo off
setlocal
cd /d "%~dp0"
set "BUILD_DIR=build\mewgenics_manager"
set "DIST_ROOT=dist"
set "APP_DIR_OUT=%DIST_ROOT%\MewgenicsManager"
set "APP_EXE_OUT=%DIST_ROOT%\MewgenicsManager.exe"
set "VERSION_FILE=VERSION"
set "OS_SUFFIX=windows"

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

if exist "%VERSION_FILE%" (
    set /p VERSION=<"%VERSION_FILE%"
) else (
    set "VERSION=dev"
)
if not defined VERSION set "VERSION=dev"
set "APP_ZIP_OUT=%DIST_ROOT%\MewgenicsManager-%VERSION%-%OS_SUFFIX%.zip"

echo Installing / updating dependencies...
%PY% -m pip install -r requirements.txt
%PY% -m pip install pyinstaller

echo.
echo Cleaning previous build output...
del /F /Q "%DIST_ROOT%\MewgenicsManager-*.zip" >nul 2>nul
if exist "%APP_DIR_OUT%" (
    attrib -R /S /D "%APP_DIR_OUT%\*" >nul 2>nul
    rmdir /S /Q "%APP_DIR_OUT%"
)
if exist "%APP_DIR_OUT%" (
    echo Warning: could not remove %APP_DIR_OUT%. Continuing with onefile build.
)
if exist "%APP_EXE_OUT%" (
    attrib -R "%APP_EXE_OUT%" >nul 2>nul
    del /F /Q "%APP_EXE_OUT%"
)
if exist "%BUILD_DIR%" (
    attrib -R /S /D "%BUILD_DIR%\*" >nul 2>nul
    rmdir /S /Q "%BUILD_DIR%"
)

echo.
echo Building standalone executable...
%PY% -m PyInstaller src/mewgenics_manager.spec --noconfirm --distpath "%DIST_ROOT%"

echo.
if exist "%APP_EXE_OUT%" (
    echo Build succeeded!
    echo Executable: %APP_EXE_OUT%
    echo.
    echo Waiting for file lock to release...
    timeout /t 3 /nobreak >nul
    echo Zipping executable...
    powershell -NoProfile -Command "Compress-Archive -Path '%APP_EXE_OUT%' -DestinationPath '%APP_ZIP_OUT%' -Force"
    if exist "%APP_ZIP_OUT%" (
        echo Zip created: %APP_ZIP_OUT%
    ) else (
        echo Warning: zip creation failed.
    )
) else (
    echo Build FAILED - check output above.
)
pause
endlocal
