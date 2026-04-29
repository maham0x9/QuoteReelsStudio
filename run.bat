@echo off
REM ============================================================
REM  QuoteReelsStudio launcher
REM  - Creates a local .venv on first run
REM  - Installs / updates Python deps
REM  - Loads PEXELS_API_KEY / PIXABAY_API_KEY from .env if present
REM  - Launches the app
REM ============================================================
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

REM ---- Locate Python -----------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not on PATH. Install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM ---- Create venv on first run ------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment in .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
    echo [setup] Installing dependencies (first run only, may take a few minutes) ...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install requirements.
        pause
        exit /b 1
    )
)

REM ---- Optional: load API keys from .env ---------------------
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set "%%A=%%B"
    )
)

REM ---- Launch ------------------------------------------------
echo [run] Starting QuoteReelsStudio ...
".venv\Scripts\python.exe" main.py
set EXITCODE=%errorlevel%
if not "%EXITCODE%"=="0" (
    echo.
    echo [QuoteReelsStudio exited with code %EXITCODE%]
    pause
)
endlocal & exit /b %EXITCODE%
