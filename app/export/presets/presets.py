"""Built-in export presets (TikTok, YouTube, Shorts, Reels, OBS, etc.)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportPreset:
    key: str
    label: str
    description: str
    width: int
    height: int
    fps: int
    container: str       # mp4|mov|webm|gif
    video_codec: str
    audio_codec: str
    crf: int
    preset: str
    bitrate_video: str | None = None
    bitrate_audio: str = "192k"


PRESETS: dict[str, ExportPreset] = {
    "youtube_1080p": ExportPreset(
        key="youtube_1080p",
        label="YouTube 1080p",
        description="1920x1080 @ 30fps H.264 (recommended YouTube upload).",
        width=1920, height=1080, fps=30,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=18, preset="medium",
    ),
    "youtube_4k": ExportPreset(
        key="youtube_4k",
        label="YouTube 4K",
        description="3840x2160 @ 30fps H.265.",
        width=3840, height=2160, fps=30,
        container="mp4", video_codec="libx265", audio_codec="aac",
        crf=20, preset="slow",
    ),
    "shorts": ExportPreset(
        key="shorts",
        label="YouTube Shorts",
        description="1080x1920 vertical @ 30fps.",
        width=1080, height=1920, fps=30,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=18, preset="medium",
    ),
    "tiktok": ExportPreset(
        key="tiktok",
        label="TikTok",
        description="1080x1920 vertical @ 30fps, optimized bitrate.",
        width=1080, height=1920, fps=30,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=20, preset="medium",
    ),
    "reels": ExportPreset(
        key="reels",
        label="Instagram Reels",
        description="1080x1920 vertical @ 30fps.",
        width=1080, height=1920, fps=30,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=20, preset="medium",
    ),
    "obs": ExportPreset(
        key="obs",
        label="OBS Loop Source",
        description="1920x1080 @ 60fps MP4 for live broadcasters.",
        width=1920, height=1080, fps=60,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=18, preset="medium",
    ),
    "wallpaper_engine": ExportPreset(
        key="wallpaper_engine",
        label="Wallpaper Engine",
        description="3840x2160 MP4 for Wallpaper Engine.",
        width=3840, height=2160, fps=30,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=20, preset="medium",
    ),
    "anime": ExportPreset(
        key="anime",
        label="Anime Loop",
        description="1920x1080 @ 60fps tuned for animated content.",
        width=1920, height=1080, fps=60,
        container="mp4", video_codec="libx264", audio_codec="aac",
        crf=18, preset="slow",
    ),
    "cinematic_4k": ExportPreset(
        key="cinematic_4k",
        label="Cinematic 4K",
        description="3840x2160 @ 24fps H.265 cinematic.",
        width=3840, height=2160, fps=24,
        container="mp4", video_codec="libx265", audio_codec="aac",
        crf=18, preset="slow",
    ),
    "gif_low": ExportPreset(
        key="gif_low",
        label="GIF (small)",
        description="640x360 @ 15fps GIF.",
        width=640, height=360, fps=15,
        container="gif", video_codec="gif", audio_codec="none",
        crf=0, preset="default",
    ),
    "webm_vp9": ExportPreset(
        key="webm_vp9",
        label="WebM VP9",
        description="1920x1080 @ 30fps VP9 (web-friendly).",
        width=1920, height=1080, fps=30,
        container="webm", video_codec="libvpx-vp9", audio_codec="libopus",
        crf=30, preset="medium",
    ),
}


def list_presets() -> list[ExportPreset]:
    return list(PRESETS.values())


def get(key: str) -> ExportPreset:
    if key not in PRESETS:
        raise KeyError(f"Unknown export preset: {key!r}")
    return PRESETS[key]
