@echo off
REM Clean cache + temp folders (best-effort, never deletes models/ or export/).

setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%venv\Scripts\python.exe"

if exist "%PY%" (
    "%PY%" -c "from app.utils.paths import ProjectPaths; from app.backend.cache import clear_temp, clear_cache; p = ProjectPaths.discover(); print('temp removed:', clear_temp(p, 0)); print('cache removed:', clear_cache(p, 0))"
) else (
    if exist "%ROOT%cache" rmdir /s /q "%ROOT%cache"
    if exist "%ROOT%temp" rmdir /s /q "%ROOT%temp"
    mkdir "%ROOT%cache"
    mkdir "%ROOT%temp"
    echo [INFO] Wiped cache/ and temp/ directories.
)
endlocal
exit /b 0
