"""Audio normalization helpers (peak + LUFS-style RMS)."""

from __future__ import annotations

from app.utils.logger import get_logger

log = get_logger("audio.normalize")


def _np():
    import numpy as np  # type: ignore[import-not-found]
    return np


def peak_normalize(buf, target_db: float = -1.0):
    """Scale ``buf`` so its loudest sample matches ``target_db``."""
    np = _np()
    a = np.asarray(buf, dtype=np.float32)
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    if peak <= 1e-9:
        return a
    target_amp = 10.0 ** (target_db / 20.0)
    return a * (target_amp / peak)


def rms_normalize(buf, target_db: float = -16.0):
    """Crude loudness normalization using RMS (LUFS-ish)."""
    np = _np()
    a = np.asarray(buf, dtype=np.float32)
    rms = float(np.sqrt(np.mean(a.astype(np.float64) ** 2))) if a.size else 0.0
    if rms <= 1e-9:
        return a
    target_amp = 10.0 ** (target_db / 20.0)
    gain = target_amp / rms
    return np.clip(a * gain, -1.0, 1.0)
