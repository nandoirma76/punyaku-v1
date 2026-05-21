# Live Streaming

## RTMP push

```python
from pathlib import Path
from app.streaming.rtmp import RtmpStreamer, RtmpTarget, PRESET_TARGETS

target = RtmpTarget(
    name="youtube",
    url=f"{PRESET_TARGETS['youtube']}/STREAM-KEY",
    bitrate_video="6000k",
    prefer_gpu=True,
)
streamer = RtmpStreamer(Path("loops/ambient_24h.mp4"), target)
streamer.on_status(lambda msg: print(msg))
streamer.start()
```

`RtmpStreamer` runs FFmpeg with `-stream_loop -1` (infinite repeat) and
re-spawns on disconnect with exponential backoff. It is fully
thread-safe and does not require the GUI.

## OBS WebSocket

`app/streaming/obs.py` implements a minimal probe (`ping()`) and a
forward-compatible `send()` method. The full WebSocket v5 protocol is
implemented by the `obsws-python` package — installing it activates real
scene-switching / source updates without changes to the rest of the code.

## Virtual camera

Punyaku does not ship a virtual camera driver. On Windows the
recommended approach is OBS Studio's built-in virtual cam (Tools →
Start Virtual Camera) with Punyaku's looped MP4 as a media source. On
Linux use the `v4l2loopback` kernel module and have FFmpeg push to
`/dev/video10`.

```bash
sudo modprobe v4l2loopback devices=1 video_nr=10 card_label="Punyaku"
ffmpeg -re -stream_loop -1 -i loops/ambient.mp4 -vcodec rawvideo -f v4l2 /dev/video10
```
