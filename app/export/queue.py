"""Background export queue.

Runs :class:`Exporter` jobs in a thread pool, exposes progress signals
suitable for the UI's queue panel. Uses ``concurrent.futures`` so it stays
portable across Windows/Linux/macOS and doesn't depend on Qt.
"""

from __future__ import annotations

import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from app.export.exporter import ExportJob, Exporter
from app.utils.logger import get_logger

log = get_logger("export.queue")


@dataclass
class QueueItem:
    id: int
    job: ExportJob
    status: str = "pending"   # pending|running|done|error|cancelled
    progress: float = 0.0
    message: str = ""
    error: str | None = None
    started_at: float | None = None
    finished_at: float | None = None
    output: Path | None = None


@dataclass
class ExportQueue:
    max_workers: int = 1
    _executor: ThreadPoolExecutor | None = field(default=None, init=False, repr=False)
    _items: dict[int, QueueItem] = field(default_factory=dict, init=False, repr=False)
    _futures: dict[int, Future] = field(default_factory=dict, init=False, repr=False)
    _next_id: int = field(default=1, init=False, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)
    _listeners: list[Callable[[QueueItem], None]] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max(1, self.max_workers))

    def add_listener(self, fn: Callable[[QueueItem], None]) -> None:
        self._listeners.append(fn)

    def items(self) -> list[QueueItem]:
        with self._lock:
            return list(self._items.values())

    def submit(self, job: ExportJob) -> QueueItem:
        with self._lock:
            item_id = self._next_id
            self._next_id += 1
            item = QueueItem(id=item_id, job=job)
            self._items[item_id] = item
        future = self._executor.submit(self._run, item)  # type: ignore[union-attr]
        self._futures[item_id] = future
        self._fire(item)
        return item

    def cancel(self, item_id: int) -> bool:
        with self._lock:
            item = self._items.get(item_id)
            future = self._futures.get(item_id)
        if not item or item.status not in ("pending", "running"):
            return False
        if future and future.cancel():
            item.status = "cancelled"
            item.finished_at = time.time()
            self._fire(item)
            return True
        return False

    def shutdown(self, wait: bool = True) -> None:
        if self._executor:
            self._executor.shutdown(wait=wait, cancel_futures=True)
        self._executor = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run(self, item: QueueItem) -> None:
        item.status = "running"
        item.started_at = time.time()
        self._fire(item)
        exporter = Exporter()
        try:
            def _progress(pct: float, message: str) -> None:
                item.progress = float(pct)
                item.message = message
                self._fire(item)

            result = exporter.export(item.job, progress=_progress)
            item.output = Path(result.output)
            item.progress = 1.0
            item.message = f"Done (quality={result.quality}, encoder={result.used_encoder})"
            item.status = "done"
        except Exception as exc:
            item.status = "error"
            item.error = str(exc)
            log.exception("Export job {} failed: {}", item.id, exc)
        finally:
            item.finished_at = time.time()
            self._fire(item)

    def _fire(self, item: QueueItem) -> None:
        for fn in list(self._listeners):
            try:
                fn(item)
            except Exception:  # pragma: no cover
                log.exception("queue listener raised")
