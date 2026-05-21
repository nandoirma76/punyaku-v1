"""Tests for the audio engine (crossfade, normalize)."""

from __future__ import annotations

import math

import numpy as np

from app.engine.audio.crossfade import (
    crossfade,
    equal_power_curve,
    fade_in,
    fade_out,
    seamless_self_loop,
)
from app.engine.audio.normalize import peak_normalize, rms_normalize


def test_equal_power_curve_endpoints() -> None:
    curve = equal_power_curve(64)
    assert math.isclose(curve[0], 0.0, abs_tol=1e-6)
    assert curve[-1] > 0.99


def test_crossfade_length_preserved() -> None:
    a = np.ones(1024, dtype=np.float32)
    b = np.full(1024, 0.5, dtype=np.float32)
    out = crossfade(a, b, fade_samples=256)
    # Output length = len(a) + len(b) - fade_samples
    assert out.shape[0] == a.shape[0] + b.shape[0] - 256


def test_seamless_self_loop_shorter_than_input() -> None:
    buf = np.sin(np.linspace(0, 6.28, 4096, dtype=np.float32))
    looped = seamless_self_loop(buf, fade_samples=512)
    assert looped.shape[0] == buf.shape[0] - 512


def test_peak_normalize_caps_at_target() -> None:
    a = np.array([0.1, -0.2, 0.05], dtype=np.float32)
    out = peak_normalize(a, target_db=-1.0)
    assert math.isclose(float(np.max(np.abs(out))), 10 ** (-1.0 / 20.0), rel_tol=1e-3)


def test_rms_normalize_does_not_overshoot() -> None:
    rng = np.random.default_rng(0)
    a = rng.standard_normal(2048).astype(np.float32) * 0.05
    out = rms_normalize(a, target_db=-16.0)
    assert float(np.max(np.abs(out))) <= 1.0


def test_fade_in_out_zero_length_safe() -> None:
    a = np.ones(8, dtype=np.float32)
    # zero / negative fade samples must not raise
    assert fade_in(a, 0).shape == (8, 1)
    assert fade_out(a, 0).shape == (8, 1)
