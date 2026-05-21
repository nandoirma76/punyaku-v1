"""High-level smoke tests.

These tests must run on a headless CI box without GPU or FFmpeg.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "app",
        "app.version",
        "app.utils.paths",
        "app.utils.logger",
        "app.utils.ffmpeg",
        "app.utils.hardware",
        "app.utils.gpu",
        "app.config.settings",
        "app.engine.video.frame_match",
        "app.engine.video.optical_flow",
        "app.engine.audio.crossfade",
        "app.engine.audio.beat",
        "app.engine.audio.normalize",
        "app.engine.loop.loop_engine",
        "app.engine.visualizer.spectrum",
        "app.export.exporter",
        "app.export.presets.presets",
        "app.export.queue",
        "app.ai.base",
        "app.ai.upscale.realesrgan_plugin",
        "app.ai.upscale.waifu2x_plugin",
        "app.ai.upscale.anime4k_plugin",
        "app.ai.interpolation.rife_plugin",
        "app.ai.interpolation.dain_plugin",
        "app.ai.restoration.gfpgan_plugin",
        "app.ai.audio.denoiser",
        "app.ai.generative.transition",
        "app.streaming.rtmp",
        "app.streaming.obs",
        "app.cloud.cloud_render",
        "app.backend.project",
        "app.backend.cache",
        "app.backend.recovery",
    ],
)
def test_imports(module: str) -> None:
    importlib.import_module(module)


def test_ai_plugins_registered() -> None:
    import app.ai.audio.denoiser  # noqa: F401
    import app.ai.generative.transition  # noqa: F401
    import app.ai.interpolation.dain_plugin  # noqa: F401
    import app.ai.interpolation.rife_plugin  # noqa: F401
    import app.ai.restoration.gfpgan_plugin  # noqa: F401
    import app.ai.upscale.anime4k_plugin  # noqa: F401

    # All concrete plugins are imported via their module's @register decorator.
    import app.ai.upscale.realesrgan_plugin  # noqa: F401
    import app.ai.upscale.waifu2x_plugin  # noqa: F401
    from app.ai.base import list_plugins

    plugins = list_plugins()
    names = {p().name for p in plugins}
    assert {
        "Real-ESRGAN",
        "Waifu2x",
        "Anime4K",
        "RIFE",
        "DAIN",
        "GFPGAN",
        "AudioDenoiser",
        "AI Transition",
    }.issubset(names)


def test_export_presets() -> None:
    from app.export.presets.presets import get, list_presets

    keys = {p.key for p in list_presets()}
    for required in ("youtube_1080p", "tiktok", "shorts", "reels", "obs", "wallpaper_engine"):
        assert required in keys
        preset = get(required)
        assert preset.width > 0 and preset.height > 0 and preset.fps > 0
