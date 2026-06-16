# app/ui/apps/games/simon_says/simon_says_screen.py

"""
@file simon_says_screen.py
@brief Pantalla y motor del minijuego de secuenciación cognitiva Simón Dice basado en Pygame y Qt.
@details Diseñado específicamente con criterios de accesibilidad cognitiva para personas mayores. 
Implementa cálculo geométrico dinámico de layouts ortogonales, tipografías autoajustables 
y síntesis matemática de ondas senoidales en estéreo para evitar la dependencia de assets en disco.
"""

import pygame
import random
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# =========================================================================
# PALETA DE COLORES RGB (CRITERIOS DE ALTO CONTRASTE)
# =========================================================================
P_BG_TOP       = (248, 242, 255)  ##< Tono RGB superior para el gradiente de fondo (Paleta pastel).
P_BG_BOTTOM    = (232, 238, 255)  ##< Tono RGB inferior para el gradiente de fondo.
P_TITLE        = (110,  20, 130)  ##< Color dominante de alta saturación para títulos.
P_SUBTITLE     = ( 90,  50, 140)  ##< Color para subtítulos y guías textuales secundarias.
P_SHADOW       = (195, 178, 215)  ##< Tono de sombreado plano (Drop-shadow flat) para emular relieve físico táctil.
P_PANEL_BORDER = (205, 185, 232)  ##< Color de las líneas divisorias de los paneles del HUD.
P_BTN_TEXT     = ( 50,  18,  70)  ##< Color del texto interno de los botones para máxima legibilidad.
P_BACK_BG      = (185, 205, 255)  ##< Color de fondo para el control interactivo de retorno.

## Estructura estática de configuración cromática y de frecuencia de audio para los inductores circulares.
SIMON_BUTTONS = [
    {"id": 0, "name": "VERDE",    "normal": ( 62, 158,  86), "lit": (118, 238, 145), "freq": 392}, # G4 (Sol)
    {"id": 1, "name": "ROJO",     "normal": (198,  60,  60), "lit": (255, 125, 125), "freq": 330}, # E4 (Mi)
    {"id": 2, "name": "AZUL",     "normal": ( 60, 108, 198), "lit": (125, 182, 255), "freq": 262}, # C4 (Do)
    {"id": 3, "name": "AMARILLO", "normal": (188, 162,  38), "lit": (255, 228,  85), "freq": 494}, # B4 (Si)
]

## Diccionario paramétrico de tiempos e hitos de victoria indexados por dificultad.
DIFFICULTY = {
    "facil":   {"max_len":  6, "show_ms": 650, "pause_ms": 300},
    "medio":   {"max_len": 10, "show_ms": 480, "pause_ms": 220},
    "dificil": {"max_len": 15, "show_ms": 320, "pause_ms": 150},
}

READY_PAUSE_SEC = 0.3  ##< Constante de tiempo de espera (segundos) antes de reproducir la secuencia.


def _fit_font(text, max_w, max_h, bold=True):
    """
    @brief Algoritmo iterativo de aproximación por convergencia para ajustar el tamaño de fuente.
    @details Realiza una búsqueda lineal descendente garantizando que el texto renderizado 
    quepa estrictamente dentro de los límites físicos (bounding box) horizontales y verticales.
    
    @param text Cadena de caracteres a medir.
    @param max_w Ancho máximo disponible en píxeles.
    @param max_h Alto máximo disponible en píxeles.
    @param bold Bandera lógica para habilitar el estilo de tipografía en negrita.
    @return pygame.font.Font Instancia tipográfica optimizada para las dimensiones dadas.
    """
    size = int(max_h * 0.90)
    while size > 8:
        f = pygame.font.SysFont("Arial", size, bold=bold)
        if f.size(text)[0] <= max_w and f.get_height() <= max_h:
            return f
        size -= 2
    return pygame.font.SysFont("Arial", 8, bold=bold)


