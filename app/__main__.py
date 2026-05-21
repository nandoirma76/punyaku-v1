"""Entry-point: ``python -m app``.

Parses CLI flags, configures logging, and launches the PyQt6 UI.
For headless/CI environments the ``--check`` flag performs a smoke test
without instantiating the GUI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.config.settings import Settings, load_settings
from app.utils.logger import configure_logger, get_logger
from app.utils.paths import ProjectPaths, ensure_runtime_dirs
from app.version import __display_name__, __version__


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="punyaku",
        description=f"{__display_name__} v{__version__}",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Disable GPU acceleration and heavy plugins (recovery mode).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose logging and developer tools.",
    )
    parser.add_argument(
        "--low-ram",
        action="store_true",
        help="Aggressive memory saving (smaller cache, smaller previews).",
    )
    parser.add_argument(
        "--performance",
        action="store_true",
        help="Maximize throughput at the cost of UI smoothness.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate environment + imports then exit (CI / smoke test).",
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=None,
        help="Open a .punyaku project file on launch.",
    )
    return parser


def _smoke_check(settings: Settings) -> int:
    """Headless validation: import every public sub-package."""
    log = get_logger("smoke")
    log.info("Running smoke check ...")

    import importlib

    modules = [
        "app.config.settings",
        "app.utils.logger",
        "app.utils.paths",
        "app.utils.ffmpeg",
        "app.utils.hardware",
        "app.utils.gpu",
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
    ]
    failures: list[tuple[str, str]] = []
    for name in modules:
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - shown to caller
            failures.append((name, repr(exc)))

    if failures:
        for mod, exc in failures:
            log.error("Import failed: {} -> {}", mod, exc)
        return 1

    log.info("Smoke check passed. {} modules imported cleanly.", len(modules))
    log.info("Runtime paths: {}", settings.paths.as_dict())
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover()
    ensure_runtime_dirs(paths)
    configure_logger(paths.logs_dir, debug=args.debug)
    log = get_logger("bootstrap")

    settings = load_settings(paths)
    settings.runtime.safe_mode = args.safe_mode
    settings.runtime.debug = args.debug
    settings.runtime.low_ram = args.low_ram
    settings.runtime.performance = args.performance
    settings.runtime.startup_project = str(args.project) if args.project else None

    log.info("=== {} v{} ===", __display_name__, __version__)
    log.info(
        "Modes: safe={} debug={} low_ram={} performance={}",
        args.safe_mode,
        args.debug,
        args.low_ram,
        args.performance,
    )

    if args.check:
        return _smoke_check(settings)

    # Lazy import: only load the Qt stack when a real UI launch is requested.
    try:
        from app.ui.application import run_gui
    except Exception as exc:  # pragma: no cover - guarded for headless boxes
        log.exception("Failed to import GUI layer: {}", exc)
        return 2

    return run_gui(settings)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
