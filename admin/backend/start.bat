@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "UNIFIED_BACKEND=%SCRIPT_DIR%..\..\backend"
set "TZB_BACKEND_ENTRY_LABEL=统一"
set "PORT=8000"
call "%UNIFIED_BACKEND%\start.bat" %*
exit /b %ERRORLEVEL%
