"""GPU detection helpers.

The goal is to answer two questions quickly and without crashing:

1. Is there a CUDA-capable GPU? (drives PyTorch wheel selection in setup.bat)
2. Which FFmpeg hardware encoders should we offer?

The detector intentionally does **not** import PyTorch at module load time -
the GUI must be able to start even on machines without torch installed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.ffmpeg import FFmpegNotFoundError, discover_ffmpeg, list_encoders
from app.utils.logger import get_logger

log = get_logger("gpu")


@dataclass
class GpuCapabilities:
    has_cuda: bool
    has_rocm: bool
    has_mps: bool
    cuda_version: str | None
    devices: list[str]
    ffmpeg_encoders: set[str]

    def best_hw_encoder(self, codec: str) -> str | None:
        nvenc = {"libx264": "h264_nvenc", "libx265": "hevc_nvenc"}.get(codec)
        amf = {"libx264": "h264_amf", "libx265": "hevc_amf"}.get(codec)
        qsv = {"libx264": "h264_qsv", "libx265": "hevc_qsv"}.get(codec)
        for enc in (nvenc, amf, qsv):
            if enc and enc in self.ffmpeg_encoders:
                return enc
        return None


def _detect_torch() -> tuple[bool, bool, bool, str | None, list[str]]:
    """Return (has_cuda, has_rocm, has_mps, cuda_version, device_names)."""
    try:
        import torch  # type: ignore[import-not-found]
    except Exception:
        return (False, False, False, None, [])

    has_cuda = bool(getattr(torch, "cuda", None) and torch.cuda.is_available())
    has_rocm = bool(getattr(torch.version, "hip", None))
    has_mps = bool(
        getattr(torch.backends, "mps", None)
        and torch.backends.mps.is_available()
    )
    cuda_version = getattr(torch.version, "cuda", None)
    devices: list[str] = []
    if has_cuda:
        for i in range(torch.cuda.device_count()):
            try:
                devices.append(torch.cuda.get_device_name(i))
            except Exception:
                devices.append(f"cuda:{i}")
    return has_cuda, has_rocm, has_mps, cuda_version, devices


def detect() -> GpuCapabilities:
    """Detect GPU + hardware encoder capabilities. Never raises."""
    has_cuda, has_rocm, has_mps, cuda_version, devices = _detect_torch()
    try:
        encoders = list_encoders(discover_ffmpeg())
    except FFmpegNotFoundError:
        encoders = set()
    caps = GpuCapabilities(
        has_cuda=has_cuda,
        has_rocm=has_rocm,
        has_mps=has_mps,
        cuda_version=cuda_version,
        devices=devices,
        ffmpeg_encoders=encoders,
    )
    log.info(
        "GPU detection: cuda={} rocm={} mps={} devices={} hw_encoders={}",
        has_cuda,
        has_rocm,
        has_mps,
        devices,
        sorted(encoders),
    )
    return caps
