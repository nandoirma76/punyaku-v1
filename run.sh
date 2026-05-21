#!/usr/bin/env bash
# ============================================================================
#  punyaku-v1 - Linux / macOS launcher with mode menu
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ROOT}/venv"
PY="${VENV}/bin/python"

if [ ! -x "${PY}" ]; then
    echo "[ERROR] Virtual environment missing. Run ./setup.sh first."
    exit 1
fi

# Direct CLI passthrough: ./run.sh --safe-mode --debug ...
if [ "$#" -gt 0 ]; then
    exec "${PY}" -m app "$@"
fi

while true; do
    cat <<'MENU'

  =======================================================================
    Punyaku Video Looper  -  Launcher
  =======================================================================
    [1] Run Application (Normal)
    [2] Run Safe Mode (no GPU, minimal plugins)
    [3] Run Debug Mode
    [4] Run Performance Mode
    [5] Run Low-RAM Mode
    [6] Install / Repair Dependencies
    [7] Check GPU Capabilities
    [8] Clean Cache + Temp
    [9] Open Logs Folder (xdg-open)
    [0] Exit

MENU
    read -rp "Enter choice: " choice
    case "${choice}" in
        1) "${PY}" -m app ;;
        2) "${PY}" -m app --safe-mode ;;
        3) "${PY}" -m app --debug ;;
        4) "${PY}" -m app --performance ;;
        5) "${PY}" -m app --low-ram ;;
        6) "${ROOT}/setup.sh" ;;
        7) "${PY}" -c "from app.utils.gpu import detect; print(detect())" ;;
        8) "${PY}" -c "from app.utils.paths import ProjectPaths; from app.backend.cache import clear_temp, clear_cache; p = ProjectPaths.discover(); print('temp removed:', clear_temp(p, 0)); print('cache removed:', clear_cache(p, 0))" ;;
        9) command -v xdg-open >/dev/null 2>&1 && xdg-open "${ROOT}/logs" || open "${ROOT}/logs" 2>/dev/null || echo "Open ${ROOT}/logs manually." ;;
        0) exit 0 ;;
        *) echo "Unknown option." ;;
    esac
done
