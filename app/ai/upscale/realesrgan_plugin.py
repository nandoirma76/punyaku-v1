"""Real-ESRGAN super-resolution plugin (interface + lazy loader)."""

from __future__ import annotations

from typing import Any

from app.ai.base import AIPlugin, ModelDescriptor, register
from app.utils.logger import get_logger

log = get_logger("ai.upscale.realesrgan")


@register
class RealESRGANPlugin(AIPlugin):
    name = "Real-ESRGAN"
    category = "upscale"
    requires_gpu = True
    description = (
        "General-purpose AI super-resolution (2x/4x). Best for live-action, "
        "wallpapers, cinematic loops."
    )

    def __init__(self) -> None:
        self._upsampler = None

    def is_available(self) -> bool:
        try:
            import realesrgan  # type: ignore[import-not-found]  # noqa: F401
            import torch  # type: ignore[import-not-found]  # noqa: F401
        except Exception:
            return False
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return [
            ModelDescriptor(
                name="RealESRGAN_x4plus.pth",
                url=(
                    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/"
                    "RealESRGAN_x4plus.pth"
                ),
                size_mb=64.0,
                required_for=["upscale-4x"],
            ),
        ]

    def load(self) -> None:
        try:
            import torch  # type: ignore[import-not-found]
            from basicsr.archs.rrdbnet_arch import RRDBNet  # type: ignore[import-not-found]
            from realesrgan import RealESRGANer  # type: ignore[import-not-found]
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Real-ESRGAN dependencies are not installed. "
                "Install via: pip install realesrgan basicsr"
            ) from exc

        model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
        self._upsampler = RealESRGANer(
            scale=4,
            model_path="models/RealESRGAN_x4plus.pth",
            model=model,
            half=torch.cuda.is_available(),
        )

    def process(self, payload: Any, **kwargs: Any) -> Any:
        if self._upsampler is None:
            self.load()
        scale = kwargs.get("scale", 4)
        output, _ = self._upsampler.enhance(payload, outscale=scale)  # type: ignore[union-attr]
        return output
