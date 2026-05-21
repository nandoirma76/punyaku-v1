"""Music visualizer preview page."""

from __future__ import annotations

import math

from PyQt6 import QtCore, QtWidgets

from app.config.settings import Settings
from app.engine.visualizer.spectrum import SpectrumAnalyzer
from app.ui.widgets.card import Card
from app.ui.widgets.visualizer import Visualizer


class VisualizerPage(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._analyzer = SpectrumAnalyzer(num_bars=64)
        self._t = 0
        self._build()

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(33)  # ~30 fps preview
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        controls = Card("Visualizer style")
        controls_layout = QtWidgets.QHBoxLayout()
        self._style_combo = QtWidgets.QComboBox()
        for style in Visualizer.STYLES:
            self._style_combo.addItem(style)
        controls_layout.addWidget(QtWidgets.QLabel("Style"))
        controls_layout.addWidget(self._style_combo)
        controls_layout.addSpacing(20)

        self._reactive_check = QtWidgets.QCheckBox("Beat reactive")
        self._reactive_check.setChecked(True)
        controls_layout.addWidget(self._reactive_check)

        controls_layout.addStretch(1)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(controls_layout)
        controls.add_body(wrap)
        layout.addWidget(controls)

        self._visualizer = Visualizer()
        viz_card = Card()
        viz_card.add_body(self._visualizer)
        layout.addWidget(viz_card, 1)

        self._style_combo.currentTextChanged.connect(self._visualizer.set_style)

    def _tick(self) -> None:
        # Drive the visualizer with a synthetic spectrum for the preview.
        # Real audio playback will replace this in the audio mixer page.
        self._t += 1
        n = 64
        bars = [
            0.5 + 0.45 * math.sin((self._t + i * 4) * 0.07) ** 2
            for i in range(n)
        ]
        # synthetic bass pulse every ~30 frames
        bass = 0.4 + 0.6 * abs(math.sin(self._t * 0.18))
        if not self._reactive_check.isChecked():
            bass = 0.4
        self._visualizer.push_frame(bars, bass)
