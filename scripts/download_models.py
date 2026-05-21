"""CLI helper that downloads the AI model weights referenced by plugins.

Usage:
    python scripts/download_models.py            # download all required
    python scripts/download_models.py realesrgan rife
    python scripts/download_models.py --list

The script is intentionally dependency-light: only ``requests`` (already
in requirements.txt) and stdlib are used.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import requests

# Make ``app`` importable when running directly from the repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Importing the plugin modules registers them with app.ai.base.
import app.ai.upscale.realesrgan_plugin  # noqa: F401,E402
import app.ai.upscale.waifu2x_plugin     # noqa: F401,E402
import app.ai.upscale.anime4k_plugin     # noqa: F401,E402
import app.ai.interpolation.rife_plugin  # noqa: F401,E402
import app.ai.interpolation.dain_plugin  # noqa: F401,E402
import app.ai.restoration.gfpgan_plugin  # noqa: F401,E402
import app.ai.audio.denoiser             # noqa: F401,E402
import app.ai.generative.transition      # noqa: F401,E402

from app.ai.base import list_plugins  # noqa: E402
from app.utils.paths import ProjectPaths  # noqa: E402


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Downloading {url}\n          -> {dest}")
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0) or 0)
        downloaded = 0
        with dest.open("wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                fh.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 / total
                    print(f"\r       {pct:5.1f}% ({downloaded / (1<<20):.1f} MB)", end="", flush=True)
        print()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Download AI plugin model weights")
    parser.add_argument("plugins", nargs="*", help="Plugin names (e.g. Real-ESRGAN). Defaults to all.")
    parser.add_argument("--list", action="store_true", help="List required models and exit.")
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    requested = {p.lower() for p in args.plugins}

    rows: list[tuple[str, str, Path]] = []
    for cls in list_plugins():
        inst = cls()
        if requested and inst.name.lower() not in requested:
            continue
        for descriptor in inst.required_models():
            dest = paths.models_dir / inst.name.lower().replace(" ", "_") / descriptor.name
            rows.append((inst.name, descriptor.url, dest))

    if args.list:
        for name, url, dest in rows:
            print(f"{name:<15}  {dest}\n                {url}")
        return 0

    for name, url, dest in rows:
        try:
            if dest.exists() and dest.stat().st_size > 1024:
                print(f"[SKIP] {name} already at {dest}")
                continue
            _download(url, dest)
        except Exception as exc:
            print(f"[ERR ] {name}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
