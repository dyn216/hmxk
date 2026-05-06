@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "CHECK_ONLY=0"
if /I "%~1"=="--check" set "CHECK_ONLY=1"

pushd "%SCRIPT_DIR%" || (
    echo ERROR: cannot enter backend directory
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python 3.8+ is required
    goto fail
)

if "%CHECK_ONLY%"=="0" (
    if not exist "venv\Scripts\python.exe" (
        echo Creating virtual environment...
        python -m venv venv
        if errorlevel 1 goto fail
    )

    call "venv\Scripts\activate.bat"
    if errorlevel 1 goto fail

    python -m pip install --upgrade pip
    if errorlevel 1 goto fail
    python -m pip install -r requirements.txt
    if errorlevel 1 goto fail

    if not exist "chronic_disease.db" (
        python init_db.py
        if errorlevel 1 goto fail
    )
) else (
    if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"
)

if "%CHECK_ONLY%"=="1" (
    python start_backend.py --check
) else (
    python start_backend.py
)
set "EXIT_CODE=%ERRORLEVEL%"
popd
if "%CHECK_ONLY%"=="0" pause
exit /b %EXIT_CODE%

:fail
set "EXIT_CODE=%ERRORLEVEL%"
if "%EXIT_CODE%"=="0" set "EXIT_CODE=1"
popd
if "%CHECK_ONLY%"=="0" pause
exit /b %EXIT_CODE%
