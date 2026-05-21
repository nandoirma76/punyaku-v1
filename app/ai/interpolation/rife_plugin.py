"""RIFE motion interpolation plugin (interface).

RIFE is used to:

* Generate smooth intermediate frames between loop boundary candidates.
* Boost frame rate (24/30 -> 60/120) for cinematic / slow motion loops.
"""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register


@register
class RIFEPlugin(AIPlugin):
    name = "RIFE"
    category = "interpolation"
    requires_gpu = True
    description = "Real-Time Intermediate Flow Estimation for smooth interpolation."

    def is_available(self) -> bool:
        try:
            import torch  # type: ignore[import-not-found]  # noqa: F401
        except Exception:
            return False
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="rife_v4.6",
                url="https://github.com/megvii-research/ECCV2022-RIFE",
                size_mb=64.0,
                required_for=["interpolation"],
            ),
        ]

    def load(self) -> None:  # pragma: no cover
        raise NotImplementedError(
            "Place RIFE weights into models/rife/ then enable in Settings -> AI."
        )

    def process(self, payload: Any, **kwargs: Any) -> Any:  # pragma: no cover
        raise NotImplementedError
