"""Typed application settings.

Settings are split into three layers:

* :class:`Defaults`    - hard-coded sane defaults baked into the code.
* :class:`UserConfig`  - user-overridable JSON saved next to the project.
* :class:`RuntimeFlags`- per-launch CLI flags (debug / safe / low-ram / ...).

The merged result is :class:`Settings`, used throughout the codebase.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.utils.paths import ProjectPaths

DEFAULT_CONFIG_FILENAME = "config.json"


@dataclass
class VideoDefaults:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "libx264"
    pix_fmt: str = "yuv420p"
    crf: int = 18
    preset: str = "medium"
    container: str = "mp4"


@dataclass
class AudioDefaults:
    sample_rate: int = 48_000
    channels: int = 2
    codec: str = "aac"
    bitrate: str = "192k"
    crossfade_ms: int = 1500
    normalize: bool = True


@dataclass
class LoopDefaults:
    target_duration_s: float = 60.0
    search_window_s: float = 2.0
    transition: str = "crossfade"      # crossfade|motion_blend|dissolve|morph|cinematic
    mode: str = "normal"               # normal|reverse|ping_pong|infinite|wallpaper|...
    motion_smoothing: bool = True
    frame_match_method: str = "auto"   # auto|pixel|optical_flow|hist


@dataclass
class ExportDefaults:
    preset: str = "youtube_1080p"
    output_dir: str = "export"
    keep_intermediate: bool = False
    use_gpu_encoder: bool = True


@dataclass
class PerformanceDefaults:
    max_workers: int = 4
    chunk_size_frames: int = 256
    cache_size_mb: int = 4096
    background_priority: bool = True
    allow_hardware_decode: bool = True


@dataclass
class UiDefaults:
    theme: str = "dark_neon"           # dark_neon|dark_glass|midnight|cyberpunk
    accent: str = "#7C5CFF"
    show_fps_overlay: bool = False
    show_hardware_monitor: bool = True
    smooth_animations: bool = True
    language: str = "id"               # id|en


@dataclass
class Defaults:
    video: VideoDefaults = field(default_factory=VideoDefaults)
    audio: AudioDefaults = field(default_factory=AudioDefaults)
    loop: LoopDefaults = field(default_factory=LoopDefaults)
    export: ExportDefaults = field(default_factory=ExportDefaults)
    performance: PerformanceDefaults = field(default_factory=PerformanceDefaults)
    ui: UiDefaults = field(default_factory=UiDefaults)


@dataclass
class RuntimeFlags:
    safe_mode: bool = False
    debug: bool = False
    low_ram: bool = False
    performance: bool = False
    startup_project: str | None = None


@dataclass
class Settings:
    paths: ProjectPaths
    defaults: Defaults = field(default_factory=Defaults)
    runtime: RuntimeFlags = field(default_factory=RuntimeFlags)
    recent_projects: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # ProjectPaths is a frozen dataclass with Paths -> str friendly via __str__
        data["paths"] = self.paths.as_dict()
        return data

    def save(self, path: Path | None = None) -> Path:
        target = path or (self.paths.config_dir / DEFAULT_CONFIG_FILENAME)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.to_dict()
        # don't persist runtime flags
        payload.pop("runtime", None)
        target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return target


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge_dict(out[key], value)
        else:
            out[key] = value
    return out


def load_settings(paths: ProjectPaths) -> Settings:
    """Load user config from disk if present, falling back to defaults."""
    cfg_path = paths.config_dir / DEFAULT_CONFIG_FILENAME
    defaults = Defaults()

    if cfg_path.exists():
        try:
            raw = json.loads(cfg_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raw = {}
        defaults_dict = asdict(defaults)
        merged = _merge_dict(defaults_dict, raw.get("defaults", {}))
        defaults = _rehydrate_defaults(merged)
        recent = list(raw.get("recent_projects", []))
    else:
        recent = []

    return Settings(
        paths=paths,
        defaults=defaults,
        recent_projects=recent,
    )


def _rehydrate_defaults(data: dict[str, Any]) -> Defaults:
    return Defaults(
        video=VideoDefaults(**data.get("video", {})),
        audio=AudioDefaults(**data.get("audio", {})),
        loop=LoopDefaults(**data.get("loop", {})),
        export=ExportDefaults(**data.get("export", {})),
        performance=PerformanceDefaults(**data.get("performance", {})),
        ui=UiDefaults(**data.get("ui", {})),
    )
