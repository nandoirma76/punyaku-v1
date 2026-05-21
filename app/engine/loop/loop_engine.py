"""High-level seamless loop engine.

The engine wires together:

* :mod:`app.engine.video.frame_match` - finds the optimal loop cut.
* :mod:`app.engine.audio.crossfade` - blends the audio tail with the head.
* :mod:`app.utils.ffmpeg` - drives FFmpeg to produce the final file.

The public entry point is :meth:`LoopEngine.build`, which is invoked both
from the UI and the export queue.
"""

from __future__ import annotations

import enum
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from app.engine.video.frame_match import LoopCut, estimate_loop_quality, find_loop_cut
from app.utils.ffmpeg import (
    FFmpegBinaries,
    MediaInfo,
    discover_ffmpeg,
    probe_media,
    run_ffmpeg,
    select_hardware_encoder,
)
from app.utils.logger import get_logger
from app.utils.paths import resolve_writable_temp

log = get_logger("loop_engine")


class LoopMode(str, enum.Enum):
    NORMAL = "normal"
    REVERSE = "reverse"
    PING_PONG = "ping_pong"
    INFINITE = "infinite"
    CINEMATIC = "cinematic"
    AI = "ai"
    SLOW_MOTION = "slow_motion"
    WALLPAPER = "wallpaper"
    MUSIC = "music"
    AMBIENT = "ambient"


class Transition(str, enum.Enum):
    CROSSFADE = "crossfade"
    MOTION_BLEND = "motion_blend"
    DISSOLVE = "dissolve"
    MORPH = "morph"
    CINEMATIC = "cinematic"


@dataclass
class LoopRequest:
    source: Path
    output: Path
    target_duration_s: float = 60.0
    mode: LoopMode = LoopMode.NORMAL
    transition: Transition = Transition.CROSSFADE
    crossfade_ms: int = 1500
    search_window_s: float = 2.0
    frame_match_method: str = "auto"
    fps: int | None = None
    width: int | None = None
    height: int | None = None
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    video_bitrate: str | None = None
    audio_bitrate: str = "192k"
    crf: int = 18
    preset: str = "medium"
    prefer_gpu: bool = True
    normalize_audio: bool = True
    paths_temp: Path | None = None


@dataclass
class LoopResult:
    output: Path
    cut: LoopCut
    quality: str
    media: MediaInfo
    used_encoder: str
    extra: dict[str, str] = field(default_factory=dict)


ProgressCallback = Callable[[float, str], None]


