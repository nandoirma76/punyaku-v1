"""RTMP push: stream a looping file (or playlist) to any RTMP target.

Implementation strategy:

* Spin up FFmpeg with ``-stream_loop -1`` reading the looped source.
* Encode with the configured codec (NVENC > AMF > QSV > software).
* Push to the user-supplied ``rtmp://`` URL.
* Auto-reconnect: if FFmpeg exits non-zero we relaunch after a backoff.

The class is deliberately decoupled from Qt so it can be reused from the
CLI ("punyaku stream --to rtmp://..." -- not yet wired up).
"""

from __future__ import annotations

import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.utils.ffmpeg import discover_ffmpeg, select_hardware_encoder
from app.utils.logger import get_logger

log = get_logger("streaming.rtmp")


@dataclass
class RtmpTarget:
    name: str
    url: str            # rtmp://live.youtube.com/app/STREAM-KEY
    prefer_gpu: bool = True
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    bitrate_video: str = "6000k"
    bitrate_audio: str = "192k"
    preset: str = "veryfast"


PRESET_TARGETS = {
    "youtube": "rtmp://a.rtmp.youtube.com/live2",
    "twitch": "rtmp://live.twitch.tv/app",
    "tiktok": "rtmp://push.tiktokcdn.com/live",
    "facebook": "rtmps://live-api-s.facebook.com:443/rtmp",
}


class RtmpStreamer:
    def __init__(self, source: Path, target: RtmpTarget) -> None:
        self.source = Path(source)
        self.target = target
        self._proc: subprocess.Popen | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._on_status: Callable[[str], None] | None = None

    def on_status(self, fn: Callable[[str], None]) -> None:
        self._on_status = fn

    def _emit(self, msg: str) -> None:
        log.info("rtmp[{}]: {}", self.target.name, msg)
        if self._on_status:
            try:
                self._on_status(msg)
            except Exception:  # pragma: no cover
                log.exception("rtmp status callback failed")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
            except Exception:  # pragma: no cover
                log.exception("terminate failed")

    def _build_cmd(self) -> list[str]:
        bins = discover_ffmpeg()
        encoder = select_hardware_encoder(self.target.video_codec, self.target.prefer_gpu)
        return [
            bins.ffmpeg, "-hide_banner", "-loglevel", "warning",
            "-re",
            "-stream_loop", "-1",
            "-i", str(self.source),
            "-c:v", encoder,
            "-preset", self.target.preset,
            "-b:v", self.target.bitrate_video,
            "-maxrate", self.target.bitrate_video,
            "-bufsize", self.target.bitrate_video,
            "-pix_fmt", "yuv420p",
            "-g", "60",
            "-c:a", self.target.audio_codec,
            "-b:a", self.target.bitrate_audio,
            "-ar", "44100",
            "-f", "flv",
            self.target.url,
        ]

    def _run_loop(self) -> None:
        backoff = 2
        while not self._stop.is_set():
            cmd = self._build_cmd()
            self._emit("starting")
            try:
                self._proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, text=True)
                stderr = self._proc.stderr
                while self._proc.poll() is None and not self._stop.is_set():
                    if stderr is None:
                        time.sleep(0.5)
                        continue
                    line = stderr.readline()
                    if not line:
                        time.sleep(0.2)
                        continue
                    line = line.strip()
                    if line:
                        self._emit(line)
                rc = self._proc.poll()
                self._emit(f"exit {rc}")
            except FileNotFoundError as exc:  # pragma: no cover
                self._emit(f"ffmpeg missing: {exc}")
                return
            except Exception as exc:  # pragma: no cover
                self._emit(f"error: {exc}")

            if self._stop.is_set():
                break
            self._emit(f"reconnect in {backoff}s")
            time.sleep(backoff)
            backoff = min(backoff * 2, 30)
