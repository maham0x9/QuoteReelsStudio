@echo off
REM ============================================================
REM  Build a standalone Windows distribution with PyInstaller.
REM  Output: dist\QuoteReelsStudio\QuoteReelsStudio.exe
REM ============================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [setup] No venv found. Running run.bat once to bootstrap...
    call run.bat /noop
)

".venv\Scripts\python.exe" -m pip install --upgrade pyinstaller
if errorlevel 1 (
    echo [ERROR] Could not install PyInstaller.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" scripts\build_exe.py
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

echo.
echo [done] Build complete: dist\QuoteReelsStudio\QuoteReelsStudio.exe
pause
endlocal
