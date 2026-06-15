import pygame
import random
import math
from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger

# ─────────────────────────────────────────────
#  PALETA  (coherente con el resto de juegos)
# ─────────────────────────────────────────────
P_BG_TOP        = (255, 240, 250)
P_BG_BOTTOM     = (230, 240, 255)
P_TITLE         = (180,  90, 180)
P_SUBTITLE      = (140, 110, 180)
P_SHADOW        = (210, 200, 225)
P_BTN_TEXT      = ( 60,  40,  90)
P_PANEL_BG      = (245, 240, 255)
P_PANEL_BORDER  = (200, 180, 230)
P_BTN_BACK      = (180, 200, 255)
P_BTN_EASY      = (150, 230, 180)
P_BTN_MEDIUM    = (255, 210, 130)
P_BTN_HARD      = (255, 160, 160)
P_BTN_EXIT      = (255, 170, 170)

P_FOUND_RING    = ( 80, 200, 120)   # círculo verde al encontrar diferencia
P_MISS_FLASH    = (220,  80,  80)   # destello rojo al fallar

# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE DIFICULTAD
# ─────────────────────────────────────────────
DIFFICULTY = {
    "facil":   {"n_objects": 8,  "n_diffs": 3, "time_limit": 0},   # sin límite
    "medio":   {"n_objects": 12, "n_diffs": 5, "time_limit": 120},  # 2 minutos
    "dificil": {"n_objects": 16, "n_diffs": 7, "time_limit": 90},   # 90 segundos
}

# ─────────────────────────────────────────────
#  TEMAS DE ESCENAS
# ─────────────────────────────────────────────
THEMES = {
    "jardin": {
        "bg":      (210, 235, 200),   # verde pálido
        "colors":  [
            (220,  80,  80),   # rojo flor
            ( 80, 160,  80),   # verde hoja
            (255, 200,  50),   # amarillo girasol
            (150,  80, 200),   # lila lavanda
            (255, 150,  50),   # naranja tulipán
            ( 60, 130,  60),   # verde oscuro
            (200, 240, 160),   # verde claro
        ],
        "shapes":  ["circle", "rect", "triangle"],
    },
    "ciudad": {
        "bg":      (200, 210, 230),   # gris azulado
        "colors":  [
            (100, 140, 200),   # azul ventana
            (180, 120,  60),   # marrón edificio
            (220, 220, 220),   # gris claro
            ( 60,  60, 100),   # azul oscuro
            (240, 180,  60),   # amarillo taxi
            (200,  60,  60),   # rojo señal
            (120, 180, 120),   # verde árbol
        ],
        "shapes":  ["rect", "rect", "circle"],   # más rectángulos (edificios)
    },
    "playa": {
        "bg":      (200, 230, 255),   # azul cielo
        "colors":  [
            (255, 220, 100),   # arena
            ( 50, 150, 220),   # azul mar
            (255, 100,  80),   # rojo sombrilla
            (255, 200,  80),   # amarillo sol
            (200, 240, 200),   # verde palmera
            (200, 180, 140),   # beige concha
            (255, 150, 100),   # coral
        ],
        "shapes":  ["circle", "triangle", "rect"],
    },
}

# ─────────────────────────────────────────────
#  AUXILIARES
# ─────────────────────────────────────────────
def _darken(color, factor=0.7):
    return tuple(max(0, int(c * factor)) for c in color)

def _lighten(color, factor=1.3):
    return tuple(min(255, int(c * factor)) for c in color)

