"""Bootstrap the PyQt6 application and main window."""

from __future__ import annotations

import sys
from typing import Any

from app.config.settings import Settings
from app.utils.logger import get_logger
from app.version import __display_name__

log = get_logger("ui.application")


def _import_qt():
    """Import PyQt6 lazily; raise a friendly error on failure."""
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover - install guard
        raise RuntimeError(
            "PyQt6 is required for the GUI. Install with: pip install PyQt6"
        ) from exc
    return QtCore, QtGui, QtWidgets


def run_gui(settings: Settings) -> int:
    """Create QApplication, show the main window, run the event loop."""
    QtCore, QtGui, QtWidgets = _import_qt()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    app.setApplicationName(__display_name__)
    app.setOrganizationName("Punyaku")
    app.setStyle("Fusion")
    _apply_theme(app, settings.defaults.ui.theme)

    # Lazy import to avoid Qt import in headless smoke checks.
    from app.ui.main_window import MainWindow

    window = MainWindow(settings)
    window.show()

    log.info("UI ready ({})", settings.defaults.ui.theme)
    return int(app.exec())


def _apply_theme(app: Any, theme: str) -> None:
    from app.ui.themes.qss import build_qss
    app.setStyleSheet(build_qss(theme))
