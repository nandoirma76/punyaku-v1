"""Qt Style Sheet (QSS) generator for the Punyaku UI.

The UI uses a single global QSS with CSS variables replaced at runtime so
themes can be switched without recompiling resources.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    bg: str = "#0B0C14"
    bg_alt: str = "#11131F"
    surface: str = "#161A2A"
    surface_alt: str = "#1C2138"
    border: str = "#2B3050"
    text: str = "#E7E9F8"
    text_dim: str = "#9BA0BD"
    accent: str = "#7C5CFF"
    accent_alt: str = "#23E8C2"
    danger: str = "#FF5C7C"
    warning: str = "#FFB547"
    success: str = "#5CE2B0"


THEMES: dict[str, Palette] = {
    "dark_neon": Palette(),
    "dark_glass": Palette(
        bg="#0E0F1A",
        surface="#1B1F33",
        accent="#9D72FF",
        accent_alt="#69E8FF",
    ),
    "midnight": Palette(
        bg="#070710",
        surface="#10101A",
        accent="#FF7AB6",
        accent_alt="#7AFFD8",
    ),
    "cyberpunk": Palette(
        bg="#0B0014",
        surface="#1A0026",
        accent="#FF3CAC",
        accent_alt="#FFE600",
        border="#3D0F4D",
    ),
}


QSS_TEMPLATE = """
* {{
    font-family: "Inter", "Segoe UI", "Helvetica Neue", sans-serif;
    color: {text};
}}

QMainWindow, QDialog, QWidget#root {{
    background-color: {bg};
}}

QFrame#sidebar {{
    background-color: {bg_alt};
    border-right: 1px solid {border};
}}

QFrame#topbar {{
    background-color: {surface};
    border-bottom: 1px solid {border};
}}

QLabel#title {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
}}

QLabel#subtitle {{
    color: {text_dim};
    font-size: 12px;
}}

QPushButton {{
    background-color: {surface};
    color: {text};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 8px 16px;
    font-weight: 500;
}}
QPushButton:hover {{
    border: 1px solid {accent};
}}
QPushButton:pressed {{
    background-color: {accent};
    color: {bg};
}}
QPushButton#primary {{
    background-color: {accent};
    color: {bg};
    border: none;
}}
QPushButton#primary:hover {{
    background-color: {accent_alt};
}}

QPushButton#nav {{
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 10px 18px;
    border-radius: 8px;
    color: {text_dim};
}}
QPushButton#nav:checked, QPushButton#nav:hover {{
    background-color: {surface};
    color: {text};
    border-left: 3px solid {accent};
}}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
    background-color: {bg_alt};
    border: 1px solid {border};
    border-radius: 8px;
    padding: 6px 10px;
    selection-background-color: {accent};
    selection-color: {bg};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QPlainTextEdit:focus, QTextEdit:focus {{
    border: 1px solid {accent};
}}

QProgressBar {{
    background-color: {bg_alt};
    border: 1px solid {border};
    border-radius: 8px;
    text-align: center;
    color: {text};
    height: 12px;
}}
QProgressBar::chunk {{
    background-color: {accent};
    border-radius: 7px;
}}

QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background-color: {border};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background-color: {accent};
    width: 16px;
    margin: -7px 0;
    border-radius: 8px;
}}

QTableWidget, QTreeView, QListView {{
    background-color: {bg_alt};
    border: 1px solid {border};
    gridline-color: {border};
    selection-background-color: {accent};
    selection-color: {bg};
}}

QHeaderView::section {{
    background-color: {surface};
    color: {text_dim};
    padding: 6px;
    border: none;
    border-right: 1px solid {border};
}}

QStatusBar {{
    background-color: {surface};
    color: {text_dim};
    border-top: 1px solid {border};
}}

QGroupBox {{
    border: 1px solid {border};
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 8px;
    color: {text_dim};
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

QToolTip {{
    background-color: {bg_alt};
    color: {text};
    border: 1px solid {accent};
    border-radius: 6px;
    padding: 4px 8px;
}}

QScrollBar:vertical {{
    background-color: {bg};
    width: 10px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: {border};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {accent};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QScrollBar:horizontal {{
    background-color: {bg};
    height: 10px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background-color: {border};
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

QFrame#card {{
    background-color: {surface};
    border: 1px solid {border};
    border-radius: 14px;
}}
QFrame#card[accent="true"] {{
    border: 1px solid {accent};
}}
"""


def build_qss(theme: str = "dark_neon") -> str:
    palette = THEMES.get(theme, THEMES["dark_neon"])
    return QSS_TEMPLATE.format(**palette.__dict__)


def list_theme_keys() -> list[str]:
    return list(THEMES.keys())
