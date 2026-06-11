import pygame
import os
import random
import time
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# ─────────────────────────────
# PALETA
# ─────────────────────────────
P_BG_TOP    = (255, 240, 250)
P_BG_BOTTOM = (230, 240, 255)

P_TITLE     = (180,  90, 180)
P_SUBTITLE  = (140, 110, 180)

P_BTN       = (255, 180, 200)
P_BTN_EXIT  = (255, 170, 170)
P_BTN_TEXT  = ( 60,  40,  90)

P_BORDER    = (200, 180, 230)
P_MATCHED   = (170, 240, 200)

P_BAR       = (245, 235, 255)


class MemoryScreen(BasePygameQtScreen):

    def __init__(self, controller=None):
        super().__init__(controller)

        logger.info("[MEMORY] init")

        self.level = 1
        self.game_state = "menu"

        self.SQUARE = 140
        self.INFO_H = 90

        self.font = pygame.font.SysFont("Arial", 30, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 58, bold=True)

        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        hidden_path = os.path.join(self.current_dir, "assets", "oculta.png")
        self.hidden = pygame.transform.scale(
            pygame.image.load(hidden_path),
            (self.SQUARE, self.SQUARE)
        )

        # sonidos
        try:
            self.sound_flip = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "voltear.wav"))
            self.sound_wrong = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "equivocado.wav"))
            self.sound_win = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "ganador.wav"))
        except:
            self.sound_flip = self.sound_wrong = self.sound_win = None

        # botones menú
        self.btn_play = pygame.Rect(0, 0, 260, 70)
        self.btn_exit = pygame.Rect(0, 0, 260, 70)

        # botón in-game (en barra inferior)
        self.btn_ingame_exit = pygame.Rect(0, 0, 160, 50)

        # partículas
        self.particles = []
        self.celebration = False

        self._reset()

    # ─────────────────────────────
    def exit_game(self):
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    # ─────────────────────────────
    def _reset(self):

        self.matrix, self.rows, self.cols = self._create(self.level)

        self.first = None
        self.second = None

        self.lock = False
        self.lock_time = None

        self.start_time = time.time()

        self.particles = []
        self.celebration = False

    # ─────────────────────────────
    def _create(self, level):

        sizes = {1:(2,2), 2:(2,4), 3:(4,4), 4:(4,6)}
        r, c = sizes[level]

        imgs = ["coco.png", "manzana.png", "limon.png", "naranja.png"]

        pairs = (r * c) // 2

        # FIX CRASH → permitir repetición
        deck = random.choices(imgs, k=pairs) * 2
        random.shuffle(deck)

        matrix = []
        i = 0

        for y in range(r):
            row = []
            for x in range(c):

                path = os.path.join(self.current_dir, "assets", deck[i])

                img = pygame.transform.scale(
                    pygame.image.load(path),
                    (self.SQUARE, self.SQUARE)
                )

                row.append({
                    "img": img,
                    "path": path,
                    "show": False,
                    "matched": False
                })

                i += 1

            matrix.append(row)

        return matrix, r, c

    # ─────────────────────────────
    def _board(self):

        w = self.cols * self.SQUARE
        h = self.rows * self.SQUARE

        ox = (self.game_width - w) // 2
        oy = (self.game_height - self.INFO_H - h) // 2 - 10

        return ox, oy

    # ─────────────────────────────
    def _ui_bar(self):
        return pygame.Rect(
            0,
            self.game_height - self.INFO_H,
            self.game_width,
            self.INFO_H
        )

    # ─────────────────────────────
    def update_logic(self):

        for e in self.events:

            # ─ MENU ─
            if self.game_state == "menu":

                if e.type == pygame.MOUSEBUTTONDOWN:
                    x, y = e.pos

                    if self.btn_play.collidepoint(x, y):
                        self.game_state = "playing"
                        self._reset()

                    elif self.btn_exit.collidepoint(x, y):
                        self.exit_game()

            # ─ GAME ─
            elif self.game_state == "playing":

                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.exit_game()

                if e.type == pygame.MOUSEBUTTONDOWN and not self.lock:

                    x, y = e.pos
                    ox, oy = self._board()

                    # botón salir in-game
                    if self.btn_ingame_exit.collidepoint(x, y):
                        self.exit_game()
                        return

                    # bloquear clicks en barra inferior
                    if y >= self.game_height - self.INFO_H:
                        continue

                    if not (ox <= x < ox + self.cols*self.SQUARE and oy <= y < oy + self.rows*self.SQUARE):
                        continue

                    cx = (x - ox) // self.SQUARE
                    cy = (y - oy) // self.SQUARE

                    card = self.matrix[cy][cx]

                    if card["show"] or card["matched"]:
                        continue

                    card["show"] = True

                    if self.first is None:
                        self.first = (cx, cy)
                        if self.sound_flip:
                            self.sound_flip.play()
                    else:
                        self.second = (cx, cy)

                        c1 = self.matrix[self.first[1]][self.first[0]]
                        c2 = self.matrix[self.second[1]][self.second[0]]

                        if c1["path"] == c2["path"]:
                            c1["matched"] = c2["matched"] = True
                            if self.sound_win:
                                self.sound_win.play()
                        else:
                            self.lock = True
                            self.lock_time = time.time()
                            if self.sound_wrong:
                                self.sound_wrong.play()

                        self.first = self.second = None

        # unlock
        if self.lock and time.time() - self.lock_time > 1:
            for r in self.matrix:
                for c in r:
                    if not c["matched"]:
                        c["show"] = False
            self.lock = False

        # WIN
        if self.game_state == "playing":

            total = self.rows * self.cols
            matched = sum(c["matched"] for r in self.matrix for c in r)

            if matched == total:

                self._spawn_particles()
                self.celebration = True

                if self.sound_win:
                    self.sound_win.play()

                time.sleep(0.6)

                if self.level < 4:
                    self.level += 1
                    self._reset()
                else:
                    self.level = 1
                    self.game_state = "menu"
                    self._reset()

    # ─────────────────────────────
    def _spawn_particles(self):

        ox, oy = self._board()

        for _ in range(120):
            self.particles.append([
                ox + random.randint(0, self.cols*self.SQUARE),
                oy + random.randint(0, self.rows*self.SQUARE),
                random.uniform(-3, 3),
                random.uniform(-6, -2),
                random.choice([(255,182,193),(173,216,230),(144,238,144)])
            ])

    # ─────────────────────────────
    def render(self):

        self._bg()

        if self.game_state == "menu":
            self._menu()

        elif self.game_state == "playing":
            self._draw_board()

    # ─────────────────────────────
    def _bg(self):

        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0]-P_BG_TOP[0])*t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1]-P_BG_TOP[1])*t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2]-P_BG_TOP[2])*t)
            pygame.draw.line(self.surface, (r,g,b), (0,y), (self.game_width,y))

    # ─────────────────────────────
    def _menu(self):

        w, h = self.game_width, self.game_height

        title = self.title_font.render(f"🃏 MEMORY - NIVEL {self.level}", True, P_TITLE)
        self.surface.blit(title, (w//2 - title.get_width()//2, h//2 - 180))

        self.btn_play.center = (w//2, h//2 - 20)
        self.btn_exit.center = (w//2, h//2 + 80)

        pygame.draw.rect(self.surface, P_BTN, self.btn_play, border_radius=20)
        pygame.draw.rect(self.surface, P_BTN_EXIT, self.btn_exit, border_radius=20)

        t1 = self.font.render("▶ JUGAR", True, P_BTN_TEXT)
        t2 = self.font.render("⛔ SALIR", True, P_BTN_TEXT)

        self.surface.blit(t1, t1.get_rect(center=self.btn_play.center))
        self.surface.blit(t2, t2.get_rect(center=self.btn_exit.center))

        sub = self.font.render("Toca para empezar ✨", True, P_SUBTITLE)
        self.surface.blit(sub, (w//2 - sub.get_width()//2, h//2 + 160))

    # ─────────────────────────────
    def _draw_board(self):

        ox, oy = self._board()

        for y in range(self.rows):
            for x in range(self.cols):

                c = self.matrix[y][x]

                px = ox + x*self.SQUARE
                py = oy + y*self.SQUARE

                img = self.hidden if not c["show"] and not c["matched"] else c["img"]

                self.surface.blit(img, (px, py))

                pygame.draw.rect(
                    self.surface,
                    P_MATCHED if c["matched"] else P_BORDER,
                    (px, py, self.SQUARE, self.SQUARE),
                    3
                )

        # ─ barra inferior
        bar = self._ui_bar()
        pygame.draw.rect(self.surface, P_BAR, bar)

        # nivel visible
        lvl = self.font.render(f"NIVEL {self.level}", True, P_SUBTITLE)
        self.surface.blit(lvl, (20, self.game_height - self.INFO_H + 25))

        # botón salir limpio
        self.btn_ingame_exit.topleft = (self.game_width - 190, self.game_height - self.INFO_H + 20)

        pygame.draw.rect(self.surface, P_BTN_EXIT, self.btn_ingame_exit, border_radius=12)

        txt = self.font.render("SALIR", True, P_BTN_TEXT)
        self.surface.blit(txt, txt.get_rect(center=self.btn_ingame_exit.center))

        # partículas
        if self.celebration:
            for p in self.particles:
                p[1] += p[3]
                p[0] += p[2]
                pygame.draw.circle(self.surface, p[4], (int(p[0]), int(p[1])), 4)
