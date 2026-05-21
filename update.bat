@echo off
REM Pull the latest code, refresh dependencies, run smoke test.

setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%venv\Scripts\python.exe"
set "PIP=%ROOT%venv\Scripts\pip.exe"

where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed. Install Git and try again.
    exit /b 1
)

echo.
echo [STEP] Pulling latest code ...
git pull --ff-only

if not exist "%PY%" (
    echo [INFO] Virtual environment missing. Running setup.bat ...
    call "%ROOT%setup.bat"
    exit /b 0
)

echo.
echo [STEP] Refreshing dependencies ...
"%PIP%" install -r requirements.txt

echo.
echo [STEP] Smoke check ...
"%PY%" -m app --check

endlocal
exit /b 0
