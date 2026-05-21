"""Tests for settings persistence."""

from __future__ import annotations

import json
from pathlib import Path

from app.config.settings import load_settings
from app.utils.paths import ProjectPaths, ensure_runtime_dirs


def _paths(tmp_path: Path) -> ProjectPaths:
    return ProjectPaths(
        root=tmp_path,
        app_dir=tmp_path / "app",
        config_dir=tmp_path / "config",
        cache_dir=tmp_path / "cache",
        temp_dir=tmp_path / "temp",
        logs_dir=tmp_path / "logs",
        export_dir=tmp_path / "export",
        models_dir=tmp_path / "models",
        plugins_dir=tmp_path / "plugins",
        assets_dir=tmp_path / "assets",
    )


def test_defaults_when_no_config(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ensure_runtime_dirs(paths)
    s = load_settings(paths)
    assert s.defaults.video.fps == 30
    assert s.defaults.loop.target_duration_s == 60.0
    assert s.defaults.ui.theme == "dark_neon"


def test_round_trip_save_load(tmp_path: Path) -> None:
    paths = _paths(tmp_path)
    ensure_runtime_dirs(paths)
    s = load_settings(paths)
    s.defaults.ui.theme = "cyberpunk"
    s.defaults.performance.max_workers = 8
    config = s.save()
    assert config.exists()

    loaded = load_settings(paths)
    assert loaded.defaults.ui.theme == "cyberpunk"
    assert loaded.defaults.performance.max_workers == 8

    raw = json.loads(config.read_text())
    assert "runtime" not in raw  # runtime flags must not be persisted
