"""Tests for the spectrum analyzer."""

from __future__ import annotations

import math

import numpy as np

from app.engine.visualizer.spectrum import SpectrumAnalyzer


def test_analyzer_handles_silence() -> None:
    sa = SpectrumAnalyzer(num_bars=32)
    frame = sa.analyze(np.zeros(2048, dtype=np.float32))
    assert len(frame.bars) == 32
    assert all(0.0 <= v <= 1.0 for v in frame.bars)
    assert math.isclose(frame.bass_energy, 0.0, abs_tol=1e-6)


def test_analyzer_responds_to_tone() -> None:
    sa = SpectrumAnalyzer(num_bars=32, sample_rate=44_100)
    t = np.arange(2048) / 44_100.0
    signal = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)
    frame = sa.analyze(signal)
    assert max(frame.bars) > 0.0
