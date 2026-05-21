# Punyaku Video Looper

> Studio aplikasi desktop **AI-powered** untuk membuat video looping seamless
> ultra halus — tanpa jeda, patah, blink, frame skip, atau audio putus.

Punyaku menyatukan **engine looping berbasis FFmpeg + OpenCV**, **deteksi
loop point dengan optical flow + histogram + pixel matching**, **audio
crossfade equal-power + BPM sync**, dan **plugin AI** (Real-ESRGAN,
Waifu2x, Anime4K, RIFE, DAIN, GFPGAN, denoiser, generative transition)
dalam satu UI PyQt6 modern dengan tema dark / neon / glassmorphism.

Target pengguna: content creator, YouTuber, TikToker, streamer, editor
video, animator, creator ambience / ASMR / music visualizer / wallpaper,
anime editor, dan studio multimedia.

---

## ✨ Highlights

- **Seamless Loop Engine** — pencarian frame match otomatis, equal-power
  audio crossfade, beat / BPM snap, multi-mode (normal, reverse,
  ping-pong, infinite, cinematic, AI, slow motion, wallpaper, music,
  ambient).
- **GPU acceleration** — auto-detect NVIDIA NVENC / AMD AMF / Intel
  QuickSync; pemilihan encoder berjenjang dengan fallback software.
- **AI plugin system** — plug-in untuk upscaling (Real-ESRGAN / Waifu2x
  / Anime4K), motion interpolation (RIFE / DAIN), face restoration
  (GFPGAN), audio denoise, dan AI transition generator. Model
  weights dimuat *lazily*, jadi GUI tetap bisa start tanpa mereka.
- **Music visualizer GPU-friendly** — 4 style (bar, wave, circle,
  particle), beat-reactive, custom accent color.
- **Export preset siap pakai** — TikTok, Shorts, Reels, YouTube 1080p /
  4K, OBS, Wallpaper Engine, Anime, Cinematic 4K, WebM VP9, GIF.
- **Batch render queue** dengan multithreading dan progress per-job.
- **Live streaming RTMP** — push ke YouTube / Twitch / TikTok / Facebook
  dengan auto-reconnect dan auto-bitrate.
- **Project file `.punyaku`** dengan autosave & crash recovery.
- **Hardware monitor** — CPU/RAM/GPU/VRAM live di topbar dan dashboard.
- **Setup otomatis** — `setup.bat` (Windows) & `setup.sh` (Linux/macOS)
  yang membuat virtualenv, install dependency, detect GPU, install
  PyTorch yang sesuai, dan menjalankan smoke check.

---

## 🚀 Quick Start

### Windows

```bat
setup.bat       :: install dependencies (sekali saja)
run.bat         :: launcher dengan menu (Normal / Safe / Debug / Performance / Low-RAM)
```

### Linux / macOS

```bash
./setup.sh
./run.sh          # menu launcher
./run.sh --debug  # atau lewatkan flag CLI langsung
```

### Tanpa launcher (manual)

```bash
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements_cpu.txt   # atau requirements_gpu.txt jika ada CUDA
python -m app                          # buka GUI
python -m app --check                  # smoke test (headless, untuk CI)
```

---

## 🧠 Pemilihan dependency

| Skenario               | Perintah install                                                                            |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| Core (UI + engine)     | `pip install -r requirements.txt`                                                            |
| Mesin dengan NVIDIA    | `pip install -r requirements.txt && pip install -r requirements_gpu.txt`                     |
| Mesin tanpa GPU        | `pip install -r requirements.txt && pip install -r requirements_cpu.txt`                     |
| Developer (tests/lint) | `pip install -r requirements_dev.txt`                                                        |

PyTorch CUDA wheel pasti dengan `--index-url
https://download.pytorch.org/whl/cuXYZ` — `setup.bat` / `setup.sh`
melakukannya otomatis ketika `nvidia-smi` terdeteksi.

---

## 🗂 Project Structure

```
punyaku-v1/
├── app/
│   ├── __main__.py                # entry: python -m app
│   ├── version.py
│   ├── config/                    # typed settings + JSON persistence
│   ├── utils/                     # logger, paths, ffmpeg, hardware, gpu
│   ├── engine/
│   │   ├── video/                 # frame matching, optical flow
│   │   ├── audio/                 # crossfade, beat, normalize
│   │   ├── loop/                  # high-level LoopEngine
│   │   └── visualizer/            # spectrum analyzer
│   ├── export/                    # exporter, presets, queue
│   ├── ai/                        # plugin interfaces (upscale/interp/restore/audio/gen)
│   ├── streaming/                 # RTMP, OBS WebSocket
│   ├── cloud/                     # cloud render stubs
│   ├── backend/                   # project file, cache mgmt, recovery
│   └── ui/                        # PyQt6 (themes, widgets, pages)
├── assets/                        # icons, splash, templates, sounds
├── cache/  temp/  logs/  export/  models/  plugins/   (runtime, gitignored)
├── install/                       # PyInstaller spec, splash
├── scripts/                       # extra dev scripts
├── docs/                          # design docs (ARCHITECTURE.md, USAGE.md, ...)
├── tests/                         # pytest smoke tests
├── requirements*.txt              # base / gpu / cpu / dev
├── pyproject.toml
├── setup.bat   setup.sh           # installers
├── run.bat     run.sh             # launchers
├── build_exe.bat
├── clean_cache.bat
└── update.bat
```

---

## 🛠 Membangun .EXE (Windows)

```bat
build_exe.bat
```

Akan menghasilkan `dist\Punyaku\Punyaku.exe`. Spec PyInstaller ada di
`install/punyaku.spec` — bisa di-edit untuk mode `--onefile`, custom
icon, dll.

---

## 🧩 Plugin AI

Semua plug-in AI mengimplementasikan kontrak yang sama
(<code>app/ai/base.py</code>). Saat tab **Settings** dibuka, daftar
plug-in akan ditampilkan dengan status `available` atau `stub (install
required)`. Setiap plug-in melaporkan model weights yang dibutuhkan,
sehingga utility downloader (lihat `docs/AI_PLUGINS.md`) bisa
mengambilnya secara on-demand.

---

## 🧪 Tests

```bash
pip install -r requirements_dev.txt
pytest -q
ruff check app
```

---

## 📚 Dokumentasi Lanjutan

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — diagram & alur data.
- [`docs/USAGE.md`](docs/USAGE.md) — panduan workflow (import → loop → export).
- [`docs/AI_PLUGINS.md`](docs/AI_PLUGINS.md) — cara mengaktifkan plugin AI.
- [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md) — tuning batch render / GPU.
- [`docs/STREAMING.md`](docs/STREAMING.md) — setup RTMP / OBS.

---

## 🪪 Lisensi

MIT — bebas digunakan untuk proyek pribadi maupun komersial.

---

## 🙋 Author

Made by [@nandoirma76](https://github.com/nandoirma76).
