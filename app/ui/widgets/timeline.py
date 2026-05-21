"""Minimal frame-accurate timeline widget.

The widget draws a track + a scrubber. It does NOT decode video itself --
it exposes signals (``positionChanged`` / ``inOutChanged``) that the
editor page wires up to media playback.
"""

from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets


class Timeline(QtWidgets.QWidget):
    positionChanged = QtCore.pyqtSignal(float)
    inOutChanged = QtCore.pyqtSignal(float, float)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(96)
        self._duration_s = 0.0
        self._position_s = 0.0
        self._in_s = 0.0
        self._out_s = 0.0
        self._dragging: str | None = None
        self.setMouseTracking(True)

    def set_duration(self, duration_s: float) -> None:
        self._duration_s = max(0.0, float(duration_s))
        if self._out_s == 0.0:
            self._out_s = self._duration_s
        self.update()

    def set_position(self, position_s: float) -> None:
        self._position_s = max(0.0, min(self._duration_s, float(position_s)))
        self.update()

    def set_in_out(self, in_s: float, out_s: float) -> None:
        self._in_s = max(0.0, min(self._duration_s, in_s))
        self._out_s = max(self._in_s, min(self._duration_s, out_s))
        self.inOutChanged.emit(self._in_s, self._out_s)
        self.update()

    def paintEvent(self, _event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        r = self.rect().adjusted(8, 14, -8, -14)

        # Track background
        p.fillRect(r, QtGui.QColor("#161A2A"))
        p.setPen(QtGui.QPen(QtGui.QColor("#2B3050"), 1))
        p.drawRect(r)

        if self._duration_s > 0:
            in_x = int(r.left() + (self._in_s / self._duration_s) * r.width())
            out_x = int(r.left() + (self._out_s / self._duration_s) * r.width())
            loop_rect = QtCore.QRect(in_x, r.top(), max(2, out_x - in_x), r.height())
            p.fillRect(loop_rect, QtGui.QColor(124, 92, 255, 80))

            pos_x = int(r.left() + (self._position_s / self._duration_s) * r.width())
            p.setPen(QtGui.QPen(QtGui.QColor("#23E8C2"), 2))
            p.drawLine(pos_x, r.top() - 6, pos_x, r.bottom() + 6)

            # in / out handles
            for x, color in ((in_x, "#7C5CFF"), (out_x, "#FF5C7C")):
                p.setBrush(QtGui.QColor(color))
                p.setPen(QtCore.Qt.PenStyle.NoPen)
                p.drawRect(QtCore.QRect(x - 3, r.top() - 8, 6, r.height() + 16))

        # Tick marks
        p.setPen(QtGui.QPen(QtGui.QColor("#2B3050"), 1))
        for i in range(0, 11):
            x = int(r.left() + (i / 10.0) * r.width())
            p.drawLine(x, r.bottom(), x, r.bottom() + 4)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._duration_s <= 0:
            return
        r = self.rect().adjusted(8, 14, -8, -14)
        x = event.position().x()
        in_x = r.left() + (self._in_s / self._duration_s) * r.width()
        out_x = r.left() + (self._out_s / self._duration_s) * r.width()
        if abs(x - in_x) < 6:
            self._dragging = "in"
        elif abs(x - out_x) < 6:
            self._dragging = "out"
        else:
            self._dragging = "pos"
            self._update_drag(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._dragging and self._duration_s > 0:
            self._update_drag(event)

    def mouseReleaseEvent(self, _event: QtGui.QMouseEvent) -> None:
        self._dragging = None

    def _update_drag(self, event: QtGui.QMouseEvent) -> None:
        r = self.rect().adjusted(8, 14, -8, -14)
        x = max(r.left(), min(r.right(), event.position().x()))
        frac = (x - r.left()) / max(1.0, r.width())
        t = frac * self._duration_s
        if self._dragging == "in":
            self._in_s = min(t, self._out_s)
            self.inOutChanged.emit(self._in_s, self._out_s)
        elif self._dragging == "out":
            self._out_s = max(t, self._in_s)
            self.inOutChanged.emit(self._in_s, self._out_s)
        else:
            self._position_s = t
            self.positionChanged.emit(self._position_s)
        self.update()
