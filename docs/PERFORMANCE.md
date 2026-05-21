# Performance Tuning

## Encoder selection

| Hardware                | Encoder used by default | Notes                                     |
| ----------------------- | ----------------------- | ----------------------------------------- |
| NVIDIA (consumer + pro) | `h264_nvenc` / `hevc_nvenc` | Lowest CPU, near-realtime 4K            |
| AMD GPU                 | `h264_amf` / `hevc_amf` | Windows + recent Mesa on Linux            |
| Intel iGPU / Arc        | `h264_qsv` / `hevc_qsv` | QuickSync, very low power                 |
| None / software         | `libx264` / `libx265`   | Use higher `preset=fast` for short clips  |

The encoder fallback chain lives in `app/utils/ffmpeg.py:select_hardware_encoder`.

## Worker pool

`Settings → Render workers` configures `ExportQueue(max_workers=N)`. For
GPU encoders, **keep `N = 1`** unless you have multiple GPUs — NVENC has
a hard session limit. For CPU encodes, use `os.cpu_count() // 2`.

## Cache strategy

The exporter writes a "base loop" intermediate to `temp/` before
expanding it to the target duration. That intermediate uses the same
encoder as the final to keep quality consistent, but you can flip
`req.keep_intermediate=True` in the export settings to inspect it.

`clean_cache.bat` / `clean_cache` menu option wipes both `cache/` and
`temp/` while preserving the `.gitkeep` markers.

## Low-RAM mode

`python -m app --low-ram` reduces:

- Frame matching downsample size (256 → 192 px).
- Cache cap (4 GB → 1 GB).
- Visualizer FFT size (1024 → 512).

(Knobs read from `Settings.runtime.low_ram` inside the engine.)

## Profiling

A simple FFmpeg profile is logged for every job to `logs/punyaku.log`:

```
ffmpeg: -hide_banner -y -ss 0.000 -to 9.500 -i ...
ffmpeg base render OK in 4.21s
ffmpeg extend OK in 18.30s
```

Wrap your run with `--debug` for full subprocess output and timings.
