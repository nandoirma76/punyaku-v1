"""Audio page: import background music, configure crossfade, analyse BPM."""

from __future__ import annotations

from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from app.config.settings import Settings
from app.engine.audio.beat import analyze
from app.ui.widgets.card import Card
from app.utils.logger import get_logger

log = get_logger("ui.audio")


class AudioPage(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._audio_path: Path | None = None
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        import_card = Card("Background music")
        row = QtWidgets.QHBoxLayout()
        self._path_edit = QtWidgets.QLineEdit()
        self._path_edit.setPlaceholderText("Pick an mp3/wav/flac/ogg/m4a ...")
        browse = QtWidgets.QPushButton("Browse")
        browse.clicked.connect(self._browse)
        analyse_btn = QtWidgets.QPushButton("Analyse BPM")
        analyse_btn.clicked.connect(self._analyse)
        row.addWidget(self._path_edit, 1)
        row.addWidget(browse)
        row.addWidget(analyse_btn)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(row)
        import_card.add_body(wrap)
        self._info = QtWidgets.QLabel("No music loaded.")
        self._info.setObjectName("subtitle")
        self._info.setWordWrap(True)
        import_card.add_body(self._info)
        layout.addWidget(import_card)

        # Effects card
        effects_card = Card("Audio effects")
        form = QtWidgets.QFormLayout()
        self._volume = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._volume.setRange(0, 200)
        self._volume.setValue(100)
        form.addRow("Volume %", self._volume)

        self._bass = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._bass.setRange(-12, 12)
        form.addRow("Bass dB", self._bass)

        self._reverb = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self._reverb.setRange(0, 100)
        form.addRow("Reverb %", self._reverb)

        self._normalize = QtWidgets.QCheckBox("Loudness normalize (-16 LUFS-ish)")
        self._normalize.setChecked(True)
        form.addRow("", self._normalize)

        self._denoise = QtWidgets.QCheckBox("AI denoise (RNNoise / spectral gating)")
        form.addRow("", self._denoise)

        wrap = QtWidgets.QWidget()
        wrap.setLayout(form)
        effects_card.add_body(wrap)
        layout.addWidget(effects_card)

        layout.addStretch(1)

    def _browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import audio",
            "",
            "Audio (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)",
        )
        if path:
            self._path_edit.setText(path)

    def _analyse(self) -> None:
        path_str = self._path_edit.text().strip()
        if not path_str:
            self._info.setText("Please pick an audio file first.")
            return
        path = Path(path_str)
        if not path.exists():
            self._info.setText(f"File not found: {path}")
            return
        try:
            info = analyze(path)
        except Exception as exc:
            self._info.setText(f"Could not analyse: {exc}")
            return
        self._audio_path = path
        self._info.setText(
            f"{path.name}  ·  {info.duration_s:0.2f}s @ {info.sample_rate} Hz  ·  "
            f"BPM: {info.bpm:0.1f}  ·  beats detected: {len(info.beat_times_s)}"
        )
