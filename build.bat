@echo off
REM Copyright (c) 2026 Malek Mzali (Louka). All rights reserved.
cd /d "%~dp0"

if not exist main.py (
    echo main.py not found next to build.bat
    pause
    exit /b 1
)

python -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto :fail

python tools\gen_version_info.py
if errorlevel 1 goto :fail

pyinstaller --clean --noconfirm LoukaKeyPulse.spec
if errorlevel 1 goto :fail

echo.
echo Done. Your build is in the dist folder.
pause
exit /b 0

:fail
echo.
echo Build failed - see the messages above.
pause
exit /b 1
