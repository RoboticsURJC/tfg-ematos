"""
@file proactive_screen.py
@brief Pantalla proactiva — diseño grande y cute para personas mayores.
"""

import pygame
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger

# ── PALETA ────────────────────────────────────────────────────────────────────
BG_TOP          = (255, 242, 252)
BG_BOTTOM       = (228, 238, 255)
PANEL_BG        = (255, 251, 255)
PANEL_BORDER    = (215, 185, 240)
SHADOW_COL      = (210, 198, 228)
TITLE_COL       = (150,  55, 165)
BODY_COL        = (110,  75, 148)
DIVIDER         = (225, 205, 245)

BTN_YES_BG      = (148, 232, 178)
BTN_YES_BORDER  = ( 90, 185, 130)
BTN_YES_TEXT    = ( 25,  90,  55)
BTN_NO_BG       = (255, 195, 210)
BTN_NO_BORDER   = (210, 140, 165)
BTN_NO_TEXT     = (110,  35,  65)

ANIM_SKIN       = (255, 213, 175)
ANIM_CLOTHES    = (148, 105, 210)
ANIM_HAIR       = ( 85,  55,  28)
ANIM_ACCENT     = (255, 148, 175)
ANIM_CIRCLE_BG  = (242, 232, 255)
ANIM_CIRCLE_BR  = (215, 185, 240)

TAG_MEM_BG      = (218, 195, 255)
TAG_MEM_FG      = ( 95,  45, 158)
TAG_MOB_BG      = (192, 242, 215)
TAG_MOB_FG      = ( 28, 120,  72)

WHITE           = (255, 255, 255)


