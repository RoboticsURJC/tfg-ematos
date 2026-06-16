# app/ui/apps/games/memory/memory_screen.py

"""
@file memory_screen.py
@brief Pantalla y motor gráfico del juego de memoria táctil basado en Pygame integrado en Qt.
@details Controla los estados de emparejamiento, reescalado dinámico de texturas, animaciones de
partículas balísticas y flujos de eventos asíncronos mediante herencia directa de BasePygameQtScreen.
"""

import pygame
import os
import random
import time
import math

from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# =========================================================================
# PALETA DE COLORES RGB (CONSTANTES DE DISEÑO)
# =========================================================================
P_BG_TOP    = (255, 240, 250)  ##< Tono RGB superior para el gradiente del fondo.
P_BG_BOTTOM = (230, 240, 255)  ##< Tono RGB inferior para el gradiente del fondo.

P_TITLE     = (180,  90, 180)  ##< Color para el rótulo de título principal.
P_SUBTITLE  = (140, 110, 180)  ##< Color para subtítulos e información de nivel.

P_BTN       = (255, 180, 200)  ##< Tono base de los botones de interacción positiva.
P_BTN_EXIT  = (255, 170, 170)  ##< Tono base para botones de cierre o salida.
P_BTN_TEXT  = ( 60,  40,  90)  ##< Color tipográfico de contraste para el texto de los botones.

P_BORDER    = (200, 180, 230)  ##< Color de contorno para las tarjetas ocultas.
P_MATCHED   = (170, 240, 200)  ##< Color de contorno aplicado a las parejas ya resueltas.

P_BAR       = (245, 235, 255)  ##< Color de fondo para la barra de herramientas inferior (HUD).


