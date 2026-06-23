# app/ui/apps/games/find_differences_screen.py

"""
@file find_differences_screen.py
@brief Motor de juego interactivo de encontrar diferencias integrado en PyQt5 mediante Pygame.
@details Genera de forma procedimental dos lienzos gráficos paralelos basados en temáticas configurables
(jardín, ciudad, playa) aplicando transformaciones aleatorias de color, escala y presencia de primitivas.
Diseñado con elementos visuales de gran escala optimizados para pantallas táctiles en Raspberry Pi.
"""

import pygame
import random
import math
from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger

# ─────────────────────────────────────────────────────────────────────────────
# PALETA DE COLORES (QSS / Pygame Coherente)
# ─────────────────────────────────────────────────────────────────────────────
P_BG_TOP        = (255, 240, 250)  ##< Color superior del gradiente de fondo.
P_BG_BOTTOM     = (230, 240, 255)  ##< Color inferior del gradiente de fondo.
P_TITLE         = (180,  90, 180)  ##< Tonalidad para textos de títulos principales.
P_SUBTITLE      = (140, 110, 180)  ##< Tonalidad para textos informativos secundarios.
P_SHADOW        = (210, 200, 225)  ##< Color de sombreado para dar profundidad tridimensional.
P_BTN_TEXT      = ( 60,  40,  90)  ##< Color del texto interno de los botones.
P_PANEL_BG      = (245, 240, 255)  ##< Color de fondo de los contenedores de datos.
P_PANEL_BORDER  = (200, 180, 230)  ##< Color para los bordes y rejillas de los lienzos.
P_BTN_BACK      = (180, 200, 255)  ##< Color del botón de retorno al menú.
P_BTN_EASY      = (150, 230, 180)  ##< Identificador verde para dificultad fácil.
P_BTN_MEDIUM    = (255, 210, 130)  ##< Identificador naranja para dificultad media.
P_BTN_HARD      = (255, 160, 160)  ##< Identificador rojo para dificultad difícil.
P_BTN_EXIT      = (255, 170, 170)  ##< Color del botón de salida del módulo de juego.

P_FOUND_RING    = ( 80, 200, 120)  ##< Círculo verde emitido al descubrir una diferencia válida.
P_MISS_FLASH    = (220,  80,  80)  ##< Destello rojo alfa emitido ante una pulsación errónea.

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE DIFICULTAD
# ─────────────────────────────────────────────────────────────────────────────
## Diccionario de configuración de parámetros lógicos indexados por nivel de dificultad.
DIFFICULTY = {
    "facil":   {"n_objects": 8,  "n_diffs": 3, "time_limit": 0},   # Sin límite temporal
    "medio":   {"n_objects": 12, "n_diffs": 5, "time_limit": 120},  # 2 minutos
    "dificil": {"n_objects": 16, "n_diffs": 7, "time_limit": 90},   # 90 segundos
}

# ─────────────────────────────────────────────────────────────────────────────
# TEMAS DE ESCENAS PROCEDIMENTALES
# ─────────────────────────────────────────────────────────────────────────────
## Estructuras temáticas que definen los fondos, paletas de dibujo y morfologías disponibles para la escena.
THEMES = {
    "jardin": {
        "bg":      (210, 235, 200),
        "colors":  [(220, 80, 80), (80, 160, 80), (255, 200, 50), (150, 80, 200), (255, 150, 50), (60, 130, 60), (200, 240, 160)],
        "shapes":  ["circle", "rect", "triangle"],
    },
    "ciudad": {
        "bg":      (200, 210, 230),
        "colors":  [(100, 140, 200), (180, 120, 60), (220, 220, 220), (60, 60, 100), (240, 180, 60), (200, 60, 60), (120, 180, 120)],
        "shapes":  ["rect", "rect", "circle"],
    },
    "playa": {
        "bg":      (200, 230, 255),
        "colors":  [(255, 220, 100), (50, 150, 220), (255, 100, 80), (255, 200, 80), (200, 240, 200), (200, 180, 140), (255, 150, 100)],
        "shapes":  ["circle", "triangle", "rect"],
    },
}


def _darken(color, factor=0.7):
    """
    @brief Atenúa u oscurece un color RGB aplicando un factor multiplicativo de escala.
    
    @param color Tupla `(R, G, B)` original.
    @param factor Coeficiente flotante de atenuación lineal.
    @return tuple Tupla `(R, G, B)` resultante normalizada en el rango [0, 255].
    """
    return tuple(max(0, int(c * factor)) for c in color)


