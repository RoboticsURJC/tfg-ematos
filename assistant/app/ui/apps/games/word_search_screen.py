import pygame
import random
import math

from app.ui.apps.games import generate
from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# ─────────────────────────────────────────────
#  PALETA PASTEL CUTE
# ─────────────────────────────────────────────
P_BG_TOP        = (255, 240, 250)   # rosa muy suave
P_BG_BOTTOM     = (230, 240, 255)   # lavanda pálido
P_TITLE         = (180,  90, 180)   # lila oscuro
P_ACCENT        = (255, 140, 170)   # rosa chicle
P_CELL_NORMAL   = (255, 255, 255)   # blanco
P_CELL_BORDER   = (200, 180, 230)   # lavanda
P_CELL_SELECT   = (180, 220, 255)   # azul bebé
P_CELL_FOUND    = (180, 255, 200)   # menta
P_CELL_HINT     = (255, 220, 130)   # melocotón
P_WORD_PANEL    = (245, 240, 255)   # blanco lavanda
P_WORD_PENDING  = ( 90,  70, 120)   # mora oscura (texto legible)
P_WORD_DONE     = (180, 180, 200)   # gris suave
P_WORD_STRIKE   = (150, 200, 170)   # verde menta
P_BTN_EASY      = (150, 230, 180)   # verde pastel
P_BTN_MEDIUM    = (255, 210, 130)   # amarillo pastel
P_BTN_HARD      = (255, 160, 160)   # rojo pastel
P_BTN_HINT      = (255, 220, 100)   # dorado pastel
P_BTN_GAME_BACK = (255, 0, 0)       # Rojo
P_BTN_BACK      = (180, 200, 255)   # azul pastel
P_BTN_TEXT      = ( 60,  40,  90)   # mora profunda
P_SHADOW        = (210, 200, 225)   # sombra suave
P_PANEL_BORDER  = (200, 180, 230)
P_SUBTITLE      = (140, 110, 180)


