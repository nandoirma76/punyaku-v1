# Architecture

Punyaku is split into four layers:

```
┌───────────────────────────────────────────────────────────────┐
│                          UI (PyQt6)                           │
│  pages/  widgets/  themes/  application.py  main_window.py    │
└──────────────▲──────────────────▲────────────────▲────────────┘
               │                  │                │
        ExportQueue          LoopEngine        Visualizer
               │                  │                │
┌──────────────┴──────────────────┴────────────────┴────────────┐
│                          ENGINE                               │
│  engine/video    engine/audio    engine/loop    engine/viz    │
└──────────────▲──────────────────▲────────────────▲────────────┘
               │                  │                │
         FFmpeg utils         Hardware/GPU      AI plugins
                                                (lazy import)
┌───────────────────────────────────────────────────────────────┐
│                         BACKEND                               │
│   project (.punyaku) · cache · recovery (autosave + crash)    │
└───────────────────────────────────────────────────────────────┘
```

## Design rules

1. **Lazy heavy imports** — anything that pulls torch / cv2 / librosa
   only does so inside a function body, not at module import. The smoke
   check (`python -m app --check`) therefore runs even when those
   packages are missing.
2. **PyQt6 is the only UI dependency**. The engine layer must not import
   `PyQt6` so it can be reused from a CLI or a future web front-end.
3. **No raw ffmpeg strings** in the UI — all FFmpeg invocations go
   through `app.utils.ffmpeg` so encoder selection (NVENC > AMF > QSV >
   software) is centralised.
4. **Plugin contract** — every AI feature implements `AIPlugin` and
   self-registers in `app.ai.base`. UIs only see metadata until a plugin
   is explicitly activated.
5. **Settings persistence** is JSON (`config/config.json`). Reading the
   settings file never raises; missing fields fall back to defaults.

## Data flow: build a loop

```
User picks clip (Editor page)
        │
        ▼
ExportJob (preset_key, duration, transition, ...)
        │
        ▼
ExportQueue.submit ──► ThreadPoolExecutor
        │
        ▼
Exporter.export() ──► LoopRequest ──► LoopEngine.build()
                                          │
                                          ├─ probe_media(ffprobe)
                                          ├─ find_loop_cut(frame_match)
                                          ├─ select_hardware_encoder
                                          ├─ FFmpeg: xfade + acrossfade
                                          └─ FFmpeg: stream_loop -t duration
        │
        ▼
QueueItem.status = "done"  ──► UI listeners refresh
```

## Recovery

`RecoveryManager` writes `temp/session.running` at startup and removes
it on graceful exit (`atexit`). If the marker is present on the next
launch, the app knows the previous session crashed and can offer to
restore the autosave found at `temp/autosave/last_project.punyaku.json`.

## Threading model

- **UI thread**: PyQt6 event loop.
- **Render workers**: `concurrent.futures.ThreadPoolExecutor`
  (configurable via Settings → "Render workers"). Each worker spawns
  FFmpeg as a subprocess and waits.
- **Hardware monitor / preview**: 1-2 Hz `QTimer` polls inside the UI.
- **Recovery autosave**: a daemon `threading.Timer` snapshots the
  current project every 60 s.

## Failure handling

- All public engine methods catch low-level exceptions and re-raise as
  `RuntimeError("ffmpeg failed: ...")` with the stderr tail attached.
- The queue captures exceptions per-job into `QueueItem.error` so the UI
  can show the failure without crashing the worker pool.
- Loguru rotates `logs/punyaku.log` at 10 MB and keeps 5 archives.
