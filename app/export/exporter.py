"""Public export API. Connects loop engine + presets + FFmpeg encoder choice."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.engine.loop.loop_engine import (
    LoopEngine,
    LoopMode,
    LoopRequest,
    LoopResult,
    Transition,
)
from app.export.presets.presets import ExportPreset, get as get_preset
from app.utils.logger import get_logger

log = get_logger("exporter")


@dataclass
class ExportJob:
    source: Path
    output: Path
    preset_key: str = "youtube_1080p"
    duration_s: float = 60.0
    mode: LoopMode = LoopMode.NORMAL
    transition: Transition = Transition.CROSSFADE
    crossfade_ms: int = 1500
    prefer_gpu: bool = True
    normalize_audio: bool = True


class Exporter:
    """Thin orchestrator that translates :class:`ExportJob` -> :class:`LoopRequest`."""

    def __init__(self) -> None:
        self._engine = LoopEngine()

    def export(self, job: ExportJob, progress=None) -> LoopResult:
        preset = get_preset(job.preset_key)
        req = self._to_request(job, preset)
        log.info("Exporting {} -> {} (preset={})", job.source, job.output, preset.key)
        return self._engine.build(req, progress=progress)

    def _to_request(self, job: ExportJob, preset: ExportPreset) -> LoopRequest:
        return LoopRequest(
            source=Path(job.source),
            output=Path(job.output),
            target_duration_s=job.duration_s,
            mode=job.mode,
            transition=job.transition,
            crossfade_ms=job.crossfade_ms,
            fps=preset.fps,
            width=preset.width,
            height=preset.height,
            video_codec=preset.video_codec,
            audio_codec=preset.audio_codec if preset.audio_codec != "none" else "aac",
            crf=preset.crf,
            preset=preset.preset,
            prefer_gpu=job.prefer_gpu,
            normalize_audio=job.normalize_audio,
        )
