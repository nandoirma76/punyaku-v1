"""Optical-flow utilities used to render smooth crossfade transitions.

A real implementation uses Farneback flow + bilinear warping. RIFE / DAIN
back-ends live in :mod:`app.ai.interpolation`; this module is the CPU/
fallback path that is always available because it ships with OpenCV.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.utils.logger import get_logger

log = get_logger("optical_flow")


@dataclass(frozen=True)
class FlowResult:
    width: int
    height: int
    mean_magnitude: float


def _imports():
    import cv2  # type: ignore[import-not-found]
    import numpy as np  # type: ignore[import-not-found]
    return cv2, np


def dense_flow(frame_a, frame_b) -> FlowResult:
    """Run Farneback dense optical flow between two BGR frames."""
    cv2, np = _imports()
    g1 = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
    mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    return FlowResult(
        width=int(g1.shape[1]),
        height=int(g1.shape[0]),
        mean_magnitude=float(mag.mean()),
    )


def warp_blend(frame_a, frame_b, alpha: float):
    """Motion-aware blend between two frames.

    ``alpha`` ranges 0..1. The implementation estimates the forward flow,
    warps both frames toward the midpoint, then blends with weights
    ``(1-alpha, alpha)``. Used as a fallback for AI motion blend.
    """
    cv2, np = _imports()
    h, w = frame_a.shape[:2]
    g1 = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
    flow = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0)

    grid_x, grid_y = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    map_x_a = grid_x + flow[..., 0] * alpha
    map_y_a = grid_y + flow[..., 1] * alpha
    map_x_b = grid_x - flow[..., 0] * (1.0 - alpha)
    map_y_b = grid_y - flow[..., 1] * (1.0 - alpha)

    warped_a = cv2.remap(frame_a, map_x_a, map_y_a, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    warped_b = cv2.remap(frame_b, map_x_b, map_y_b, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return cv2.addWeighted(warped_a, 1.0 - alpha, warped_b, alpha, 0.0)
