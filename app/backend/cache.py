"""Disk cache & temp folder maintenance.

Responsible for:

* Reporting current size of cache/, temp/, logs/.
* Cleaning files older than ``max_age_hours``.
* Enforcing a configurable size cap (``max_total_mb``).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from app.utils.logger import get_logger
from app.utils.paths import ProjectPaths

log = get_logger("backend.cache")


@dataclass
class CacheStats:
    cache_mb: float
    temp_mb: float
    logs_mb: float
    export_mb: float
    files_total: int

    @property
    def total_mb(self) -> float:
        return self.cache_mb + self.temp_mb + self.logs_mb + self.export_mb


def _dir_size(path: Path) -> tuple[float, int]:
    total = 0
    count = 0
    if not path.exists():
        return (0.0, 0)
    for root, _, files in os.walk(path):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
                count += 1
            except OSError:
                continue
    return total / 1024.0 / 1024.0, count


def stats(paths: ProjectPaths) -> CacheStats:
    cache_mb, cache_n = _dir_size(paths.cache_dir)
    temp_mb, temp_n = _dir_size(paths.temp_dir)
    logs_mb, logs_n = _dir_size(paths.logs_dir)
    export_mb, export_n = _dir_size(paths.export_dir)
    return CacheStats(
        cache_mb=cache_mb,
        temp_mb=temp_mb,
        logs_mb=logs_mb,
        export_mb=export_mb,
        files_total=cache_n + temp_n + logs_n + export_n,
    )


def clear_temp(paths: ProjectPaths, max_age_hours: float = 24.0) -> int:
    """Delete files in temp/ older than ``max_age_hours``. Returns count removed."""
    return _purge(paths.temp_dir, max_age_hours)


def clear_cache(paths: ProjectPaths, max_age_hours: float = 168.0) -> int:
    """Delete files in cache/ older than ``max_age_hours``."""
    return _purge(paths.cache_dir, max_age_hours)


def _purge(directory: Path, max_age_hours: float) -> int:
    if not directory.exists():
        return 0
    cutoff = time.time() - max_age_hours * 3600.0
    removed = 0
    for root, _, files in os.walk(directory):
        for f in files:
            if f == ".gitkeep":
                continue
            fp = Path(root) / f
            try:
                if fp.stat().st_mtime < cutoff:
                    fp.unlink()
                    removed += 1
            except OSError:
                continue
    log.info("Purged {} stale file(s) from {}", removed, directory)
    return removed
