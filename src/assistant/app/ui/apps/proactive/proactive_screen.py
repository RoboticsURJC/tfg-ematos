"""
@file proactive_screen.py
@brief Pantalla proactiva — SOLUCIÓN ABSOLUTA: Renderizado dinámico basado en la superficie real.
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

    def __init__(self, suggestion, controller=None, on_accept=None, on_dismiss=None,
                 width=1024, height=600):
        super().__init__(controller, width, height)
        self.suggestion = suggestion
        self.on_accept  = on_accept
        self.on_dismiss = on_dismiss
        self._t         = 0.0
        self._appear    = 0.0
        self._dismissed = False
        
        # Inicialización de fuentes masivas y legibles
        self.f_tag   = pygame.font.SysFont("Arial", 28, bold=True)
        self.f_title = pygame.font.SysFont("Arial", 64, bold=True)  
        self.f_body  = pygame.font.SysFont("Arial", 42, bold=True)  
        self.f_btn   = pygame.font.SysFont("Arial", 40, bold=True)  

        # Inicializamos los rectángulos vacíos; se calcularán dinámicamente en caliente
        self.btn_yes = pygame.Rect(0, 0, 0, 0)
        self.btn_no  = pygame.Rect(0, 0, 0, 0)

        logger.info(f"[PROACTIVE SCREEN] {suggestion['title']}")
        self.start()

    def update_logic(self):
        self._appear = min(self._appear + 0.08, 1.0)
        self._t += 0.04

    def mousePressEvent(self, event):
        if self._dismissed:
            return
        
        # Mapeo de coordenadas basado en la geometría de la ejecución actual
        pos = self._qt_to_game_pos((event.x(), event.y()))

        # Forzamos una actualización de colisión con los rectángulos reales calculados en el render
        if self.btn_yes.collidepoint(pos):
            self._dismissed = True
            logger.info(f"[PROACTIVE] Aceptado → {self.suggestion['action']}")
            if self.controller:
                self.controller.on_proactive_dismissed()
            if self.on_accept:
                self.on_accept(self.suggestion["action"])

        elif self.btn_no.collidepoint(pos):
            self._dismissed = True
            logger.info("[PROACTIVE] Descartado")
            if self.controller:
                self.controller.on_proactive_dismissed()
            if self.on_dismiss:
                self.on_dismiss()

    # ── RENDER Y RE-CÁLCULO GEOMÉTRICO EN TIEMPO REAL ─────────────────────────

    def render(self):
        # 1. Obtener dimensiones dinámicas reales de la superficie actual de Pygame
        rect_pantalla = self.surface.get_rect()
        W = rect_pantalla.width
        H = rect_pantalla.height

        # Si el tamaño devuelto es absurdo o no se ha inicializado el buffer, saltamos frame
        if W < 100 or H < 100:
            return

        # 2. Dibujar Fondo de gradiente estructurado
        self._draw_bg(W, H)
        
        if self._appear < 0.01:
            return

        # Efecto sutil de subida al aparecer (afecta a los textos superiores)
        dy = int((1.0 - self._appear) * 20)

        # 3. Distribución estricta de la Cascada Vertical
        # --- SECCIÓN SUPERIOR: Animación ---
        anim_cx = W // 2
        anim_cy = int(H * 0.23) + dy   # Posicionado proporcionalmente arriba
        anim_r  = 100
        
        self._draw_tag(dy)
        self._draw_animation(anim_cx, anim_cy, anim_r)

        # --- SECCIÓN CENTRAL: Textos (Título + Cuerpo envuelto) ---
        txt_y = anim_cy + anim_r + 25
        txt_w = W - 140
        
        # Título Centrado
        title = self.suggestion["title"].upper()
        ts_title = self.f_title.render(title, True, TITLE_COL)
        ttx = (W - ts_title.get_width()) // 2
        self.surface.blit(ts_title, (ttx, txt_y))

        # Línea divisoria centrada
        line_y = txt_y + ts_title.get_height() + 10
        llen = 550
        lx = (W - llen) // 2
        pygame.draw.line(self.surface, DIVIDER, (lx, line_y), (lx + llen, line_y), 4)

        # Párrafo explicativo centrado
        body_text = self.suggestion["body"]
        rendered_lines = self._render_wrapped_text(body_text, self.f_body, BODY_COL, txt_w)
        
        line_h = self.f_body.get_height() + 8
        body_start_y = line_y + 15

        for i, line_surface in enumerate(rendered_lines):
            lx2 = (W - line_surface.get_width()) // 2
            self.surface.blit(line_surface, (lx2, body_start_y + i * line_h))

        # --- SECCIÓN INFERIOR: Anclaje Matemático de Botones ---
        BW = 340
        BH = 90
        GAP = 60
        BOTTOM_MARGIN = 35
        
        # Posición Y fija pegada abajo del todo de la ventana real
        btn_y = H - BH - BOTTOM_MARGIN
        
        total_btn_width = (BW * 2) + GAP
        start_btn_x = (W - total_btn_width) // 2

        # Actualizamos las propiedades de la clase para que `mousePressEvent` use las mismas coordenadas
        self.btn_yes = pygame.Rect(start_btn_x, btn_y, BW, BH)
        self.btn_no  = pygame.Rect(start_btn_x + BW + GAP, btn_y, BW, BH)

        # Dibujamos físicamente los botones en su sitio final
        self._draw_buttons()

    # ── SUB-MÉTODOS DE DIBUJO CON AK-47 GEOMÉTRICO ───────────────────────────

    def _draw_bg(self, W, H):
        for y in range(H):
            t = y / H
            r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
            g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
            b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (W, y))

    def _draw_tag(self, dy):
        kind = self.suggestion.get("type", "memory")
        bg, fg = (TAG_MEM_BG, TAG_MEM_FG) if kind == "memory" else (TAG_MOB_BG, TAG_MOB_FG)
        label  = "Ejercicio mental ✨" if kind == "memory" else "Ejercicio físico 🌿"
        
        ts     = self.f_tag.render(label, True, fg)
        pad_x, pad_y = 18, 8
        tw, th = ts.get_width() + pad_x*2, ts.get_height() + pad_y*2
        
        tr     = pygame.Rect(35, 25 + dy, tw, th)
        pygame.draw.rect(self.surface, bg, tr, border_radius=15)
        pygame.draw.rect(self.surface, fg, tr, 2, border_radius=15)
        self.surface.blit(ts, (tr.x + pad_x, tr.y + pad_y))

    def _render_wrapped_text(self, text, font, color, max_width):
        paragraphs = text.split('\n')
        lines = []
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph: continue
            words = paragraph.split(' ')
            current_line = []
            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))
        return [font.render(line, True, color) for line in lines]

    def _draw_animation(self, cx, cy, r):
        pygame.draw.circle(self.surface, ANIM_CIRCLE_BG, (cx, cy), r)
        pygame.draw.circle(self.surface, ANIM_CIRCLE_BR, (cx, cy), r, 5)

        pulse_r = r + int(6 * math.sin(self._t * 2.5))
        s = pygame.Surface((pulse_r*2+6, pulse_r*2+6), pygame.SRCALPHA)
        pygame.draw.circle(s, (*ANIM_CIRCLE_BR, 40), (pulse_r+3, pulse_r+3), pulse_r, 4)
        self.surface.blit(s, (cx - pulse_r - 3, cy - pulse_r - 3))

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
        sc       = r / 85.0 
        head_r   = int(24 * sc)
        body_h   = int(52 * sc)
        neck_h   = int(12 * sc)
        torso_top = cy + int(15 * sc)
        head_y   = torso_top - neck_h - head_r

        pygame.draw.rect(self.surface, ANIM_CLOTHES, (cx - int(35 * sc), torso_top, int(35 * sc)*2, body_h), 0, 10)
        pygame.draw.rect(self.surface, ANIM_SKIN, (cx - int(6*sc), torso_top - neck_h, int(12*sc), neck_h))

        ox = int(head_r * 0.7 * math.sin(head_tilt))
        pygame.draw.circle(self.surface, ANIM_SKIN, (cx + ox, head_y), head_r)
        pygame.draw.arc(self.surface, ANIM_HAIR, (cx + ox - head_r, head_y - head_r, head_r*2, head_r+3), 0, math.pi, int(6*sc)+3)

        ey = head_y - int(5*sc)
        pygame.draw.circle(self.surface, (50, 30, 80), (cx + ox - int(9*sc), ey), max(4, int(4*sc)))
        pygame.draw.circle(self.surface, (50, 30, 80), (cx + ox + int(9*sc), ey), max(4, int(4*sc)))
        
        pygame.draw.arc(self.surface, ANIM_ACCENT, (cx + ox - int(10*sc), head_y + int(3*sc), int(20*sc), int(12*sc)), math.pi, 2*math.pi, max(3, int(3*sc)))
        return head_y, torso_top, body_h, sc

    def _anim_shoulders(self, cx, cy, r):
        head_y, torso_top, body_h, sc = self._figure(cx, cy, r)
        arm_len = int(50 * sc)
        shoulder_y = torso_top + int(12 * sc)
        tw = int(35 * sc)
        angle = math.sin(self._t * 2.5) * 0.7
        for side in (-1, 1):
            a  = angle * side
            sx = cx + side * tw
            ex = sx + side * int(arm_len * math.cos(a - math.pi/2 + 0.3))
            ey = shoulder_y + int(arm_len * math.sin(a - math.pi/2 + 0.3)) + int(25*sc)
            pygame.draw.line(self.surface, ANIM_SKIN, (sx, shoulder_y), (ex, ey), max(5, int(6*sc)))
            pygame.draw.circle(self.surface, ANIM_ACCENT, (ex, ey), max(5, int(6*sc)))

    def _anim_neck(self, cx, cy, r):
        tilt = math.sin(self._t * 1.5) * 0.5
        self._figure(cx, cy, r, head_tilt=tilt)
        sc = r / 85.0
        head_r = int(24*sc)
        hy  = cy + int(15*sc) - int(12*sc) - head_r
        direction = 1 if tilt > 0 else -1
        ax  = cx + direction * int(r * 0.75)
        pygame.draw.line(self.surface, ANIM_ACCENT, (cx, hy), (ax, hy), 4)

    def _anim_breath(self, cx, cy, r):
        phase = (math.sin(self._t * 1.2) + 1) / 2
        self._figure(cx, cy, r)
        sc = r / 85.0
        torso_top, body_h = cy + int(15*sc), int(55*sc)
        chest_cy  = torso_top + body_h // 2
        for i in range(3):
            wr    = int((r * 0.3 + i * r * 0.18) * (0.85 + phase * 0.2))
            alpha = int(180 * max(0, 1 - i * 0.35) * phase)
            ws = pygame.Surface((wr*2, wr*2), pygame.SRCALPHA)
            pygame.draw.circle(ws, (*ANIM_ACCENT, alpha), (wr, wr), wr, max(3, int(3*sc)))
            self.surface.blit(ws, (cx - wr, chest_cy - wr))

    def _anim_hands(self, cx, cy, r):
        open_f = (math.sin(self._t * 2.5) + 1) / 2
        sc = r / 85.0
        for side, hx in [(-1, cx - int(38*sc)), (1, cx + int(38*sc))]:
            hy   = cy + int(22*sc)
            pw, ph = int((28 + open_f * 10) * sc), int((24 + open_f * 8) * sc)
            pygame.draw.ellipse(self.surface, ANIM_SKIN, (hx-pw//2, hy-ph//2, pw, ph))
        cnt = int(self._t / (math.pi / 2.5)) % 11
        cf  = pygame.font.SysFont("Arial", max(24, int(26*sc)), bold=True)
        cs  = cf.render(str(cnt), True, TITLE_COL)
        self.surface.blit(cs, (cx - cs.get_width()//2, cy + int(50*sc)))

    def _anim_walk(self, cx, cy, r):
        step = math.sin(self._t * 3.0)
        sc   = r / 85.0
        head_y, torso_top, body_h, sc2 = self._figure(cx, cy - int(14*sc), r)
        hip_y, leg_len = torso_top + body_h, int(45 * sc)
        for side in (-1, 1):
            angle = step * side * 0.5
            kx    = cx + side * int(leg_len * 0.5 * math.sin(angle))
            ky    = hip_y + int(leg_len * 0.5 * math.cos(angle))
            fx    = kx + side * int(leg_len * 0.45 * math.sin(angle * 0.5))
            fy    = ky + int(leg_len * 0.5)
            pygame.draw.line(self.surface, ANIM_CLOTHES, (cx + side*int(10*sc), hip_y), (kx,ky), max(6,int(7*sc)))
            pygame.draw.line(self.surface, ANIM_SKIN,    (kx, ky), (fx, fy),            max(5,int(6*sc)))

    def _anim_brain(self, cx, cy, r):
        pulse = 1.0 + 0.1 * math.sin(self._t * 2.5)
        br    = int(r * 0.52 * pulse)
        for dx, dy2, rx, ry in [
            (-br//4, int(br*0.05), int(br*1.05), int(br*0.9)),
            ( br//4, int(br*0.05), int(br*1.05), int(br*0.9)),
        ]:
            s = pygame.Surface((rx*2, ry*2), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (*ANIM_CLOTHES, 200), (0, 0, rx*2, ry*2))
            self.surface.blit(s, (cx+dx-rx, cy+dy2-ry))
        qf = pygame.font.SysFont("Arial", int(44 * pulse), bold=True)
        qs = qf.render("?", True, WHITE)
        self.surface.blit(qs, (cx - qs.get_width()//2, cy - qs.get_height()//2))

    def _draw_buttons(self):
        self._btn(self.btn_yes, "VAMOS! 🙌", BTN_YES_BG, BTN_YES_BORDER, BTN_YES_TEXT)
        self._btn(self.btn_no,  "AHORA NO",  BTN_NO_BG,  BTN_NO_BORDER,  BTN_NO_TEXT)

    def _btn(self, rect, text, bg, border, txt_color):
        sr = rect.move(6, 6)
        pygame.draw.rect(self.surface, SHADOW_COL, sr, border_radius=28)
        
        pygame.draw.rect(self.surface, bg, rect, border_radius=28)
        pygame.draw.rect(self.surface, border, rect, 4, border_radius=28)
        
        shine_h = rect.height // 3
        ss = pygame.Surface((rect.width - 20, shine_h), pygame.SRCALPHA)
        ss.fill((255, 255, 255, 60))
        self.surface.blit(ss, (rect.x + 10, rect.y + 6))
        
        ts = self.f_btn.render(text, True, txt_color)
        tx = rect.x + (rect.width - ts.get_width()) // 2
        ty = rect.y + (rect.height - ts.get_height()) // 2
        self.surface.blit(ts, (tx, ty))