def _lighten(color, factor=1.3):
    """
    @brief Intensifica o aclara un color RGB aplicando un factor multiplicativo de escala.
    
    @param color Tupla `(R, G, B)` original.
    @param factor Coeficiente flotante de amplificación lineal.
    @return tuple Tupla `(R, G, B)` resultante acotada en el rango [0, 255].
    """
    return tuple(min(255, int(c * factor)) for c in color)


class SceneObject:
    """
    @brief Entidad abstracta que representa una primitiva geométrica dibujable dentro de los lienzos.
    """

    def __init__(self, shape, x, y, w, h, color, border_color=None):
        """
        @brief Constructor de SceneObject.
        
        @param shape Cadena identificadora de la morfología ("circle" | "rect" | "triangle").
        @param x Coordenada de origen horizontal local.
        @param y Coordenada de origen vertical local.
        @param w Ancho de la caja delimitadora del objeto.
        @param h Alto de la caja delimitadora del objeto.
        @param color Tupla RGB que define el tono de relleno.
        @param border_color Tupla RGB opcional para el trazo exterior del contorno.
        """
        self.shape        = shape
        self.x            = x
        self.y            = y
        self.w            = w
        self.h            = h
        self.color        = color
        self.border_color = border_color or _darken(color, 0.6)

    def copy(self):
        """
        @brief Duplica la instancia actual para su posterior manipulación o mutación aislada.
        
        @return SceneObject Nueva copia exacta clonada en memoria.
        """
        return SceneObject(
            self.shape, self.x, self.y, self.w, self.h,
            self.color, self.border_color
        )

    def get_rect(self, offset_x=0, offset_y=0):
        """
        @brief Devuelve el objeto delimitador `pygame.Rect` proyectado con offsets globales de pantalla.
        
        @param offset_x Desplazamiento horizontal del lienzo contenedor.
        @param offset_y Desplazamiento vertical del lienzo contenedor.
        @return pygame.Rect Rectángulo absoluto en coordenadas de ventana.
        """
        return pygame.Rect(self.x + offset_x, self.y + offset_y, self.w, self.h)

    def draw(self, surface, offset_x=0, offset_y=0):
        """
        @brief Renderiza la primitiva geométrica en la superficie destino aplicando los offsets indicados.
        
        @param surface Superficie (`pygame.Surface`) de dibujo.
        @param offset_x Margen de traslación horizontal.
        @param offset_y Margen de traslación vertical.
        """
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


def generate_scene(n_objects: int, theme_name: str, canvas_w: int, canvas_h: int) -> list:
    """
    @brief Genera procedimentalmente una colección de objetos distribuidos sobre una rejilla ortogonal desordenada.
    @details Segmenta el lienzo en regiones proporcionales para mitigar colisiones directas o solapamientos 
    masivos de las primitivas geométricas, aplicando variaciones aleatorias de tamaño y posición dentro de cada celda.
    
    @param n_objects Número total de elementos que se instanciarán en la escena.
    @param theme_name Identificador de texto de la paleta temática a emplear.
    @param canvas_w Ancho útil de la superficie de renderizado.
    @param canvas_h Alto útil de la superficie de renderizado.
    @return list Vector relleno de instancias de tipo SceneObject.
    """
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


class Difference:
    """
    @brief Estructura de control que define una diferencia inyectada entre los dos lienzos.
    """

    def __init__(self, diff_type: str, obj_index: int, zone: pygame.Rect):
        """
        @brief Constructor de Difference.
        
        @param diff_type Naturaleza de la mutación ("color_change" | "remove" | "size_change" | "add").
        @param obj_index Índice del vector de elementos asociado al cambio.
        @param zone Área rectangular delimitadora para el chequeo de colisiones o clics táctiles.
        """
        self.diff_type  = diff_type
        self.obj_index  = obj_index
        self.zone       = zone
        self.found      = False


def apply_differences(base_objects: list, n_diffs: int, canvas_w: int, canvas_h: int, theme_name: str):
    """
    @brief Toma una escena base y genera una copia mutada inyectando un número determinado de diferencias lógicas.
    @details Selecciona de manera aleatoria objetos para alterar sus atributos de color, escala, 
    eliminar su visibilidad o añadir nuevos componentes huérfanos sobre zonas libres del canvas.
    
    @param base_objects Colección original de objetos que componen el lienzo primario A.
    @param n_diffs Número estricto de mutaciones a inyectar en la escena modificada B.
    @param canvas_w Ancho útil de la superficie de renderizado.
    @param canvas_h Alto útil de la superficie de renderizado.
    @param theme_name Identificador del tema gráfico para la extracción de colores de reemplazo.
    @return tuple Una tupla contenedora de `(lista_objetos_mutados, lista_de_instancias_Difference)`.
    """
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


