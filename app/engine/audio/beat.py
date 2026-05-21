"""Beat / BPM analysis using librosa.

Used to align loop boundaries to musical beats so the crossfade lands on a
musically natural transition.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.utils.logger import get_logger

log = get_logger("audio.beat")


@dataclass(frozen=True)
class BeatInfo:
    bpm: float
    beat_times_s: list[float]
    duration_s: float
    sample_rate: int


def analyze(path: Path | str, sr: int | None = 22_050) -> BeatInfo:
    """Run librosa beat tracker on ``path`` and return :class:`BeatInfo`."""
    try:
        import librosa  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "librosa is required for beat analysis. Install via requirements.txt."
        ) from exc

    y, sample_rate = librosa.load(str(path), sr=sr, mono=True)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate, units="time")
    duration = float(librosa.get_duration(y=y, sr=sample_rate))
    tempo_value = float(tempo[0]) if hasattr(tempo, "__len__") and len(tempo) else float(tempo)
    return BeatInfo(
        bpm=tempo_value,
        beat_times_s=[float(t) for t in beats],
        duration_s=duration,
        sample_rate=int(sample_rate),
    )


def snap_to_beat(time_s: float, beats: list[float], tolerance_s: float = 0.25) -> float:
    """Snap ``time_s`` to the closest beat within ``tolerance_s`` seconds."""
    if not beats:
        return time_s
    closest = min(beats, key=lambda b: abs(b - time_s))
    return closest if abs(closest - time_s) <= tolerance_s else time_s
