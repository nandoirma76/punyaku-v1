"""Main application window with sidebar navigation."""

from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from app.backend.recovery import RecoveryManager
from app.config.settings import Settings
from app.export.queue import ExportQueue
from app.ui.pages.audio_page import AudioPage
from app.ui.pages.dashboard import DashboardPage
from app.ui.pages.editor_page import EditorPage
from app.ui.pages.export_page import ExportPage
from app.ui.pages.queue_page import QueuePage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.visualizer_page import VisualizerPage
from app.ui.widgets.hardware_strip import HardwareStrip
from app.utils.logger import get_logger
from app.version import __display_name__, __version__

log = get_logger("ui.main_window")


class _NavButton(QtWidgets.QPushButton):
    def __init__(self, text: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("nav")
        self.setCheckable(True)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        font = self.font()
        font.setPointSizeF(font.pointSizeF() + 0.5)
        self.setFont(font)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.setObjectName("root")
        self.setWindowTitle(f"{__display_name__} v{__version__}")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 740)

        self.queue = ExportQueue(max_workers=settings.defaults.performance.max_workers)
        self.recovery = RecoveryManager(settings.paths)
        self.recovery.begin_session()

        self._setup_ui()
        self._setup_status_bar()

    # ------------------------------------------------------------------
    # UI layout
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        central = QtWidgets.QWidget()
        central.setObjectName("root")
        self.setCentralWidget(central)

        root_layout = QtWidgets.QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._make_sidebar(), 0)
        right = QtWidgets.QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._make_topbar(), 0)
        right.addWidget(self._make_stack(), 1)

        right_container = QtWidgets.QWidget()
        right_container.setLayout(right)
        root_layout.addWidget(right_container, 1)

    def _make_sidebar(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setObjectName("sidebar")
        frame.setFixedWidth(228)
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)

        title = QtWidgets.QLabel(__display_name__)
        title.setObjectName("title")
        subtitle = QtWidgets.QLabel("Seamless looping studio")
        subtitle.setObjectName("subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        self._nav_group = QtWidgets.QButtonGroup(self)
        self._nav_group.setExclusive(True)

        nav_items = [
            ("Dashboard", "dashboard"),
            ("Video Editor", "editor"),
            ("Audio", "audio"),
            ("Visualizer", "visualizer"),
            ("Export", "export"),
            ("Queue", "queue"),
            ("Settings", "settings"),
        ]
        for text, key in nav_items:
            btn = _NavButton(text)
            btn.setProperty("key", key)
            btn.clicked.connect(self._on_nav_clicked)
            layout.addWidget(btn)
            self._nav_group.addButton(btn)
            if key == "dashboard":
                btn.setChecked(True)

        layout.addStretch(1)

        version = QtWidgets.QLabel(f"v{__version__}")
        version.setObjectName("subtitle")
        version.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        return frame

    def _make_topbar(self) -> QtWidgets.QWidget:
        frame = QtWidgets.QFrame()
        frame.setObjectName("topbar")
        frame.setFixedHeight(64)
        layout = QtWidgets.QHBoxLayout(frame)
        layout.setContentsMargins(20, 8, 20, 8)
        layout.setSpacing(12)

        self._title_label = QtWidgets.QLabel("Dashboard")
        self._title_label.setObjectName("title")
        layout.addWidget(self._title_label)
        layout.addStretch(1)

        self._hw_strip = HardwareStrip()
        layout.addWidget(self._hw_strip)
        return frame

    def _make_stack(self) -> QtWidgets.QWidget:
        self._stack = QtWidgets.QStackedWidget()
        self._stack.setContentsMargins(0, 0, 0, 0)

        self.dashboard = DashboardPage(self.settings)
        self.editor = EditorPage(self.settings, self.queue)
        self.audio = AudioPage(self.settings)
        self.visualizer = VisualizerPage(self.settings)
        self.export = ExportPage(self.settings, self.queue)
        self.queue_page = QueuePage(self.queue)
        self.settings_page = SettingsPage(self.settings)

        for w in (
            self.dashboard,
            self.editor,
            self.audio,
            self.visualizer,
            self.export,
            self.queue_page,
            self.settings_page,
        ):
            self._stack.addWidget(w)

        return self._stack

    def _setup_status_bar(self) -> None:
        status = QtWidgets.QStatusBar()
        status.showMessage(f"{__display_name__} ready")
        self.setStatusBar(status)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_nav_clicked(self) -> None:
        sender = self.sender()
        if not isinstance(sender, QtWidgets.QPushButton):
            return
        key = sender.property("key")
        idx_map = {
            "dashboard": 0,
            "editor": 1,
            "audio": 2,
            "visualizer": 3,
            "export": 4,
            "queue": 5,
            "settings": 6,
        }
        idx = idx_map.get(key, 0)
        self._stack.setCurrentIndex(idx)
        self._title_label.setText(sender.text())

    # ------------------------------------------------------------------

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        log.info("Shutting down ...")
        try:
            self.queue.shutdown(wait=False)
        finally:
            self.recovery.end_session()
        super().closeEvent(event)
