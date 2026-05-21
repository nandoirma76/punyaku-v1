"""Crash recovery: write a marker file at startup, clear on graceful exit.

If a marker is present when the app starts, the previous session crashed
and we can offer to restore the autosave found in ``temp/autosave/``.
"""

from __future__ import annotations

import atexit
import json
import os
import threading
import time
from dataclasses import asdict
from pathlib import Path

from app.backend.project import Project
from app.utils.logger import get_logger
from app.utils.paths import ProjectPaths

log = get_logger("backend.recovery")

MARKER = "session.running"
AUTOSAVE = "autosave/last_project.punyaku.json"


class RecoveryManager:
    def __init__(self, paths: ProjectPaths, autosave_interval_s: float = 60.0) -> None:
        self.paths = paths
        self.autosave_interval_s = autosave_interval_s
        self._marker = paths.temp_dir / MARKER
        self._autosave = paths.temp_dir / AUTOSAVE
        self._timer: threading.Timer | None = None
        self._project_supplier = None

    def begin_session(self) -> None:
        self._marker.parent.mkdir(parents=True, exist_ok=True)
        self._marker.write_text(str(os.getpid()), encoding="utf-8")
        atexit.register(self.end_session)
        log.info("Recovery marker created at {}", self._marker)

    def end_session(self) -> None:
        try:
            if self._marker.exists():
                self._marker.unlink()
        except OSError:  # pragma: no cover
            pass
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def previous_session_crashed(self) -> bool:
        return self._marker.exists()

    def autosave_path(self) -> Path:
        return self._autosave

    def register_project_supplier(self, supplier) -> None:
        self._project_supplier = supplier
        self._schedule()

    def _schedule(self) -> None:
        self._timer = threading.Timer(self.autosave_interval_s, self._tick)
        self._timer.daemon = True
        self._timer.start()

    def _tick(self) -> None:
        try:
            project = self._project_supplier() if self._project_supplier else None
            if project is not None:
                self._write_autosave(project)
        except Exception:  # pragma: no cover - never break the app
            log.exception("autosave failed")
        finally:
            self._schedule()

    def _write_autosave(self, project: Project) -> None:
        self._autosave.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(project)
        payload["autosaved_at"] = time.time()
        self._autosave.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        log.debug("Autosaved project -> {}", self._autosave)
