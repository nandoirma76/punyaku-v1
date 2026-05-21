"""Tests for the .punyaku project file format."""

from __future__ import annotations

from pathlib import Path

from app.backend.project import ClipReference, ExportConfig, LoopConfig, Project


def test_project_round_trip(tmp_path: Path) -> None:
    project = Project(
        name="Sample",
        clips=[ClipReference(path="/tmp/clip.mp4", role="video", in_point_s=1.0, out_point_s=4.0)],
        loop=LoopConfig(target_duration_s=120.0, mode="ping_pong"),
        export=ExportConfig(preset_key="tiktok"),
        metadata={"author": "punyaku"},
    )
    out = project.save(tmp_path / "demo")
    assert out.exists()
    assert out.suffix == ".punyaku"

    loaded = Project.load(out)
    assert loaded.name == "Sample"
    assert loaded.loop.mode == "ping_pong"
    assert loaded.export.preset_key == "tiktok"
    assert loaded.clips[0].in_point_s == 1.0
