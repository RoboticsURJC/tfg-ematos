# app/ui/apps/proactive_screen.py

"""
@file proactive_screen.py
@brief Pantalla de interfaz proactiva para el usuario.
@details Clase basada en Pygame que renderiza dinámicamente sugerencias de memoria 
y movilidad. Incluye animaciones procedimentales y una gestión de geometría 
adaptativa para el escalado de elementos en tiempo real.
"""

import pygame
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger

# ── PALETA DE COLORES (Alto Contraste) ─────────────────────────────────────────
BG_TOP          = (255, 248, 253)
BG_BOTTOM       = (235, 242, 255)
SHADOW_COL      = (200, 185, 220)
TITLE_COL       = (130,  30, 145)
BODY_COL        = ( 90,  50, 120)
DIVIDER         = (210, 190, 235)

BTN_YES_BG      = (120, 220, 155)
BTN_YES_BORDER  = ( 70, 170, 110)
BTN_YES_TEXT    = ( 15,  70,  40)
BTN_NO_BG       = (255, 180, 195)
BTN_NO_BORDER   = (200, 120, 145)
BTN_NO_TEXT     = ( 90,  20,  50)

ANIM_SKIN       = (255, 213, 175)
ANIM_CLOTHES    = (130,  85, 195)
ANIM_HAIR       = ( 75,  45,  20)
ANIM_ACCENT     = (255, 120, 160)
ANIM_CIRCLE_BG  = (255, 255, 255)
ANIM_CIRCLE_BR  = (195, 165, 220)

TAG_MEM_BG      = (205, 180, 255)
TAG_MEM_FG      = ( 80,  30, 140)
TAG_MOB_BG      = (170, 235, 200)
TAG_MOB_FG      = ( 20, 100,  60)

WHITE           = (255, 255, 255)


class ProactiveScreen(BasePygameQtScreen):
    """
    @brief Pantalla UI proactiva que presenta sugerencias interactivas.
    """

    def __init__(self, suggestion, controller=None, on_accept=None, on_dismiss=None,
                 width=1024, height=600):
        """
        @brief Inicializa la pantalla proactiva.
        @param suggestion Diccionario con los datos de la sugerencia (tipo, título, cuerpo, etc.).
        @param controller Objeto controlador del sistema.
        @param on_accept Callback cuando el usuario acepta la propuesta.
        @param on_dismiss Callback cuando el usuario descarta la propuesta.
        @param width Ancho base de la ventana.
        @param height Alto base de la ventana.
        """
        super().__init__(controller, width, height)
        self.suggestion = suggestion
        self.on_accept  = on_accept
        self.on_dismiss = on_dismiss
        self._t         = 0.0
        self._appear    = 0.0
        self._dismissed = False
        
        self.f_tag   = pygame.font.SysFont("Arial", 28, bold=True)
        self.f_title = pygame.font.SysFont("Arial", 64, bold=True)  
        self.f_body  = pygame.font.SysFont("Arial", 42, bold=True)  
        self.f_btn   = pygame.font.SysFont("Arial", 40, bold=True)  

        self.btn_yes = pygame.Rect(0, 0, 0, 0)
        self.btn_no  = pygame.Rect(0, 0, 0, 0)

        logger.info(f"[PROACTIVE SCREEN] {suggestion['title']}")
        self.start()

    def update_logic(self):
        """@brief Actualiza la animación de aparición y el contador de tiempo interno."""
        self._appear = min(self._appear + 0.08, 1.0)
        self._t += 0.04

    def mousePressEvent(self, event):
        """
        @brief Gestiona la interacción táctil/ratón calculando colisiones dinámicas.
        @param event Evento de entrada de Qt.
        """
        if self._dismissed: return
        pos = self._qt_to_game_pos((event.x(), event.y()))

        if self.btn_yes.collidepoint(pos):
            self._dismissed = True
            logger.info(f"[PROACTIVE] Aceptado → {self.suggestion['action']}")
            if self.controller: self.controller.on_proactive_dismissed()
            if self.on_accept: self.on_accept(self.suggestion["action"])

        elif self.btn_no.collidepoint(pos):
            self._dismissed = True
            logger.info("[PROACTIVE] Descartado")
            if self.controller: self.controller.on_proactive_dismissed()
            if self.on_dismiss: self.on_dismiss()

    # ── RENDER Y RE-CÁLCULO GEOMÉTRICO ─────────────────────────

    def render(self):
        """
        @brief Renderiza toda la interfaz.
        @details Recalcula posiciones basándose en el tamaño real de la superficie.
        """
        rect_pantalla = self.surface.get_rect()
        W, H = rect_pantalla.width, rect_pantalla.height
        if W < 100 or H < 100: return

        self._draw_bg(W, H)
        if self._appear < 0.01: return

        dy = int((1.0 - self._appear) * 20)

        # Sección Superior: Etiqueta y Animación
        anim_cx, anim_cy = W // 2, int(H * 0.23) + dy
        anim_r = 100
        
        self._draw_tag(dy)
        self._draw_animation(anim_cx, anim_cy, anim_r)

        # Sección Central: Textos
        txt_y = anim_cy + anim_r + 25
        txt_w = W - 140
        
        title = self.suggestion["title"].upper()
        ts_title = self.f_title.render(title, True, TITLE_COL)
        ttx = (W - ts_title.get_width()) // 2
        self.surface.blit(ts_title, (ttx, txt_y))

        line_y = txt_y + ts_title.get_height() + 10
        llen = 550
        lx = (W - llen) // 2
        pygame.draw.line(self.surface, DIVIDER, (lx, line_y), (lx + llen, line_y), 4)

        rendered_lines = self._render_wrapped_text(self.suggestion["body"], self.f_body, BODY_COL, txt_w)
        line_h = self.f_body.get_height() + 8
        body_start_y = line_y + 15
        for i, ls in enumerate(rendered_lines):
            lx2 = (W - ls.get_width()) // 2
            self.surface.blit(ls, (lx2, body_start_y + i * line_h))

        # Sección Inferior: Botones
        BW, BH, GAP, BOTTOM_MARGIN = 340, 90, 60, 35
        btn_y = H - BH - BOTTOM_MARGIN
        start_btn_x = (W - ((BW * 2) + GAP)) // 2

        self.btn_yes = pygame.Rect(start_btn_x, btn_y, BW, BH)
        self.btn_no  = pygame.Rect(start_btn_x + BW + GAP, btn_y, BW, BH)
        self._draw_buttons()

    # ── SUB-MÉTODOS DE DIBUJO ──────────────────────────────────

    def _draw_bg(self, W, H):
        """@brief Dibuja un gradiente vertical de fondo."""
        for y in range(H):
            t = y / H
            c = [int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)]
            pygame.draw.line(self.surface, c, (0, y), (W, y))

    def _render_wrapped_text(self, text, font, color, max_width):
        """@brief Ajusta bloques de texto dentro de un ancho máximo."""
        # [Implementación simplificada para Doxygen]
        return [font.render(line, True, color) for line in text.split('\n')]

    def _draw_animation(self, cx, cy, r):
        """@brief Control central de las animaciones procedimentales."""
        # [Detalle: lógica que elige qué animación de personaje mostrar]
        pass
    
    def _figure(self, cx, cy, r, head_tilt=0.0):
        """@brief Dibuja un personaje humanoide estilizado."""
        pass