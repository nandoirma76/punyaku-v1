"""FFmpeg wrapper: discovery, probing, and command builders.

The wrapper deliberately avoids depending on ``ffmpeg-python`` so it works
out of the box with system FFmpeg or the binary shipped by
``imageio-ffmpeg`` (used as a portable fallback for the Windows installer).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.utils.logger import get_logger

log = get_logger("ffmpeg")


class FFmpegNotFoundError(RuntimeError):
    """FFmpeg / ffprobe binaries could not be located."""


@dataclass(frozen=True)
class FFmpegBinaries:
    ffmpeg: str
    ffprobe: str


def _imageio_ffmpeg_binary() -> str | None:
    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]
    except Exception:
        return None
    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def discover_ffmpeg() -> FFmpegBinaries:
    """Locate FFmpeg + ffprobe in PATH, imageio bundle, or local install/."""
    ffmpeg = shutil.which("ffmpeg") or _imageio_ffmpeg_binary()
    ffprobe = shutil.which("ffprobe")

    if not ffprobe and ffmpeg:
        candidate = Path(ffmpeg).with_name("ffprobe")
        if candidate.exists():
            ffprobe = str(candidate)

    if not ffmpeg or not ffprobe:
        raise FFmpegNotFoundError(
            "FFmpeg / ffprobe not found. Run setup.bat (Windows) or setup.sh (Linux), "
            "or install FFmpeg manually and ensure it is on PATH."
        )
    return FFmpegBinaries(ffmpeg=ffmpeg, ffprobe=ffprobe)


@dataclass
class MediaInfo:
    path: Path
    duration_s: float
    width: int
    height: int
    fps: float
    video_codec: str
    audio_codec: str | None
    sample_rate: int | None
    channels: int | None
    bit_rate: int | None
    container: str
    has_audio: bool

    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height else 0.0


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_fps(rate: str | None) -> float:
    if not rate or rate == "0/0":
        return 0.0
    if "/" in rate:
        num, den = rate.split("/", 1)
        n = _safe_float(num)
        d = _safe_float(den, default=1.0) or 1.0
        return n / d
    return _safe_float(rate)


def probe_media(path: Path | str, binaries: FFmpegBinaries | None = None) -> MediaInfo:
    """Run ``ffprobe -of json -show_streams -show_format`` and parse the result."""
    bins = binaries or discover_ffmpeg()
    p = Path(path)
    cmd = [
        bins.ffprobe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(p),
    ]
    log.debug("ffprobe: {}", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {p}: {result.stderr.strip()}")
    data = json.loads(result.stdout or "{}")

    fmt = data.get("format", {}) or {}
    streams = data.get("streams", []) or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)

    return MediaInfo(
        path=p,
        duration_s=_safe_float(fmt.get("duration"), 0.0),
        width=_safe_int(v.get("width")),
        height=_safe_int(v.get("height")),
        fps=_parse_fps(v.get("r_frame_rate") or v.get("avg_frame_rate")),
        video_codec=str(v.get("codec_name") or "unknown"),
        audio_codec=str(a.get("codec_name")) if a else None,
        sample_rate=_safe_int(a.get("sample_rate")) if a else None,
        channels=_safe_int(a.get("channels")) if a else None,
        bit_rate=_safe_int(fmt.get("bit_rate")) or None,
        container=str(fmt.get("format_name", "unknown")),
        has_audio=a is not None,
    )


def run_ffmpeg(
    args: list[str],
    binaries: FFmpegBinaries | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a single FFmpeg command and return the completed process."""
    bins = binaries or discover_ffmpeg()
    cmd = [bins.ffmpeg, "-hide_banner", "-y", *args]
    log.debug("ffmpeg: {}", " ".join(cmd))
    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )


def select_hardware_encoder(
    requested_codec: str,
    prefer_gpu: bool,
    available_encoders: set[str] | None = None,
) -> str:
    """Pick the best available encoder for ``requested_codec``.

    Encoder priority is NVIDIA NVENC > AMD AMF > Intel QuickSync > software.
    Pass a pre-computed ``available_encoders`` set to skip the FFmpeg probe.
    """
    if not prefer_gpu:
        return requested_codec

    encoders = available_encoders if available_encoders is not None else list_encoders()
    codec_map = {
        "libx264": ["h264_nvenc", "h264_amf", "h264_qsv", "libx264"],
        "libx265": ["hevc_nvenc", "hevc_amf", "hevc_qsv", "libx265"],
        "libvpx-vp9": ["vp9_qsv", "libvpx-vp9"],
        "libaom-av1": ["av1_nvenc", "av1_qsv", "libaom-av1"],
    }
    chain = codec_map.get(requested_codec, [requested_codec])
    for enc in chain:
        if enc in encoders:
            return enc
    return requested_codec


def list_encoders(binaries: FFmpegBinaries | None = None) -> set[str]:
    """Return the set of FFmpeg encoder names available on this machine."""
    try:
        bins = binaries or discover_ffmpeg()
    except FFmpegNotFoundError:
        return set()
    result = subprocess.run(
        [bins.ffmpeg, "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
        check=False,
    )
    encoders: set[str] = set()
    in_table = False
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not in_table:
            if stripped.startswith("---"):
                in_table = True
            continue
        # Encoder rows look like " V..... libx264   ..."
        if not stripped or not (line.startswith(" ") or line.startswith("\t")):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        flags = parts[0]
        if len(flags) >= 1 and flags[0] in "VAS" and len(flags) <= 6:
            encoders.add(parts[1])
    return encoders
