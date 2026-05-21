"""``.punyaku`` project file format (JSON-based) + load/save helpers."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.utils.logger import get_logger
from app.version import __version__

log = get_logger("backend.project")

PROJECT_SUFFIX = ".punyaku"


@dataclass
class ClipReference:
    path: str
    role: str = "video"   # video|audio|background_music
    in_point_s: float = 0.0
    out_point_s: float = 0.0
    notes: str = ""


@dataclass
class LoopConfig:
    target_duration_s: float = 60.0
    mode: str = "normal"
    transition: str = "crossfade"
    crossfade_ms: int = 1500
    frame_match_method: str = "auto"
    search_window_s: float = 2.0


@dataclass
class ExportConfig:
    preset_key: str = "youtube_1080p"
    output_dir: str = "export"
    prefer_gpu: bool = True


@dataclass
class Project:
    name: str = "Untitled"
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    app_version: str = __version__
    clips: list[ClipReference] = field(default_factory=list)
    loop: LoopConfig = field(default_factory=LoopConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    metadata: dict[str, str] = field(default_factory=dict)

    def touch(self) -> None:
        self.modified_at = time.time()

    def save(self, path: Path) -> Path:
        if not str(path).endswith(PROJECT_SUFFIX):
            path = path.with_suffix(PROJECT_SUFFIX)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.touch()
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.info("Saved project: {}", path)
        return path

    @classmethod
    def load(cls, path: Path) -> Project:
        log.info("Loading project: {}", path)
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        clips = [ClipReference(**c) for c in data.get("clips", [])]
        loop = LoopConfig(**data.get("loop", {}))
        export_cfg = ExportConfig(**data.get("export", {}))
        return cls(
            name=data.get("name", "Untitled"),
            created_at=data.get("created_at", time.time()),
            modified_at=data.get("modified_at", time.time()),
            app_version=data.get("app_version", __version__),
            clips=clips,
            loop=loop,
            export=export_cfg,
            metadata=data.get("metadata", {}),
        )