class MemoryScreen(BasePygameQtScreen):
    """
    @brief Orquestador gráfico y lógico del minijuego de memoria.
    @details Administra las transiciones de nivel aumentando de forma geométrica el tamaño 
    de la rejilla y controlando los hilos de renderizado y captura de colisiones.
    """

    def __init__(self, controller=None):
        """
        @brief Constructor de la clase MemoryScreen.
        @details Inicializa los buffers de fuentes tipográficas, inicializa el subsistema de audio 
        mezclador de Pygame e instancia los rectángulos de colisión estáticos del menú.
        
        @param controller Instancia del enrutador central de vistas de la UI.
        """
        super().__init__(controller)

        logger.info("[MEMORY] Inicializando pantalla de memoria.")

        self.level = 1                         ##< Escalón de dificultad activo (Rangos de 1 a 4).
        self.game_state = "menu"               ##< Máquina de estados del flujo visual ("menu" | "playing").

        self.SQUARE = 140                      ##< Dimensión longitudinal en píxeles de cada tarjeta cuadrada.
        self.INFO_H = 90                       ##< Altura en píxeles asignada a la barra de control inferior (HUD).

        self.font = pygame.font.SysFont("Arial", 30, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 58, bold=True)

        self.current_dir = os.path.dirname(os.path.abspath(__file__))

        # Inicialización y escalado de la textura de la tarjeta oculta (dorso)
        hidden_path = os.path.join(self.current_dir, "assets", "oculta.png")
        self.hidden = pygame.transform.scale(
            pygame.image.load(hidden_path),
            (self.SQUARE, self.SQUARE)
        )

        # Inicialización defensiva del subsistema de audio nativo de Pygame
        try:
            self.sound_flip = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "voltear.wav"))
            self.sound_wrong = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "equivocado.wav"))
            self.sound_win = pygame.mixer.Sound(os.path.join(self.current_dir, "assets", "ganador.wav"))
        except Exception as e:
            logger.warning(f"[MEMORY] No se pudo inicializar el mezclador de audio (Hardware de audio ausente): {e}")
            self.sound_flip = self.sound_wrong = self.sound_win = None

        # Instanciación geométrica de botones en formato de rectángulos contenedores
        self.btn_play = pygame.Rect(0, 0, 260, 70)
        self.btn_exit = pygame.Rect(0, 0, 260, 70)
        self.btn_ingame_exit = pygame.Rect(0, 0, 160, 50)

        self.particles = []                    ##< Contenedor dinámico de vectores balísticos para las partículas de victoria.
        self.celebration = False               ##< Bandera lógica que activa el bucle de actualización del render de partículas.

        self._reset()

    def exit_game(self):
        """
        @brief Detiene de forma segura el bucle de renderizado e invoca el retorno hacia el hub de juegos de Qt.
        """
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    def _reset(self):
        """
        @brief Reinicia los punteros de control de emparejamiento y reconstruye la matriz según el nivel.
        """
        self.matrix, self.rows, self.cols = self._create(self.level)

        self.first = None                      ##< Tupla `(cx, cy)` de coordenadas de la primera carta seleccionada.
        self.second = None                     ##< Tupla `(cx, cy)` de coordenadas de la segunda carta seleccionada.

        self.lock = False                      ##< Estado de bloqueo táctil temporal (impide clicks durante la animación de error).
        self.lock_time = None                  ##< Registro temporal (timestamp) de inicio del bloqueo de pantalla.

        self.start_time = time.time()          ##< Marca de tiempo del inicio de la partida.

        self.particles = []
        self.celebration = False

    def _create(self, level):
        """
        @brief Inicializa la estructura del mazo e instancia las texturas en memoria según la dificultad.
        
        @param level Entero del escalón de dificultad que define las dimensiones matriciales.
        @return tuple Devuelve `(matrix, rows, cols)` donde matrix es una cuadrícula bidimensional de diccionarios.
        """
        sizes = {1: (2, 2), 2: (2, 4), 3: (4, 4), 4: (4, 6)}
        r, c = sizes[level]

        imgs = ["coco.png", "manzana.png", "limon.png", "naranja.png"]
        pairs = (r * c) // 2

        # Selección aleatoria adaptativa permitiendo repetición si la densidad supera al pool original
        deck = random.choices(imgs, k=pairs) * 2
        random.shuffle(deck)

        matrix = []
        i = 0

        for y in range(r):
            row = []
            for x in range(c):
                path = os.path.join(self.current_dir, "assets", deck[i])
                
                # Transformación de escala en caliente sobre la superficie de Pygame
                img = pygame.transform.scale(
                    pygame.image.load(path),
                    (self.SQUARE, self.SQUARE)
                )

                row.append({
                    "img": img,
                    "path": path,
                    "show": False,       # Control de visibilidad transitoria (volteada)
                    "matched": False     # Estado definitivo de resolución de la pareja
                })
                i += 1
            matrix.append(row)

        return matrix, r, c

    def _board(self):
        """
        @brief Calcula los desfases (offsets) espaciales para centrar geométricamente la matriz en la pantalla.
        
        @return tuple Desfases `(ox, oy)` en píxeles medidos desde el vértice superior izquierdo.
        """
        w = self.cols * self.SQUARE
        h = self.rows * self.SQUARE

        ox = (self.game_width - w) // 2
        oy = (self.game_height - self.INFO_H - h) // 2 - 10
        return ox, oy

    def _ui_bar(self):
        """
        @brief Genera la caja de colisión y dibujo asociada al HUD inferior.
        
        @return pygame.Rect Rectángulo absoluto que acota la barra inferior.
        """
        return pygame.Rect(
            0,
            self.game_height - self.INFO_H,
            self.game_width,
            self.INFO_H
        )

    def update_logic(self):
        """
        @brief Motor cíclico principal encargado de la resolución de la lógica de negocio y entrada por eventos.
        @details Procesa la pila asíncrona de eventos capturando clicks de la pantalla táctil, colisiones 
        geométricas y coordina el desbloqueo diferido de las tarjetas erróneas mediante temporizadores.
        """
        for e in self.events:

            # ── GESTIÓN DE EVENTOS: MODO MENÚ ─────────────────────
            if self.game_state == "menu":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    x, y = e.pos

                    if self.btn_play.collidepoint(x, y):
                        self.game_state = "playing"
                        self._reset()
                    elif self.btn_exit.collidepoint(x, y):
                        self.exit_game()

            # ── GESTIÓN DE EVENTOS: MODO EN JUEGO ──────────────────
            elif self.game_state == "playing":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.exit_game()

                if e.type == pygame.MOUSEBUTTONDOWN and not self.lock:
                    x, y = e.pos
                    ox, oy = self._board()

                    # Intercepción táctil del control de salida del HUD
                    if self.btn_ingame_exit.collidepoint(x, y):
                        self.exit_game()
                        return

                    # Abortar eventos si impactan dentro del marco inferior del HUD
                    if y >= self.game_height - self.INFO_H:
                        continue

                    # Validar si el click se sitúa dentro del perímetro útil de la grilla de juego
                    if not (ox <= x < ox + self.cols * self.SQUARE and oy <= y < oy + self.rows * self.SQUARE):
                        continue

                    # Conversión lineal de coordenadas absolutas de pantalla a índices discretos de matriz
                    cx = (x - ox) // self.SQUARE
                    cy = (y - oy) // self.SQUARE

                    card = self.matrix[cy][cx]

                    # Ignorar si la carta ya está visible o resuelta
                    if card["show"] or card["matched"]:
                        continue

                    card["show"] = True

                    # Lógica de emparejamiento de dos pasos
                    if self.first is None:
                        self.first = (cx, cy)
                        if self.sound_flip:
                            self.sound_flip.play()
                    else:
                        self.second = (cx, cy)

                        c1 = self.matrix[self.first[1]][self.first[0]]
                        c2 = self.matrix[self.second[1]][self.second[0]]

                        # Validación de coincidencia por firma de ruta de archivo
                        if c1["path"] == c2["path"]:
                            c1["matched"] = c2["matched"] = True
                            if self.sound_win:
                                self.sound_win.play()
                        else:
                            # Activación del bloqueo táctil para dar tiempo a la memorización visual del error
                            self.lock = True
                            self.lock_time = time.time()
                            if self.sound_wrong:
                                self.sound_wrong.play()

                        self.first = self.second = None

        # Rutina de desbloqueo diferido (Sincronización basada en tiempo real no bloqueante de hilos)
        if self.lock and time.time() - self.lock_time > 1.0:
            for r in self.matrix:
                for c in r:
                    if not c["matched"]:
                        c["show"] = False
            self.lock = False

        # ── VERIFICACIÓN DE CONDICIÓN DE VICTORIA ────────────────
        if self.game_state == "playing":
            total = self.rows * self.cols
            matched = sum(c["matched"] for r in self.matrix for c in r)

            if matched == total:
                self._spawn_particles()
                self.celebration = True

                if self.sound_win:
                    self.sound_win.play()

                # Pequeña pausa estética estructurada para percibir el último acierto antes de transicionar
                time.sleep(0.6)

                if self.level < 4:
                    self.level += 1
                    self._reset()
                else:
                    # Bucle completado: Retorno cíclico controlado al menú principal
                    self.level = 1
                    self.game_state = "menu"
                    self._reset()

    def _spawn_particles(self):
        """
        @brief Genera y siembra aleatoriamente los descriptores cinemáticos para el sistema de partículas.
        @details Puebla el contenedor dinámico con una estructura de vector `[x, y, dx, dy, color]`
        calculando la proyección inicial desde los bordes de la cuadrícula activa.
        """
        ox, oy = self._board()

        for _ in range(120):
            self.particles.append([
                ox + random.randint(0, self.cols * self.SQUARE),
                oy + random.randint(0, self.rows * self.SQUARE),
                random.uniform(-3, 3),   # Velocidad horizontal en el eje X (delta x)
                random.uniform(-6, -2),  # Vector de impulso vertical inicial ascendente (delta y)
                random.choice([(255, 182, 193), (173, 216, 230), (144, 238, 144)])  # Paleta pastel de partículas
            ])

    def render(self):
        """
        @brief Canalizador centralizado del ciclo de dibujado.
        """
        self._bg()

        if self.game_state == "menu":
            self._menu()
        elif self.game_state == "playing":
            self._draw_board()

    def _bg(self):
        """
        @brief Dibuja un gradiente cromático vertical en tiempo real directamente en la superficie principal.
        @details **Optimización de memoria:** Interpola linealmente los colores RGB línea a línea evitando
        la sobrecarga que implicaría reescalar de forma continua un mapa de bits estático gigante.
        """
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))

    def _menu(self):
        """
        @brief Renderiza los elementos de la interfaz de usuario, textos y formas asociadas a la vista de Menú.
        """
        w, h = self.game_width, self.game_height

        title = self.title_font.render(f"MEMORY - NIVEL {self.level}", True, P_TITLE)
        self.surface.blit(title, (w // 2 - title.get_width() // 2, h // 2 - 180))

        # Centrado geométrico dinámico de las cajas de colisión de los botones
        self.btn_play.center = (w // 2, h // 2 - 20)
        self.btn_exit.center = (w // 2, h // 2 + 80)

        pygame.draw.rect(self.surface, P_BTN, self.btn_play, border_radius=20)
        pygame.draw.rect(self.surface, P_BTN_EXIT, self.btn_exit, border_radius=20)

        t1 = self.font.render("▶ JUGAR", True, P_BTN_TEXT)
        t2 = self.font.render(" SALIR", True, P_BTN_TEXT)

        self.surface.blit(t1, t1.get_rect(center=self.btn_play.center))
        self.surface.blit(t2, t2.get_rect(center=self.btn_exit.center))

        sub = self.font.render("Toca para empezar ", True, P_SUBTITLE)
        self.surface.blit(sub, (w // 2 - sub.get_width() // 2, h // 2 + 160))

    def _draw_board(self):
        """
        @brief Renderiza el tablero de juego activo, las tarjetas, los bordes de estado de control y el HUD.
        @details Modifica dinámicamente la posición de los vectores de partículas en base a su delta cinemático
        si la bandera de celebración se encuentra activa.
        """
        ox, oy = self._board()

        for y in range(self.rows):
            for x in range(self.cols):
                c = self.matrix[y][x]

                px = ox + x * self.SQUARE
                py = oy + y * self.SQUARE

                # Selección condicional de textura (Enmascaramiento de estado)
                img = self.hidden if not c["show"] and not c["matched"] else c["img"]
                self.surface.blit(img, (px, py))

                # Pintado del contorno de estado de la tarjeta
                pygame.draw.rect(
                    self.surface,
                    P_MATCHED if c["matched"] else P_BORDER,
                    (px, py, self.SQUARE, self.SQUARE),
                    3
                )

        # ── RENDERIZADO DEL HUD INFERIOR ─────────────────────────
        bar = self._ui_bar()
        pygame.draw.rect(self.surface, P_BAR, bar)

        # Render de texto informativo de progreso
        lvl = self.font.render(f"NIVEL {self.level}", True, P_SUBTITLE)
        self.surface.blit(lvl, (20, self.game_height - self.INFO_H + 25))

        # Posicionamiento dinámico del botón de salida In-Game
        self.btn_ingame_exit.topleft = (self.game_width - 190, self.game_height - self.INFO_H + 20)
        pygame.draw.rect(self.surface, P_BTN_EXIT, self.btn_ingame_exit, border_radius=12)

        txt = self.font.render("SALIR", True, P_BTN_TEXT)
        self.surface.blit(txt, txt.get_rect(center=self.btn_ingame_exit.center))

        # ── MOTOR FÍSICO DE PARTÍCULAS DE CELEBRACIÓN ────────────
        if self.celebration:
            for p in self.particles:
                p[1] += p[3]  # Desplazamiento Y aplicando velocidad (Afectación vertical)
                p[0] += p[2]  # Desplazamiento X aplicando velocidad (Afectación horizontal)
                pygame.draw.circle(self.surface, p[4], (int(p[0]), int(p[1])), 4)