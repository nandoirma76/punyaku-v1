"""Audio-reactive visualizer widget (spectrum / bar / wave / circle)."""

from __future__ import annotations

import math
from collections.abc import Sequence

from PyQt6 import QtCore, QtGui, QtWidgets


class Visualizer(QtWidgets.QWidget):
    """Renders a :class:`SpectrumFrame` using the selected style."""

    STYLES = ("bar", "wave", "circle", "particle")

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._bars: list[float] = []
        self._bass = 0.0
        self._style = "bar"
        self._accent = QtGui.QColor("#7C5CFF")
        self._accent_alt = QtGui.QColor("#23E8C2")

    def set_style(self, style: str) -> None:
        if style in self.STYLES:
            self._style = style
            self.update()

    def set_accent(self, primary: str, secondary: str) -> None:
        self._accent = QtGui.QColor(primary)
        self._accent_alt = QtGui.QColor(secondary)

    def push_frame(self, bars: Sequence[float], bass: float = 0.0) -> None:
        self._bars = list(bars)
        self._bass = float(bass)
        self.update()

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        rect = self.rect()
        p.fillRect(rect, QtGui.QColor("#0B0C14"))
        if not self._bars:
            return
        method = getattr(self, f"_paint_{self._style}", self._paint_bar)
        method(p, rect)

    # ------------------------------------------------------------------
    # Style implementations
    # ------------------------------------------------------------------

    def _paint_bar(self, p: QtGui.QPainter, rect: QtCore.QRect) -> None:
        n = len(self._bars)
        gap = 3
        bar_w = max(1.0, (rect.width() - (n + 1) * gap) / n)
        x = rect.left() + gap
        for value in self._bars:
            h = value * rect.height()
            grad = QtGui.QLinearGradient(0, rect.bottom(), 0, rect.bottom() - h)
            grad.setColorAt(0.0, self._accent)
            grad.setColorAt(1.0, self._accent_alt)
            p.setBrush(grad)
            p.setPen(QtCore.Qt.PenStyle.NoPen)
            p.drawRoundedRect(QtCore.QRectF(x, rect.bottom() - h, bar_w, h), 2, 2)
            x += bar_w + gap

    def _paint_wave(self, p: QtGui.QPainter, rect: QtCore.QRect) -> None:
        pen = QtGui.QPen(self._accent_alt, 2.0)
        p.setPen(pen)
        n = len(self._bars)
        cx = rect.center().x()
        cy = rect.center().y()
        last_pt: QtCore.QPointF | None = None
        for i, value in enumerate(self._bars):
            x = rect.left() + (i / max(1, n - 1)) * rect.width()
            y = cy + (value - 0.5) * rect.height() * 0.8
            pt = QtCore.QPointF(x, y)
            if last_pt is not None:
                p.drawLine(last_pt, pt)
            last_pt = pt
        # accent dot at center
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.setBrush(self._accent)
        p.drawEllipse(QtCore.QPointF(cx, cy), 4 + self._bass * 10, 4 + self._bass * 10)

    def _paint_circle(self, p: QtGui.QPainter, rect: QtCore.QRect) -> None:
        n = len(self._bars)
        cx, cy = rect.center().x(), rect.center().y()
        base_r = min(rect.width(), rect.height()) * 0.18
        for i, value in enumerate(self._bars):
            angle = (i / max(1, n)) * math.tau
            r = base_r + value * base_r
            x1 = cx + math.cos(angle) * base_r
            y1 = cy + math.sin(angle) * base_r
            x2 = cx + math.cos(angle) * r
            y2 = cy + math.sin(angle) * r
            p.setPen(QtGui.QPen(self._accent, 2))
            p.drawLine(QtCore.QPointF(x1, y1), QtCore.QPointF(x2, y2))
        glow = QtGui.QRadialGradient(QtCore.QPointF(cx, cy), base_r * (1 + self._bass))
        glow.setColorAt(0.0, QtGui.QColor(self._accent_alt.red(), self._accent_alt.green(), self._accent_alt.blue(), 150))
        glow.setColorAt(1.0, QtGui.QColor(0, 0, 0, 0))
        p.setBrush(glow)
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        p.drawEllipse(QtCore.QPointF(cx, cy), base_r * (1 + self._bass), base_r * (1 + self._bass))

    def _paint_particle(self, p: QtGui.QPainter, rect: QtCore.QRect) -> None:
        # placeholder: render bass-driven particles around the center
        cx, cy = rect.center().x(), rect.center().y()
        p.setPen(QtCore.Qt.PenStyle.NoPen)
        for i, value in enumerate(self._bars):
            angle = (i / max(1, len(self._bars))) * math.tau
            radius = (40 + value * 200) * (1 + self._bass)
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            size = 2 + value * 8
            color = QtGui.QColor(self._accent)
            color.setAlphaF(0.4 + value * 0.6)
            p.setBrush(color)
            p.drawEllipse(QtCore.QPointF(x, y), size, size)
