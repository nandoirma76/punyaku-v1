"""Resolve and create the directory layout used by the application.

The project supports two modes:

* **Source / dev mode**: when running from a git checkout we put runtime
  data inside the project tree (``cache/``, ``temp/``, ``logs/``, ``export/``,
  ``models/``, ``plugins/``).
* **Frozen / installed mode**: when running from a PyInstaller bundle we
  store user data in the platform-appropriate user directory (via
  ``appdirs``) so the install location stays read-only.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # pragma: no cover - appdirs is optional at import time
    from appdirs import user_data_dir
except Exception:  # pragma: no cover
    def user_data_dir(app: str, author: str = "") -> str:  # type: ignore[unused-ignore]
        return str(Path.home() / f".{app}")


APP_NAME = "punyaku"
APP_AUTHOR = "nandoirma"


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    app_dir: Path
    config_dir: Path
    cache_dir: Path
    temp_dir: Path
    logs_dir: Path
    export_dir: Path
    models_dir: Path
    plugins_dir: Path
    assets_dir: Path

    def as_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.__dict__.items()}

    @classmethod
    def discover(cls) -> ProjectPaths:
        if getattr(sys, "frozen", False):  # PyInstaller bundle
            install_root = Path(sys.executable).resolve().parent
            user_root = Path(user_data_dir(APP_NAME, APP_AUTHOR))
            return cls(
                root=install_root,
                app_dir=install_root / "app",
                config_dir=user_root / "config",
                cache_dir=user_root / "cache",
                temp_dir=user_root / "temp",
                logs_dir=user_root / "logs",
                export_dir=user_root / "export",
                models_dir=user_root / "models",
                plugins_dir=user_root / "plugins",
                assets_dir=install_root / "assets",
            )

        # Dev / source checkout: app package lives at <root>/app/
        here = Path(__file__).resolve()
        root = here.parents[2]
        return cls(
            root=root,
            app_dir=root / "app",
            config_dir=root / "app" / "config",
            cache_dir=root / "cache",
            temp_dir=root / "temp",
            logs_dir=root / "logs",
            export_dir=root / "export",
            models_dir=root / "models",
            plugins_dir=root / "plugins",
            assets_dir=root / "assets",
        )


def ensure_runtime_dirs(paths: ProjectPaths) -> None:
    """Create runtime directories (cache, temp, logs, export, models, plugins)."""
    for attr in (
        "config_dir",
        "cache_dir",
        "temp_dir",
        "logs_dir",
        "export_dir",
        "models_dir",
        "plugins_dir",
    ):
        d: Path = getattr(paths, attr)
        d.mkdir(parents=True, exist_ok=True)


def resolve_writable_temp(paths: ProjectPaths, name: str) -> Path:
    """Resolve a writable temp file in :attr:`paths.temp_dir`."""
    paths.temp_dir.mkdir(parents=True, exist_ok=True)
    target = paths.temp_dir / name
    return target


def human_size(num_bytes: float) -> str:
    """Format a byte count as a short human-readable string."""
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    n = float(num_bytes)
    for u in units:
        if abs(n) < 1024.0:
            return f"{n:.1f} {u}"
        n /= 1024.0
    return f"{n:.1f} EB"


def safe_path(value: Any) -> Path:
    """Coerce arbitrary input into a :class:`Path` and expand ``~``."""
    return Path(os.fspath(value)).expanduser()