class ProactiveScreen(BasePygameQtScreen):

    def __init__(self, suggestion, controller=None, on_accept=None, on_dismiss=None,
                 width=1024, height=600):
        super().__init__(controller, width, height)
        self.suggestion = suggestion
        self.on_accept  = on_accept
        self.on_dismiss = on_dismiss
        self._t         = 0.0
        self._appear    = 0.0
        self._dismissed = False
        self._icon_bottom = 0
        self._build_layout()
        logger.info(f"[PROACTIVE SCREEN] {suggestion['title']}")
        self.start()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self):
        W, H = self.game_width, self.game_height

        # Panel principal: Ocupa casi toda la pantalla para aprovechar espacio
        PAD  = 20
        PW   = min(W - PAD * 2, 980)
        PH   = min(H - PAD * 2, 560)
        self.panel = pygame.Rect((W - PW) // 2, (H - PH) // 2, PW, PH)

        # Columna izquierda: Animación (42 % del panel)
        ANIM_W       = int(PW * 0.42)
        self.anim_cx = self.panel.x + ANIM_W // 2
        self.anim_cy = self.panel.y + PH // 2
        self.anim_r  = min(ANIM_W // 2 - 20, int(PH * 0.40))

        # Divisor vertical intermedio
        self.div_x = self.panel.x + ANIM_W

        # Columna derecha: Textos y Contenido (58 % del panel)
        # Ajustamos márgenes internos para que el bloque no se pegue a los bordes
        self.txt_x = self.div_x + 32
        self.txt_w = PW - ANIM_W - 64
        self.txt_y = self.panel.y + 64

        # Botones — ¡Súper Grandes y fáciles de pulsar para abuelitos!
        BW  = max(int(self.txt_w * 0.45), 200)
        BH  = 80  # Altura ampliada de 68 a 80
        GAP = 24  # Separación generosa entre botones
        
        # Centrado perfecto de la pareja de botones dentro del ancho de la columna de texto
        bx  = self.txt_x + (self.txt_w - (BW * 2 + GAP)) // 2
        by  = self.panel.bottom - BH - 36
        
        self.btn_yes = pygame.Rect(bx,           by, BW, BH)
        self.btn_no  = pygame.Rect(bx + BW + GAP, by, BW, BH)

        # Fuentes — Escaladas a tamaños gigantescos para legibilidad extrema
        self.f_tag   = pygame.font.SysFont("Arial", 22, bold=True)
        self.f_title = pygame.font.SysFont("Arial", 42, bold=True)  # Subido de 34 a 42
        self.f_body  = pygame.font.SysFont("Arial", 28)             # Subido de 24 a 28
        self.f_btn   = pygame.font.SysFont("Arial", 32, bold=True)  # Subido de 26 a 32

    # ── Lógica ────────────────────────────────────────────────────────────────

    def update_logic(self):
        self._appear = min(self._appear + 0.08, 1.0)
        self._t += 0.038

    # ── Eventos ───────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if self._dismissed:
            return
        pos = self._qt_to_game_pos((event.x(), event.y()))
        if self.btn_yes.collidepoint(pos):
            self._dismissed = True
            logger.info(f"[PROACTIVE] Aceptado → {self.suggestion['action']}")
            if self.on_accept:
                self.on_accept(self.suggestion["action"])
        elif self.btn_no.collidepoint(pos):
            self._dismissed = True
            logger.info("[PROACTIVE] Descartado")
            if self.on_dismiss:
                self.on_dismiss()

    # ── Render ────────────────────────────────────────────────────────────────

    def render(self):
        self._draw_bg()
        if self._appear < 0.03:
            return
        # Slide-in suave desde abajo
        offset_y = int((1.0 - self._appear) * 60)
        self.surface.scroll(0, -offset_y) if offset_y else None
        self._draw_panel(offset_y)
        self._draw_tag(offset_y)
        self._draw_animation(offset_y)
        self._draw_divider(offset_y)
        self._draw_texts(offset_y)
        self._draw_buttons(offset_y)

    def _draw_bg(self):
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))
        # Burbujas decorativas de fondo
        for bx, by, br, alpha in [(70,55,48,22),(self.game_width-75,70,62,16),
                                   (55,self.game_height-65,40,18),
                                   (self.game_width-55,self.game_height-55,36,18)]:
            s = pygame.Surface((br*2, br*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (185,148,225, int(alpha * self._appear)), (br,br), br)
            self.surface.blit(s, (bx-br, by-br))

    def _shifted(self, rect, dy):
        return rect.move(0, dy)

    def _draw_panel(self, dy):
        p = self._shifted(self.panel, dy)
        a = int(255 * self._appear)
        sh = p.move(8, 8)
        ss = pygame.Surface((sh.width, sh.height), pygame.SRCALPHA)
        ss.fill((*SHADOW_COL, a // 3))
        self.surface.blit(ss, sh.topleft)
        ps = pygame.Surface((p.width, p.height), pygame.SRCALPHA)
        ps.fill((*PANEL_BG, a))
        self.surface.blit(ps, p.topleft)
        pygame.draw.rect(self.surface, PANEL_BORDER, p, 3, border_radius=32)

    def _draw_tag(self, dy):
        kind = self.suggestion.get("type", "memory")
        bg, fg = (TAG_MEM_BG, TAG_MEM_FG) if kind == "memory" else (TAG_MOB_BG, TAG_MOB_FG)
        label  = "Ejercicio mental ✨" if kind == "memory" else "Ejercicio físico 🌿"
        ts     = self.f_tag.render(label, True, fg)
        pad    = 18
        tw, th = ts.get_width() + pad*2, ts.get_height() + 12
        tx     = self.panel.x + 32
        ty     = self.panel.y + dy - th // 2
        tr     = pygame.Rect(tx, ty, tw, th)
        pygame.draw.rect(self.surface, bg, tr, border_radius=16)
        pygame.draw.rect(self.surface, fg, tr, 2, border_radius=16)
        self.surface.blit(ts, (tr.x + pad, tr.y + 6))

    def _draw_divider(self, dy):
        x = self.div_x
        pygame.draw.line(self.surface,
                         DIVIDER,
                         (x, self.panel.y + dy + 32),
                         (x, self.panel.bottom + dy - 32), 2)

    # ── ANIMACIONES (Se adaptan automáticamente al nuevo tamaño) ──────────────

    def _draw_animation(self, dy):
        cx = self.anim_cx
        cy = self.anim_cy + dy
        r  = self.anim_r

        pygame.draw.circle(self.surface, ANIM_CIRCLE_BG, (cx, cy), r)
        pygame.draw.circle(self.surface, ANIM_CIRCLE_BR, (cx, cy), r, 3)

        pulse_r = r + int(6 * math.sin(self._t * 2))
        s = pygame.Surface((pulse_r*2+4, pulse_r*2+4), pygame.SRCALPHA)
        pygame.draw.circle(s, (*ANIM_CIRCLE_BR, 60), (pulse_r+2, pulse_r+2), pulse_r, 3)
        self.surface.blit(s, (cx - pulse_r - 2, cy - pulse_r - 2))

        action = self.suggestion.get("action", "memory")
        title  = self.suggestion.get("title", "").lower()

        if action in ("memory", "wordsearch"):
            self._anim_brain(cx, cy, r)
        elif "cuello" in title:
            self._anim_neck(cx, cy, r)
        elif "respir" in title:
            self._anim_breath(cx, cy, r)
        elif "manos" in title:
            self._anim_hands(cx, cy, r)
        elif "levant" in title or "pasos" in title:
            self._anim_walk(cx, cy, r)
        else:
            self._anim_shoulders(cx, cy, r)

    def _figure(self, cx, cy, r, head_tilt=0.0):
        sc       = r / 80.0
        head_r   = int(22 * sc)
        body_h   = int(48 * sc)
        neck_h   = int(10 * sc)
        torso_top = cy + int(10 * sc)
        head_y   = torso_top - neck_h - head_r

        pygame.draw.rect(self.surface, ANIM_CLOTHES,
                         (cx - int(30 * sc), torso_top, int(30 * sc)*2, body_h), 0, 8)
        pygame.draw.rect(self.surface, ANIM_SKIN,
                         (cx - int(5*sc), torso_top - neck_h, int(10*sc), neck_h))
        
        ox = int(head_r * 0.7 * math.sin(head_tilt))
        pygame.draw.circle(self.surface, ANIM_SKIN, (cx + ox, head_y), head_r)
        pygame.draw.arc(self.surface, ANIM_HAIR,
                        (cx + ox - head_r, head_y - head_r, head_r*2, head_r+2),
                        0, math.pi, int(5*sc)+2)
        
        ey = head_y - int(4*sc)
        pygame.draw.circle(self.surface, (60, 38, 88), (cx + ox - int(8*sc), ey), max(3, int(3.5*sc)))
        pygame.draw.circle(self.surface, (60, 38, 88), (cx + ox + int(8*sc), ey), max(3, int(3.5*sc)))
        pygame.draw.circle(self.surface, WHITE, (cx + ox - int(6*sc), ey - int(2*sc)), max(1, int(1.5*sc)))
        pygame.draw.circle(self.surface, WHITE, (cx + ox + int(10*sc), ey - int(2*sc)), max(1, int(1.5*sc)))
        pygame.draw.arc(self.surface, ANIM_ACCENT,
                        (cx + ox - int(8*sc), head_y + int(2*sc), int(16*sc), int(10*sc)),
                        math.pi, 2*math.pi, max(2, int(2.5*sc)))
        return head_y, torso_top, body_h, sc

    def _anim_shoulders(self, cx, cy, r):
        head_y, torso_top, body_h, sc = self._figure(cx, cy, r)
        arm_len = int(42 * sc)
        shoulder_y = torso_top + int(10 * sc)
        tw = int(30 * sc)
        angle = math.sin(self._t * 2.2) * 0.65
        for side in (-1, 1):
            a  = angle * side
            sx = cx + side * tw
            ex = sx + side * int(arm_len * math.cos(a - math.pi/2 + 0.3))
            ey = shoulder_y + int(arm_len * math.sin(a - math.pi/2 + 0.3)) + int(22*sc)
            pygame.draw.line(self.surface, ANIM_SKIN, (sx, shoulder_y), (ex, ey), max(4, int(5*sc)))
            pygame.draw.circle(self.surface, ANIM_ACCENT, (ex, ey), max(4, int(5*sc)))
        for i in range(4):
            aa = self._t * 2.5 + i * math.pi / 2
            ax = cx + int((r*0.78) * math.cos(aa))
            ay = cy + int((r*0.78) * math.sin(aa))
            pygame.draw.circle(self.surface, ANIM_ACCENT, (ax, ay), max(3, int(4*sc)))

    def _anim_neck(self, cx, cy, r):
        tilt = math.sin(self._t * 1.4) * 0.42
        self._figure(cx, cy, r, head_tilt=tilt)
        sc  = r / 80.0
        head_r = int(22*sc)
        hy  = cy + int(10*sc) - int(10*sc) - head_r
        direction = 1 if tilt > 0 else -1
        ax  = cx + direction * int(r * 0.72)
        pygame.draw.line(self.surface, ANIM_ACCENT, (cx, hy), (ax, hy), 3)
        tip = ax + direction * 10
        pygame.draw.polygon(self.surface, ANIM_ACCENT, [
            (tip, hy), (tip - direction*10, hy - 6), (tip - direction*10, hy + 6)
        ])

    def _anim_breath(self, cx, cy, r):
        phase = (math.sin(self._t * 1.1) + 1) / 2
        self._figure(cx, cy, r)
        sc = r / 80.0
        torso_top = cy + int(10*sc)
        body_h    = int(48*sc)
        chest_cy  = torso_top + body_h // 2
        for i in range(4):
            wr    = int((r * 0.28 + i * r * 0.16) * (0.85 + phase * 0.18))
            alpha = int(190 * max(0, 1 - i * 0.28) * phase)
            ws = pygame.Surface((wr*2, wr*2), pygame.SRCALPHA)
            pygame.draw.circle(ws, (*ANIM_ACCENT, alpha), (wr, wr), wr, max(2, int(2.5*sc)))
            self.surface.blit(ws, (cx - wr, chest_cy - wr))
        pf = pygame.font.SysFont("Arial", max(18, int(20*sc)), bold=True)
        ps = pf.render(f"{int(phase*100)}%", True, TITLE_COL)
        self.surface.blit(ps, (cx - ps.get_width()//2, torso_top + body_h + int(8*sc)))

    def _anim_hands(self, cx, cy, r):
        open_f = (math.sin(self._t * 2.2) + 1) / 2
        sc = r / 80.0
        for side, hx in [(-1, cx - int(32*sc)), (1, cx + int(32*sc))]:
            hy   = cy + int(18*sc)
            pw   = int((24 + open_f * 8) * sc)
            ph   = int((20 + open_f * 6) * sc)
            pygame.draw.ellipse(self.surface, ANIM_SKIN, (hx-pw//2, hy-ph//2, pw, ph))
            for i in range(4):
                ba = -0.35 + i * 0.22
                oa = ba - open_f * 0.85
                fl = int(16*sc)
                fx = hx + side * int(fl * math.cos(oa))
                fy = hy - ph//2 - int(fl * abs(math.sin(oa)))
                pygame.draw.line(self.surface, ANIM_SKIN, (hx, hy - ph//2), (fx, fy), max(3, int(4*sc)))
                pygame.draw.circle(self.surface, ANIM_ACCENT, (fx, fy), max(2, int(3*sc)))
        cnt = int(self._t / (math.pi / 2.2)) % 11
        cf  = pygame.font.SysFont("Arial", max(20, int(22*sc)), bold=True)
        cs  = cf.render(str(cnt), True, TITLE_COL)
        self.surface.blit(cs, (cx - cs.get_width()//2, cy + int(48*sc)))

    def _anim_walk(self, cx, cy, r):
        step = math.sin(self._t * 2.8)
        sc   = r / 80.0
        head_y, torso_top, body_h, sc2 = self._figure(cx, cy - int(14*sc), r)
        hip_y   = torso_top + body_h
        leg_len = int(42 * sc)
        tw      = int(28 * sc)
        for side in (-1, 1):
            angle = step * side * 0.48
            kx    = cx + side * int(leg_len * 0.5 * math.sin(angle))
            ky    = hip_y + int(leg_len * 0.5 * math.cos(angle))
            fx    = kx + side * int(leg_len * 0.45 * math.sin(angle * 0.5))
            fy    = ky + int(leg_len * 0.48)
            pygame.draw.line(self.surface, ANIM_CLOTHES, (cx + side*int(8*sc), hip_y), (kx,ky), max(5,int(6*sc)))
            pygame.draw.line(self.surface, ANIM_SKIN,    (kx, ky), (fx, fy),            max(4,int(5*sc)))
            pygame.draw.ellipse(self.surface, ANIM_CLOTHES, (fx-int(9*sc), fy-int(4*sc), int(16*sc), int(8*sc)))
        arm_len = int(30*sc)
        for side in (-1, 1):
            angle = step * side * -0.38
            ex = cx + side * int(arm_len * math.sin(angle + 0.8))
            ey = torso_top + int(14*sc) + int(arm_len * math.cos(angle + 0.8))
            pygame.draw.line(self.surface, ANIM_SKIN, (cx + side*tw, torso_top + int(8*sc)), (ex,ey), max(4,int(5*sc)))
        steps = int(self._t / math.pi) % 11
        sf    = pygame.font.SysFont("Arial", max(18, int(19*sc)), bold=True)
        ss    = sf.render(f"{steps} pasos", True, TITLE_COL)
        self.surface.blit(ss, (cx - ss.get_width()//2, hip_y + int(44*sc)))

    def _anim_brain(self, cx, cy, r):
        pulse = 1.0 + 0.09 * math.sin(self._t * 2.2)
        br    = int(r * 0.52 * pulse)
        for dx, dy2, rx, ry in [
            (-br//4, int(br*0.05), int(br*1.02), int(br*0.88)),
            ( br//4, int(br*0.05), int(br*1.02), int(br*0.88)),
            (-br//3, -int(br*0.3), int(br*0.72), int(br*0.62)),
            ( br//3, -int(br*0.3), int(br*0.72), int(br*0.62)),
        ]:
            s = pygame.Surface((rx*2, ry*2), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*ANIM_CLOTHES, 190), (0, 0, rx*2, ry*2))
            self.surface.blit(s, (cx+dx-rx, cy+dy2-ry))
        for i in range(6):
            a  = self._t * 1.8 + i * math.tau / 6
            nx = cx + int(br * 0.62 * math.cos(a))
            ny = cy + int(br * 0.62 * math.sin(a))
            sp = int(4 + 3 * math.sin(self._t * 3.5 + i))
            pygame.draw.circle(self.surface, ANIM_ACCENT, (nx, ny), sp)
        qf = pygame.font.SysFont("Arial", int(36 * pulse), bold=True)
        qs = qf.render("?", True, WHITE)
        self.surface.blit(qs, (cx - qs.get_width()//2, cy - qs.get_height()//2))

    # ── Textos ────────────────────────────────────────────────────────────────

    def _draw_texts(self, dy):
        tx  = self.txt_x
        ty  = self.txt_y + dy
        tw  = self.txt_w
        btn_y = self.btn_yes.y + dy

        # Límite inferior dinámico antes de los botones
        available_h = btn_y - ty - 32

        # Título
        title = self.suggestion["title"]
        f_title = self.f_title
        ts = f_title.render(title, True, TITLE_COL)
        
        # Ajuste dinámico por seguridad si el título es larguísimo
        if ts.get_width() > tw:
            f_title = pygame.font.SysFont("Arial", 34, bold=True)
            ts = f_title.render(title, True, TITLE_COL)
            
        ttx = tx + (tw - ts.get_width()) // 2
        sh  = f_title.render(title, True, SHADOW_COL)
        self.surface.blit(sh, (ttx + 2, ty + 2))
        self.surface.blit(ts, (ttx, ty))

        # Línea decorativa intermedia (más ancha y vistosa)
        line_y = ty + ts.get_height() + 14
        llen   = min(tw - 40, 320)
        lx     = tx + (tw - llen) // 2
        pygame.draw.line(self.surface, PANEL_BORDER, (lx, line_y), (lx + llen, line_y), 3)

        # Cuerpo del mensaje
        lines   = [l.strip() for l in self.suggestion["body"].split("\n") if l.strip()]
        f_body  = self.f_body
        line_h  = f_body.get_height() + 12  # Más espacio entre líneas
        total_h = len(lines) * line_h
        
        # Centrado vertical refinado en el espacio libre
        body_start = line_y + 24 + max(0, (available_h - ts.get_height() - 36 - total_h) // 2)

        for i, line in enumerate(lines):
            ls  = f_body.render(line, True, BODY_COL)
            lx2 = tx + (tw - ls.get_width()) // 2  # Centrado horizontal perfecto por línea
            self.surface.blit(ls, (lx2, body_start + i * line_h))

    # ── Botones ───────────────────────────────────────────────────────────────

    def _draw_buttons(self, dy):
        self._btn(self._shifted(self.btn_yes, dy), "Vamos! 🙌",   BTN_YES_BG, BTN_YES_BORDER, BTN_YES_TEXT)
        self._btn(self._shifted(self.btn_no,  dy), "Ahora no",    BTN_NO_BG,  BTN_NO_BORDER,  BTN_NO_TEXT)

    def _btn(self, rect, text, bg, border, txt_color):
        # Sombra pronunciada
        sr = rect.move(5, 6)
        pygame.draw.rect(self.surface, SHADOW_COL, sr, border_radius=26)
        # Cuerpo
        pygame.draw.rect(self.surface, bg, rect, border_radius=26)
        # Borde grueso
        pygame.draw.rect(self.surface, border, rect, 3, border_radius=26)
        # Efecto brillo superior (glossy cute)
        shine_h = rect.height // 3
        ss = pygame.Surface((rect.width - 16, shine_h), pygame.SRCALPHA)
        ss.fill((255, 255, 255, 65))
        self.surface.blit(ss, (rect.x + 8, rect.y + 6))
        # Texto gigante centrado
        ts = self.f_btn.render(text, True, txt_color)
        self.surface.blit(ts, (
            rect.x + (rect.width  - ts.get_width())  // 2,
            rect.y + (rect.height - ts.get_height()) // 2,
        ))

