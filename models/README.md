# Models directory

This folder is the destination for AI model weights downloaded by the
auto-installer or copied manually.

Expected sub-folders:

```
models/
├── realesrgan/        # RealESRGAN_x4plus.pth, RealESRGAN_anime_6B.pth
├── rife/              # rife_v4.6.pth
├── gfpgan/            # GFPGANv1.4.pth
├── waifu2x-ncnn/      # waifu2x-ncnn-vulkan binary + .param/.bin pairs
└── anime4k/           # Anime4K_*.glsl shaders
```

`.pth`, `.onnx`, `.bin`, `.ckpt`, and `.safetensors` files are excluded
from git via `.gitignore`.

Run `python -m app --check` after placing weights to confirm the plugins
detect them.
