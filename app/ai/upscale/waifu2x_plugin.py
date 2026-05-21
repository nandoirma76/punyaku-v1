"""Waifu2x plugin (anime-optimised super-resolution)."""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register
from app.utils.logger import get_logger

log = get_logger("ai.upscale.waifu2x")


@register
class Waifu2xPlugin(AIPlugin):
    name = "Waifu2x"
    category = "upscale"
    requires_gpu = False
    description = "Anime-style upscaler with denoise (NCNN back-end via waifu2x-ncnn-vulkan)."

    def is_available(self) -> bool:
        try:
            import shutil  # noqa: F401  - kept for symmetry with other plugins
        except Exception:
            return False
        # The recommended distribution is the standalone waifu2x-ncnn-vulkan
        # CLI. We detect it lazily via PATH inside :meth:`load`.
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="waifu2x-ncnn-vulkan",
                url="https://github.com/nihui/waifu2x-ncnn-vulkan/releases",
                size_mb=8.0,
                required_for=["anime-upscale"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover - external binary
        import shutil
        if not shutil.which("waifu2x-ncnn-vulkan"):
            raise RuntimeError(
                "waifu2x-ncnn-vulkan binary not found. Place it in plugins/ "
                "or install via setup script."
            )

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError(
            "Waifu2x runs as an external binary; pipe frames via FFmpeg + the "
            "waifu2x-ncnn-vulkan CLI. See docs/AI_PLUGINS.md."
        )
