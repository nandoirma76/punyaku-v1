"""Centralised logger configuration on top of :mod:`loguru`.

Falls back to the stdlib ``logging`` module if loguru is unavailable
(e.g. during a minimal smoke test).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

try:
    from loguru import logger as _loguru_logger  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    _loguru_logger = None  # type: ignore[assignment]

_CONFIGURED = False


class _StdLogShim:
    """Adapter exposing a loguru-like API on top of stdlib logging."""

    def __init__(self, name: str) -> None:
        self._log = logging.getLogger(name)

    def _fmt(self, msg: str, args: tuple[Any, ...]) -> str:
        if not args:
            return msg
        try:
            return msg.format(*args)
        except Exception:
            return msg + " " + " ".join(repr(a) for a in args)

    def debug(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.debug(self._fmt(msg, args))

    def info(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.info(self._fmt(msg, args))

    def warning(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.warning(self._fmt(msg, args))

    def error(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.error(self._fmt(msg, args))

    def exception(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.exception(self._fmt(msg, args))

    def critical(self, msg: str, *args: Any, **_: Any) -> None:
        self._log.critical(self._fmt(msg, args))


def configure_logger(log_dir: Path, debug: bool = False) -> None:
    """Configure global logger sinks: console + rotating log file."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "punyaku.log"

    if _loguru_logger is not None:
        _loguru_logger.remove()
        level = "DEBUG" if debug else "INFO"
        _loguru_logger.add(
            sys.stderr,
            level=level,
            colorize=True,
            backtrace=False,
            diagnose=debug,
            format=(
                "<green>{time:HH:mm:ss}</green> | "
                "<level>{level: <7}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
                "{message}"
            ),
        )
        _loguru_logger.add(
            str(log_file),
            level="DEBUG",
            rotation="10 MB",
            retention=5,
            encoding="utf-8",
            backtrace=True,
            diagnose=False,
        )
    else:  # pragma: no cover - stdlib fallback
        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO,
            format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            handlers=[
                logging.StreamHandler(sys.stderr),
                logging.FileHandler(log_file, encoding="utf-8"),
            ],
        )

    _CONFIGURED = True


def get_logger(name: str) -> Any:
    """Return a logger-like object (loguru when available, stdlib otherwise)."""
    if _loguru_logger is not None:
        return _loguru_logger.bind(name=name)
    return _StdLogShim(name)