# ─────────────────────────────────────────────
#  OBJETO DE ESCENA
# ─────────────────────────────────────────────
class SceneObject:
    def __init__(self, shape, x, y, w, h, color, border_color=None):
        self.shape        = shape         # "circle" | "rect" | "triangle"
        self.x            = x
        self.y            = y
        self.w            = w
        self.h            = h
        self.color        = color
        self.border_color = border_color or _darken(color, 0.6)

    def copy(self):
        return SceneObject(
            self.shape, self.x, self.y, self.w, self.h,
            self.color, self.border_color
        )

    def get_rect(self, offset_x=0, offset_y=0):
        return pygame.Rect(self.x + offset_x, self.y + offset_y, self.w, self.h)

    def draw(self, surface, offset_x=0, offset_y=0):
        px = self.x + offset_x
        py = self.y + offset_y

        if self.shape == "circle":
            cx = px + self.w // 2
            cy = py + self.h // 2
            r  = min(self.w, self.h) // 2
            if r <= 0: return
            pygame.draw.circle(surface, self.color,        (cx, cy), r)
            pygame.draw.circle(surface, self.border_color, (cx, cy), r, 2)

        elif self.shape == "rect":
            rr = pygame.Rect(px, py, self.w, self.h)
            pygame.draw.rect(surface, self.color,        rr, border_radius=6)
            pygame.draw.rect(surface, self.border_color, rr, 2, border_radius=6)

        elif self.shape == "triangle":
            pts = [
                (px + self.w // 2, py),
                (px,               py + self.h),
                (px + self.w,      py + self.h),
            ]
            pygame.draw.polygon(surface, self.color,        pts)
            pygame.draw.polygon(surface, self.border_color, pts, 2)

# ─────────────────────────────────────────────
#  GENERADOR DE ESCENAS
# ─────────────────────────────────────────────
def generate_scene(n_objects: int, theme_name: str, canvas_w: int, canvas_h: int) -> list:
    theme   = THEMES[theme_name]
    objects = []

    min_size = max(30, canvas_w // 14)
    max_size = max(55, canvas_w // 8)

    cols = max(3, int(math.sqrt(n_objects * canvas_w / canvas_h)))
    rows = max(3, int(math.ceil(n_objects / cols)) + 1)

    cell_w = canvas_w // cols
    cell_h = canvas_h // rows

    cells = [(c, r) for c in range(cols) for r in range(rows)]
    random.shuffle(cells)

    for i in range(min(n_objects, len(cells))):
        col, row = cells[i]
        shape    = random.choice(theme["shapes"])
        color    = random.choice(theme["colors"])
        w        = random.randint(min_size, max_size)
        h        = random.randint(min_size, max_size)

        margin = 8
        cx_min = col * cell_w + margin
        cx_max = max(cx_min + 1, (col + 1) * cell_w - w - margin)
        cy_min = row * cell_h + margin
        cy_max = max(cy_min + 1, (row + 1) * cell_h - h - margin)

        x = random.randint(cx_min, cx_max)
        y = random.randint(cy_min, cy_max)

        x = max(margin, min(x, canvas_w - w - margin))
        y = max(margin, min(y, canvas_h - h - margin))

        objects.append(SceneObject(shape, x, y, w, h, color))

    return objects

# ─────────────────────────────────────────────
#  MOTOR DE DIFERENCIAS
# ─────────────────────────────────────────────
class Difference:
    def __init__(self, diff_type: str, obj_index: int, zone: pygame.Rect):
        self.diff_type  = diff_type   # "color_change" | "remove" | "size_change" | "add"
        self.obj_index  = obj_index
        self.zone       = zone        # Área local del canvas
        self.found      = False

def apply_differences(base_objects: list, n_diffs: int, canvas_w: int, canvas_h: int, theme_name: str):
    theme    = THEMES[theme_name]
    modified = [obj.copy() for obj in base_objects]
    diffs    = []

    available = list(range(len(modified)))
    random.shuffle(available)

    diff_types = ["color_change", "size_change", "remove", "add"]
    applied    = 0
    idx_cursor = 0

    while applied < n_diffs:
        dtype = random.choice(diff_types)

        if dtype in ("color_change", "size_change", "remove"):
            if idx_cursor >= len(available):
                dtype = "add"
            else:
                obj_idx = available[idx_cursor]
                idx_cursor += 1
                obj = modified[obj_idx]

                if dtype == "color_change":
                    old_color  = obj.color
                    candidates = [c for c in theme["colors"] if c != old_color]
                    new_color  = random.choice(candidates) if candidates else _lighten(old_color)
                    obj.color        = new_color
                    obj.border_color = _darken(new_color, 0.6)
                    zone = pygame.Rect(obj.x, obj.y, obj.w, obj.h)
                    diffs.append(Difference("color_change", obj_idx, zone))
                    applied += 1

                elif dtype == "size_change":
                    factor = random.choice([0.65, 0.7, 1.3, 1.35])
                    old_w, old_h = obj.w, obj.h
                    obj.w = max(25, int(obj.w * factor))
                    obj.h = max(25, int(obj.h * factor))
                    
                    if obj.x + obj.w > canvas_w: obj.x = canvas_w - obj.w - 5
                    if obj.y + obj.h > canvas_h: obj.y = canvas_h - obj.h - 5
                    
                    zone = pygame.Rect(obj.x, obj.y, obj.w, obj.h).union(pygame.Rect(obj.x, obj.y, old_w, old_h))
                    diffs.append(Difference("size_change", obj_idx, zone))
                    applied += 1

                elif dtype == "remove":
                    zone = pygame.Rect(obj.x, obj.y, obj.w, obj.h)
                    obj.color        = None  
                    obj.border_color = None
                    diffs.append(Difference("remove", obj_idx, zone))
                    applied += 1

        if dtype == "add":
            shape  = random.choice(theme["shapes"])
            color  = random.choice(theme["colors"])
            min_s  = max(30, canvas_w // 14)
            max_s  = max(55, canvas_w // 8)
            w      = random.randint(min_s, max_s)
            h      = random.randint(min_s, max_s)
            x      = random.randint(10, canvas_w - w - 10)
            y      = random.randint(10, canvas_h - h - 10)
            
            new_obj = SceneObject(shape, x, y, w, h, color)
            modified.append(new_obj)
            zone = pygame.Rect(x, y, w, h)
            diffs.append(Difference("add", len(modified) - 1, zone))
            applied += 1

    return modified, diffs

# ─────────────────────────────────────────────
#  PANTALLA PRINCIPAL
# ─────────────────────────────────────────────
class FindDifferencesScreen(BasePygameQtScreen):
    def __init__(self, controller=None, width=1024, height=600):
        super().__init__(controller, width, height)
        logger.info("[DIFF] Iniciada FindDifferencesScreen")

        self.state      = "menu"
        self.difficulty = "facil"
        self.theme_name = "jardin"

        self.objects_a   = []
        self.objects_b   = []
        self.differences = []

        self.canvas_rect_a = pygame.Rect(0, 0, 0, 0)
        self.canvas_rect_b = pygame.Rect(0, 0, 0, 0)
        self._canvas_a_surf = None
        self._canvas_b_surf = None

        self._miss_flashes   = []
        self._found_rings    = []

        self._elapsed    = 0.0
        self._time_limit = 0
        self._ring_pulse = 0.0
        self._win_timer  = 0.0

        self._init_menu_buttons()

    def exit_game(self):
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    def _init_menu_buttons(self):
        w, h = self.game_width, self.game_height
        cx   = w // 2
        # REAJUSTE DE MENÚ: Botones más grandes (altura 62) y bien distribuidos verticalmente
        self.btn_easy   = pygame.Rect(cx - 150, 190, 300, 62)
        self.btn_medium = pygame.Rect(cx - 150, 270, 300, 62)
        self.btn_hard   = pygame.Rect(cx - 150, 350, 300, 62)
        self.btn_exit   = pygame.Rect(cx - 150, 445, 300, 52)
        self.btn_back   = pygame.Rect(12, self.game_height - 64, 130, 48)

    def start_game(self, difficulty: str):
        self.difficulty  = difficulty
        self.theme_name  = random.choice(list(THEMES.keys()))
        cfg              = DIFFICULTY[difficulty]

        self._elapsed    = 0.0
        self._time_limit = cfg["time_limit"]
        self._miss_flashes.clear()
        self._found_rings.clear()
        self._win_timer  = 0.0

        self._calculate_layout()

        cw = self.canvas_rect_a.width
        ch = self.canvas_rect_a.height

        self.objects_a = generate_scene(cfg["n_objects"], self.theme_name, cw, ch)
        self.objects_b, self.differences = apply_differences(
            self.objects_a, cfg["n_diffs"], cw, ch, self.theme_name
        )

        self._render_canvas_a()
        self._render_canvas_b()

        self.state = "playing"
        logger.info(f"[DIFF] Partida — dificultad={difficulty}, tema={self.theme_name}")

    def _calculate_layout(self):
        HEADER_H = 90
        FOOTER_H = 72
        GAP      = 12
        MARGIN   = 14

        total_w  = self.game_width - (MARGIN * 2) - GAP
        total_h  = self.game_height - HEADER_H - FOOTER_H

        canvas_w = total_w // 2
        canvas_h = total_h

        self.canvas_rect_a = pygame.Rect(MARGIN, HEADER_H, canvas_w, canvas_h)
        self.canvas_rect_b = pygame.Rect(MARGIN + canvas_w + GAP, HEADER_H, canvas_w, canvas_h)

    def _render_canvas_a(self):
        bg   = THEMES[self.theme_name]["bg"]
        surf = pygame.Surface((self.canvas_rect_a.width, self.canvas_rect_a.height))
        surf.fill(bg)
        for obj in self.objects_a:
            if obj.color is not None:
                obj.draw(surf)
        self._canvas_a_surf = surf

    def _render_canvas_b(self):
        bg   = THEMES[self.theme_name]["bg"]
        surf = pygame.Surface((self.canvas_rect_b.width, self.canvas_rect_b.height))
        surf.fill(bg)
        for obj in self.objects_b:
            if obj.color is not None:
                obj.draw(surf)
        self._canvas_b_surf = surf

    def update_logic(self):
        dt = 1.0 / 60.0

        if self.state == "playing":
            self._elapsed    += dt
            self._ring_pulse  = (self._ring_pulse + dt * 4) % (2 * math.pi)
            self._miss_flashes = [(x, y, t - dt) for x, y, t in self._miss_flashes if t - dt > 0]

            if self._time_limit > 0 and self._elapsed >= self._time_limit:
                self.state = "timeout"
                return

            if len(self.differences) > 0 and all(d.found for d in self.differences):
                self.state      = "win"
                self._win_timer = 4.0

        elif self.state == "win":
            self._win_timer -= dt
            self._ring_pulse  = (self._ring_pulse + dt * 4) % (2 * math.pi)
            if self._win_timer <= 0:
                self.state = "menu"

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

        elif self.state == "playing":
            if self.btn_back.collidepoint(pos):
                self.state = "menu"
                return
            self._handle_canvas_click(pos)

        elif self.state in ("win", "timeout"):
            self.state = "menu"

    def _handle_canvas_click(self, pos):
        HIT_MARGIN = 24  

        in_a = self.canvas_rect_a.collidepoint(pos)
        in_b = self.canvas_rect_b.collidepoint(pos)

        if not in_a and not in_b:
            return

        if in_a:
            local_x = pos[0] - self.canvas_rect_a.x
            local_y = pos[1] - self.canvas_rect_a.y
        else:
            local_x = pos[0] - self.canvas_rect_b.x
            local_y = pos[1] - self.canvas_rect_b.y

        hit_area = pygame.Rect(
            local_x - HIT_MARGIN, local_y - HIT_MARGIN,
            HIT_MARGIN * 2,       HIT_MARGIN * 2
        )

        found_diff = None
        for diff in self.differences:
            if not diff.found and diff.zone.colliderect(hit_area):
                found_diff = diff
                break

        if found_diff:
            found_diff.found = True
            cx_local = found_diff.zone.centerx
            cy_local = found_diff.zone.centery # CORREGIDO: Se elimina el duplicado erróneo con NameError que tenías aquí
            
            self._found_rings.append((cx_local + self.canvas_rect_a.x, cy_local + self.canvas_rect_a.y, found_diff))
            self._found_rings.append((cx_local + self.canvas_rect_b.x, cy_local + self.canvas_rect_b.y, found_diff))
            logger.info(f"[DIFF] Diferencia encontrada: {found_diff.diff_type}")
        else:
            self._miss_flashes.append((pos[0], pos[1], 0.4))
            logger.debug(f"[DIFF] Clic fallido en ({local_x}, {local_y})")

    # ──────────────────────────────────────────
    #  RENDERING
    # ──────────────────────────────────────────
    def render(self):
        self._draw_bg()
        if self.state == "menu":
            self._draw_menu()
        elif self.state in ("playing", "win", "timeout"):
            self._draw_game()
            if self.state == "win":
                self._draw_win_overlay()
            elif self.state == "timeout":
                self._draw_timeout_overlay()

    def _draw_bg(self):
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))

    def _draw_menu(self):
        w = self.game_width
        tf = pygame.font.Font(None, 64) # Ajustado a 64 para evitar desborde lateral
        
        shadow = tf.render("ENCUENTRA LAS DIFERENCIAS", True, P_SHADOW)
        title  = tf.render("ENCUENTRA LAS DIFERENCIAS", True, P_TITLE)
        self.surface.blit(shadow, (w // 2 - shadow.get_width() // 2 + 3, 63))
        self.surface.blit(title,  (w // 2 - title.get_width()  // 2,     60))

        sf  = pygame.font.Font(None, 36)
        sub = sf.render("Pulsa en las diferencias entre las dos imágenes 🔍", True, P_SUBTITLE)
        self.surface.blit(sub, (w // 2 - sub.get_width() // 2, 130)) # Espaciado de 130 para dar aire

        self._draw_button(self.btn_easy,   "FÁCIL  — 3 diferencias",  P_BTN_EASY)
        self._draw_button(self.btn_medium, "MEDIO  — 5 diferencias",  P_BTN_MEDIUM)
        self._draw_button(self.btn_hard,   "DIFÍCIL — 7 diferencias", P_BTN_HARD)
        self._draw_button(self.btn_exit,   "⬅ Volver",                P_BTN_EXIT)

    def _draw_game(self):
        self._draw_canvases()
        self._draw_found_rings()
        self._draw_miss_flashes()
        self._draw_header()
        self._draw_footer()

    def _draw_header(self):
        w = self.game_width
        hbar = pygame.Surface((w, 86), pygame.SRCALPHA)
        hbar.fill((245, 235, 255, 200))
        self.surface.blit(hbar, (0, 0))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, 86), (w, 86), 2)

        # TEXTO GRANDE: Ajustado a un tamaño contundente de 42
        tf = pygame.font.Font(None, 42)
        tit = tf.render(f"🔍  ESTILO: {self.theme_name.upper()}", True, P_TITLE)
        self.surface.blit(tit, (w // 2 - tit.get_width() // 2, 12))

        found = sum(1 for d in self.differences if d.found)
        total = len(self.differences)

        # PROGRESO: Subido a tamaño 30 para mejor lectura
        cf = pygame.font.Font(None, 30)
        ct = cf.render(f"Progreso: {found} / {total}", True, P_SUBTITLE)
        self.surface.blit(ct, (w // 2 - ct.get_width() // 2, 50))

        # BOLITAS HUD (Ajustadas dinámicamente con gap controlado)
        if total > 0:
            dot_r = 7
            dot_gap = 6
            dot_total_w = total * (dot_r * 2) + (total - 1) * dot_gap
            dot_x = w // 2 - dot_total_w // 2 + dot_r
            dot_y = 74
            for diff in self.differences:
                color = P_FOUND_RING if diff.found else (210, 205, 225)
                pygame.draw.circle(self.surface, color, (dot_x, dot_y), dot_r)
                if not diff.found:
                    pygame.draw.circle(self.surface, P_PANEL_BORDER, (dot_x, dot_y), dot_r, 1)
                dot_x += (dot_r * 2) + dot_gap

        if self._time_limit > 0:
            remaining = max(0.0, self._time_limit - self._elapsed)
            color = (220, 70, 70) if remaining < 20 else P_SUBTITLE
            tf2 = pygame.font.Font(None, 34)
            ts  = tf2.render(f"⏱  {int(remaining)}s", True, color)
            self.surface.blit(ts, (w - ts.get_width() - 25, 15))

    def _draw_canvases(self):
        if self._canvas_a_surf is None or self._canvas_b_surf is None:
            return

        for surf, rect, label in [
            (self._canvas_a_surf, self.canvas_rect_a, "Original A"),
            (self._canvas_b_surf, self.canvas_rect_b, "Modificada B"),
        ]:
            shadow_r = rect.inflate(6, 6).move(3, 3)
            pygame.draw.rect(self.surface, P_SHADOW, shadow_r, border_radius=10)
            self.surface.blit(surf, rect.topleft)
            pygame.draw.rect(self.surface, P_PANEL_BORDER, rect, 3, border_radius=8)

            lf = pygame.font.Font(None, 24)
            ls = lf.render(label, True, P_SUBTITLE)
            self.surface.blit(ls, (rect.x + 10, rect.y + 8))

    def _draw_found_rings(self):
        base_r = 26
        pulse  = int(math.sin(self._ring_pulse) * 3)

        for cx, cy, diff in self._found_rings:
            r = base_r + pulse
            if r <= 0: r = 1
            
            ring_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*P_FOUND_RING, 45), (r + 3, r + 3), r)
            pygame.draw.circle(ring_surf, (*P_FOUND_RING, 230), (r + 3, r + 3), r, 3)
            self.surface.blit(ring_surf, (cx - r - 3, cy - r - 3))

            cf  = pygame.font.Font(None, 28)
            cts = cf.render("✓", True, P_FOUND_RING)
            self.surface.blit(cts, (cx - cts.get_width() // 2, cy - cts.get_height() // 2))

    def _draw_miss_flashes(self):
        for fx, fy, ft in self._miss_flashes:
            alpha = int(ft / 0.4 * 150)
            if alpha <= 0: continue
            r = 20
            fs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(fs, (*P_MISS_FLASH, alpha), (r, r), r)
            self.surface.blit(fs, (fx - r, fy - r))

    def _draw_footer(self):
        BAR_H = 64
        bar_y = self.game_height - BAR_H
        bar   = pygame.Surface((self.game_width, BAR_H), pygame.SRCALPHA)
        bar.fill((245, 235, 255, 200))
        self.surface.blit(bar, (0, bar_y))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, bar_y), (self.game_width, bar_y), 2)

        self.btn_back = pygame.Rect(14, bar_y + 10, 130, 44)
        self._draw_button(self.btn_back, "⬅ Menú", P_BTN_BACK)

        hf  = pygame.font.Font(None, 24)
        ht  = hf.render("Tip: Las diferencias se pueden marcar en cualquiera de los dos lados", True, P_SUBTITLE)
        self.surface.blit(ht, (self.game_width // 2 - ht.get_width() // 2, bar_y + 22))

    def _draw_win_overlay(self):
        overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
        overlay.fill((210, 245, 220, 200))
        self.surface.blit(overlay, (0, 0))

        tf  = pygame.font.Font(None, 82)
        tx  = tf.render("¡COMPLETADO! 🎉", True, (40, 140, 70))
        self.surface.blit(tx, (self.game_width // 2 - tx.get_width() // 2, self.game_height // 2 - 50))

        sf  = pygame.font.Font(None, 36)
        st  = sf.render(f"¡Encontraste las {len(self.differences)} diferencias con éxito!", True, (60, 110, 80))
        self.surface.blit(st, (self.game_width // 2 - st.get_width() // 2, self.game_height // 2 + 25))

    def _draw_timeout_overlay(self):
        overlay = pygame.Surface((self.game_width, self.game_height), pygame.SRCALPHA)
        overlay.fill((255, 210, 210, 180))
        self.surface.blit(overlay, (0, 0))

        tf  = pygame.font.Font(None, 74)
        tx  = tf.render("¡Tiempo Agotado! ⏱", True, (170, 50, 50))
        self.surface.blit(tx, (self.game_width // 2 - tx.get_width() // 2, self.game_height // 2 - 60))

        for diff in self.differences:
            if not diff.found:
                for offset_x, offset_y in [
                    (self.canvas_rect_a.x, self.canvas_rect_a.y),
                    (self.canvas_rect_b.x, self.canvas_rect_b.y)
                ]:
                    rx = diff.zone.x + offset_x
                    ry = diff.zone.y + offset_y
                    pygame.draw.rect(self.surface, (230, 50, 50), (rx - 2, ry - 2, diff.zone.w + 4, diff.zone.h + 4), 3, border_radius=6)

        sf = pygame.font.Font(None, 32)
        st = sf.render("Haz clic en cualquier parte para volver al menú principal", True, (130, 50, 50))
        self.surface.blit(st, (self.game_width // 2 - st.get_width() // 2, self.game_height // 2 + 40))

    def _draw_button(self, rect, text, color):
        sr = rect.move(2, 2)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=16)
        pygame.draw.rect(self.surface, color,    rect, border_radius=16)
        pygame.draw.rect(self.surface, (255, 255, 255), rect, 2, border_radius=16)
        
        f  = pygame.font.Font(None, 30)
        ts = f.render(text, True, P_BTN_TEXT)
        self.surface.blit(ts, (rect.x + (rect.width - ts.get_width()) // 2, rect.y + (rect.height - ts.get_height()) // 2))
