# app/ui/screens/games_screen.py

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtSvg import QSvgWidget
import os, tempfile

from app.core.logger import logger


# ── Fondo multicolor pastel ───────────────────────────────────────────────────
_GAMES_QSS = """
QWidget#GamesMain {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.00 #ffd6e7,
        stop:0.25 #ffecd2,
        stop:0.50 #d4f0ff,
        stop:0.75 #d8f5e4,
        stop:1.00 #e8d8ff
    );
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}
QLabel#TitleLabel {
    color: #3a1a5c;
    background: rgba(255,255,255,0.70);
    border: 4px solid rgba(180,120,220,0.55);
    border-radius: 34px;
    padding: 16px 50px;
    letter-spacing: 2px;
}
QLabel#SubLabel {
    color: #5a3a7a;
    background: transparent;
}
QPushButton#BackBtn {
    background-color: rgba(255,255,255,0.75);
    border: 4px solid #c490e4;
    border-radius: 32px;
    color: #3a1a5c;
    font-size: 26px;
    font-weight: 900;
}
QPushButton#BackBtn:hover   { background-color: #f0e0ff; border-color: #a060c8; }
QPushButton#BackBtn:pressed { background-color: #e0c8ff; padding-top: 6px; }
"""

# ── SVGs (sin emojis, compatible Raspberry Pi) ───────────────────────────────
_SVG_BRAIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <path d="M32 6c-5 0-9 3-10 7-1-1-3-2-5-2-4 0-7 3-7 7
           0 1 0 2 1 3C8 22 6 25 6 28c0 4 3 7 7 8-1 1-1 3-1 4
           0 5 4 9 9 9 1 0 3 0 4-1 1 3 4 6 7 6s6-3 7-6
           c1 1 3 1 4 1 5 0 9-4 9-9 0-1 0-3-1-4 4-1 7-4 7-8
           0-3-2-6-5-7 1-1 1-2 1-3 0-4-3-7-7-7-2 0-4 1-5 2
           -1-4-5-7-10-7z"
        fill="none" stroke="ICONCOLOR" stroke-width="3.5"
        stroke-linecap="round" stroke-linejoin="round"/>
  <line x1="32" y1="16" x2="32" y2="48" stroke="ICONCOLOR" stroke-width="3"
        stroke-linecap="round"/>
  <path d="M22 22 Q27 28 22 34" fill="none" stroke="ICONCOLOR"
        stroke-width="2.5" stroke-linecap="round"/>
  <path d="M42 22 Q37 28 42 34" fill="none" stroke="ICONCOLOR"
        stroke-width="2.5" stroke-linecap="round"/>
</svg>"""

_SVG_NUMBER = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="8" y="8" width="48" height="48" rx="10"
        fill="none" stroke="ICONCOLOR" stroke-width="3.5"/>
  <text x="32" y="42" font-family="monospace" font-size="30" font-weight="bold"
        text-anchor="middle" fill="ICONCOLOR">42</text>
  <line x1="16" y1="50" x2="48" y2="50" stroke="ICONCOLOR"
        stroke-width="2.5" stroke-linecap="round"/>
</svg>"""

_SVG_WORDS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="6" y="10" width="52" height="44" rx="8"
        fill="none" stroke="ICONCOLOR" stroke-width="3.5"/>
  <line x1="14" y1="24" x2="50" y2="24" stroke="ICONCOLOR"
        stroke-width="3" stroke-linecap="round"/>
  <line x1="14" y1="34" x2="50" y2="34" stroke="ICONCOLOR"
        stroke-width="3" stroke-linecap="round"/>
  <line x1="14" y1="44" x2="36" y2="44" stroke="ICONCOLOR"
        stroke-width="3" stroke-linecap="round"/>
  <circle cx="54" cy="14" r="8" fill="none"
          stroke="ICONCOLOR" stroke-width="3"/>
  <text x="54" y="19" font-family="monospace" font-size="12" font-weight="bold"
        text-anchor="middle" fill="ICONCOLOR">A</text>