class WordSearchScreen(BasePygameQtScreen):
    """
    Sopa de Letras — estilo pastel cute, layout centrado y corregido
    """

    def __init__(self, controller=None, width=1024, height=600):
        super().__init__(controller, width, height)
        logger.info("[SOPA] Iniciada WordSearchScreen pastel")

        self.state = "menu"
        self.difficulty = None

        self.selected      = []
        self.current_path  = []
        self.words_to_guess = []
        self.hint_cell     = None

        self.CELL      = 50
        self.GRID_POS  = (40, 100)
        self.WORD_LIST_X = 0
        self.WORD_LIST_Y = 100

        self.scroll_offset = 0
        self.max_scroll    = 0
        self._mouse_pressed = False

        self._init_buttons()
        self.letter_cache = {}
    
    def exit_game(self):
        self.stop()
        
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()
            
    # ──────────────────────────────────────────
    # BOTONES  (se recalculan también en _calculate_layout)
    # ──────────────────────────────────────────
    def _init_buttons(self):
        w, h = self.game_width, self.game_height
        self.btn_easy   = pygame.Rect(w // 2 - 140, 185, 280, 72)
        self.btn_medium = pygame.Rect(w // 2 - 140, 277, 280, 72)
        self.btn_hard   = pygame.Rect(w // 2 - 140, 369, 280, 72)
        self.btn_game_back = pygame.Rect(20, 20, 140, 55)
        
        # Placeholders — se redefinen en _calculate_layout
        self.btn_hint = pygame.Rect(0, 0, 0, 0)
        self.btn_back = pygame.Rect(0, 0, 0, 0)

    # ──────────────────────────────────────────
    # START
    # ──────────────────────────────────────────
    def start_game(self, difficulty):
        self.difficulty = difficulty
        generate.set_difficulty(difficulty)
        generate.generate_board()

        self.words_to_guess = generate.words_copy[:]
        self.selected       = []
        self.current_path   = []
        self.hint_cell      = None
        self.scroll_offset  = 0

        self._calculate_layout()
        self._cache_letters()
        self._update_scroll_range()
        self.state = "game"
        logger.info(f"[SOPA] Juego iniciado — dificultad: {difficulty}")

    # ──────────────────────────────────────────
    # LAYOUT  ← aquí estaba el bug principal
    # ──────────────────────────────────────────
    def _calculate_layout(self):
        """
        Divide la pantalla en dos columnas:
          • Columna izquierda: grid centrado en su área
          • Columna derecha:   lista de palabras
          • Franja inferior:   botones (sin solaparse con el grid)
        """
        grid = generate.GRID_SIZE

        LIST_W   = 250   # ancho fijo de la columna de palabras
        MARGIN   = 20    # márgenes laterales y entre columnas
        TOP_Y    = 80    # y de inicio del grid (espacio para título)
        BTN_H    = 64    # alto de botones inferiores
        BTN_GAP  = 12    # separación entre botón y borde inferior
        BOTTOM_RESERVED = BTN_H + BTN_GAP * 2   # franja inferior reservada

        # Área disponible para el grid
        available_w = self.game_width - LIST_W - MARGIN * 3
        available_h = self.game_height - TOP_Y - BOTTOM_RESERVED - MARGIN

        cell_by_w = available_w // grid
        cell_by_h = available_h // grid
        self.CELL = max(min(cell_by_w, cell_by_h, 62), 38)

        grid_px_w = grid * self.CELL
        grid_px_h = grid * self.CELL

        # Centrar el grid dentro de su área izquierda
        left_area_w = self.game_width - LIST_W - MARGIN * 3
        grid_x = MARGIN + (left_area_w - grid_px_w) // 2
        grid_y = TOP_Y + (available_h - grid_px_h) // 2
        grid_y = max(grid_y, TOP_Y)   # nunca sube del título

        self.GRID_POS = (grid_x, grid_y)

        # Lista de palabras — a la derecha del grid
        self.WORD_LIST_X = MARGIN * 2 + left_area_w
        self.WORD_LIST_Y = TOP_Y

        # Botones en la franja inferior, fuera del área del grid
        btn_y = self.game_height - BTN_H - BTN_GAP
        btn_w = 150
        self.btn_back = pygame.Rect(MARGIN, btn_y, btn_w, BTN_H)
        self.btn_hint = pygame.Rect(
            self.game_width - MARGIN - btn_w, btn_y, btn_w, BTN_H
        )

        logger.info(
            f"[SOPA] Layout — grid ({grid_x},{grid_y}) cell={self.CELL} "
            f"lista_x={self.WORD_LIST_X} btn_y={btn_y}"
        )

    def _update_scroll_range(self):
        if self.words_to_guess:
            words_h  = len(self.words_to_guess) * 36
            panel_h  = self.game_height - self.WORD_LIST_Y - 80
            self.max_scroll = max(0, words_h - panel_h)
        else:
            self.max_scroll = 0
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    # ──────────────────────────────────────────
    # CACHE LETRAS
    # ──────────────────────────────────────────
    def _cache_letters(self):
        self.letter_cache = {}
        font_size = max(int(self.CELL * 0.58), 20)
        font = pygame.font.Font(None, font_size)
        for y, row in enumerate(generate.grid):
            for x, letter in enumerate(row):
                surf = font.render(letter.upper(), True, P_BTN_TEXT)
                px = self.GRID_POS[0] + x * self.CELL + (self.CELL - surf.get_width())  // 2
                py = self.GRID_POS[1] + y * self.CELL + (self.CELL - surf.get_height()) // 2
                self.letter_cache[(x, y)] = (surf, (px, py))

    # ──────────────────────────────────────────
    # LÓGICA
    # ──────────────────────────────────────────
    def update_logic(self):
        if self.state == "game" and len(self.words_to_guess) == 0:
            self._win()

    # ──────────────────────────────────────────
    # EVENTOS
    # ──────────────────────────────────────────
    def mousePressEvent(self, event):
        self._mouse_pressed = True
        pos = self._qt_to_game_pos((event.x(), event.y()))

        if self.state == "menu":

            if self.btn_game_back.collidepoint(pos):
                self.exit_game()
                return
              
            if self.btn_easy.collidepoint(pos):
                self.start_game("facil")

            elif self.btn_medium.collidepoint(pos):
                self.start_game("medio")

            elif self.btn_hard.collidepoint(pos):
                self.start_game("dificil")

        elif self.state == "game":
            if self.btn_back.collidepoint(pos):
                self.state = "menu"
                
            elif self.btn_hint.collidepoint(pos):
                self.hint_cell = self._get_hint_cell()
            else:
                self._handle_grid_click(pos)

    def mouseMoveEvent(self, event):
        pos = self._qt_to_game_pos((event.x(), event.y()))
        if self._mouse_pressed and self.state == "game":
            if not self.btn_hint.collidepoint(pos) and not self.btn_back.collidepoint(pos):
                self._handle_grid_drag(pos)

    def mouseReleaseEvent(self, event):
        self._mouse_pressed = False
        if self.state == "game" and self.current_path:
            self._validate_selection()
            self.current_path.clear()

    # ──────────────────────────────────────────
    # GRID INPUT
    # ──────────────────────────────────────────
    def _handle_grid_click(self, pos):
        grid_rect = pygame.Rect(
            self.GRID_POS[0], self.GRID_POS[1],
            generate.GRID_SIZE * self.CELL,
            generate.GRID_SIZE * self.CELL
        )
        if grid_rect.collidepoint(pos):
            x = (pos[0] - self.GRID_POS[0]) // self.CELL
            y = (pos[1] - self.GRID_POS[1]) // self.CELL
            if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
                self.current_path = [(x, y)]

    def _handle_grid_drag(self, pos):
        grid_rect = pygame.Rect(
            self.GRID_POS[0], self.GRID_POS[1],
            generate.GRID_SIZE * self.CELL,
            generate.GRID_SIZE * self.CELL
        )
        if grid_rect.collidepoint(pos):
            x = (pos[0] - self.GRID_POS[0]) // self.CELL
            y = (pos[1] - self.GRID_POS[1]) // self.CELL
            if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
                cell = (x, y)
                if cell not in self.current_path:
                    temp = self.current_path + [cell]
                    if self._is_straight_line(temp):
                        self.current_path.append(cell)

    def _is_straight_line(self, path):
        if len(path) < 2:
            return True
        dx = path[1][0] - path[0][0]
        dy = path[1][1] - path[0][1]
        if dx != 0 and dy != 0:
            return False
        dx = (dx // abs(dx)) if dx != 0 else 0
        dy = (dy // abs(dy)) if dy != 0 else 0
        for i in range(1, len(path)):
            sx = path[i][0] - path[i-1][0]
            sy = path[i][1] - path[i-1][1]
            sx = (sx // abs(sx)) if sx != 0 else 0
            sy = (sy // abs(sy)) if sy != 0 else 0
            if sx != dx or sy != dy:
                return False
        return True

    def _validate_selection(self):
        if len(self.current_path) < 2:
            return False
        word = "".join(generate.grid[y][x] for (x, y) in self.current_path)
        found_word = None
        if word in self.words_to_guess:
            found_word = word
        elif word[::-1] in self.words_to_guess:
            found_word = word[::-1]
        if found_word:
            for (x, y) in self.current_path:
                self.selected.append([x, y])
            self.words_to_guess.remove(found_word)
            if self.hint_cell is not None:
                for (x, y) in self.current_path:
                    if self.hint_cell == (x, y):
                        self.hint_cell = None
                        break
            self._update_scroll_range()
            return True
        return False

    def _get_hint_cell(self):
        for word in self.words_to_guess:
            wup = word.upper()
            if wup in generate.word_positions:
                positions = generate.word_positions[wup]
                if positions:
                    x, y = positions[0]
                    return (x, y)
        return None

    # ──────────────────────────────────────────
    # RENDER
    # ──────────────────────────────────────────
    def render(self):
        self._draw_bg()
        if self.state == "menu":
            self._draw_menu()
        else:
            self._draw_game()

    def _draw_bg(self):
        """Degradado pastel vertical"""
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))

    # ── MENÚ ──────────────────────────────────
    def _draw_menu(self):
        w = self.game_width

        # Título
        tf = pygame.font.Font(None, 78)
        shadow = tf.render(" SOPA DE LETRAS", True, P_SHADOW)
        title  = tf.render(" SOPA DE LETRAS", True, P_TITLE)
        self.surface.blit(shadow, (w // 2 - shadow.get_width() // 2 + 3, 58))
        self.surface.blit(title,  (w // 2 - title.get_width()  // 2,     55))

        sf = pygame.font.Font(None, 50)
        sub = sf.render("Elige la dificultad ✨", True, P_SUBTITLE)
        self.surface.blit(sub, (w // 2 - sub.get_width() // 2, 138))

        self._draw_button(self.btn_easy,   " FÁCIL",   P_BTN_EASY)
        self._draw_button(self.btn_medium, " MEDIO",   P_BTN_MEDIUM)
        self._draw_button(self.btn_hard,   " DIFÍCIL", P_BTN_HARD)
        self._draw_button(self.btn_game_back, "VOLVER", P_BTN_GAME_BACK)

    # ── JUEGO ─────────────────────────────────
    def _draw_game(self):
        self._draw_grid()
        self._draw_words()
        self._draw_bottom_bar()

    def _draw_grid(self):
        for y in range(generate.GRID_SIZE):
            for x in range(generate.GRID_SIZE):
                rect = pygame.Rect(
                    self.GRID_POS[0] + x * self.CELL,
                    self.GRID_POS[1] + y * self.CELL,
                    self.CELL, self.CELL
                )
                in_path  = (x, y) in self.current_path
                in_found = [x, y] in self.selected

                if in_path:
                    color = P_CELL_SELECT
                elif in_found:
                    color = P_CELL_FOUND
                else:
                    color = P_CELL_NORMAL

                pygame.draw.rect(self.surface, color,         rect, 0, border_radius=8)
                border = P_ACCENT if in_path else P_CELL_BORDER
                pygame.draw.rect(self.surface, border,        rect, 2, border_radius=8)

        # Letras
        for (surf, pos) in self.letter_cache.values():
            self.surface.blit(surf, pos)

        # Hint
        if self.hint_cell is not None:
            hx, hy = self.hint_cell
            if 0 <= hx < generate.GRID_SIZE and 0 <= hy < generate.GRID_SIZE:
                hr = pygame.Rect(
                    self.GRID_POS[0] + hx * self.CELL,
                    self.GRID_POS[1] + hy * self.CELL,
                    self.CELL, self.CELL
                )
                pygame.draw.rect(self.surface, P_CELL_HINT, hr, 5, border_radius=8)

    def _draw_words(self):
        LIST_W   = 230
        LIST_H   = self.game_height - self.WORD_LIST_Y - 90
        panel    = pygame.Rect(self.WORD_LIST_X - 10, self.WORD_LIST_Y - 10,
                               LIST_W + 20, LIST_H + 20)

        # Sombra del panel
        shadow_r = panel.move(4, 4)
        pygame.draw.rect(self.surface, P_SHADOW, shadow_r, border_radius=16)
        pygame.draw.rect(self.surface, P_WORD_PANEL,   panel, border_radius=16)
        pygame.draw.rect(self.surface, P_PANEL_BORDER, panel, 2, border_radius=16)

        # Título del panel
        hf = pygame.font.Font(None, 30)
        ht = hf.render("✏️  PALABRAS", True, P_TITLE)
        self.surface.blit(ht, (self.WORD_LIST_X + 12, self.WORD_LIST_Y + 8))
        pygame.draw.line(
            self.surface, P_PANEL_BORDER,
            (self.WORD_LIST_X + 8,  self.WORD_LIST_Y + 46),
            (self.WORD_LIST_X + LIST_W - 8, self.WORD_LIST_Y + 46), 2
        )

        # Palabras con clipping
        clip_area = pygame.Rect(
            self.WORD_LIST_X, self.WORD_LIST_Y + 52,
            LIST_W, LIST_H - 52
        )
        old_clip = self.surface.get_clip()
        self.surface.set_clip(clip_area)

        wf  = pygame.font.Font(None, 30)
        yp  = self.WORD_LIST_Y + 56 - self.scroll_offset

        for word in generate.words_copy:
            pending = word in self.words_to_guess
            color   = P_WORD_PENDING if pending else P_WORD_DONE
            ws      = wf.render(word, True, color)
            self.surface.blit(ws, (self.WORD_LIST_X + 16, yp))
            if not pending:
                ly = yp + ws.get_height() // 2
                pygame.draw.line(
                    self.surface, P_WORD_STRIKE,
                    (self.WORD_LIST_X + 16, ly),
                    (self.WORD_LIST_X + 16 + ws.get_width(), ly), 2
                )
            yp += 34

        self.surface.set_clip(old_clip)

        # Scrollbar
        if self.max_scroll > 0:
            sb_x = self.WORD_LIST_X + LIST_W - 10
            sb_bg = pygame.Rect(sb_x, self.WORD_LIST_Y + 52, 6, LIST_H - 52)
            pygame.draw.rect(self.surface, P_SHADOW, sb_bg, border_radius=3)
            sh   = max(28, (LIST_H - 52) * (LIST_H - 52) / (len(generate.words_copy) * 34))
            sy   = self.WORD_LIST_Y + 52 + (self.scroll_offset / self.max_scroll) * (LIST_H - 52 - sh)
            pygame.draw.rect(self.surface, P_ACCENT,
                             pygame.Rect(sb_x, int(sy), 6, int(sh)), border_radius=3)

    def _draw_bottom_bar(self):
        """Franja inferior con fondo translúcido y botones"""
        BAR_H = 80
        bar_y = self.game_height - BAR_H
        bar   = pygame.Surface((self.game_width, BAR_H), pygame.SRCALPHA)
        bar.fill((245, 235, 255, 200))
        self.surface.blit(bar, (0, bar_y))
        pygame.draw.line(self.surface, P_PANEL_BORDER,
                         (0, bar_y), (self.game_width, bar_y), 2)

        self._draw_button(self.btn_hint, "💡 Pista",  P_BTN_HINT)
        self._draw_button(self.btn_back, "⬅ Menú",  P_BTN_BACK)

    # ── BOTÓN PASTEL ──────────────────────────
    def _draw_button(self, rect, text, color):
        # Sombra
        sr = rect.move(3, 3)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=18)
        # Cuerpo
        pygame.draw.rect(self.surface, color, rect, border_radius=18)
        # Borde blanco
        pygame.draw.rect(self.surface, (255, 255, 255), rect, 2, border_radius=18)
        # Texto
        f  = pygame.font.Font(None, 34)
        ts = f.render(text, True, P_BTN_TEXT)
        self.surface.blit(
            ts,
            (rect.x + (rect.width  - ts.get_width())  // 2,
             rect.y + (rect.height - ts.get_height()) // 2)
        )

    # ──────────────────────────────────────────
    # WIN
    # ──────────────────────────────────────────
    def _win(self):
        self.state = "menu"
        self.words_to_guess = []
        logger.info("[SOPA] ¡Completado!")
