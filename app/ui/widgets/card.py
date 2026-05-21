"""Simple ``QFrame`` styled as a glass-card container."""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets


class Card(QtWidgets.QFrame):
    def __init__(self, title: str = "", parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)

        if title:
            label = QtWidgets.QLabel(title)
            label.setObjectName("subtitle")
            label.setStyleSheet("font-weight:600; color:#9BA0BD; letter-spacing:1px;")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
            self._layout.addWidget(label)

    def add_body(self, widget: QtWidgets.QWidget) -> None:
        self._layout.addWidget(widget)

    def add_row(self, *widgets: QtWidgets.QWidget) -> None:
        row = QtWidgets.QHBoxLayout()
        for w in widgets:
            row.addWidget(w)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(row)
        self._layout.addWidget(wrap)

    def set_accent(self, on: bool) -> None:
        self.setProperty("accent", "true" if on else "false")
        self.style().unpolish(self)
        self.style().polish(self)
