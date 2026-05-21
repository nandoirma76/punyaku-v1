"""Compact live CPU / RAM / GPU usage strip shown in the top bar."""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from app.utils.hardware import HardwareSnapshot, snapshot


class _Metric(QtWidgets.QWidget):
    def __init__(self, label: str) -> None:
        super().__init__()
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        self._label = QtWidgets.QLabel(label)
        self._label.setObjectName("subtitle")
        self._bar = QtWidgets.QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedWidth(80)
        self._value = QtWidgets.QLabel("0%")
        self._value.setObjectName("subtitle")
        self._value.setFixedWidth(40)
        layout.addWidget(self._label)
        layout.addWidget(self._bar)
        layout.addWidget(self._value)

    def update_value(self, pct: float) -> None:
        pct = max(0.0, min(100.0, float(pct)))
        self._bar.setValue(int(pct))
        self._value.setText(f"{pct:0.0f}%")


class HardwareStrip(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self._cpu = _Metric("CPU")
        self._ram = _Metric("RAM")
        self._gpu = _Metric("GPU")
        for m in (self._cpu, self._ram, self._gpu):
            layout.addWidget(m)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1500)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    def _refresh(self) -> None:
        snap: HardwareSnapshot = snapshot()
        self._cpu.update_value(snap.cpu_pct)
        self._ram.update_value(snap.ram_pct)
        gpu = snap.gpus[0] if snap.gpus else None
        self._gpu.update_value(gpu.load_pct if gpu else 0.0)
