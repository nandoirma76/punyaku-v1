#!/usr/bin/env bash
# ============================================================================
#  punyaku-v1 - Linux / macOS installer
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="${ROOT}/venv"
PY="${VENV}/bin/python"
PIP="${VENV}/bin/pip"
LOG="${ROOT}/logs/setup.log"

mkdir -p "${ROOT}/logs"
: > "${LOG}"

step() { printf "\n\033[1;36m[STEP]\033[0m %s\n" "$1" | tee -a "${LOG}"; }
info() { printf "\033[0;32m[INFO]\033[0m %s\n" "$1" | tee -a "${LOG}"; }
warn() { printf "\033[0;33m[WARN]\033[0m %s\n" "$1" | tee -a "${LOG}"; }
err()  { printf "\033[0;31m[ERR ]\033[0m %s\n" "$1" | tee -a "${LOG}"; }

cat <<'BANNER'
========================================================================
  Punyaku Video Looper  -  Linux / macOS installer
========================================================================
BANNER

# ---- 1) Python ----
step "Checking Python 3.10+"
if ! command -v python3 >/dev/null 2>&1; then
    err "python3 not found. Install Python 3.10+ first."
    exit 1
fi
PY_VERSION="$(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:2])))')"
info "Python: ${PY_VERSION}"

# ---- 2) Virtual env ----
if [ ! -x "${PY}" ]; then
    step "Creating virtual environment in venv/"
    python3 -m venv "${VENV}"
fi

step "Upgrading pip / wheel / setuptools"
"${PY}" -m pip install --upgrade pip wheel setuptools >>"${LOG}" 2>&1

# ---- 3) Base requirements ----
step "Installing core requirements (this can take several minutes)"
"${PIP}" install -r "${ROOT}/requirements.txt" >>"${LOG}" 2>&1

# ---- 4) GPU detection ----
step "Detecting GPU"
if command -v nvidia-smi >/dev/null 2>&1; then
    info "NVIDIA GPU detected. Installing CUDA PyTorch wheels."
    "${PIP}" install --index-url https://download.pytorch.org/whl/cu121 \
        torch torchvision torchaudio >>"${LOG}" 2>&1 || warn "CUDA torch install failed; using default index."
    "${PIP}" install -r "${ROOT}/requirements_gpu.txt" >>"${LOG}" 2>&1
elif [ "$(uname)" = "Darwin" ]; then
    info "macOS detected. Installing default PyTorch (MPS support included)."
    "${PIP}" install -r "${ROOT}/requirements_cpu.txt" >>"${LOG}" 2>&1
else
    info "No NVIDIA GPU detected. Installing CPU-only PyTorch."
    "${PIP}" install -r "${ROOT}/requirements_cpu.txt" >>"${LOG}" 2>&1
fi

# ---- 5) FFmpeg ----
step "Checking FFmpeg"
if command -v ffmpeg >/dev/null 2>&1; then
    info "System FFmpeg found: $(command -v ffmpeg)"
else
    warn "System FFmpeg missing. imageio-ffmpeg already bundled a portable binary."
fi

# ---- 6) Runtime folders ----
step "Creating runtime folders"
for d in cache temp logs export models plugins; do
    mkdir -p "${ROOT}/${d}"
done

# ---- 7) Smoke test ----
step "Running smoke check (python -m app --check)"
if ! "${PY}" -m app --check; then
    err "Smoke check failed. See logs/setup.log."
    exit 1
fi

cat <<'DONE'
========================================================================
  Setup finished successfully.
  Run "./run.sh" to launch Punyaku.
========================================================================
DONE
