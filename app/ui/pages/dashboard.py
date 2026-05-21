"""Dashboard / landing page: hardware, recent projects, quick actions."""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from app.config.settings import Settings
from app.ui.widgets.card import Card
from app.utils.hardware import snapshot
from app.utils.paths import human_size
from app.version import __display_name__, __tagline__, __version__


class DashboardPage(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._build()

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setInterval(2500)
        self._refresh_timer.timeout.connect(self._refresh_metrics)
        self._refresh_timer.start()
        self._refresh_metrics()

    def _build(self) -> None:
        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        # ---------- Hero
        hero = Card()
        hero_layout = QtWidgets.QVBoxLayout()
        hero_title = QtWidgets.QLabel(f"{__display_name__}  ·  v{__version__}")
        hero_title.setObjectName("title")
        hero_sub = QtWidgets.QLabel(__tagline__)
        hero_sub.setObjectName("subtitle")
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_sub)

        actions = QtWidgets.QHBoxLayout()
        actions.setSpacing(10)
        self.new_btn = QtWidgets.QPushButton("New Loop Project")
        self.new_btn.setObjectName("primary")
        self.open_btn = QtWidgets.QPushButton("Open Project ...")
        self.import_btn = QtWidgets.QPushButton("Quick Import")
        for b in (self.new_btn, self.open_btn, self.import_btn):
            actions.addWidget(b)
        actions.addStretch(1)
        hero_layout.addLayout(actions)
        hero_widget = QtWidgets.QWidget()
        hero_widget.setLayout(hero_layout)
        hero.add_body(hero_widget)
        outer.addWidget(hero)

        # ---------- Metrics grid
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        self._cpu_card = self._build_metric_card("CPU", "0 %")
        self._ram_card = self._build_metric_card("RAM", "0 / 0 GB")
        self._gpu_card = self._build_metric_card("GPU", "—")
        self._cache_card = self._build_metric_card("Cache", "0 MB")
        grid.addWidget(self._cpu_card[0], 0, 0)
        grid.addWidget(self._ram_card[0], 0, 1)
        grid.addWidget(self._gpu_card[0], 0, 2)
        grid.addWidget(self._cache_card[0], 0, 3)

        outer.addLayout(grid)

        # ---------- Recent + tips
        bottom = QtWidgets.QHBoxLayout()
        bottom.setSpacing(14)

        recent_card = Card("Recent projects")
        self._recent_list = QtWidgets.QListWidget()
        self._recent_list.setMinimumHeight(220)
        for p in self.settings.recent_projects[:8]:
            self._recent_list.addItem(p)
        if not self.settings.recent_projects:
            self._recent_list.addItem("No recent projects yet.")
        recent_card.add_body(self._recent_list)
        bottom.addWidget(recent_card, 2)

        tips_card = Card("Tips for ultra-smooth loops")
        tips = QtWidgets.QLabel(
            "• Pick a 1-2 s search window for natural movement.\n"
            "• Snap loop end to the nearest BPM beat when using music.\n"
            "• Enable motion blend for organic footage; crossfade for static scenes.\n"
            "• Use the 4K cinematic preset for wallpaper exports.\n"
            "• Turn on GPU encoding in Settings to halve render time."
        )
        tips.setWordWrap(True)
        tips.setStyleSheet("color:#9BA0BD; line-height: 1.6em;")
        tips_card.add_body(tips)
        bottom.addWidget(tips_card, 1)

        outer.addLayout(bottom, 1)

    def _build_metric_card(self, title: str, value_text: str) -> tuple[Card, QtWidgets.QLabel]:
        card = Card(title.upper())
        value = QtWidgets.QLabel(value_text)
        value.setStyleSheet("font-size:24px; font-weight:600;")
        card.add_body(value)
        return card, value

    def _refresh_metrics(self) -> None:
        snap = snapshot()
        self._cpu_card[1].setText(f"{snap.cpu_pct:0.0f} %")
        self._ram_card[1].setText(
            f"{snap.ram_used_mb / 1024:0.1f} / {snap.ram_total_mb / 1024:0.1f} GB ({snap.ram_pct:0.0f}%)"
        )
        if snap.gpus:
            g = snap.gpus[0]
            self._gpu_card[1].setText(f"{g.name}\n{g.load_pct:0.0f}% · {g.mem_used_mb / 1024:0.1f} GB")
        else:
            self._gpu_card[1].setText("No GPU detected\n(software fallback)")

        from app.backend.cache import stats
        s = stats(self.settings.paths)
        self._cache_card[1].setText(
            f"{s.total_mb:0.1f} MB total\n{s.files_total} files · {human_size(s.cache_mb * 1024 * 1024)} cache"
        )
