import pygame
import random
import time
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# ─────────────────────────────────────────────
#  PALETA PASTEL CUTE & ALTO CONTRASTE (MENÚ CORREGIDO)
# ─────────────────────────────────────────────
P_BG_TOP        = (255, 240, 250)
P_BG_BOTTOM     = (230, 240, 255)
P_TITLE         = (130,  30, 145)   # Lila profundo de alto contraste
P_SUBTITLE      = (100,  60, 150)   # Púrpura medio muy legible
P_SHADOW        = (195, 175, 215)   # Sombra pastel definida
P_PANEL_BORDER  = (200, 180, 230)

# Colores energéticos pero en tonos pastel para los botones del menú de dificultad
M_BTN_EASY_BG   = (145, 235, 175)   # Verde menta brillante
M_BTN_EASY_BRD  = ( 85, 185, 120)
M_BTN_MED_BG    = (255, 215, 115)   # Amarillo plátano suave
M_BTN_MED_BRD   = (215, 160,  50)
M_BTN_HARD_BG   = (255, 155, 170)   # Coral pastel intenso
M_BTN_HARD_BRD  = (215,  90, 110)
M_BTN_EXIT_BG   = (255, 170, 170)   # Rojo pastel
M_BTN_EXIT_BRD  = (220, 110, 110)
M_BTN_TEXT      = ( 50,  20,  70)   # Texto mora oscuro para lectura perfecta

# Colores base juego (Se mantienen coherentes)
P_BTN_TEXT      = ( 60,  40,  90)
P_BTN_BACK      = (180, 200, 255)

SIMON_BUTTONS = [
    {"id": 0, "label": "🟢", "normal": (120, 200, 140), "lit": (180, 255, 180), "freq": 392},  # Sol
    {"id": 1, "label": "🔴", "normal": (220, 110, 110), "lit": (255, 180, 180), "freq": 330},  # Mi
    {"id": 2, "label": "🔵", "normal": (110, 150, 220), "lit": (180, 210, 255), "freq": 262},  # Do
    {"id": 3, "label": "🟡", "normal": (220, 200, 100), "lit": (255, 240, 150), "freq": 494},  # Si
]

DIFFICULTY = {
    "facil":   {"start_len": 2, "max_len": 6,  "show_ms": 900,  "pause_ms": 400},
    "medio":   {"start_len": 3, "max_len": 10, "show_ms": 650,  "pause_ms": 300},
    "dificil": {"start_len": 4, "max_len": 15, "show_ms": 450,  "pause_ms": 200},
}


