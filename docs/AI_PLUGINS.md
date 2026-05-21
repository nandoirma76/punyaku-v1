# AI Plugins

Every AI feature is exposed through a plugin in `app/ai/`. Plugins
self-register on import via the `@register` decorator.

| Plugin             | Category       | Status    | Dependencies                                  |
| ------------------ | -------------- | --------- | --------------------------------------------- |
| Real-ESRGAN        | upscale        | available | `realesrgan`, `basicsr`, `torch`              |
| Waifu2x            | upscale        | external  | `waifu2x-ncnn-vulkan` binary on PATH          |
| Anime4K            | upscale        | external  | Anime4K shader pack + OpenGL/Vulkan context   |
| RIFE               | interpolation  | available | `torch`, model weights in `models/rife/`      |
| DAIN               | interpolation  | external  | Original CUDA repo + weights                  |
| GFPGAN             | restoration    | available | `gfpgan`                                      |
| AudioDenoiser      | audio          | available | `noisereduce` (optional)                      |
| AITransition       | generative     | stub      | FILM / Stable Video Diffusion (planned)       |

`available` means the dependency is detected and the plugin's `load()`
method should succeed. `external` means a binary or weights have to be
provided manually (because of license / size constraints).

## Activating a plugin

1. Install the heavy dependencies (e.g. `pip install realesrgan
   basicsr`).
2. Download the model weights into the matching folder under `models/`
   (`models/realesrgan/RealESRGAN_x4plus.pth`,
   `models/rife/rife_v4.6.pth`, etc.).
3. Restart Punyaku. The Settings tab will now list the plugin as
   *available*.

## Authoring a new plugin

```python
from app.ai.base import AIPlugin, ModelDescriptor, register

@register
class MyPlugin(AIPlugin):
    name = "MyPlugin"
    category = "upscale"
    requires_gpu = True
    description = "Short user-facing description."

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
        except Exception:
            return False
        return True

    def required_models(self) -> list[ModelDescriptor]:
        return [ModelDescriptor(name="my-weights.pth", url="https://...", size_mb=42)]

    def load(self) -> None:
        ...  # lazy import + load weights

    def process(self, payload, **kwargs):
        ...  # run inference and return the result
```

Drop the file into `app/ai/<category>/`. It is picked up by the smoke
test and surfaced in the Settings page automatically.