class SimonSaysScreen(BasePygameQtScreen):
    """
    @brief Pantalla interactiva del juego Simón Dice con optimizaciones ergonómicas para adultos mayores.
    """

    HEADER_H = 120   ##< Altura en píxeles reservada para el panel superior de datos e instrucciones.
    FOOTER_H =  68   ##< Altura en píxeles del HUD inferior de navegación.
    LABEL_H  = 110   ##< Altura de la franja central empleada para el refuerzo visual del nombre del color en texto.

    def __init__(self, controller=None, width=1024, height=600):
        """
        @brief Constructor de la clase SimonSaysScreen.
        @details Inicializa la máquina de estados lógicos y define los contenedores de colisión geométrica.
        
        @param controller Instancia del enrutador o máquina de control de interfaces de la app.
        @param width Dimensión horizontal por defecto del lienzo de dibujo.
        @param height Dimensión vertical por defecto del lienzo de dibujo.
        """
        super().__init__(controller, width, height)
        logger.info("[SIMON] Inicializando pantalla del Simón Dice.")

        self.state      = "menu"       ##< Máquina de estados lógicos principal ("menu" | "showing" | "waiting" | "correct" | "wrong" | "win").
        self.difficulty = "facil"      ##< Clave identificadora de dificultad activa.

        self.sequence     = []         ##< Vector de enteros `[0-3]` que almacena la secuencia de colores de la ronda actual.
        self.player_index = 0          ##< Puntero de control del paso de la secuencia que está ingresando el usuario.
        self.show_index   = 0          ##< Puntero del paso que está siendo reproducido por el motor en modo "showing".
        self.lit_button   = None       ##< Índice entero del botón actualmente activo/iluminado en pantalla (None si están todos apagados).

        self.score  = 0                ##< Puntuación de la ronda actual (basada en la longitud de la secuencia).
        self.record = 0                ##< Mejor marca histórica registrada en la sesión de juego.

        self._phase      = "ready"     ##< Estado transitorio del reloj interno de reproducción ("ready" | "on" | "off").
        self._show_timer = 0.0         ##< Acumulador temporal para sincronizar los tiempos de encendido y apagado de luces.

        self._feedback_timer = 0.0     ##< Temporizador residual para sostener las pantallas superpuestas (overlays) de acierto/error.
        self.FEEDBACK_DUR    = 1.5     ##< Duración estática en segundos de las animaciones de retroalimentación.

        self._pulse     = 0.0          ##< Factor normalizado de interpolación `[0.0, 1.0]` para la animación de pulsación de acierto.
        self._pulse_dir = 1            ##< Dirección matemática del pulso (1 ascendente, -1 descendente).

        self._sounds        = {}       ##< Diccionario que indexa las muestras de sonido dinámicas generadas (`{id: Sound}`).
        self._sounds_loaded = False    ##< Estado del subsistema de síntesis matemática de sonido de la pantalla.

        self._circle_centers = []      ##< Colección de tuplas `(x, y)` con el baricentro geométrico calculado para los 4 botones circulares.
        self._circle_r       = 0       ##< Radio óptimo calculado en píxeles para los botones circulares de juego.
        self._layout_done    = False   ##< Control de estado de resolución de las coordenadas físicas del lienzo.

        # Inicialización por defecto de las cajas de colisión táctil
        self.btn_easy   = pygame.Rect(0, 0, 1, 1)
        self.btn_medium = pygame.Rect(0, 0, 1, 1)
        self.btn_hard   = pygame.Rect(0, 0, 1, 1)
        self.btn_exit   = pygame.Rect(0, 0, 1, 1)
        self.btn_back   = pygame.Rect(0, 0, 1, 1)

    def exit_game(self):
        """
        @brief Cierra de forma ordenada el sub-entorno de ejecución de Pygame y retorna al launcher de Qt.
        """
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    # =========================================================================
    # SUBSISTEMA DE SÍNTESIS DE AUDIO (SIN ASSETS EN DISCO)
    # =========================================================================
    def _init_sounds(self):
        """
        @brief Sintetiza matemáticamente ondas senoidales e inicializa el subsistema de sonido.
        @details **Resiliencia de ejecución:** Utiliza transformaciones de matrices y envolventes 
        exponenciales decrecientes por software a través de NumPy. Si las librerías científicas o el
        hardware del controlador de sonido están ausentes, intercepta la excepción para evitar un fallo crítico (crash).
        """
        if self._sounds_loaded:
            return
        try:
            import numpy as np
            sr = 44100
            t  = np.linspace(0, 0.4, int(sr * 0.4), endpoint=False)
            
            # Síntesis matemática de las frecuencias de los colores
            for btn in SIMON_BUTTONS:
                wave   = np.sin(2 * math.pi * btn["freq"] * t)
                fade   = np.linspace(1.0, 0.0, len(t)) ** 2  # Envolvente parabólica de atenuación
                stereo = np.column_stack([(wave * fade * 24000).astype(np.int16)] * 2)
                self._sounds[btn["id"]] = pygame.sndarray.make_sound(stereo)
            
            # Síntesis matemática del ruido blanco (Frecuencia de Error / Zumbido)
            noise  = np.random.randint(-6000, 6000, int(sr * 0.45), dtype=np.int16)
            env    = np.linspace(1.0, 0.0, len(noise)) ** 1.5
            stereo = np.column_stack([(noise * env).astype(np.int16)] * 2)
            self._sounds["wrong"] = pygame.sndarray.make_sound(stereo)
            
            self._sounds_loaded = True
        except Exception as e:
            logger.warning(f"[SIMON] El subsistema de sonido no está disponible en este hardware: {e}")

    def _play_sound(self, key):
        """
        @brief Lanza de forma asíncrona la reproducción del búfer de sonido indexado.
        
        @param key Identificador único del recurso sonoro (`int` para colores | `str` para efectos).
        """
        s = self._sounds.get(key)
        if s:
            try: s.play()
            except Exception: pass

    # =========================================================================
    # ARITMÉTICA DE DISEÑO ADAPTATIVO (LAYOUT EN FILA)
    # =========================================================================
    def _calculate_layout(self):
        """
        @brief Distribuye espacialmente 4 inductores circulares idénticos alineados de forma horizontal.
        @details Calcula de forma dinámica el radio ideal óptimo y equidistante, aislando las zonas 
        sensibles reservadas para el Header, el subpanel textual y el Footer para mitigar solapamientos visuales.
        """
        W, H = self.game_width, self.game_height
        GAP  = 24  # Distancia de separación fija entre los bordes de los círculos

        NAME_BELOW = 38
        area_top = self.HEADER_H + self.LABEL_H
        area_bot = H - self.FOOTER_H - NAME_BELOW
        area_h   = area_bot - area_top
        area_w   = W - 80

        # Resolución matemática de la cota máxima del radio en función del espacio geométrico disponible
        r_by_w = (area_w - GAP * 3) // 8
        r_by_h = area_h // 2
        r = max(min(r_by_w, r_by_h, 105), 52)

        total_w = 4 * (r * 2) + 3 * GAP
        start_x = (W - total_w) // 2 + r
        cy = area_top + area_h // 2

        # Inyección de coordenadas absolutas en el vector de centros
        self._circle_centers = [
            (start_x + i * (r * 2 + GAP), cy) for i in range(4)
        ]
        self._circle_r    = r
        self._layout_done = True
        logger.info(f"[SIMON] Rejilla resuelta de forma adaptativa: r={r}, eje_y={cy}")

    # =========================================================================
    # FLUJO INTERNO Y MÁQUINA DE ESTADOS
    # =========================================================================
    def start_game(self, difficulty: str):
        """
        @brief Inicializa los parámetros de control e inicia una nueva partida.
        
        @param difficulty Cadena de texto que configura la velocidad del temporizador del juego.
        """
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

    def _add_to_sequence(self):
        """
        @brief Añade un nuevo índice aleatorio `[0-3]` a la secuencia para subir el nivel.
        """
        self.sequence.append(random.randint(0, 3))
        self.score = len(self.sequence)

    def _start_showing(self):
        """
        @brief Configura las variables para iniciar la reproducción automática de colores.
        """
        self.show_index   = 0
        self.player_index = 0
        self.lit_button   = None
        self._show_timer  = 0.0
        self._phase       = "ready"

    def update_logic(self):
        """
        @brief Motor cíclico principal para la resolución de tiempos y animaciones por interpolación.
        @details Controla de forma no bloqueante el paso del tiempo entre destellos y el desvanecimiento 
        de las transiciones de las pantallas superpuestas (overlays) de respuesta.
        """
        dt = 1.0 / 60.0  # Delta time teórico basado en el refresco objetivo de la pantalla

        if self.state == "showing":
            self._update_showing(dt)

        elif self.state in ("correct", "wrong"):
            self._feedback_timer -= dt
            
            # Oscilación armónica de la opacidad del color verde durante el estado correcto
            if self.state == "correct":
                self._pulse += self._pulse_dir * dt * 3
                if   self._pulse >= 1.0: self._pulse, self._pulse_dir = 1.0, -1
                elif self._pulse <= 0.0: self._pulse, self._pulse_dir = 0.0,  1
                
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
                    self.lit_button = None
                    self.state = "menu"

    def _update_showing(self, dt):
        """
        @brief Máquina de estados secundaria que gestiona el ritmo de parpadeo de los colores.
        
        @param dt Fracción de tiempo transcurrido (Delta Time).
        """
        cfg      = DIFFICULTY[self.difficulty]
        show_s   = cfg["show_ms"]  / 1000.0
        pause_s  = cfg["pause_ms"] / 1000.0
        self._show_timer += dt

        if self._phase == "ready":
            if self._show_timer >= READY_PAUSE_SEC:
                self._show_timer = 0.0
                self._phase      = "off"

        elif self._phase == "off":
            if self._show_timer >= pause_s:
                if self.show_index >= len(self.sequence):
                    self.lit_button = None
                    self.state      = "waiting"  # Cede el turno al jugador humano
                    return
                self.lit_button  = self.sequence[self.show_index]
                self._show_timer = 0.0
                self._phase      = "on"
                self._play_sound(self.lit_button)

        elif self._phase == "on":
            if self._show_timer >= show_s:
                self.show_index  += 1
                self.lit_button   = None
                self._show_timer  = 0.0
                self._phase       = "off"

    # =========================================================================
    # CAPTURA Y PROCESAMIENTO DE ENTRADAS TÁCTILES
    # =========================================================================
    def mousePressEvent(self, event):
        """
        @brief Enrutador nativo de la capa de eventos de Qt transformados al entorno físico de Pygame.
        
        @param event Instancia del evento nativo de tipo QMouseEvent.
        """
        pos = self._qt_to_game_pos((event.x(), event.y()))

        if self.state == "menu":
            if   self.btn_easy.collidepoint(pos):   self.start_game("facil")
            elif self.btn_medium.collidepoint(pos):  self.start_game("medio")
            elif self.btn_hard.collidepoint(pos):    self.start_game("dificil")
            elif self.btn_exit.collidepoint(pos):    self.exit_game()

        elif self.state == "waiting":
            if self.btn_back.collidepoint(pos):
                self.lit_button = None; self.state = "menu"; return
            self._handle_press(pos)

        elif self.state in ("showing", "win"):
            if self.btn_back.collidepoint(pos):
                self.lit_button = None; self.state = "menu"

    def _handle_press(self, pos):
        """
        @brief Evalúa mediante cálculo analítico de distancias euclidianas la colisión radial de los clicks.
        @details Aplica un margen de tolerancia perimetral (+12 píxeles) para mitigar imprecisiones 
        asociadas a temblores o baja sensibilidad en pantallas táctiles resistivas/capacitivas.
        
        @param pos Tupla `(x, y)` posicional de entrada.
        """
        r = self._circle_r
        for i, (cx, cy) in enumerate(self._circle_centers):
            dx, dy = pos[0] - cx, pos[1] - cy
            # Evaluación del radio interno empleando la ecuación analítica de la circunferencia: x^2 + y^2 <= r^2
            if dx*dx + dy*dy <= (r + 12)**2:
                self.lit_button = i
                self._play_sound(i)
                
                # Validación de coincidencia con la secuencia almacenada
                if i == self.sequence[self.player_index]:
                    self.player_index += 1
                    if self.player_index >= len(self.sequence):
                        if len(self.sequence) > self.record:
                            self.record = len(self.sequence)
                        self.state           = "correct"
                        self._feedback_timer = self.FEEDBACK_DUR
                        self._pulse = 0.0; self._pulse_dir = 1
                else:
                    self._play_sound("wrong")
                    self.state           = "wrong"
                    self._feedback_timer = self.FEEDBACK_DUR
                break

    # =========================================================================
    # SISTEMA DE RENDICIÓN VISUAL (RENDER)
    # =========================================================================
    def render(self):
        """
        @brief Orquestador del ciclo de dibujo principal sobre la superficie gráfica activa.
        """
        if self.game_width < 100 or self.game_height < 100:
            return
        self._draw_bg()
        if self.state == "menu":
            self._draw_menu()
        elif self.state == "win":
            self._draw_win()
        else:
            self._draw_game()

    def _draw_bg(self):
        """
        @brief Renderiza el fondo de la pantalla aplicando un gradiente lineal de color vertical.
        """
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0]-P_BG_TOP[0])*t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1]-P_BG_TOP[1])*t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2]-P_BG_TOP[2])*t)
            pygame.draw.line(self.surface, (r,g,b), (0,y), (self.game_width,y))

    def _draw_menu(self):
        """
        @brief Dibuja la interfaz completa del Menú Principal, selectores de dificultad y récords.
        """
        W, H = self.game_width, self.game_height

        # Rótulo de título principal provisto de sombra proyectada (Drop-Shadow flat)
        f_t = _fit_font("SIMÓN DICE", W - 80, 88)
        ts  = f_t.render("SIMÓN DICE", True, P_TITLE)
        sh  = f_t.render("SIMÓN DICE", True, P_SHADOW)
        cx  = (W - ts.get_width()) // 2
        self.surface.blit(sh, (cx+4, 34))
        self.surface.blit(ts, (cx, 30))

        f_s  = _fit_font("Repite la secuencia de colores", W - 100, 36, bold=False)
        sub  = f_s.render("Repite la secuencia de colores", True, P_SUBTITLE)
        self.surface.blit(sub, ((W - sub.get_width())//2, 126))

        top_y = 174
        if self.record > 0:
            f_r = _fit_font(f"Mejor marca: {self.record} pasos", W-200, 30, bold=False)
            rs  = f_r.render(f"  Mejor marca: {self.record} pasos", True, P_TITLE)
            self.surface.blit(rs, ((W-rs.get_width())//2, top_y))
            top_y += 40

        CONFIGS = [
            ("facil",   "FÁCIL",   "hasta 6 pasos",  (140, 228, 168), ( 70, 168, 105)),
            ("medio",   "MEDIO",   "hasta 10 pasos", (255, 210, 108), (200, 150,  40)),
            ("dificil", "DIFÍCIL", "hasta 15 pasos", (255, 145, 160), (205,  80, 100)),
        ]
        BW  = min(W - 120, 440)
        BH  = 72
        GAP = 14
        bx  = (W - BW) // 2
        by  = top_y + 8

        # Dibujado iterativo de los botones de dificultad con relieves
        for key, label, desc, bg, bd in CONFIGS:
            rect = pygame.Rect(bx, by, BW, BH)
            if key == "facil":   self.btn_easy   = rect.copy()
            elif key == "medio": self.btn_medium  = rect.copy()
            else:                self.btn_hard    = rect.copy()

            pygame.draw.rect(self.surface, P_SHADOW, rect.move(4,4), border_radius=20)
            pygame.draw.rect(self.surface, bg,       rect,           border_radius=20)
            pygame.draw.rect(self.surface, bd,       rect, 3,        border_radius=20)

            f_l = _fit_font(label, BW//3 - 20, BH - 20)
            ls  = f_l.render(label, True, P_BTN_TEXT)
            self.surface.blit(ls, (rect.x+24, rect.y+(BH-ls.get_height())//2))

            f_d = _fit_font(desc, BW//2 - 20, BH-26, bold=False)
            ds  = f_d.render(desc, True, P_BTN_TEXT)
            self.surface.blit(ds, (rect.right-ds.get_width()-24, rect.y+(BH-ds.get_height())//2))
            by += BH + GAP

        # Botón volver al lanzador
        EW, EH = 210, 54
        self.btn_exit = pygame.Rect((W-EW)//2, H-EH-20, EW, EH)
        pygame.draw.rect(self.surface, P_SHADOW,  self.btn_exit.move(3,3), border_radius=16)
        pygame.draw.rect(self.surface, P_BACK_BG, self.btn_exit,           border_radius=16)
        f_e = _fit_font("VOLVER", EW-28, EH-16)
        es  = f_e.render("VOLVER", True, P_BTN_TEXT)
        self.surface.blit(es, (self.btn_exit.x+(EW-es.get_width())//2, self.btn_exit.y+(EH-es.get_height())//2))

    def _draw_game(self):
        """
        @brief Renderiza el escenario de juego activo orquestando la composición de capas.
        """
        self._draw_header()
        self._draw_color_label()
        self._draw_circles()
        self._draw_footer()
        if self.state in ("correct", "wrong"):
            self._draw_feedback_overlay()

    def _draw_header(self):
        """
        @brief Compone el panel superior (HUD informativo) de control de la partida.
        """
        W  = self.game_width
        HH = self.HEADER_H

        bar = pygame.Surface((W, HH), pygame.SRCALPHA)
        bar.fill((250, 244, 255, 200))
        self.surface.blit(bar, (0, 0))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, HH), (W, HH), 2)

        f_lv = _fit_font(f"Nivel {self.score}", W // 3, HH - 30)
        lv   = f_lv.render(f"Nivel {self.score}", True, P_TITLE)
        self.surface.blit(lv, (22, (HH - lv.get_height()) // 2))

        if self.record > 0:
            f_r = _fit_font(f"Mejor: {self.record}", W // 4, 26, bold=False)
            rs  = f_r.render(f"Mejor: {self.record}", True, P_SUBTITLE)
            self.surface.blit(rs, (W - rs.get_width() - 18, 10))

        msgs = {
            "showing": "Mira con atención...",
            "waiting": f"Tu turno  —  paso {self.player_index + 1} de {len(self.sequence)}",
            "correct": "¡Muy bien!",
            "wrong":   "¡Ese no era!",
        }
        msg   = msgs.get(self.state, "")
        color = (50, 155, 70)  if self.state == "correct" else \
                (180, 40, 40) if self.state == "wrong"   else P_SUBTITLE
        
        f_msg = _fit_font(msg, W - 60, HH - 24)
        ms    = f_msg.render(msg, True, color)
        self.surface.blit(ms, (W // 2 - ms.get_width() // 2, (HH - ms.get_height()) // 2))

    def _draw_color_label(self):
        """
        @brief Refuerzo cognitivo textual. Renderiza el nombre del color activo en letras gigantes.
        @details Proporciona una vía secundaria de discriminación a usuarios con daltonismo o fatiga visual.
        """
        W = self.game_width
        y0 = self.HEADER_H
        h  = self.LABEL_H

        if self.state == "showing":
            if self.lit_button is not None:
                btn   = SIMON_BUTTONS[self.lit_button]
                text  = btn["name"]
                color = btn["lit"]
                
                # Renderiza una banda horizontal translúcida con la tonalidad del color
                bg_surf = pygame.Surface((W, h), pygame.SRCALPHA)
                r, g, b = btn["normal"]
                bg_surf.fill((r, g, b, 38))
                self.surface.blit(bg_surf, (0, y0))
            else:
                text  = "· · ·"
                color = P_PANEL_BORDER

            f    = _fit_font(text, W - 60, h - 16)
            sh   = f.render(text, True, P_SHADOW)
            surf = f.render(text, True, color)
            cx   = W // 2 - surf.get_width() // 2
            cy   = y0 + (h - surf.get_height()) // 2
            self.surface.blit(sh,   (cx + 3, cy + 3))
            self.surface.blit(surf, (cx,     cy))

        elif self.state == "waiting":
            paso = f"Paso {self.player_index + 1} de {len(self.sequence)}"
            f    = _fit_font(paso, W - 120, h - 40, bold=False)
            surf = f.render(paso, True, P_SUBTITLE)
            self.surface.blit(surf, (W // 2 - surf.get_width() // 2, y0 + (h - surf.get_height()) // 2))

    def _draw_circles(self):
        """
        @brief Genera y dibuja los círculos interactivos en sus respectivas posiciones calculadas.
        @details Aplica efectos tridimensionales mediante sombreado alfa simulado y destellos de
        arco superiores para realzar el estado luminoso ("lit") de los componentes.
        """
        if not self._layout_done:
            return

        r = self._circle_r

        for i, (cx, cy) in enumerate(self._circle_centers):
            btn    = SIMON_BUTTONS[i]
            is_lit = (self.lit_button == i)
            color  = btn["lit"] if is_lit else btn["normal"]

            # Capa 1: Renderizado de la sombra difusa mediante un plano alfa independiente
            shadow_surf = pygame.Surface((r*2+20, r*2+20), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (0, 0, 0, 40), (r+6, r+8), r)
            self.surface.blit(shadow_surf, (cx - r - 6 + 2, cy - r - 6))

            # Capa 2: Dibujado geométrica del cuerpo del botón
            radius = r + (10 if is_lit else 0)
            pygame.draw.circle(self.surface, color, (cx, cy), radius)

            # Capa 3: Anillo perimetral de contraste externo
            bw = 6 if is_lit else 3
            pygame.draw.circle(self.surface, (255, 255, 255), (cx, cy), radius, bw)

            # Capa 4: Brillo interno esférico para simular sensación de volumen óptico 3D
            if is_lit:
                highlight = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(highlight, (255, 255, 255, 55),
                                   (radius - radius//3, radius - radius//4), radius // 3)
                self.surface.blit(highlight, (cx - radius, cy - radius))

            # Capa 5: Rótulo tipográfico inferior con el nombre del color
            name_y = cy + radius + 10
            f_n  = _fit_font(btn["name"], r * 2 + 20, 32, bold=False)
            ns   = f_n.render(btn["name"], True, (255, 255, 255) if is_lit else P_BTN_TEXT)
            self.surface.blit(ns, (cx - ns.get_width() // 2, name_y))

    def _draw_footer(self):
        """
        @brief Dibuja la barra inferior de control que aloja el botón de abortar partida.
        """
        W, H = self.game_width, self.game_height
        FH   = self.FOOTER_H
        fy   = H - FH

        bar = pygame.Surface((W, FH), pygame.SRCALPHA)
        bar.fill((245, 238, 255, 210))
        self.surface.blit(bar, (0, fy))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, fy), (W, fy), 2)

        BW, BH = 160, 50
        self.btn_back = pygame.Rect(16, fy + (FH - BH) // 2, BW, BH)
        pygame.draw.rect(self.surface, P_SHADOW,  self.btn_back.move(3,3), border_radius=14)
        pygame.draw.rect(self.surface, P_BACK_BG, self.btn_back,           border_radius=14)
        
        f_b = _fit_font("MENÚ", BW - 20, BH - 14)
        bs  = f_b.render("MENÚ", True, P_BTN_TEXT)
        self.surface.blit(bs, (self.btn_back.x + (BW - bs.get_width()) // 2, self.btn_back.y + (BH - bs.get_height()) // 2))

    def _draw_feedback_overlay(self):
        """
        @brief Compone un telón translúcido superpuesto a pantalla completa para comunicar el resultado.
        """
        W, H = self.game_width, self.game_height

        if self.state == "correct":
            # Efecto pulsante armónico basado en la función seno
            alpha = int(60 * abs(math.sin(self._pulse * math.pi)))
            ov    = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((80, 210, 110, alpha))
            self.surface.blit(ov, (0, 0))

            f  = _fit_font("¡MUY BIEN!", W - 80, H // 4)
            sh = f.render("¡MUY BIEN!", True, (30, 110, 50))
            tx = f.render("¡MUY BIEN!", True, (80, 210, 110))
            cx = W // 2 - tx.get_width() // 2
            cy = H // 2 - tx.get_height() // 2
            self.surface.blit(sh, (cx + 3, cy + 3))
            self.surface.blit(tx, (cx, cy))

        elif self.state == "wrong":
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((210, 60, 60, 45))
            self.surface.blit(ov, (0, 0))

            f  = _fit_font("¡Ese no era!", W - 80, H // 5)
            tx = f.render("¡Ese no era!", True, (180, 40, 40))
            cx = W // 2 - tx.get_width() // 2
            cy = H // 2 - tx.get_height() // 2 - 20
            self.surface.blit(tx, (cx, cy))

            # Pista textual de apoyo para recordar cuál era el color correcto de la secuencia
            correct = SIMON_BUTTONS[self.sequence[self.player_index]]
            hint    = f"Era el {correct['name']}"
            f2  = _fit_font(hint, W - 120, H // 8)
            ht  = f2.render(hint, True, correct["lit"])
            self.surface.blit(ht, (W // 2 - ht.get_width() // 2, cy + tx.get_height() + 16))

    def _draw_win(self):
        """
        @brief Renderiza los mensajes e hitos gráficos correspondientes a la victoria por completar el nivel.
        """
        W, H = self.game_width, self.game_height
        f    = _fit_font("¡GANASTE!", W - 80, H // 4)
        tx   = f.render("¡GANASTE!", True, P_TITLE)
        self.surface.blit(tx, (W // 2 - tx.get_width() // 2, H // 2 - 120))

        sub = f"Completaste los {len(self.sequence)} pasos"
        f2  = _fit_font(sub, W - 120, H // 8, bold=False)
        st  = f2.render(sub, True, P_SUBTITLE)
        self.surface.blit(st, (W // 2 - st.get_width() // 2, H // 2 - 20))

        BW, BH = 290, 70
        self.btn_back = pygame.Rect((W - BW) // 2, H // 2 + 55, BW, BH)
        pygame.draw.rect(self.surface, P_SHADOW,  self.btn_back.move(4,4), border_radius=18)
        pygame.draw.rect(self.surface, P_BACK_BG, self.btn_back,           border_radius=18)
        
        f3 = _fit_font("MENÚ PRINCIPAL", BW - 30, BH - 18)
        bs = f3.render("MENÚ PRINCIPAL", True, P_BTN_TEXT)
        self.surface.blit(bs, (self.btn_back.x + (BW - bs.get_width()) // 2, self.btn_back.y + (BH - bs.get_height()) // 2))