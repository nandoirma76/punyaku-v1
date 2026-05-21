"""PyInstaller spec for Punyaku Video Looper.

Build with: ``pyinstaller install/punyaku.spec --noconfirm``.

The resulting ``dist/Punyaku/`` directory contains a self-contained build.
Pass ``--onefile`` (after editing this spec) to produce a single executable
at the cost of slower startup.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# When invoked by PyInstaller, ``__file__`` is the spec file.
HERE = Path(os.path.abspath(SPECPATH))  # type: ignore[name-defined]
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

block_cipher = None

added_files = [
    (str(ROOT / "assets"), "assets"),
    (str(ROOT / "app" / "config"), "app/config"),
]

hidden_imports = [
    "app.ai.upscale.realesrgan_plugin",
    "app.ai.upscale.waifu2x_plugin",
    "app.ai.upscale.anime4k_plugin",
    "app.ai.interpolation.rife_plugin",
    "app.ai.interpolation.dain_plugin",
    "app.ai.restoration.gfpgan_plugin",
    "app.ai.audio.denoiser",
    "app.ai.generative.transition",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "loguru",
    "librosa",
    "cv2",
]

a = Analysis(
    [str(ROOT / "app" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib.tests",
        "PyQt5",
        "PySide6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Punyaku",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "assets" / "icons" / "punyaku.ico") if (ROOT / "assets" / "icons" / "punyaku.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Punyaku",
)