class FindDifferencesScreen(BasePygameQtScreen):
    """
    @brief Pantalla del juego encargada de gestionar el ciclo de vida, la lógica y el renderizado.
    """

    def __init__(self, controller=None, width=1024, height=600):
        """
        @brief Constructor de FindDifferencesScreen.
        
        @param controller Instancia del enrutador central de vistas de la UI.
        @param width Resolución horizontal virtual de la ventana.
        @param height Resolución vertical virtual de la ventana.
        """
        super().__init__(controller, width, height)
        logger.info("[DIFF] Iniciada FindDifferencesScreen")

        ## Estado de la máquina de ejecución interna ("menu" | "playing" | "win" | "timeout").
        self.state      = "menu"
        
        ## Nivel de dificultad activo en la partida en curso.
        self.difficulty = "facil"
        
        ## Identificador temático visual seleccionado para la ronda de juego.
        self.theme_name = "jardin"

        ## Colección de SceneObjects asignados al lienzo izquierdo A.
        self.objects_a   = []
        
        ## Colección de SceneObjects asignados al lienzo derecho B.
        self.objects_b   = []
        
        ## Colección dinámica de diferencias inyectadas activas en la ronda.
        self.differences = []

        ## Región geométrica absoluta que ocupa el lienzo A en la ventana.
        self.canvas_rect_a = pygame.Rect(0, 0, 0, 0)
        
        ## Región geométrica absoluta que ocupa el lienzo B en la ventana.
        self.canvas_rect_b = pygame.Rect(0, 0, 0, 0)
        
        ## Búfer gráfico estático para el caché visual del lienzo A.
        self._canvas_a_surf = None
        
        ## Búfer gráfico estático para el caché visual del lienzo B.
        self._canvas_b_surf = None

        ## Lista de destellos activos generados por pulsaciones erróneas.
        self._miss_flashes   = []
        
        ## Lista de anillos de realce verde correspondientes a aciertos confirmados.
        self._found_rings    = []

        ## Contador incremental de tiempo de juego transcurrido en segundos.
        self._elapsed    = 0.0
        
        ## Límite de tiempo máximo permitido extraído de la dificultad (0 implica infinito).
        self._time_limit = 0
        
        ## Variable oscilatoria armónica continua para efectos de pulsado gráfico.
        self._ring_pulse = 0.0
        
        ## Temporizador de persistencia para congelar la pantalla de victoria antes de salir.
        self._win_timer  = 0.0

        # Mapeos geométricos de la botonera del menú
        self.btn_easy   = pygame.Rect(0, 0, 0, 0)
        self.btn_medium = pygame.Rect(0, 0, 0, 0)
        self.btn_hard   = pygame.Rect(0, 0, 0, 0)
        self.btn_exit   = pygame.Rect(0, 0, 0, 0)
        self.btn_back   = pygame.Rect(0, 0, 0, 0)

    def exit_game(self):
        """
        @brief Termina la ejecución lúdica activa y cede el control del foco al hub central de juegos.
        """
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    def start_game(self, difficulty: str):
        """
        @brief Inicializa y arranca una partida limpiando los contadores y generando los mapas.
        
        @param difficulty Cadena identificadora del nivel de dificultad a setear ("facil" | "medio" | "dificil").
        """
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
        """
        @brief Calcula de forma estricta los rectángulos de visualización de los lienzos.
        @details Reserva espacios proporcionales para barras de cabecera amplificadas (`HEADER_H`)
        y pie de página (`FOOTER_H`), dividiendo el espacio libre restante equitativamente en dos mitades.
        """
        HEADER_H = 140
        FOOTER_H = 80
        GAP      = 16
        MARGIN   = 16

        surf_w = self.surface.get_width()
        surf_h = self.surface.get_height()

        total_w  = surf_w - (MARGIN * 2) - GAP
        total_h  = surf_h - HEADER_H - FOOTER_H

        canvas_w = total_w // 2
        canvas_h = total_h

        self.canvas_rect_a = pygame.Rect(MARGIN, HEADER_H, canvas_w, canvas_h)
        self.canvas_rect_b = pygame.Rect(MARGIN + canvas_w + GAP, HEADER_H, canvas_w, canvas_h)

    def _render_canvas_a(self):
        """
        @brief Dibuja y cachea en una superficie aislada los objetos estáticos del lienzo A.
        """
        bg   = THEMES[self.theme_name]["bg"]
        surf = pygame.Surface((self.canvas_rect_a.width, self.canvas_rect_a.height))
        surf.fill(bg)
        for obj in self.objects_a:
            if obj.color is not None:
                obj.draw(surf)
        self._canvas_a_surf = surf

    def _render_canvas_b(self):
        """
        @brief Dibuja y cachea en una superficie aislada los objetos estáticos del lienzo B.
        """
        bg   = THEMES[self.theme_name]["bg"]
        surf = pygame.Surface((self.canvas_rect_b.width, self.canvas_rect_b.height))
        surf.fill(bg)
        for obj in self.objects_b:
            if obj.color is not None:
                obj.draw(surf)
        self._canvas_b_surf = surf

    def update_logic(self):
        """
        @brief Procesa la actualización cronológica de la partida, animaciones alfa y límites de tiempo.
        @details Implementa las cláusulas de guarda necesarias para conmutar las pantallas de fin 
        de juego en función de los contadores asíncronos (`dt`).
        """
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
        """
        @brief Intercepta los eventos físicos de pulsación y los evalúa contra las cajas de colisión.
        
        @param event Objeto del evento nativo de tipo QMouseEvent.
        """
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
        """
        @brief Evalúa si un clic táctil colisiona con el radio de acierto de alguna diferencia latente.
        @details Convierte las coordenadas globales a márgenes locales de lienzo e infla un rectángulo 
        de tolerancia (`HIT_MARGIN`) para compensar la imprecisión en pantallas táctiles resistivas/capacitivas.
        
        @param pos Tupla `(x, y)` con el píxel de contacto absoluto en la ventana de juego.
        """
        HIT_MARGIN = 55

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
            cy_local = found_diff.zone.centery
            
            # Espejado simétrico del anillo indicador en ambos lienzos para facilitar el feedback
            self._found_rings.append((cx_local + self.canvas_rect_a.x, cy_local + self.canvas_rect_a.y, found_diff))
            self._found_rings.append((cx_local + self.canvas_rect_b.x, cy_local + self.canvas_rect_b.y, found_diff))
            logger.info(f"[DIFF] Diferencia encontrada: {found_diff.diff_type}")
        else:
            self._miss_flashes.append((pos[0], pos[1], 0.4))
            logger.debug(f"[DIFF] Clic fallido en coordenadas relativas ({local_x}, {local_y})")

    # ── Orquestación de Canales de Dibujo (Rendering) ─────────────────────────

    def render(self):
        """
        @brief Canal maestro de dibujo que vacía y refresca el búfer gráfico principal según el estado.
        """
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
        """
        @brief Genera y pinta un fondo degradado vertical interpolando linealmente las constantes de color.
        """
        surf_h = self.surface.get_height()
        surf_w = self.surface.get_width()
        for y in range(surf_h):
            t = y / surf_h
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (surf_w, y))

    def _draw_menu(self):
        """
        @brief Estampa la interfaz del menú principal, textos informativos y botones gigantes.
        """
        w = self.surface.get_width()
        h = self.surface.get_height()
        cx = w // 2
        
        btn_w = 620
        btn_h = 110
        
        self.btn_easy   = pygame.Rect(cx - (btn_w // 2), int(h * 0.32), btn_w, btn_h)
        self.btn_medium = pygame.Rect(cx - (btn_w // 2), int(h * 0.46), btn_w, btn_h)
        self.btn_hard   = pygame.Rect(cx - (btn_w // 2), int(h * 0.60), btn_w, btn_h)
        self.btn_exit   = pygame.Rect(cx - (btn_w // 2), int(h * 0.78), btn_w, 90)

        tf = pygame.font.Font(None, 110)
        shadow = tf.render("ENCUENTRA LAS DIFERENCIAS", True, P_SHADOW)
        title  = tf.render("ENCUENTRA LAS DIFERENCIAS", True, P_TITLE)
        
        self.surface.blit(shadow, (cx - shadow.get_width() // 2 + 3, int(h * 0.10) + 3))
        self.surface.blit(title,  (cx - title.get_width()  // 2, int(h * 0.10)))

        sf  = pygame.font.Font(None, 60)
        sub = sf.render("Pulsa en las diferencias entre las dos imágenes", True, P_SUBTITLE)
        self.surface.blit(sub, (cx - sub.get_width() // 2, int(h * 0.22)))

        self._draw_button(self.btn_easy,   "FÁCIL  —  3 diferencias",  P_BTN_EASY,   fontSize=60)
        self._draw_button(self.btn_medium, "MEDIO  —  5 diferencias",  P_BTN_MEDIUM, fontSize=60)
        self._draw_button(self.btn_hard,   "DIFÍCIL —  7 diferencias", P_BTN_HARD,   fontSize=60)
        self._draw_button(self.btn_exit,   " Volver",                 P_BTN_EXIT,   fontSize=60)

    def _draw_game(self):
        """
        @brief Compone de forma aditiva los elementos mecánicos activos de la partida en curso.
        """
        self._draw_canvases()
        self._draw_found_rings()
        self._draw_miss_flashes()
        self._draw_header()
        self._draw_footer()

    def _draw_header(self):
        """
        @brief Renderiza el panel translúcido superior, el progreso mediante esferas y el cronómetro.
        """
        w = self.surface.get_width()
        HEADER_H = 140
        
        hbar = pygame.Surface((w, HEADER_H), pygame.SRCALPHA)
        hbar.fill((245, 235, 255, 200))
        self.surface.blit(hbar, (0, 0))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, HEADER_H), (w, HEADER_H), 2)

        tf = pygame.font.Font(None, 72)
        tit = tf.render(f"🔍  ESTILO: {self.theme_name.upper()}", True, P_TITLE)
        self.surface.blit(tit, (w // 2 - tit.get_width() // 2, 10))

        found = sum(1 for d in self.differences if d.found)
        total = len(self.differences)

        cf = pygame.font.Font(None, 52)
        ct = cf.render(f"Progreso: {found} / {total}", True, P_SUBTITLE)
        self.surface.blit(ct, (w // 2 - ct.get_width() // 2, 54))

        if total > 0:
            dot_r = 9
            dot_gap = 8
            dot_total_w = total * (dot_r * 2) + (total - 1) * dot_gap
            dot_x = w // 2 - dot_total_w // 2 + dot_r
            dot_y = 90
            for diff in self.differences:
                color = P_FOUND_RING if diff.found else (210, 205, 225)
                pygame.draw.circle(self.surface, color, (dot_x, dot_y), dot_r)
                if not diff.found:
                    pygame.draw.circle(self.surface, P_PANEL_BORDER, (dot_x, dot_y), dot_r, 1)
                dot_x += (dot_r * 2) + dot_gap

        if self._time_limit > 0:
            remaining = max(0.0, self._time_limit - self._elapsed)
            color = (220, 70, 70) if remaining < 20 else P_SUBTITLE
            tf2 = pygame.font.Font(None, 42)
            ts  = tf2.render(f"⏱  {int(remaining)}s", True, color)
            self.surface.blit(ts, (w - ts.get_width() - 25, 25))

    def _draw_canvases(self):
        """
        @brief Proyecta sobre la superficie global las copas cacheadas de los dos cuadros lúdicos.
        """
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

            lf = pygame.font.Font(None, 32)
            ls = lf.render(label, True, P_SUBTITLE)
            self.surface.blit(ls, (rect.x + 12, rect.y + 10))

    def _draw_found_rings(self):
        """
        @brief Pinta anillos armónicos expansivos y marcas de verificación sobre las diferencias descubiertas.
        """
        base_r = 30
        pulse  = int(math.sin(self._ring_pulse) * 4)

        for cx, cy, diff in self._found_rings:
            r = base_r + pulse
            if r <= 0: r = 1
            
            ring_surf = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (*P_FOUND_RING, 45), (r + 3, r + 3), r)
            pygame.draw.circle(ring_surf, (*P_FOUND_RING, 230), (r + 3, r + 3), r, 3)
            self.surface.blit(ring_surf, (cx - r - 3, cy - r - 3))

            cf  = pygame.font.Font(None, 36)
            cts = cf.render("✓", True, P_FOUND_RING)
            self.surface.blit(cts, (cx - cts.get_width() // 2, cy - cts.get_height() // 2))

    def _draw_miss_flashes(self):
        """
        @brief Renderiza círculos de advertencia con atenuación exponencial alfa para los fallos.
        """
        for fx, fy, ft in self._miss_flashes:
            alpha = int(ft / 0.4 * 150)
            if alpha <= 0: continue
            r = 26
            fs = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(fs, (*P_MISS_FLASH, alpha), (r, r), r)
            self.surface.blit(fs, (fx - r, fy - r))

    def _draw_footer(self):
        """
        @brief Pinta la barra de pie de página y actualiza el botón de salida parcial.
        """
        w = self.surface.get_width()
        h = self.surface.get_height()
        BAR_H = 80
        bar_y = h - BAR_H
        bar   = pygame.Surface((w, BAR_H), pygame.SRCALPHA)
        bar.fill((245, 235, 255, 200))
        self.surface.blit(bar, (0, bar_y))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, bar_y), (w, bar_y), 2)

        self.btn_back = pygame.Rect(20, bar_y + 12, 260, 70)
        self._draw_button(self.btn_back, " Menú", P_BTN_BACK, fontSize=48)

        hf  = pygame.font.Font(None, 30)
        ht  = hf.render("Tip: Las diferencias se pueden marcar en cualquiera de los dos lados", True, P_SUBTITLE)
        self.surface.blit(ht, (w // 2 - ht.get_width() // 2, bar_y + 26))

    def _draw_win_overlay(self):
        """
        @brief Superpone una cortina verde translúcida que indica la resolución exitosa del juego.
        """
        w = self.surface.get_width()
        h = self.surface.get_height()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((210, 245, 220, 200))
        self.surface.blit(overlay, (0, 0))

        tf  = pygame.font.Font(None, 92)
        tx  = tf.render("¡COMPLETADO! 🎉", True, (40, 140, 70))
        self.surface.blit(tx, (w // 2 - tx.get_width() // 2, h // 2 - 50))

        sf  = pygame.font.Font(None, 42)
        st  = sf.render(f"¡Encontraste las {len(self.differences)} diferencias con éxito!", True, (60, 110, 80))
        self.surface.blit(st, (w // 2 - st.get_width() // 2, h // 2 + 25))

    def _draw_timeout_overlay(self):
        """
        @brief Superpone una cortina roja translúcida detallando la ubicación de las diferencias no encontradas.
        """
        w = self.surface.get_width()
        h = self.surface.get_height()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((255, 210, 210, 180))
        self.surface.blit(overlay, (0, 0))

        tf  = pygame.font.Font(None, 86)
        tx  = tf.render("¡Tiempo Agotado! ⏱", True, (170, 50, 50))
        self.surface.blit(tx, (w // 2 - tx.get_width() // 2, h // 2 - 60))

        # Remarcado explícito de los objetivos no descubiertos mediante cajas rojas de contorno
        for diff in self.differences:
            if not diff.found:
                for offset_x, offset_y in [
                    (self.canvas_rect_a.x, self.canvas_rect_a.y),
                    (self.canvas_rect_b.x, self.canvas_rect_b.y)
                ]:
                    rx = diff.zone.x + offset_x
                    ry = diff.zone.y + offset_y
                    pygame.draw.rect(self.surface, (230, 50, 50), (rx - 2, ry - 2, diff.zone.w + 4, diff.zone.h + 4), 3, border_radius=6)

        sf = pygame.font.Font(None, 38)
        st = sf.render("Haz clic en cualquier parte para volver al menú principal", True, (130, 50, 50))
        self.surface.blit(st, (w // 2 - st.get_width() // 2, h // 2 + 40))

    def _draw_button(self, rect, text, color, fontSize=38):
        """
        @brief Dibuja de forma atómica un botón estilizado con sombras proyectadas y texto centrado.
        
        @param rect Estructura `pygame.Rect` que define el tamaño y posición del control.
        @param text Cadena de texto a estampar en su interior.
        @param color Tupla RGB con el tono base del relleno.
        @param fontSize Tamaño entero de la fuente tipográfica para la renderización.
        """
        sr = rect.move(2, 2)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=18)
        pygame.draw.rect(self.surface, color,    rect, border_radius=18)
        pygame.draw.rect(self.surface, (255, 255, 255), rect, 2, border_radius=18)
        
        f  = pygame.font.Font(None, fontSize)
        ts = f.render(text, True, P_BTN_TEXT)
        self.surface.blit(ts, (rect.x + (rect.width - ts.get_width()) // 2, rect.y + (rect.height - ts.get_height()) // 2))