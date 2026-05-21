@echo off
REM ============================================================================
REM   punyaku-v1 - Windows launcher
REM   Provides a menu: normal / safe / debug / performance / utilities.
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "VENV=%ROOT%venv"
set "PY=%VENV%\Scripts\python.exe"

if not exist "%PY%" (
    echo [ERROR] Virtual environment missing. Run setup.bat first.
    exit /b 1
)

:menu
cls
echo  =======================================================================
echo    Punyaku Video Looper  -  Launcher
echo  =======================================================================
echo.
echo    [1] Run Application (Normal)
echo    [2] Run Safe Mode (no GPU, minimal plugins)
echo    [3] Run Debug Mode
echo    [4] Run Performance Mode
echo    [5] Run Low-RAM Mode
echo    [6] Install / Repair Dependencies
echo    [7] Check GPU Capabilities
echo    [8] Clean Cache + Temp
echo    [9] Open Logs Folder
echo    [0] Exit
echo.
set /p choice=Enter choice:

if "%choice%"=="1" goto :run_normal
if "%choice%"=="2" goto :run_safe
if "%choice%"=="3" goto :run_debug
if "%choice%"=="4" goto :run_perf
if "%choice%"=="5" goto :run_lowram
if "%choice%"=="6" goto :reinstall
if "%choice%"=="7" goto :gpu
if "%choice%"=="8" goto :clean
if "%choice%"=="9" goto :logs
if "%choice%"=="0" exit /b 0
goto :menu

:run_normal
"%PY%" -m app
goto :after_run

:run_safe
"%PY%" -m app --safe-mode
goto :after_run

:run_debug
"%PY%" -m app --debug
goto :after_run

:run_perf
"%PY%" -m app --performance
goto :after_run

:run_lowram
"%PY%" -m app --low-ram
goto :after_run

:reinstall
call "%ROOT%setup.bat"
pause
goto :menu

:gpu
"%PY%" -c "from app.utils.gpu import detect; print(detect())"
pause
goto :menu

:clean
"%PY%" -c "from app.utils.paths import ProjectPaths; from app.backend.cache import clear_temp, clear_cache; p = ProjectPaths.discover(); print('temp:', clear_temp(p, 0)); print('cache:', clear_cache(p, 0))"
pause
goto :menu

:logs
start "" "%ROOT%logs"
goto :menu

:after_run
echo.
echo Application exited.  Press any key to return to the menu.
pause >nul
goto :menu
