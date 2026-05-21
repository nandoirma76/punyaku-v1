"""Anime4K shader pipeline plugin (interface)."""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register


@register
class Anime4KPlugin(AIPlugin):
    name = "Anime4K"
    category = "upscale"
    requires_gpu = True
    description = "Real-time anime upscaling via GLSL shaders (Anime4K v4 chain)."

    def is_available(self) -> bool:
        return False

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="Anime4K shader pack",
                url="https://github.com/bloc97/Anime4K/releases",
                size_mb=1.0,
                required_for=["anime-shader"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Anime4K requires the GLSL shader pack and an OpenGL/Vulkan render context. "
            "Configure paths in app/config/anime4k.json and re-launch."
        )

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
