"""Optional splash screen used by PyInstaller builds.

A minimalist Qt splash that displays the logo while the main window is
imported (``app.ui.main_window`` pulls a lot of heavy modules).
"""

from __future__ import annotations

import sys
from pathlib import Path


def show_splash() -> None:  # pragma: no cover - UI only
    from PyQt6 import QtCore, QtGui, QtWidgets

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    pixmap_path = Path(__file__).parent.parent / "assets" / "icons" / "splash.png"
    if pixmap_path.exists():
        pixmap = QtGui.QPixmap(str(pixmap_path))
    else:
        pixmap = QtGui.QPixmap(560, 320)
        pixmap.fill(QtGui.QColor("#0B0C14"))
    splash = QtWidgets.QSplashScreen(pixmap, QtCore.Qt.WindowType.WindowStaysOnTopHint)
    splash.showMessage(
        "Punyaku Video Looper — starting up ...",
        QtCore.Qt.AlignmentFlag.AlignBottom | QtCore.Qt.AlignmentFlag.AlignHCenter,
        QtGui.QColor("#E7E9F8"),
    )
    splash.show()
    app.processEvents()
    QtCore.QTimer.singleShot(2200, splash.close)


if __name__ == "__main__":  # pragma: no cover
    show_splash()
