# app/ui/apps/games/base_pygame_qt_screen.py

import numpy as np
import pygame

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QSizePolicy
from PyQt5.QtCore    import QTimer, Qt
from PyQt5.QtGui     import QImage, QPixmap

from app.core.logger import logger


# Inicializar SOLO los subsistemas que necesitamos (sin display ni audio de pygame)
# pygame.display NO se inicializa: Qt gestiona la ventana; inicializarlo en
# Raspberry Pi choca con el framebuffer de Qt y causa segfault.
pygame.font.init()
pygame.mixer.init()   # quitar esta línea si no hay audio en el juego


class BasePygameQtScreen(QWidget):
    """
    Loop pygame integrado en un QWidget de Qt.
    Raspberry Pi: numpy surfarray evita el segfault de image.tostring en ARM.
    Sin pygame.display ni pygame.event (no hay ventana pygame real).
    """

    def __init__(self, controller=None, width=1024, height=600):
        super().__init__()

        self.controller  = controller
        self.game_width  = width
        self.game_height = height

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.surface = pygame.Surface((self.game_width, self.game_height))
        self.clock   = pygame.time.Clock()
        self.running = False
        self.events  = []   # lista vacía — los eventos llegan por Qt

        # Layout que estira el label al 100 %
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label.setStyleSheet("background: black;")
        layout.addWidget(self.label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------
    def start(self):
        self._sync_surface_size()
        self.running = True
        self.timer.start(16)
        logger.debug("[BASE PYGAME] start()")

    def stop(self):
        self.running = False
        self.timer.stop()
        logger.debug("[BASE PYGAME] stop()")

    # ------------------------------------------------------------------
    # Redimensionado
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_surface_size()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_surface_size()

    def _sync_surface_size(self):
        w = self.width()  if self.width()  > 0 else self.game_width
        h = self.height() if self.height() > 0 else self.game_height
        if w != self.game_width or h != self.game_height:
            self.game_width  = w
            self.game_height = h
            self.surface = pygame.Surface((w, h))
            logger.debug(f"[BASE PYGAME] surface → {w}x{h}")

    # ------------------------------------------------------------------
    # Loop — eventos llegan via mousePressEvent / keyPressEvent de Qt
    # ------------------------------------------------------------------
    def _tick(self):
        if not self.running:
            return
        self.update_logic()
        self.render()
        self._blit_to_label()
        self.events = []   # limpiar tras cada frame
        self.clock.tick(60)

    def _blit_to_label(self):
        """Surface pygame → QPixmap via numpy (seguro en ARM)."""
        try:
            arr = pygame.surfarray.array3d(self.surface)  # (W, H, 3)
            arr = np.ascontiguousarray(np.transpose(arr, (1, 0, 2)))  # (H, W, 3)
            h, w, ch = arr.shape
            image  = QImage(arr.data, w, h, w * ch, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(image).scaled(
                self.label.width(), self.label.height(),
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.label.setPixmap(pixmap)
        except Exception as exc:
            logger.error(f"[BASE PYGAME] _blit_to_label error: {exc}")

    # ------------------------------------------------------------------
    # Entrada Qt → eventos pygame sintéticos para las subclases
    # ------------------------------------------------------------------
    def mousePressEvent(self, qt_event):
        """Convierte el clic de Qt en un evento pygame.MOUSEBUTTONDOWN."""
        pos = (qt_event.x(), qt_event.y())
        # Ajustar si el pixmap está centrado con letterbox
        pos = self._qt_to_game_pos(pos)
        pg_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            {"pos": pos, "button": qt_event.button()}
        )
        self.events.append(pg_event)
        super().mousePressEvent(qt_event)

    def keyPressEvent(self, qt_event):
        """Convierte tecla Qt en pygame.KEYDOWN (mapeo básico)."""
        from PyQt5.QtCore import Qt as QtConst
        key_map = {
            QtConst.Key_Escape: pygame.K_ESCAPE,
            QtConst.Key_Return: pygame.K_RETURN,
            QtConst.Key_Space:  pygame.K_SPACE,
        }
        pg_key = key_map.get(qt_event.key(), 0)
        if pg_key:
            pg_event = pygame.event.Event(pygame.KEYDOWN, {"key": pg_key})
            self.events.append(pg_event)
        super().keyPressEvent(qt_event)

    def _qt_to_game_pos(self, pos):
        """
        Convierte coordenadas del QLabel (que puede tener letterbox)
        a coordenadas de la surface de pygame.
        """
        lw = self.label.width()
        lh = self.label.height()
        gw = self.game_width
        gh = self.game_height

        # Escala usada por el scaled() de _blit_to_label (KeepAspectRatio)
        scale = min(lw / gw, lh / gh)
        rendered_w = int(gw * scale)
        rendered_h = int(gh * scale)

        # Offset del área negra (letterbox)
        ox = (lw - rendered_w) // 2
        oy = (lh - rendered_h) // 2

        x = int((pos[0] - ox) / scale)
        y = int((pos[1] - oy) / scale)

        # Clamp dentro de la surface
        x = max(0, min(x, gw - 1))
        y = max(0, min(y, gh - 1))
        return (x, y)

    # ------------------------------------------------------------------
    # Overrides para subclases
    # ------------------------------------------------------------------
    def update_logic(self):
        pass

    def render(self):
        pass
