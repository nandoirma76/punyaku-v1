# Usage Guide

This guide assumes you have already run `setup.bat` / `setup.sh`.

## 1. Import a clip

1. Open the **Video Editor** tab.
2. Drag a video onto the *Source clip* area, or click **Browse**.
3. Click **Inspect** to probe the clip via `ffprobe` (you'll see
   width × height × FPS × duration × codec).

Supported containers: `mp4`, `mkv`, `mov`, `avi`, `webm`, `flv`, `gif`.

## 2. Configure the loop

The *Loop settings* card exposes:

| Field           | What it does                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------- |
| Target duration | Final length after the seamless loop is repeated (1 s — 24 h).                                  |
| Loop mode       | `normal`, `reverse`, `ping_pong`, `infinite`, `cinematic`, `ai`, `slow_motion`, `wallpaper`, ... |
| Transition      | `crossfade`, `motion_blend`, `dissolve`, `morph`, `cinematic` (mapped to FFmpeg `xfade`).       |
| Crossfade ms    | Length of the blended overlap region. Defaults to 1500 ms.                                      |
| Frame match     | `auto`, `pixel`, `histogram`, `optical_flow`. `auto` combines pixel + histogram.                |
| Prefer hw encoder | When checked, picks NVENC / AMF / QSV automatically.                                          |

## 3. Pick a preset and render

In the *Render* card choose a preset (TikTok, Shorts, Reels, YouTube,
OBS, Wallpaper Engine, Anime, Cinematic 4K, WebM, GIF). Click **Add to
Queue** to enqueue the job — the queue runs jobs in the background using
the worker pool configured under Settings → "Render workers".

## 4. Watch progress

Open the **Queue** tab. Each row shows the job ID, source clip, preset,
status (`pending` → `running` → `done` / `error`), progress percent, and
final output path. You can clear finished jobs from the toolbar.

## 5. Music visualizer

Open the **Visualizer** tab. Pick a style (`bar`, `wave`, `circle`,
`particle`) and toggle beat-reactive. The preview is driven by a
synthetic spectrum until you connect a real audio source — that is wired
in the *Audio* tab.

## 6. Audio

Open the **Audio** tab to import a music file, run BPM analysis (powered
by `librosa.beat.beat_track`), and tweak per-track effects (volume, bass,
reverb, normalize, AI denoise).

## 7. Settings

The **Settings** tab persists changes to `app/config/config.json`:

- Theme (`dark_neon`, `dark_glass`, `midnight`, `cyberpunk`).
- Language (`id` / `en`).
- Render worker count.
- Cache cap (MB).
- "Prefer hardware encoder" default.

It also lists detected GPU capabilities (CUDA, ROCm, MPS, FFmpeg
encoders) and the status of every AI plugin (`available` /
`stub (install required)`).

## 8. CLI flags

```text
python -m app                 # normal mode
python -m app --safe-mode     # disable GPU + heavy plugins
python -m app --debug         # verbose logs, dev tools
python -m app --low-ram       # smaller caches, smaller previews
python -m app --performance   # max throughput, less UI smoothness
python -m app --check         # headless smoke test (used by CI)
python -m app --project foo.punyaku
```
