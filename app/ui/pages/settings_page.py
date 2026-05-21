"""Application settings (general + AI + streaming + cloud)."""

from __future__ import annotations

from PyQt6 import QtCore, QtWidgets

from app.config.settings import Settings
from app.ui.themes.qss import list_theme_keys
from app.ui.widgets.card import Card
from app.utils.gpu import detect


class SettingsPage(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._build()

    def _build(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        general = Card("General")
        form = QtWidgets.QFormLayout()
        self._theme_combo = QtWidgets.QComboBox()
        for key in list_theme_keys():
            self._theme_combo.addItem(key)
        self._theme_combo.setCurrentText(self.settings.defaults.ui.theme)
        form.addRow("Theme", self._theme_combo)

        self._language_combo = QtWidgets.QComboBox()
        for code, label in (("id", "Bahasa Indonesia"), ("en", "English")):
            self._language_combo.addItem(label, code)
        idx = self._language_combo.findData(self.settings.defaults.ui.language)
        if idx >= 0:
            self._language_combo.setCurrentIndex(idx)
        form.addRow("Language", self._language_combo)

        self._max_workers = QtWidgets.QSpinBox()
        self._max_workers.setRange(1, 64)
        self._max_workers.setValue(self.settings.defaults.performance.max_workers)
        form.addRow("Render workers", self._max_workers)

        self._cache_cap = QtWidgets.QSpinBox()
        self._cache_cap.setRange(256, 64_000)
        self._cache_cap.setValue(self.settings.defaults.performance.cache_size_mb)
        self._cache_cap.setSuffix(" MB")
        form.addRow("Cache cap", self._cache_cap)

        wrap = QtWidgets.QWidget()
        wrap.setLayout(form)
        general.add_body(wrap)
        layout.addWidget(general)

        # GPU / hardware
        gpu_card = Card("Hardware & GPU")
        caps = detect()
        gpu_info = QtWidgets.QLabel()
        gpu_info.setTextFormat(QtCore.Qt.TextFormat.RichText)
        encoders = ", ".join(sorted(caps.ffmpeg_encoders)) or "—"
        devices = "<br>".join(caps.devices) or "no CUDA devices"
        gpu_info.setText(
            f"<b>CUDA</b>: {caps.has_cuda} (toolkit {caps.cuda_version})<br>"
            f"<b>ROCm</b>: {caps.has_rocm} · <b>MPS</b>: {caps.has_mps}<br>"
            f"<b>Devices</b>: {devices}<br>"
            f"<b>FFmpeg encoders</b>: {encoders}"
        )
        gpu_info.setWordWrap(True)
        gpu_card.add_body(gpu_info)

        self._prefer_gpu = QtWidgets.QCheckBox("Use hardware encoder when available")
        self._prefer_gpu.setChecked(self.settings.defaults.export.use_gpu_encoder)
        gpu_card.add_body(self._prefer_gpu)
        layout.addWidget(gpu_card)

        # AI / plugins
        ai_card = Card("AI plugins")
        from app.ai.base import list_plugins
        listing = QtWidgets.QLabel()
        listing.setWordWrap(True)
        listing.setTextFormat(QtCore.Qt.TextFormat.RichText)
        items = []
        for cls in list_plugins():
            inst = cls()
            avail = "available" if inst.is_available() else "stub (install required)"
            items.append(f"• <b>{inst.name}</b> [{inst.category}] — {avail}")
        listing.setText("<br>".join(items) or "No plugins discovered.")
        ai_card.add_body(listing)
        layout.addWidget(ai_card)

        # Buttons
        bottom = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save settings")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        bottom.addStretch(1)
        bottom.addWidget(save_btn)
        wrap = QtWidgets.QWidget()
        wrap.setLayout(bottom)
        layout.addWidget(wrap)

        layout.addStretch(1)

    def _save(self) -> None:
        s = self.settings
        s.defaults.ui.theme = self._theme_combo.currentText()
        s.defaults.ui.language = self._language_combo.currentData()
        s.defaults.performance.max_workers = int(self._max_workers.value())
        s.defaults.performance.cache_size_mb = int(self._cache_cap.value())
        s.defaults.export.use_gpu_encoder = self._prefer_gpu.isChecked()
        path = s.save()
        QtWidgets.QMessageBox.information(
            self,
            "Settings saved",
            f"Settings written to:\n{path}\n\nRestart the app for theme changes to apply globally.",
        )
