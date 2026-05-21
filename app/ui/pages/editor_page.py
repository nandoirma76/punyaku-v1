"""Video editor page: import clip, configure loop, build."""

from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from app.config.settings import Settings
from app.engine.loop.loop_engine import LoopMode, Transition
from app.export.exporter import ExportJob
from app.export.presets.presets import list_presets
from app.export.queue import ExportQueue
from app.ui.widgets.card import Card
from app.ui.widgets.timeline import Timeline
from app.utils.ffmpeg import FFmpegNotFoundError, probe_media
from app.utils.logger import get_logger

log = get_logger("ui.editor")


class EditorPage(QtWidgets.QWidget):
    def __init__(
        self,
        settings: Settings,
        queue: ExportQueue,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.queue = queue
        self._source: Path | None = None
        self._duration_s: float = 0.0
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Import card
        import_card = Card("Source clip")
        import_row = QtWidgets.QHBoxLayout()
        self._path_edit = QtWidgets.QLineEdit()
        self._path_edit.setPlaceholderText("Drag & drop a video here, or click Browse ...")
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self._browse)
        self._probe_btn = QtWidgets.QPushButton("Inspect")
        self._probe_btn.clicked.connect(self._probe)
        import_row.addWidget(self._path_edit, 1)
        import_row.addWidget(browse)
        import_row.addWidget(self._probe_btn)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(import_row)
        import_card.add_body(wrap)

        self._info_label = QtWidgets.QLabel("No clip loaded.")
        self._info_label.setObjectName("subtitle")
        self._info_label.setWordWrap(True)
        import_card.add_body(self._info_label)
        layout.addWidget(import_card)

        # Timeline card
        timeline_card = Card("Timeline")
        self._timeline = Timeline()
        timeline_card.add_body(self._timeline)
        layout.addWidget(timeline_card)

        # Settings + build cards in a row
        bottom = QtWidgets.QHBoxLayout()
        bottom.setSpacing(14)

        settings_card = Card("Loop settings")
        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        self._duration_spin = QtWidgets.QDoubleSpinBox()
        self._duration_spin.setRange(1.0, 86_400.0)
        self._duration_spin.setValue(self.settings.defaults.loop.target_duration_s)
        self._duration_spin.setSuffix(" s")
        form.addRow("Target duration", self._duration_spin)

        self._mode_combo = QtWidgets.QComboBox()
        for mode in LoopMode:
            self._mode_combo.addItem(mode.value, mode)
        form.addRow("Loop mode", self._mode_combo)

        self._transition_combo = QtWidgets.QComboBox()
        for t in Transition:
            self._transition_combo.addItem(t.value, t)
        form.addRow("Transition", self._transition_combo)

        self._crossfade_spin = QtWidgets.QSpinBox()
        self._crossfade_spin.setRange(50, 10_000)
        self._crossfade_spin.setValue(self.settings.defaults.audio.crossfade_ms)
        self._crossfade_spin.setSuffix(" ms")
        form.addRow("Crossfade", self._crossfade_spin)

        self._method_combo = QtWidgets.QComboBox()
        for m in ("auto", "pixel", "histogram", "optical_flow"):
            self._method_combo.addItem(m)
        form.addRow("Frame match", self._method_combo)

        self._gpu_check = QtWidgets.QCheckBox("Prefer hardware encoder (NVENC/AMF/QSV)")
        self._gpu_check.setChecked(self.settings.defaults.export.use_gpu_encoder)
        form.addRow("", self._gpu_check)

        settings_widget = QtWidgets.QWidget()
        settings_widget.setLayout(form)
        settings_card.add_body(settings_widget)
        bottom.addWidget(settings_card, 1)

        export_card = Card("Render")
        rform = QtWidgets.QFormLayout()
        self._preset_combo = QtWidgets.QComboBox()
        for preset in list_presets():
            self._preset_combo.addItem(f"{preset.label}  ·  {preset.width}x{preset.height}@{preset.fps}", preset.key)
        rform.addRow("Export preset", self._preset_combo)

        self._output_edit = QtWidgets.QLineEdit()
        self._output_edit.setPlaceholderText("Output path will be inferred from preset.")
        rform.addRow("Output", self._output_edit)

        build_btn = QtWidgets.QPushButton("Add to Queue")
        build_btn.setObjectName("primary")
        build_btn.clicked.connect(self._enqueue)
        rform.addRow(build_btn)

        self._status_label = QtWidgets.QLabel("")
        self._status_label.setObjectName("subtitle")
        rform.addRow(self._status_label)

        rwidget = QtWidgets.QWidget()
        rwidget.setLayout(rform)
        export_card.add_body(rwidget)
        bottom.addWidget(export_card, 1)

        layout.addLayout(bottom)

        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # Drag & drop
    # ------------------------------------------------------------------

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.is_file():
                self._path_edit.setText(str(path))
                self._probe()
                return

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import video clip",
            "",
            "Videos (*.mp4 *.mkv *.mov *.avi *.webm *.flv *.gif)",
        )
        if path:
            self._path_edit.setText(path)
            self._probe()

    def _probe(self) -> None:
        path_str = self._path_edit.text().strip()
        if not path_str:
            return
        path = Path(path_str)
        if not path.exists():
            self._info_label.setText(f"File not found: {path}")
            return
        self._source = path
        try:
            info = probe_media(path)
        except FFmpegNotFoundError as exc:
            self._info_label.setText(str(exc))
            return
        except Exception as exc:
            self._info_label.setText(f"Could not probe: {exc}")
            return
        self._duration_s = info.duration_s
        self._timeline.set_duration(info.duration_s)
        self._timeline.set_in_out(0.0, info.duration_s)
        self._info_label.setText(
            f"{path.name}  ·  {info.width}x{info.height} @ {info.fps:0.2f} fps  ·  "
            f"{info.duration_s:0.2f} s  ·  codec={info.video_codec}, audio={'yes' if info.has_audio else 'no'}"
        )

    def _enqueue(self) -> None:
        if not self._source:
            self._status_label.setText("Please import a video first.")
            return
        preset_key = self._preset_combo.currentData() or "youtube_1080p"
        output_path = self._output_edit.text().strip()
        if not output_path:
            stem = self._source.stem
            output_path = str(self.settings.paths.export_dir / f"{stem}_loop_{preset_key}.mp4")
        job = ExportJob(
            source=self._source,
            output=Path(output_path),
            preset_key=str(preset_key),
            duration_s=float(self._duration_spin.value()),
            mode=self._mode_combo.currentData(),
            transition=self._transition_combo.currentData(),
            crossfade_ms=int(self._crossfade_spin.value()),
            prefer_gpu=self._gpu_check.isChecked(),
        )
        item = self.queue.submit(job)
        self._status_label.setText(f"Queued job #{item.id} -> {output_path}")
        log.info("Editor enqueued job {} for {}", item.id, self._source)
