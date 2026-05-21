"""Standalone export-preset manager (batch + single-file)."""

from __future__ import annotations

from pathlib import Path

from PyQt6 import QtWidgets

from app.config.settings import Settings
from app.export.exporter import ExportJob
from app.export.presets.presets import list_presets
from app.export.queue import ExportQueue
from app.ui.widgets.card import Card


class ExportPage(QtWidgets.QWidget):
    def __init__(
        self,
        settings: Settings,
        queue: ExportQueue,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.queue = queue
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        intro = Card("Export presets")
        intro.add_body(QtWidgets.QLabel(
            "Select a preset, pick a source clip, and the exporter will queue "
            "a job that uses the seamless loop engine + the preset's resolution, "
            "FPS, codec, and container."
        ))
        layout.addWidget(intro)

        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for i, preset in enumerate(list_presets()):
            card = Card(preset.label)
            desc = QtWidgets.QLabel(preset.description)
            desc.setWordWrap(True)
            desc.setObjectName("subtitle")
            card.add_body(desc)
            spec = QtWidgets.QLabel(
                f"{preset.width}x{preset.height} @ {preset.fps} fps  ·  "
                f"{preset.video_codec}/{preset.audio_codec}"
            )
            card.add_body(spec)
            use_btn = QtWidgets.QPushButton("Use this preset")
            use_btn.setObjectName("primary")
            use_btn.clicked.connect(lambda _checked=False, k=preset.key: self._use_preset(k))
            card.add_body(use_btn)
            grid.addWidget(card, i // 3, i % 3)
        layout.addLayout(grid)
        layout.addStretch(1)

    def _use_preset(self, preset_key: str) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Pick source clip for batch export",
            "",
            "Videos (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.gif)",
        )
        if not path:
            return
        source = Path(path)
        output = self.settings.paths.export_dir / f"{source.stem}_{preset_key}.mp4"
        job = ExportJob(
            source=source,
            output=output,
            preset_key=preset_key,
            duration_s=self.settings.defaults.loop.target_duration_s,
            crossfade_ms=self.settings.defaults.audio.crossfade_ms,
            prefer_gpu=self.settings.defaults.export.use_gpu_encoder,
        )
        item = self.queue.submit(job)
        QtWidgets.QMessageBox.information(
            self,
            "Queued",
            f"Queued export job #{item.id} ({preset_key}).\nOutput: {output}",
        )