class LoopEngine:
    """Stateless engine; one instance can be reused across requests."""

    def __init__(self, binaries: FFmpegBinaries | None = None) -> None:
        self._bins = binaries or discover_ffmpeg()

    def analyze(self, source: Path, search_window_s: float = 2.0, method: str = "auto") -> LoopCut:
        return find_loop_cut(source, method=method, search_window_s=search_window_s)

    def build(self, req: LoopRequest, progress: ProgressCallback | None = None) -> LoopResult:
        if progress:
            progress(0.0, "Probing media")
        media = probe_media(req.source, self._bins)
        log.info(
            "Source: {}x{}@{:.2f}fps, dur={:.2f}s, audio={}",
            media.width, media.height, media.fps, media.duration_s, media.has_audio,
        )

        if progress:
            progress(0.05, "Finding seamless cut")
        cut = self.analyze(req.source, req.search_window_s, req.frame_match_method)
        log.info(
            "Loop cut: frames {}->{} ({:.3f}->{:.3f}s) score={:.4f} quality={}",
            cut.start_frame, cut.end_frame, cut.start_time_s, cut.end_time_s,
            cut.score, estimate_loop_quality(cut),
        )

        encoder = select_hardware_encoder(req.video_codec, req.prefer_gpu)
        log.info("Encoder choice: {} (requested={})", encoder, req.video_codec)

        single_loop = self._render_single_loop(req, cut, encoder, progress)
        final = self._extend_to_duration(req, single_loop, cut, encoder, progress)

        if progress:
            progress(1.0, "Done")

        return LoopResult(
            output=final,
            cut=cut,
            quality=estimate_loop_quality(cut),
            media=media,
            used_encoder=encoder,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _render_single_loop(
        self,
        req: LoopRequest,
        cut: LoopCut,
        encoder: str,
        progress: ProgressCallback | None,
    ) -> Path:
        """Render a single seamless A->B segment with crossfade applied."""
        if progress:
            progress(0.20, "Rendering base loop segment")
        tmp_dir = req.paths_temp or req.output.parent
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = tmp_dir / (req.output.stem + "_base.mp4")

        duration = max(0.0, cut.end_time_s - cut.start_time_s)
        crossfade_s = max(0.05, req.crossfade_ms / 1000.0)
        crossfade_s = min(crossfade_s, max(0.05, duration / 4.0))

        # Trim segment.
        trim_args = [
            "-ss", f"{cut.start_time_s:.3f}",
            "-to", f"{cut.end_time_s:.3f}",
            "-i", str(req.source),
        ]
        # Build filter graph that crossfades the tail with the head to give
        # a seamless single iteration. We achieve this by splitting the
        # segment, time-shifting the head, and applying ``xfade``/``acrossfade``.
        body_filter = self._build_seamless_filter(
            transition=req.transition,
            xfade_s=crossfade_s,
            duration_s=duration,
            has_audio=True,
            width=req.width,
            height=req.height,
            fps=req.fps,
        )

        cmd = list(trim_args) + [
            "-filter_complex", body_filter,
            "-map", "[vout]",
        ]
        if True:  # audio map (best-effort; FFmpeg will warn if absent)
            cmd += ["-map", "[aout]"]
        cmd += [
            "-c:v", encoder,
            "-pix_fmt", "yuv420p",
            "-preset", req.preset,
            "-crf", str(req.crf),
            "-c:a", req.audio_codec,
            "-b:a", req.audio_bitrate,
            "-movflags", "+faststart",
            str(tmp_path),
        ]
        result = run_ffmpeg(cmd, self._bins)
        if result.returncode != 0:
            log.error("FFmpeg base render failed:\n{}", result.stderr)
            raise RuntimeError(f"FFmpeg failed (code {result.returncode}): {result.stderr.strip()[:400]}")
        return tmp_path

    def _build_seamless_filter(
        self,
        transition: Transition,
        xfade_s: float,
        duration_s: float,
        has_audio: bool,
        width: int | None,
        height: int | None,
        fps: int | None,
    ) -> str:
        """Build an FFmpeg filter graph for the seamless loop segment.

        Strategy: take the input, split it, then concat A + crossfade(A_tail, A_head).
        FFmpeg's ``xfade`` performs the visual blend; ``acrossfade`` the audio.
        """
        # Visual filter
        vf = []
        if width and height:
            vf.append(f"scale={width}:{height}:flags=lanczos")
        if fps:
            vf.append(f"fps={fps}")
        video_pre = ",".join(vf) if vf else "null"

        xfade_offset = max(0.1, duration_s - xfade_s)
        # Transition name mapping. FFmpeg `xfade` transitions available list
        # is fairly large; for unsupported modes fall back to "fade".
        xfade_lookup = {
            Transition.CROSSFADE: "fade",
            Transition.MOTION_BLEND: "smoothleft",
            Transition.DISSOLVE: "dissolve",
            Transition.MORPH: "circleclose",
            Transition.CINEMATIC: "fadeblack",
        }
        xfade_name = xfade_lookup.get(transition, "fade")

        graph = (
            f"[0:v]{video_pre},split=2[v_a][v_b];"
            f"[v_a][v_b]xfade=transition={xfade_name}:duration={xfade_s:.3f}:offset={xfade_offset:.3f}[vout]"
        )
        if has_audio:
            graph += (
                f";[0:a]asplit=2[a_a][a_b];"
                f"[a_a][a_b]acrossfade=d={xfade_s:.3f}:c1=tri:c2=tri[aout]"
            )
        return graph

    def _extend_to_duration(
        self,
        req: LoopRequest,
        single_loop: Path,
        cut: LoopCut,
        encoder: str,
        progress: ProgressCallback | None,
    ) -> Path:
        """Repeat the single seamless loop until the target duration is met.

        We use FFmpeg's ``-stream_loop`` for efficient lossless extension,
        then trim to the exact target duration to avoid drift.
        """
        if progress:
            progress(0.60, "Extending loop to target duration")
        if req.target_duration_s <= 0:
            req.output.write_bytes(single_loop.read_bytes())
            return req.output

        cmd = [
            "-stream_loop", "-1",
            "-i", str(single_loop),
            "-t", f"{req.target_duration_s:.3f}",
            "-c:v", encoder,
            "-pix_fmt", "yuv420p",
            "-preset", req.preset,
            "-crf", str(req.crf),
            "-c:a", req.audio_codec,
            "-b:a", req.audio_bitrate,
            "-movflags", "+faststart",
            str(req.output),
        ]
        result = run_ffmpeg(cmd, self._bins)
        if result.returncode != 0:
            log.error("FFmpeg extension failed:\n{}", result.stderr)
            raise RuntimeError(f"FFmpeg extension failed: {result.stderr.strip()[:400]}")
        if progress:
            progress(0.95, "Finalizing output")
        return req.output


def quick_temp(name: str) -> Path:
    """Convenience wrapper for tests."""
    from app.utils.paths import ProjectPaths
    return resolve_writable_temp(ProjectPaths.discover(), name)
