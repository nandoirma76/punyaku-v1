"""GFPGAN face restoration plugin (interface)."""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register


@register
class GFPGANPlugin(AIPlugin):
    name = "GFPGAN"
    category = "restoration"
    requires_gpu = False
    description = "Face restoration that pairs nicely with Real-ESRGAN upscaling."

    def is_available(self) -> bool:
        try:
            import gfpgan  # type: ignore[import-not-found]  # noqa: F401
        except Exception:
            return False
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="GFPGANv1.4.pth",
                url=(
                    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/"
                    "GFPGANv1.4.pth"
                ),
                size_mb=348.0,
                required_for=["face-restore"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover
        raise NotImplementedError("Install gfpgan via requirements_gpu.txt to enable.")

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
