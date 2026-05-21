"""AI-generated transition plugin (interface).

The intended back-end is Stable Video Diffusion / FILM / Frame
Interpolation models. For now we expose the interface so the UI can
list it as a planned feature.
"""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register


@register
class AITransitionPlugin(AIPlugin):
    name = "AI Transition"
    category = "generative"
    requires_gpu = True
    description = "Synthesize cinematic transitions between dissimilar frames."

    def is_available(self) -> bool:
        return False

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="FILM (Frame Interpolation for Large Motion)",
                url="https://github.com/google-research/frame-interpolation",
                size_mb=160.0,
                required_for=["ai-transition"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover
        raise NotImplementedError("Configure FILM weights in models/ai_transition/.")

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
