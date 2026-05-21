@echo off
REM ============================================================================
REM   punyaku-v1 - PyInstaller build script
REM ============================================================================

setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] Virtual environment missing. Run setup.bat first.
    exit /b 1
)

"%PY%" -m pip install --upgrade pyinstaller
"%PY%" -m PyInstaller install\punyaku.spec --noconfirm

echo.
echo Build done. Binary in dist\Punyaku\
endlocal
exit /b 0
