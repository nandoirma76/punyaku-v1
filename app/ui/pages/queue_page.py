"""Render queue page (live updates from :class:`ExportQueue`)."""

from __future__ import annotations

import time

from PyQt6 import QtCore, QtWidgets

from app.export.queue import ExportQueue, QueueItem
from app.ui.widgets.card import Card


class QueuePage(QtWidgets.QWidget):
    _statusSignal = QtCore.pyqtSignal(object)

    def __init__(self, queue: ExportQueue, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.queue = queue
        self._build()
        self._statusSignal.connect(self._on_status)
        queue.add_listener(self._statusSignal.emit)
        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh)
        self._timer.start()
        self._refresh()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        card = Card("Render queue")
        self._table = QtWidgets.QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(
            ["#", "Source", "Preset", "Status", "Progress", "Output"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self._table.verticalHeader().setVisible(False)
        card.add_body(self._table)

        toolbar = QtWidgets.QHBoxLayout()
        clear_btn = QtWidgets.QPushButton("Clear finished")
        clear_btn.clicked.connect(self._clear_finished)
        toolbar.addStretch(1)
        toolbar.addWidget(clear_btn)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(toolbar)
        card.add_body(wrap)

        layout.addWidget(card)

    def _refresh(self) -> None:
        items = self.queue.items()
        self._table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_row(row, item)

    def _on_status(self, item: QueueItem) -> None:
        # Just trigger a full refresh; the queue is short and updates are rare.
        self._refresh()

    def _set_row(self, row: int, item: QueueItem) -> None:
        self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(item.id)))
        self._table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.job.source)))
        self._table.setItem(row, 2, QtWidgets.QTableWidgetItem(item.job.preset_key))
        status_text = item.status
        if item.error:
            status_text = f"error: {item.error}"
        self._table.setItem(row, 3, QtWidgets.QTableWidgetItem(status_text))
        self._table.setItem(row, 4, QtWidgets.QTableWidgetItem(f"{item.progress * 100:0.0f}%"))
        self._table.setItem(
            row, 5, QtWidgets.QTableWidgetItem(str(item.output or item.job.output))
        )

    def _clear_finished(self) -> None:
        # Best-effort: snapshot items so we don't mutate while iterating.
        # The queue does not currently support remove(); we visually filter.
        # Future work: extend ExportQueue with a remove(item_id) API.
        kept = []
        for item in self.queue.items():
            if item.status in ("pending", "running"):
                kept.append(item)
        self._table.setRowCount(len(kept))
        for row, item in enumerate(kept):
            self._set_row(row, item)
        time.sleep(0.05)  # let the queue's listener fire if a job is mid-flight
