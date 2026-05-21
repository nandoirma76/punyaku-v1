"""Find seamless loop cut points by matching the start of the clip to the end.

Strategy (all run lazily, no OpenCV import at module load):

* Sample ``N`` candidate frames near the head and tail of the clip.
* Compute three similarity scores: pixel L2 distance, downsampled histogram
  correlation, and (optionally) optical-flow magnitude continuity.
* Combine into a weighted score; pick the best pair.

The result is a :class:`LoopCut` describing the start/end frame indices and
timestamps that produce the smoothest loop.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from app.utils.logger import get_logger

log = get_logger("frame_match")


@dataclass(frozen=True)
class LoopCut:
    start_frame: int
    end_frame: int
    start_time_s: float
    end_time_s: float
    score: float           # 0 = identical, larger = worse
    method: str            # pixel|histogram|optical_flow|combined

    def duration_s(self) -> float:
        return max(0.0, self.end_time_s - self.start_time_s)


def _import_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
        return cv2
    except Exception as exc:  # pragma: no cover - import-time guard
        raise RuntimeError(
            "OpenCV is required for frame matching. Install with: "
            "pip install opencv-python-headless"
        ) from exc


def _import_numpy():
    try:
        import numpy as np  # type: ignore[import-not-found]
        return np
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("NumPy is required for frame matching.") from exc


def _resize(cv2, frame, max_dim: int = 256):
    h, w = frame.shape[:2]
    scale = max_dim / float(max(h, w))
    if scale >= 1.0:
        return frame
    return cv2.resize(frame, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def _read_frames(cv2, path: Path, indices: list[int]):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV cannot open {path}")
    frames = {}
    try:
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ok, frame = cap.read()
            if ok:
                frames[idx] = _resize(cv2, frame)
    finally:
        cap.release()
    return frames


def _histogram(cv2, np, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [64], [0, 256])
    cv2.normalize(hist, hist)
    return hist


def find_loop_cut(
    video_path: Path | str,
    method: str = "auto",
    search_window_s: float = 2.0,
    num_samples: int = 24,
    pixel_weight: float = 0.6,
    hist_weight: float = 0.4,
) -> LoopCut:
    """Find the best seamless loop cut for ``video_path``.

    Args:
        method: ``auto``, ``pixel``, ``histogram``, or ``optical_flow``.
            ``auto`` runs pixel + histogram and combines them.
        search_window_s: how many seconds at each end of the clip to sample.
        num_samples: number of candidate frames per end.
    """
    cv2 = _import_cv2()
    np = _import_numpy()
    path = Path(video_path)

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV cannot open {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    cap.release()

    if total_frames < 4:
        raise RuntimeError(f"{path} has too few frames ({total_frames}).")

    window_frames = max(2, int(round(search_window_s * fps)))
    window_frames = min(window_frames, total_frames // 2 - 1)
    head_indices = list(range(0, window_frames, max(1, window_frames // num_samples)))
    tail_start = max(0, total_frames - 1 - window_frames)
    tail_indices = list(range(tail_start, total_frames - 1, max(1, window_frames // num_samples)))

    all_idx = sorted(set(head_indices + tail_indices))
    frames = _read_frames(cv2, path, all_idx)

    if not frames:
        raise RuntimeError(f"Could not decode any frames from {path}")

    head_frames = [(i, frames[i]) for i in head_indices if i in frames]
    tail_frames = [(i, frames[i]) for i in tail_indices if i in frames]

    if not head_frames or not tail_frames:
        raise RuntimeError("Sampling failed: empty head or tail.")

    best: tuple[float, int, int] | None = None

    use_pixel = method in ("pixel", "auto")
    use_hist = method in ("histogram", "auto")
    use_flow = method in ("optical_flow",)

    head_hist = {i: _histogram(cv2, np, f) for i, f in head_frames} if use_hist else {}
    tail_hist = {i: _histogram(cv2, np, f) for i, f in tail_frames} if use_hist else {}

    for h_idx, h_frame in head_frames:
        for t_idx, t_frame in tail_frames:
            if t_idx <= h_idx + 1:
                continue
            score = 0.0
            if use_pixel:
                diff = cv2.absdiff(h_frame, t_frame)
                pixel_score = float(diff.mean()) / 255.0
                score += pixel_weight * pixel_score
            if use_hist:
                corr = cv2.compareHist(
                    head_hist[h_idx], tail_hist[t_idx], cv2.HISTCMP_CORREL
                )
                hist_score = max(0.0, 1.0 - float(corr))
                score += hist_weight * hist_score
            if use_flow:
                # quick optical flow magnitude comparison (single dx)
                hg = cv2.cvtColor(h_frame, cv2.COLOR_BGR2GRAY)
                tg = cv2.cvtColor(t_frame, cv2.COLOR_BGR2GRAY)
                flow = cv2.calcOpticalFlowFarneback(
                    tg, hg, None, 0.5, 1, 11, 2, 5, 1.1, 0
                )
                score += float(np.linalg.norm(flow) / (flow.size or 1))
            if best is None or score < best[0]:
                best = (score, h_idx, t_idx)
        # Avoid blowing up the loop count on huge clips
        if len(head_frames) * len(tail_frames) > 4096:
            break

    if best is None:
        raise RuntimeError("Could not find any candidate loop cut.")

    score, h_idx, t_idx = best
    return LoopCut(
        start_frame=int(h_idx),
        end_frame=int(t_idx),
        start_time_s=h_idx / max(fps, 1e-6),
        end_time_s=t_idx / max(fps, 1e-6),
        score=float(score),
        method=method,
    )


def estimate_loop_quality(cut: LoopCut) -> str:
    """Return a human label for a loop cut score."""
    s = cut.score
    if s < 0.05:
        return "excellent"
    if s < 0.12:
        return "good"
    if s < 0.25:
        return "acceptable"
    if math.isfinite(s):
        return "rough"
    return "unknown"