</svg>"""


def _write_svg(svg_text: str, color: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".svg")
    with os.fdopen(fd, "w") as f:
        f.write(svg_text.replace("ICONCOLOR", color))
    return path


# ── Tarjeta de juego ─────────────────────────────────────────────────────────
class GameCard(QWidget):
    clicked = pyqtSignal(str)

    def __init__(self, game_id, label, svg_src,
                 bg, border, hover, fg, parent=None):
        super().__init__(parent)
        self.game_id = game_id

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName(f"Card_{game_id}")
        self.setStyleSheet(f"""
            QWidget#Card_{game_id} {{
                background-color: {bg};
                border: 5px solid {border};
                border-radius: 40px;
            }}
            QWidget#Card_{game_id}:hover {{
                background-color: {hover};
            }}
        """)
        self.setFixedSize(340, 340)
        self.setCursor(Qt.PointingHandCursor)

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(24, 28, 24, 24)
        vlay.setSpacing(16)
        vlay.setAlignment(Qt.AlignCenter)

        # Icono SVG
        svg_path = _write_svg(svg_src, fg)
        icon = QSvgWidget(svg_path)
        icon.setFixedSize(QSize(130, 130))
        icon.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Segoe UI", 28, QFont.Black))
        lbl.setStyleSheet(f"color: {fg}; background: transparent;")

        vlay.addStretch()
        vlay.addWidget(icon, alignment=Qt.AlignCenter)
        vlay.addWidget(lbl)
        vlay.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)


# ── Pantalla principal ────────────────────────────────────────────────────────
class GamesScreen(QWidget):

    back_requested = pyqtSignal()

    _GAMES = [
        {
            "id":     "memory",
            "label":  "Memoria",
            "svg":    _SVG_BRAIN,
            "bg":     "#ffc8dd",   # rosa pastel
            "border": "#e0709a",
            "hover":  "#ffdde8",
            "fg":     "#6b002a",
        },
        {
            "id":     "simon_says",
            "label":  "Simon Dice",
            "svg":    _SVG_NUMBER,
            "bg":     "#e5eab5",   # amarillo pastel
            "border": "#adaf4c",
            "hover":  "#f1f5d0",
            "fg":     "#3d3c0a",
        },
        {
            "id":     "find_diferences",
            "label":  "Encuentra\n las diferencias",
            "svg":    _SVG_NUMBER,
            "bg":     "#b5ceea",   # verde menta pastel
            "border": "#4c6baf",
            "hover":  "#d0ddf5",
            "fg":     "#0a1c3d",
        },
        {
            "id":     "word_search",
            "label":  "Palabras",
            "svg":    _SVG_WORDS,
            "bg":     "#ffd6a5",   # melocoton pastel
            "border": "#e08030",
            "hover":  "#ffe8c8",
            "fg":     "#4a1e00",
        },
    ]

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("GamesMain")
        self.setStyleSheet(_GAMES_QSS)

        logger.info("[GAMES] Iniciando pantalla")

        root = QVBoxLayout(self)
        root.setContentsMargins(50, 36, 50, 36)
        root.setSpacing(24)

        # ── Titulo ────────────────────────────────────────────────
        title = QLabel("Juegos")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 58, QFont.Black))

        subtitle = QLabel("Elige una actividad divertida")
        subtitle.setObjectName("SubLabel")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 26))

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(8)

        # ── Grid de tarjetas ──────────────────────────────────────
        grid_wrap = QHBoxLayout()
        grid_wrap.addStretch()

        grid = QGridLayout()
        grid.setSpacing(40)

        for idx, g in enumerate(self._GAMES):
            card = GameCard(
                game_id=g["id"],
                label=g["label"],
                svg_src=g["svg"],
                bg=g["bg"],
                border=g["border"],
                hover=g["hover"],
                fg=g["fg"],
            )
            card.clicked.connect(self._launch)
            row, col = divmod(idx, 2)
            grid.addWidget(card, row, col, Qt.AlignCenter)

        grid_wrap.addLayout(grid)
        grid_wrap.addStretch()
        root.addLayout(grid_wrap)

        root.addStretch()

        # ── Volver ────────────────────────────────────────────────
        back_row = QHBoxLayout()
        self.back_btn = QPushButton("  Volver")
        self.back_btn.setObjectName("BackBtn")
        self.back_btn.setFixedSize(280, 80)
        self.back_btn.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.back_btn.clicked.connect(self.go_back)
        back_row.addStretch()
        back_row.addWidget(self.back_btn)
        root.addLayout(back_row)

    def _launch(self, game_id: str):
        logger.info(f"[GAMES] Lanzando juego: {game_id}")
        if self.controller:
            self.controller.open_game(game_id)

    def go_back(self):
        logger.info("[GAMES] Volviendo al launcher")
        self.back_requested.emit()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()
