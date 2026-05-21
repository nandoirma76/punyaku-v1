"""Audio crossfade utilities.

Implements equal-power crossfade between two ``numpy`` audio buffers and a
helper that wraps a single buffer into a seamless loop by crossfading the
tail with the head.
"""

from __future__ import annotations

from app.utils.logger import get_logger

log = get_logger("audio.crossfade")


def _np():
    import numpy as np  # type: ignore[import-not-found]
    return np


def equal_power_curve(n: int, falling: bool = False):
    """Return an ``n``-length equal-power curve in [0, 1] (cosine-shaped)."""
    np = _np()
    if n <= 1:
        return np.ones(max(n, 1), dtype=np.float32)
    t = np.linspace(0.0, 1.0, n, dtype=np.float32)
    curve = np.sin(0.5 * np.pi * t) ** 0.5
    return curve[::-1] if falling else curve


def crossfade(buf_a, buf_b, fade_samples: int):
    """Equal-power crossfade ``buf_a`` -> ``buf_b`` over ``fade_samples``."""
    np = _np()
    a = np.asarray(buf_a, dtype=np.float32)
    b = np.asarray(buf_b, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    if b.ndim == 1:
        b = b[:, None]
    n = min(fade_samples, a.shape[0], b.shape[0])
    if n <= 0:
        return np.concatenate([a, b], axis=0)
    rising = equal_power_curve(n)
    falling = equal_power_curve(n, falling=True)
    a_tail = a[-n:] * falling[:, None]
    b_head = b[:n] * rising[:, None]
    mixed = a_tail + b_head
    return np.concatenate([a[:-n], mixed, b[n:]], axis=0)


def seamless_self_loop(buf, fade_samples: int):
    """Crossfade the tail of ``buf`` with its head to produce a seamless loop.

    Returned buffer has the same length as the input (the fade region is
    blended in place).
    """
    np = _np()
    a = np.asarray(buf, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    n = min(fade_samples, a.shape[0] // 2)
    if n <= 0:
        return a
    rising = equal_power_curve(n)
    falling = equal_power_curve(n, falling=True)
    head = a[:n].copy()
    tail = a[-n:].copy()
    blended_head = head * rising[:, None] + tail * falling[:, None]
    out = a.copy()
    out[:n] = blended_head
    out = out[: a.shape[0] - n]
    return out


def fade_in(buf, fade_samples: int):
    np = _np()
    a = np.asarray(buf, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    n = min(fade_samples, a.shape[0])
    if n <= 0:
        return a
    curve = equal_power_curve(n)
    a[:n] = a[:n] * curve[:, None]
    return a


def fade_out(buf, fade_samples: int):
    np = _np()
    a = np.asarray(buf, dtype=np.float32)
    if a.ndim == 1:
        a = a[:, None]
    n = min(fade_samples, a.shape[0])
    if n <= 0:
        return a
    curve = equal_power_curve(n, falling=True)
    a[-n:] = a[-n:] * curve[:, None]
    return a
