"""DAIN motion interpolation plugin (interface)."""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register


@register
class DAINPlugin(AIPlugin):
    name = "DAIN"
    category = "interpolation"
    requires_gpu = True
    description = "Depth-Aware Video Interpolation (CUDA only, very VRAM heavy)."

    def is_available(self) -> bool:
        return False  # heavy CUDA build; opt-in only

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="DAIN model bundle",
                url="https://github.com/baowenbo/DAIN",
                size_mb=200.0,
                required_for=["interpolation-cinematic"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover
        raise NotImplementedError("Enable DAIN by installing the original CUDA repo.")

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
