"""Real-time spectrum analyzer used by the music visualizer page.

The visualizer is fed PCM samples and returns a normalised magnitude
array suitable for any of the four built-in renderers:

* spectrum (bar)
* circle
* wave
* particle (beat reactive)

Pure-NumPy implementation; UI rendering happens in :mod:`app.ui.widgets.visualizer`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.logger import get_logger

log = get_logger("visualizer.spectrum")


@dataclass(frozen=True)
class SpectrumFrame:
    bars: list[float]      # 0..1 magnitudes
    bass_energy: float     # 0..1 low-band energy (beat reactive)
    mid_energy: float
    high_energy: float


def _np():
    import numpy as np  # type: ignore[import-not-found]
    return np


class SpectrumAnalyzer:
    def __init__(
        self,
        sample_rate: int = 44_100,
        fft_size: int = 1024,
        num_bars: int = 64,
        smoothing: float = 0.7,
    ) -> None:
        self.sample_rate = sample_rate
        self.fft_size = fft_size
        self.num_bars = num_bars
        self.smoothing = float(smoothing)
        self._prev = None  # type: ignore[assignment]
        self._window = self._hann_window(fft_size)

    def _hann_window(self, n: int):
        np = _np()
        return 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(n) / max(1, n - 1))

    def analyze(self, samples) -> SpectrumFrame:
        np = _np()
        s = np.asarray(samples, dtype=np.float32)
        if s.ndim > 1:
            s = s.mean(axis=1)
        n = min(self.fft_size, s.size)
        if n < 16:
            return SpectrumFrame([0.0] * self.num_bars, 0.0, 0.0, 0.0)
        windowed = s[-n:] * self._window[-n:]
        spectrum = np.abs(np.fft.rfft(windowed))
        # Log-spaced bar grouping
        idx = np.geomspace(2, max(3, spectrum.size - 1), self.num_bars + 1).astype(int)
        bars = []
        for i in range(self.num_bars):
            lo, hi = idx[i], max(idx[i] + 1, idx[i + 1])
            bars.append(float(spectrum[lo:hi].mean() if hi > lo else 0.0))
        bars_arr = np.asarray(bars, dtype=np.float32)
        peak = float(bars_arr.max()) if bars_arr.size else 0.0
        if peak > 0:
            bars_arr /= peak
        if self._prev is not None and self._prev.shape == bars_arr.shape:
            bars_arr = self.smoothing * self._prev + (1.0 - self.smoothing) * bars_arr
        self._prev = bars_arr
        third = max(1, len(bars_arr) // 3)
        return SpectrumFrame(
            bars=[float(b) for b in bars_arr],
            bass_energy=float(bars_arr[:third].mean()),
            mid_energy=float(bars_arr[third:2 * third].mean()),
            high_energy=float(bars_arr[2 * third:].mean()),
        )
