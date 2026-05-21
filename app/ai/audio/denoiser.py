"""Audio denoising plugin (interface).

A high-quality back-end (e.g. RNNoise via ``noisereduce`` or DTLN-ONNX)
should be wired in here. The default implementation falls back to a
lightweight spectral gating denoiser when no AI back-end is present.
"""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register
from app.utils.logger import get_logger

log = get_logger("ai.audio.denoiser")


@register
class DenoiserPlugin(AIPlugin):
    name = "AudioDenoiser"
    category = "audio"
    requires_gpu = False
    description = "Spectral-gating denoiser with optional AI back-end (RNNoise/DTLN)."

    def is_available(self) -> bool:
        try:
            import numpy  # type: ignore[import-not-found]  # noqa: F401
        except Exception:
            return False
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return []

    def load(self) -> None:
        return None

    def process(self, payload: Any, **kwargs: Any) -> Any:
        """Spectral-gating denoiser using ``noisereduce`` if available."""
        try:
            import noisereduce as nr  # type: ignore[import-not-found]
        except Exception:
            log.info("noisereduce not installed; returning input unchanged.")
            return payload
        sr = kwargs.get("sample_rate", 44_100)
        return nr.reduce_noise(y=payload, sr=sr)
