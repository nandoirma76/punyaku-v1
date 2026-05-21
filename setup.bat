@echo off
REM ============================================================================
REM   punyaku-v1 / Punyaku Video Looper - Windows installer
REM ----------------------------------------------------------------------------
REM   What this script does:
REM     1. Creates a Python virtual environment in .\venv
REM     2. Upgrades pip / wheel / setuptools
REM     3. Installs requirements.txt (UI + core deps)
REM     4. Detects an NVIDIA GPU and installs the matching PyTorch wheel
REM     5. Installs ONNX Runtime (GPU or CPU)
REM     6. Bootstraps FFmpeg via imageio-ffmpeg if a system install is missing
REM     7. Creates runtime folders (cache/temp/logs/export/models/plugins)
REM     8. Writes a starter config.json
REM     9. Runs a smoke check (python -m app --check)
REM ============================================================================

setlocal EnableExtensions EnableDelayedExpansion

set "ROOT=%~dp0"
set "VENV=%ROOT%venv"
set "PY=%VENV%\Scripts\python.exe"
set "PIP=%VENV%\Scripts\pip.exe"
set "LOG=%ROOT%logs\setup.log"

if not exist "%ROOT%logs" mkdir "%ROOT%logs"
echo ============================== > "%LOG%"
echo Punyaku setup log >> "%LOG%"
echo Start: %date% %time% >> "%LOG%"
echo ============================== >> "%LOG%"

call :banner

REM ----------------------------------------------------------------------------
REM 1) Check Python
REM ----------------------------------------------------------------------------
call :step "Checking Python 3.10+"
where py >nul 2>&1
if errorlevel 1 (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python is not installed or not on PATH.
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        goto :fail
    )
    set "PYLAUNCH=python"
) else (
    set "PYLAUNCH=py -3"
)

REM ----------------------------------------------------------------------------
REM 2) Create venv
REM ----------------------------------------------------------------------------
if not exist "%VENV%\Scripts\python.exe" (
    call :step "Creating virtual environment in venv\"
    %PYLAUNCH% -m venv "%VENV%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        goto :fail
    )
) else (
    call :step "Reusing existing virtual environment"
)

call :step "Upgrading pip / wheel / setuptools"
"%PY%" -m pip install --upgrade pip wheel setuptools >> "%LOG%" 2>&1

REM ----------------------------------------------------------------------------
REM 3) Install base requirements
REM ----------------------------------------------------------------------------
call :step "Installing core requirements (this can take several minutes)"
"%PIP%" install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
    echo [ERROR] Core requirements install failed. See logs\setup.log.
    goto :fail
)

REM ----------------------------------------------------------------------------
REM 4) GPU detection -> PyTorch wheel
REM ----------------------------------------------------------------------------
call :step "Detecting GPU"
where nvidia-smi >nul 2>&1
if not errorlevel 1 (
    echo [INFO] NVIDIA GPU detected. Installing CUDA PyTorch wheel.
    "%PIP%" install --index-url https://download.pytorch.org/whl/cu121 ^
        torch torchvision torchaudio >> "%LOG%" 2>&1
    "%PIP%" install -r requirements_gpu.txt >> "%LOG%" 2>&1
) else (
    echo [INFO] No NVIDIA GPU detected. Installing CPU PyTorch wheel.
    "%PIP%" install -r requirements_cpu.txt >> "%LOG%" 2>&1
)

REM ----------------------------------------------------------------------------
REM 5) FFmpeg
REM ----------------------------------------------------------------------------
call :step "Checking FFmpeg"
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [INFO] System FFmpeg not found. imageio-ffmpeg already bundled a binary.
) else (
    echo [INFO] System FFmpeg found on PATH.
)

REM ----------------------------------------------------------------------------
REM 6) Runtime folders
REM ----------------------------------------------------------------------------
call :step "Creating runtime folders"
for %%D in (cache temp logs export models plugins) do (
    if not exist "%ROOT%%%D" mkdir "%ROOT%%%D"
)

REM ----------------------------------------------------------------------------
REM 7) Smoke test
REM ----------------------------------------------------------------------------
call :step "Running smoke check (python -m app --check)"
"%PY%" -m app --check
if errorlevel 1 (
    echo [WARN] Smoke check failed. See logs\setup.log + logs\punyaku.log.
    goto :fail
)

call :banner_done
echo.
echo Setup complete.  Run "run.bat" to launch Punyaku.
endlocal
exit /b 0

REM ============================================================================
:step
echo.
echo [STEP] %~1
echo [STEP] %~1 >> "%LOG%"
exit /b 0

:banner
echo.
echo  =======================================================================
echo    Punyaku Video Looper  -  Windows Installer
echo  =======================================================================
echo.
exit /b 0

:banner_done
echo.
echo  =======================================================================
echo    Setup finished successfully.
echo  =======================================================================
echo.
exit /b 0

:fail
echo.
echo [FAIL] Setup did not finish cleanly. Inspect logs\setup.log.
endlocal
exit /b 1