class SimonSaysScreen(BasePygameQtScreen):
    """
    Simón Dice — optimizado con fuentes masivas y menú dinámico auto-centrado
    """

    def __init__(self, controller=None, width=1024, height=600):
        super().__init__(controller, width, height)
        logger.info("[SIMON] Iniciada SimonSaysScreen")

        self.state      = "menu"
        self.difficulty = "facil"

        self.sequence      = []
        self.player_index  = 0
        self.show_index    = 0
        self.lit_button    = None
        self.lit_start_ms  = 0

        self.score         = 0
        self.record        = 0

        self._show_timer   = 0.0
        self._phase        = "on"
        self._feedback_timer = 0.0
        self.FEEDBACK_DUR  = 1.2

        self._pulse        = 0.0
        self._pulse_dir    = 1

        self._sounds = {}
        self._sounds_loaded = False

        # Fuentes del sistema robustas y GRANDES
        self.m_f_title    = pygame.font.SysFont("Arial", 78, bold=True)
        self.m_f_subtitle = pygame.font.SysFont("Arial", 40, bold=True)
        self.m_f_btn      = pygame.font.SysFont("Arial", 36, bold=True)
        
        # Fuentes dentro del juego agrandadas significativamente
        self.g_f_level    = pygame.font.SysFont("Arial", 64, bold=True) # Antes ~52 sin negrita
        self.g_f_status   = pygame.font.SysFont("Arial", 38, bold=True) # Antes ~30 sin negrita

        # Rectángulos del menú (Se re-calculan dinámicamente)
        self.btn_easy   = pygame.Rect(0, 0, 0, 0)
        self.btn_medium = pygame.Rect(0, 0, 0, 0)
        self.btn_hard   = pygame.Rect(0, 0, 0, 0)
        self.btn_exit   = pygame.Rect(0, 0, 0, 0)
        self.btn_back   = pygame.Rect(0, 0, 0, 0)

        self._btn_rects  = []
        self._layout_calculated = False

    def exit_game(self):
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    def _init_sounds(self):
        if self._sounds_loaded:
            return
        try:
            import numpy as np
            sample_rate = 44100
            duration    = 0.4
            t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

            for btn in SIMON_BUTTONS:
                freq  = btn["freq"]
                wave  = np.sin(2 * math.pi * freq * t)
                fade  = np.linspace(1.0, 0.0, len(t)) ** 2
                wave  = (wave * fade * 24000).astype(np.int16)
                stereo = np.column_stack([wave, wave])
                sound  = pygame.sndarray.make_sound(stereo)
                self._sounds[btn["id"]] = sound

            noise = np.random.randint(-8000, 8000, int(sample_rate * 0.5), dtype=np.int16)
            env   = np.linspace(1.0, 0.0, len(noise)) ** 1.5
            noise = (noise * env).astype(np.int16)
            stereo_noise = np.column_stack([noise, noise])
            self._sounds["wrong"] = pygame.sndarray.make_sound(stereo_noise)

            self._sounds_loaded = True
            logger.info("[SIMON] Sonidos generados correctamente")
        except Exception as e:
            logger.warning(f"[SIMON] Sin sonido (numpy/mixer no activos): {e}")
            self._sounds = {}

    def _play_sound(self, key):
        if key in self._sounds:
            try:
                self._sounds[key].play()
            except Exception:
                pass

    def _calculate_layout(self):
        w, h = self.game_width, self.game_height
        TOP_RESERVE    = 130  # Más espacio para los textos grandes
        BOTTOM_RESERVE = 85  
        GAP            = 20  

        available_h = h - TOP_RESERVE - BOTTOM_RESERVE
        available_w = w - 200  

        btn_size = min(
            (available_w - GAP) // 2,
            (available_h - GAP) // 2,
            190  
        )
        btn_size = max(btn_size, 120)

        total_w = btn_size * 2 + GAP
        total_h = btn_size * 2 + GAP
        start_x = (w - total_w) // 2
        start_y = TOP_RESERVE + (available_h - total_h) // 2

        self._btn_rects = [
            pygame.Rect(start_x,                  start_y,                  btn_size, btn_size),  # 0 verde
            pygame.Rect(start_x + btn_size + GAP, start_y,                  btn_size, btn_size),  # 1 rojo
            pygame.Rect(start_x,                  start_y + btn_size + GAP, btn_size, btn_size),  # 2 azul
            pygame.Rect(start_x + btn_size + GAP, start_y + btn_size + GAP, btn_size, btn_size),  # 3 amarillo
        ]
        self._layout_calculated = True

    def start_game(self, difficulty):
        self._init_sounds()
        self.difficulty   = difficulty
        self.sequence     = []
        self.player_index = 0
        self.score        = 0
        self.lit_button   = None

        self._calculate_layout()
        self._add_to_sequence()  
        self._start_showing()
        self.state = "showing"
        logger.info(f"[SIMON] Partida iniciada — dificultad: {difficulty}")

    def _add_to_sequence(self):
        self.sequence.append(random.randint(0, 3))
        self.score = len(self.sequence) - 1

    def _start_showing(self):
        self.show_index   = 0
        self.player_index = 0
        self.lit_button   = None
        self._show_timer  = 0.0
        self._phase       = "off"

    def update_logic(self):
        dt = 1.0 / 60.0  
        if self.state == "showing":
            self._update_showing(dt)
        elif self.state in ("correct", "wrong"):
            self._feedback_timer -= dt
            if self.state == "correct":
                self._pulse += self._pulse_dir * dt * 3
                if self._pulse >= 1.0:
                    self._pulse = 1.0
                    self._pulse_dir = -1
                elif self._pulse <= 0.0:
                    self._pulse = 0.0
                    self._pulse_dir = 1

            if self._feedback_timer <= 0:
                if self.state == "correct":
                    cfg = DIFFICULTY[self.difficulty]
                    if len(self.sequence) >= cfg["max_len"]:
                        self.state = "win"
                    else:
                        self._add_to_sequence()
                        self._start_showing()
                        self.state = "showing"
                else:
                    self.state = "menu"

    def _update_showing(self, dt):
        cfg       = DIFFICULTY[self.difficulty]
        show_sec  = cfg["show_ms"]  / 1000.0
        pause_sec = cfg["pause_ms"] / 1000.0
        self._show_timer += dt

        if self._phase == "off":
            if self._show_timer >= pause_sec:
                if self.show_index >= len(self.sequence):
                    self.lit_button  = None
                    self.state       = "waiting"
                    return
                self.lit_button   = self.sequence[self.show_index]
                self._show_timer  = 0.0
                self._phase       = "on"
                self._play_sound(self.lit_button)
        elif self._phase == "on":
            if self._show_timer >= show_sec:
                self.show_index  += 1
                self.lit_button   = None
                self._show_timer  = 0.0
                self._phase       = "off"

    def mousePressEvent(self, event):
        pos = self._qt_to_game_pos((event.x(), event.y()))

        if self.state == "menu":
            if self.btn_easy.collidepoint(pos):
                self.start_game("facil")
            elif self.btn_medium.collidepoint(pos):
                self.start_game("medio")
            elif self.btn_hard.collidepoint(pos):
                self.start_game("dificil")
            elif self.btn_exit.collidepoint(pos):
                self.exit_game()
        elif self.state == "waiting":
            if self.btn_back.collidepoint(pos):
                self.state = "menu"
                return
            self._handle_button_press(pos)
        elif self.state in ("showing", "correct", "wrong", "win"):
            if self.btn_back.collidepoint(pos):
                self.state = "menu"

    def _handle_button_press(self, pos):
        for i, rect in enumerate(self._btn_rects):
            if rect.collidepoint(pos):
                self.lit_button = i
                self._play_sound(i)
                if i == self.sequence[self.player_index]:
                    self.player_index += 1
                    if self.player_index >= len(self.sequence):
                        if len(self.sequence) > self.record:
                            self.record = len(self.sequence)
                        self.state          = "correct"
                        self._feedback_timer = self.FEEDBACK_DUR
                        self._pulse         = 0.0
                        self._pulse_dir     = 1
                else:
                    self._play_sound("wrong")
                    self.state           = "wrong"
                    self._feedback_timer = self.FEEDBACK_DUR
                break

    # ──────────────────────────────────────────
    #  RENDER PRINCIPAL AUTOMÁTICO
    # ──────────────────────────────────────────
    def render(self):
        rect_pantalla = self.surface.get_rect()
        W = rect_pantalla.width
        H = rect_pantalla.height

        if W < 100 or H < 100:
            return

        self._draw_bg()
        if self.state == "menu":
            self._draw_menu_dinamico(W, H)
        elif self.state == "win":
            self._draw_win()
        else:
            self._draw_game()

    def _draw_bg(self):
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))

    # ── NUEVO MENÚ DE DIFICULTAD EXTRA GRANDE Y COLORIDO ──
    def _draw_menu_dinamico(self, W, H):
        # Título Centrado
        ts_title = self.m_f_title.render("SIMÓN DICE", True, P_TITLE)
        ts_shadow = self.m_f_title.render("SIMÓN DICE", True, P_SHADOW)
        tx = (W - ts_title.get_width()) // 2
        self.surface.blit(ts_shadow, (tx + 4, 49))
        self.surface.blit(ts_title, (tx, 45))

        # Subtítulo
        ts_sub = self.m_f_subtitle.render("Repite la secuencia de colores ✨", True, P_SUBTITLE)
        sx = (W - ts_sub.get_width()) // 2
        self.surface.blit(ts_sub, (sx, 125))

        # Récord / Mejor puntuación
        if self.record > 0:
            rf = pygame.font.SysFont("Arial", 30, bold=True)
            rec = rf.render(f"🏆 Mejor marca: {self.record} pasos", True, P_TITLE)
            self.surface.blit(rec, ((W - rec.get_width()) // 2, 175))

        # Layout de botones colosales en torre central
        BW = 380
        BH = 76
        GAP = 18
        start_y = 225
        cx = (W - BW) // 2

        self.btn_easy   = pygame.Rect(cx, start_y, BW, BH)
        self.btn_medium = pygame.Rect(cx, start_y + BH + GAP, BW, BH)
        self.btn_hard   = pygame.Rect(cx, start_y + (BH + GAP) * 2, BW, BH)
        self.btn_exit   = pygame.Rect((W - 240) // 2, H - 85, 240, 60)

        # Render de botones relucientes
        self._draw_menu_btn(self.btn_easy,   "FÁCIL  (hasta 6) ",  M_BTN_EASY_BG, M_BTN_EASY_BRD)
        self._draw_menu_btn(self.btn_medium, "MEDIO  (hasta 10) ", M_BTN_MED_BG,  M_BTN_MED_BRD)
        self._draw_menu_btn(self.btn_hard,   "DIFÍCIL (hasta 15) ", M_BTN_HARD_BG, M_BTN_HARD_BRD)
        self._draw_menu_btn(self.btn_exit,   "⬅ VOLVER",             M_BTN_EXIT_BG, M_BTN_EXIT_BRD)

    def _draw_menu_btn(self, rect, text, bg_color, brd_color):
        """Dibuja los botones grandes del menú con sombras 3D"""
        sr = rect.move(5, 5)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=22)
        pygame.draw.rect(self.surface, bg_color, rect, border_radius=22)
        pygame.draw.rect(self.surface, brd_color, rect, 4, border_radius=22)
        
        ts = self.m_f_btn.render(text, True, M_BTN_TEXT)
        self.surface.blit(
            ts,
            (rect.x + (rect.width - ts.get_width()) // 2,
             rect.y + (rect.height - ts.get_height()) // 2)
        )

    # ── JUEGO (TEXTOS AGRANDADOS Y EN NEGRITA) ──────────────────────
    def _draw_game(self):
        self._draw_header()
        self._draw_simon_buttons()
        self._draw_bottom_bar()
        self._draw_state_overlay()

    def _draw_header(self):
        w = self.game_width
        hbar = pygame.Surface((w, 115), pygame.SRCALPHA) # Un poco más alto para fuentes grandes
        hbar.fill((245, 235, 255, 180))
        self.surface.blit(hbar, (0, 0))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, 115), (w, 115), 2)

        # Nivel en Texto Gigante
        level = self.g_f_level.render(f"Nivel {len(self.sequence)}", True, P_TITLE)
        self.surface.blit(level, (w // 2 - level.get_width() // 2, 8))

        # Indicadores de secuencia redimensionados
        dot_r  = 11 # Crecieron las bolitas
        total  = len(self.sequence)
        dot_w  = total * (dot_r * 2 + 8)
        dot_x  = w // 2 - dot_w // 2 + dot_r
        dot_y  = 68

        for i, btn_id in enumerate(self.sequence):
            color  = SIMON_BUTTONS[btn_id]["normal"]
            filled = (self.state == "waiting" and i < self.player_index) or \
                     (self.state == "correct") or \
                     (self.state == "wrong" and i < self.player_index)
            if filled:
                pygame.draw.circle(self.surface, SIMON_BUTTONS[btn_id]["lit"], (dot_x, dot_y), dot_r)
            else:
                pygame.draw.circle(self.surface, color,                                   (dot_x, dot_y), dot_r, 3)
            dot_x += dot_r * 2 + 8

        # Mensajes de estado en Negrita y de lectura Clara
        msgs = {
            "showing": "¡Observa la secuencia atentamente!",
            "waiting": f"Tu turno — Paso {self.player_index + 1} de {len(self.sequence)}",
            "correct": "¡Muy bien! ",
            "wrong":   "¡Ups! Inténtalo de nuevo",
        }
        msg = msgs.get(self.state, "")
        ms  = self.g_f_status.render(msg, True, P_SUBTITLE)
        self.surface.blit(ms, (w // 2 - ms.get_width() // 2, 86))

    def _draw_simon_buttons(self):
        if not self._layout_calculated:
            return

        for i, btn_data in enumerate(SIMON_BUTTONS):
            rect = self._btn_rects[i]
            is_lit = (self.lit_button == i)
            color = btn_data["lit"] if is_lit else btn_data["normal"]

            if is_lit:
                inflate = 10
                draw_rect = rect.inflate(inflate, inflate)
            else:
                draw_rect = rect

            shadow_r = draw_rect.move(5, 5)
            pygame.draw.rect(self.surface, P_SHADOW, shadow_r, border_radius=26)
            pygame.draw.rect(self.surface, color, draw_rect, border_radius=26)

            border_w = 5 if is_lit else 3
            pygame.draw.rect(self.surface, (255, 255, 255), draw_rect, border_w, border_radius=26)

            shine = pygame.Surface((draw_rect.width, draw_rect.height // 3), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 60 if not is_lit else 110))
            self.surface.blit(shine, (draw_rect.x, draw_rect.y + 4), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_bottom_bar(self):
        BAR_H = 75
        bar_y = self.game_height - BAR_H
        bar   = pygame.Surface((self.game_width, BAR_H), pygame.SRCALPHA)
        bar.fill((245, 235, 255, 200))
        self.surface.blit(bar, (0, bar_y))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, bar_y), (self.game_width, bar_y), 2)

        self.btn_back = pygame.Rect(20, bar_y + 12, 140, 50)
        self._draw_button(self.btn_back, "⬅ Menú", P_BTN_BACK)

    def _draw_state_overlay(self):
        if self.state == "correct":
            alpha = int(60 * abs(math.sin(self._pulse * math.pi)))
            overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
            overlay.fill((100, 230, 130, alpha))
            self.surface.blit(overlay, (0, 0))

            ff  = pygame.font.SysFont("Arial", 75, bold=True)
            ftx = ff.render("¡BIEN HECHO! ", True, (60, 160, 80))
            cx  = self.game_width  // 2 - ftx.get_width()  // 2
            cy  = self.game_height // 2 - ftx.get_height() // 2
            self.surface.blit(ftx, (cx + 3, cy + 3))
            ftx2 = ff.render("¡BIEN HECHO! ", True, (80, 200, 100))
            self.surface.blit(ftx2, (cx, cy))

        elif self.state == "wrong":
            overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
            overlay.fill((230, 80, 80, 50))
            self.surface.blit(overlay, (0, 0))

            ff  = pygame.font.SysFont("Arial", 70, bold=True)
            ftx = ff.render("¡Ups! Ese no era... 😅", True, (180, 60, 60))
            cx  = self.game_width  // 2 - ftx.get_width()  // 2
            cy  = self.game_height // 2 - ftx.get_height() // 2
            self.surface.blit(ftx, (cx, cy))

    def _draw_win(self):
        w, h = self.game_width, self.game_height
        tf  = pygame.font.SysFont("Arial", 84, bold=True)
        tx  = tf.render("¡GANASTE! ", True, P_TITLE)
        self.surface.blit(tx, (w // 2 - tx.get_width() // 2, h // 2 - 120))

        sf  = pygame.font.SysFont("Arial", 44, bold=True)
        sx  = sf.render(f"Completaste los {len(self.sequence)} pasos", True, P_SUBTITLE)
        self.surface.blit(sx, (w // 2 - sx.get_width() // 2, h // 2 - 30))

        btn_back_win = pygame.Rect(w // 2 - 150, h // 2 + 60, 300, 70)
        self._draw_button(btn_back_win, "⬅ Menú principal", P_BTN_BACK)
        self.btn_back = btn_back_win

    def _draw_button(self, rect, text, color):
        sr = rect.move(3, 3)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=18)
        pygame.draw.rect(self.surface, color,    rect, border_radius=18)
        pygame.draw.rect(self.surface, (255, 255, 255), rect, 2, border_radius=18)
        
        f  = pygame.font.SysFont("Arial", 32, bold=True)
        ts = f.render(text, True, P_BTN_TEXT)
        self.surface.blit(
            ts,
            (rect.x + (rect.width  - ts.get_width())  // 2,
             rect.y + (rect.height - ts.get_height()) // 2)
        )
