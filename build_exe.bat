@echo off
setlocal EnableDelayedExpansion
title BB Webp Converter - Build

echo.
echo  ================================================
echo   BB Webp Converter  --  Build Script
echo  ================================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Please install Python 3.9+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    pause & exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% found.
echo.

:: ── Install dependencies ──────────────────────────────────────────────────────
echo  Installing / verifying dependencies...
echo.
python -m pip install --upgrade pip -q
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause & exit /b 1
)
echo  [OK] Dependencies ready.
echo.

:: ── Find tkinterdnd2 data dir ─────────────────────────────────────────────────
for /f "delims=" %%p in ('python -c "import tkinterdnd2,os; print(os.path.dirname(tkinterdnd2.__file__))"') do set TKDND_DIR=%%p
echo  [OK] tkinterdnd2 found at: %TKDND_DIR%
echo.

:: ── Build with PyInstaller ────────────────────────────────────────────────────
echo  Building standalone .exe (this takes ~30-60 seconds) ...
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "BBWebpConverter" ^
    --add-data "%TKDND_DIR%\tkdnd;tkinterdnd2/tkdnd" ^
    --hidden-import="PIL._tkinter_finder" ^
    --hidden-import="tkinterdnd2" ^
    --collect-all tkinterdnd2 ^
    webp2png.py

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. See output above.
    pause & exit /b 1
)

echo.
echo  ================================================
echo   BUILD COMPLETE!
echo  ================================================
echo.
echo  Your app is at:  dist\BBWebpConverter.exe
echo.
echo  Drop it anywhere on your PC and run it.
echo  No installation, no FFmpeg, no Python needed!
echo.
pause
