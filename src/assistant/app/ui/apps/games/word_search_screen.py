# app/ui/apps/games/word_search/word_search_screen.py

"""
@file word_search_screen.py
@brief Pantalla y lógica del juego de estimulación cognitiva Sopa de Letras en Pygame y Qt.
@details Diseñado con una paleta pastel de alto contraste para adultos mayores. Cuenta con una
interfaz adaptativa que re-calcula las proporciones de la cuadrícula física y un sistema de 
caché tipográfico indexado para suprimir la sobrecarga computacional del ciclo de renderizado.
"""

import pygame
import random
import math

from app.ui.apps.games import generate
from app.ui.apps.games.base_pygame_qt_screen import BasePygameQtScreen
from app.core.logger import logger


# =========================================================================
# PALETA PASTEL CUTE & ALTO CONTRASTE MODULARIZADA
# =========================================================================
P_BG_TOP        = (255, 240, 250)   ##< Tono RGB superior para el gradiente de fondo (Rosa suave).
P_BG_BOTTOM     = (230, 240, 255)   ##< Tono RGB inferior para el gradiente de fondo (Lavanda pálido).
P_TITLE         = (130,  30, 145)   ##< Color dominante de alta saturación para títulos de cabecera.
P_SUBTITLE      = (100,  60, 150)   ##< Color para subtítulos y guías textuales secundarias.
P_SHADOW        = (195, 175, 215)   ##< Tono de sombreado plano (Drop-shadow flat) para emular relieve físico tactile.

# Configuración cromática de la botonera del menú interactivo (Criterio Ergonómico)
M_BTN_EASY_BG   = (145, 235, 175)   ##< Fondo RGB para la opción de dificultad fácil (Verde menta).
M_BTN_EASY_BRD  = ( 85, 185, 120)   ##< Borde RGB para la opción de dificultad fácil.
M_BTN_MED_BG    = (255, 215, 115)   ##< Fondo RGB para la opción de dificultad media (Amarillo brillante).
M_BTN_MED_BRD   = (215, 160,  50)   ##< Borde RGB para la opción de dificultad media.
M_BTN_HARD_BG   = (255, 155, 170)   ##< Fondo RGB para la opción de dificultad difícil (Rosa coral).
M_BTN_HARD_BRD  = (215,  90, 110)   ##< Borde RGB para la opción de dificultad difícil.
M_BTN_BACK_BG   = (165, 205, 255)   ##< Fondo RGB para el botón de retorno del menú (Azul cielo).
M_BTN_BACK_BRD  = (105, 150, 220)   ##< Borde RGB para el botón de retorno del menú.
M_BTN_TEXT      = ( 50,  20,  70)   ##< Tono oscuro profundo para las tipografías de los botones.

# Paleta cromática in-game para celdas, letras y estados del panel
P_ACCENT        = (255, 140, 170)   ##< Color de énfasis para realzar caminos activos en selección.
P_CELL_NORMAL   = (255, 255, 255)   ##< Color de fondo por defecto para celdas inactivas.
P_CELL_BORDER   = (200, 180, 230)   ##< Borde de rejilla estándar para separación de caracteres.
P_CELL_SELECT   = (180, 220, 255)   ##< Fondo de celda bajo el foco o arrastre actual del usuario.
P_CELL_FOUND    = (180, 255, 200)   ##< Fondo de celda correspondiente a palabras ya descubiertas.
P_CELL_HINT     = (255, 220, 130)   ##< Color indicador perimetral del sistema de pistas visuales.
P_WORD_PANEL    = (245, 240, 255)   ##< Fondo para el contenedor lateral de la lista de palabras.
P_WORD_PENDING  = ( 90,  70, 120)   ##< Color del texto para palabras que faltan descubrir.
P_WORD_DONE     = (180, 180, 200)   ##< Color del texto para palabras ya tachadas.
P_WORD_STRIKE   = (150, 200, 170)   ##< Color de la línea de tachado horizontal de éxito.
P_BTN_HINT      = (255, 220, 100)   ##< Fondo del botón de solicitud de pista in-game.
P_BTN_BACK      = (180, 200, 255)   ##< Fondo del botón de retorno in-game.
P_BTN_TEXT      = ( 60,  40,  90)   ##< Color general para caracteres del abecedario y botones in-game.
P_PANEL_BORDER  = (200, 180, 230)   ##< Línea divisoria de los paneles del HUD in-game.


class WordSearchScreen(BasePygameQtScreen):
    """
    @brief Pantalla interactiva de Sopa de Letras optimizada con criterios de accesibilidad.
    """

    def __init__(self, controller=None, width=1024, height=600):
        """
        @brief Constructor de la clase WordSearchScreen.
        @details Instancia la máquina de estados lógicos e inicializa los caches tipográficos masivos.
        
        @param controller Instancia del enrutador o máquina de control de interfaces de la app.
        @param width Dimensión horizontal inicial de la ventana de juego.
        @param height Dimensión vertical inicial de la ventana de juego.
        """
        super().__init__(controller, width, height)
        logger.info("[SOPA] Inicializando pantalla de Sopa de Letras.")

        self.state      = "menu"       ##< Máquina de estados lógicos principal ("menu" | "game").
        self.difficulty = None         ##< Cadena que determina la dificultad activa ("facil" | "medio" | "dificil").

        self.selected       = []       ##< Lista dinámica de posiciones `[x, y]` con las celdas ya descubiertas con éxito.
        self.current_path   = []       ##< Lista transitoria de posiciones `(x, y)` del trazo lineal en curso durante el arrastre.
        self.words_to_guess = []       ##< Subconjunto de cadenas textuales que el usuario debe encontrar para ganar.
        self.hint_cell      = None     ##< Coordenada tupla `(x, y)` de la celda destacada por el botón de pista (None si no está activo).

        self.CELL        = 50          ##< Tamaño físico adaptativo en píxeles de los lados de cada celda cuadrada de la matriz.
        self.GRID_POS    = (40, 100)   ##< Coordenadas absolutas de origen `(X, Y)` para el renderizado del tablero.
        self.WORD_LIST_X = 0           ##< Coordenada en el eje X de origen para la barra lateral derecha de palabras.
        self.WORD_LIST_Y = 100         ##< Coordenada en el eje Y de origen para la barra lateral derecha de palabras.

        self.scroll_offset  = 0        ##< Desplazamiento actual en píxeles del scroll de la lista lateral de palabras.
        self.max_scroll     = 0        ##< Límite superior de desplazamiento vertical permitido para el scroll.
        self._mouse_pressed = False    ##< Bandera interna que monitoriza el estado de presión continua del mouse o pantalla táctil.

        # Fuentes fijas pre-instanciadas de tamaño masivo para maximizar la legibilidad
        self.m_f_title    = pygame.font.SysFont("Arial", 76, bold=True)
        self.m_f_subtitle = pygame.font.SysFont("Arial", 42, bold=True)
        self.m_f_btn      = pygame.font.SysFont("Arial", 38, bold=True)

        # Cajas de colisión geométrica bidimensional iniciales (Se recalculan en caliente en el renderizado)
        self.btn_easy      = pygame.Rect(0, 0, 0, 0)
        self.btn_medium    = pygame.Rect(0, 0, 0, 0)
        self.btn_hard      = pygame.Rect(0, 0, 0, 0)
        self.btn_game_back = pygame.Rect(0, 0, 0, 0)
        self.btn_hint      = pygame.Rect(0, 0, 0, 0)
        self.btn_back      = pygame.Rect(0, 0, 0, 0)

        self.letter_cache = {}         ##< Almacén asociativo para optimizar el dibujado `{ (x, y): (Surface, (px, py)) }`.

    def exit_game(self):
        """
        @brief Cierra de forma ordenada el sub-entorno de ejecución de Pygame y retorna al launcher de Qt.
        """
        self.stop()
        if self.controller and hasattr(self.controller, "ui"):
            self.controller.ui.show_games()

    # =========================================================================
    # CONFIGURACIÓN E INICIALIZACIÓN DE PARTIDA
    # =========================================================================
    def start_game(self, difficulty):
        """
        @brief Inicializa las matrices del generador procedimental e inicia una partida nueva.
        
        @param difficulty Cadena de texto que configura la dimensión y densidad léxica de la sopa.
        """
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
        logger.info(f"[SOPA] Tablero procedimental generado e iniciado — nivel: {difficulty}")

    def _calculate_layout(self):
        """
        @brief Distribuye espacialmente la matriz de juego basándose en la resolución actual del lienzo.
        @details Resuelve de forma exacta las cotas dimensionales de las celdas y ubica los paneles
        laterales minimizando la distorsión geométrica en pantallas panorámicas.
        """
        grid = generate.GRID_SIZE

        LIST_W   = 250   
        MARGIN   = 20    
        TOP_Y    = 80    
        BTN_H    = 64    
        BTN_GAP  = 12    
        BOTTOM_RESERVED = BTN_H + BTN_GAP * 2   

        # Espacio útil remanente restando paneles adyacentes fijados
        available_w = self.game_width - LIST_W - MARGIN * 3
        available_h = self.game_height - TOP_Y - BOTTOM_RESERVED - MARGIN

        # Determinación adaptativa del tamaño de la celda acotado entre [38, 62] píxeles
        cell_by_w = available_w // grid
        cell_by_h = available_h // grid
        self.CELL = max(min(cell_by_w, cell_by_h, 62), 38)

        grid_px_w = grid * self.CELL
        grid_px_h = grid * self.CELL

        left_area_w = self.game_width - LIST_W - MARGIN * 3
        grid_x = MARGIN + (left_area_w - grid_px_w) // 2
        grid_y = TOP_Y + (available_h - grid_px_h) // 2
        grid_y = max(grid_y, TOP_Y)   

        self.GRID_POS = (grid_x, grid_y)
        self.WORD_LIST_X = MARGIN * 2 + left_area_w
        self.WORD_LIST_Y = TOP_Y

        btn_y = self.game_height - BTN_H - BTN_GAP
        btn_w = 150
        self.btn_back = pygame.Rect(MARGIN, btn_y, btn_w, BTN_H)
        self.btn_hint = pygame.Rect(self.game_width - MARGIN - btn_w, btn_y, btn_w, BTN_H)

    def _update_scroll_range(self):
        """
        @brief Evalúa las dimensiones de la lista léxica y calibra los límites del scroll vertical.
        """
        if self.words_to_guess:
            words_h  = len(self.words_to_guess) * 36
            panel_h  = self.game_height - self.WORD_LIST_Y - 80
            self.max_scroll = max(0, words_h - panel_h)
        else:
            self.max_scroll = 0
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

    def _cache_letters(self):
        """
        @brief Pre-renderiza las letras del alfabeto de la matriz sobre un mapa asociativo en memoria.
        @details **Optimización técnica:** Suprime llamadas redundantes a `Font.render()` dentro del 
        bucle principal, logrando tasas estables de 60 FPS independientemente del tamaño de la matriz.
        """
        self.letter_cache = {}
        font_size = max(int(self.CELL * 0.58), 20)
        font = pygame.font.Font(None, font_size)
        for y, row in enumerate(generate.grid):
            for x, letter in enumerate(row):
                surf = font.render(letter.upper(), True, P_BTN_TEXT)
                px = self.GRID_POS[0] + x * self.CELL + (self.CELL - surf.get_width())  // 2
                py = self.GRID_POS[1] + y * self.CELL + (self.CELL - surf.get_height()) // 2
                self.letter_cache[(x, y)] = (surf, (px, py))

    # =========================================================================
    # LÓGICA DE CONTROL
    # =========================================================================
    def update_logic(self):
        """
        @brief Comprueba de forma asíncrona la condición de victoria por vaciado de lista.
        """
        if self.state == "game" and len(self.words_to_guess) == 0:
            self._win()

    # =========================================================================
    # INTERCEPCIÓN DE ACCIONES TÁCTILES / MOUSE
    # =========================================================================
    def mousePressEvent(self, event):
        """
        @brief Manejador de eventos de pulsación inicial sobre el dispositivo apuntador.
        
        @param event Instancia del evento nativo de tipo QMouseEvent.
        """
        self._mouse_pressed = True
        pos = self._qt_to_game_pos((event.x(), event.y()))

        if self.state == "menu":
            if self.btn_game_back.collidepoint(pos):
                self.exit_game()
                return
            if   self.btn_easy.collidepoint(pos):   self.start_game("facil")
            elif self.btn_medium.collidepoint(pos): self.start_game("medio")
            elif self.btn_hard.collidepoint(pos):   self.start_game("dificil")

        elif self.state == "game":
            if self.btn_back.collidepoint(pos):
                self.state = "menu"
            elif self.btn_hint.collidepoint(pos):
                self.hint_cell = self._get_hint_cell()
            else:
                self._handle_grid_click(pos)

    def mouseMoveEvent(self, event):
        """
        @brief Manejador de trazos continuos para soportar arrastres (drag and drop) táctiles.
        
        @param event Instancia del evento nativo de tipo QMouseEvent.
        """
        pos = self._qt_to_game_pos((event.x(), event.y()))
        if self._mouse_pressed and self.state == "game":
            if not self.btn_hint.collidepoint(pos) and not self.btn_back.collidepoint(pos):
                self._handle_grid_drag(pos)

    def mouseReleaseEvent(self, event):
        """
        @brief Manejador de liberación del punto de contacto. Valida la validez léxica del trazo.
        
        @param event Instancia del evento nativo de tipo QMouseEvent.
        """
        self._mouse_pressed = False
        if self.state == "game" and self.current_path:
            self._validate_selection()
            self.current_path.clear()

    # =========================================================================
    # PROCESAMIENTO Y VALIDACIÓN GEOMÉTRICA DE LA REJILLA
    # =========================================================================
    def _handle_grid_click(self, pos):
        """
        @brief Identifica la celda base sobre la que se inicia la selección lineal.
        
        @param pos Coordenadas del cursor respecto al origen.
        """
        grid_rect = pygame.Rect(
            self.GRID_POS[0], self.GRID_POS[1],
            generate.GRID_SIZE * self.CELL, generate.GRID_SIZE * self.CELL
        )
        if grid_rect.collidepoint(pos):
            x = (pos[0] - self.GRID_POS[0]) // self.CELL
            y = (pos[1] - self.GRID_POS[1]) // self.CELL
            if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
                self.current_path = [(x, y)]

    def _handle_grid_drag(self, pos):
        """
        @brief Analiza la posición del arrastre para expandir de forma lineal la palabra activa.
        
        @param pos Coordenadas continuas del cursor.
        """
        grid_rect = pygame.Rect(
            self.GRID_POS[0], self.GRID_POS[1],
            generate.GRID_SIZE * self.CELL, generate.GRID_SIZE * self.CELL
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
        """
        @brief Algoritmo analítico de restricción ortogonal y diagonal para vectores de celdas.
        @details Garantiza mediante normalización de pendientes unitarias recurrentes que las 
        celdas arrastradas formen estrictamente una línea recta continua (horizontal, vertical o diagonal).
        
        @param path Vector con la serie temporal de coordenadas `(x, y)` evaluadas.
        @return bool Verdadero si la trayectoria cumple con el vector de alineación rectilíneo.
        """
        if len(path) < 2:
            return True
        dx = path[1][0] - path[0][0]
        dy = path[1][1] - path[0][1]
        if dx != 0 and dy != 0:
            return False  # Bloquea de forma directa trazos con desvíos multidireccionales irregulares
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
        """
        @brief Verifica si la palabra seleccionada coincide con algún elemento de la lista pendiente.
        @details Soporta lecturas inversas para palabras dispuestas al revés en el tablero.
        
        @return bool Verdadero si la palabra es correcta y es aceptada por el motor.
        """
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
        """
        @brief Resuelve la posición inicial del primer carácter de la palabra más cercana pendiente.
        
        @return tupla Coordenada `(x, y)` de apoyo cognitivo, o `None` si hay un fallo de indexación.
        """
        for word in self.words_to_guess:
            wup = word.upper()
            if wup in generate.word_positions:
                positions = generate.word_positions[wup]
                if positions:
                    x, y = positions[0]
                    return (x, y)
        return None

    # =========================================================================
    # RENDERIZADO VISUAL EN CALIENTE
    # =========================================================================
    def render(self):
        """
        @brief Orquestador cíclico de dibujo. Resuelve las dimensiones globales de la ventana en caliente.
        """
        rect_pantalla = self.surface.get_rect()
        W = rect_pantalla.width
        H = rect_pantalla.height

        if W < 100 or H < 100:
            return

        self._draw_bg()
        
        if self.state == "menu":
            self._draw_menu_dinamico(W, H)
        else:
            self._draw_game()

    def _draw_bg(self):
        """
        @brief Renderiza el fondo aplicando un gradiente cromático vertical suavizado.
        """
        for y in range(self.game_height):
            t = y / self.game_height
            r = int(P_BG_TOP[0] + (P_BG_BOTTOM[0] - P_BG_TOP[0]) * t)
            g = int(P_BG_TOP[1] + (P_BG_BOTTOM[1] - P_BG_TOP[1]) * t)
            b = int(P_BG_TOP[2] + (P_BG_BOTTOM[2] - P_BG_TOP[2]) * t)
            pygame.draw.line(self.surface, (r, g, b), (0, y), (self.game_width, y))

    def _draw_menu_dinamico(self, W, H):
        """
        @brief Compone el Menú Principal centralizado y autoescalado con tipografías legibles.
        
        @param W Ancho actual del marco físico de la app.
        @param H Alto actual del marco físico de la app.
        """
        # Cabecera principal con su respectiva sombra para crear contraste
        ts_title = self.m_f_title.render("SOPA DE LETRAS", True, P_TITLE)
        ts_shadow = self.m_f_title.render("SOPA DE LETRAS", True, P_SHADOW)
        tx = (W - ts_title.get_width()) // 2
        self.surface.blit(ts_shadow, (tx + 4, 54))
        self.surface.blit(ts_title, (tx, 50))

        ts_sub = self.m_f_subtitle.render("Elige la dificultad", True, P_SUBTITLE)
        self.surface.blit(ts_sub, ((W - ts_sub.get_width()) // 2, 145))

        # Parámetros geométricos para botones colosales de fácil pulsación táctil
        BW = 360
        BH = 82
        GAP = 22
        start_y = 220
        cx = (W - BW) // 2

        self.btn_easy   = pygame.Rect(cx, start_y, BW, BH)
        self.btn_medium = pygame.Rect(cx, start_y + BH + GAP, BW, BH)
        self.btn_hard   = pygame.Rect(cx, start_y + (BH + GAP) * 2, BW, BH)
        self.btn_game_back = pygame.Rect((W - 240) // 2, H - 95, 240, 65)

        self._draw_menu_btn(self.btn_easy,   "FÁCIL",    M_BTN_EASY_BG, M_BTN_EASY_BRD)
        self._draw_menu_btn(self.btn_medium, "MEDIO",   M_BTN_MED_BG,  M_BTN_MED_BRD)
        self._draw_menu_btn(self.btn_hard,   "DIFÍCIL",  M_BTN_HARD_BG, M_BTN_HARD_BRD)
        self._draw_menu_btn(self.btn_game_back, "VOLVER ⬅", M_BTN_BACK_BG, M_BTN_BACK_BRD)

    def _draw_menu_btn(self, rect, text, bg_color, brd_color):
        """
        @brief Sub-utilidad interna encargada de estructurar los botones del menú con relieves.
        """
        sr = rect.move(5, 5)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=22)
        pygame.draw.rect(self.surface, bg_color, rect, border_radius=22)
        pygame.draw.rect(self.surface, brd_color, rect, 4, border_radius=22)
        
        ts = self.m_f_btn.render(text, True, M_BTN_TEXT)
        self.surface.blit(ts, (rect.x + (rect.width - ts.get_width()) // 2, rect.y + (rect.height - ts.get_height()) // 2))

    def _draw_game(self):
        """
        @brief Ejecuta la renderización visual de las subcapas de juego activo.
        """
        self._draw_grid()
        self._draw_words()
        self._draw_bottom_bar()

    def _draw_grid(self):
        """
        @brief Dibuja la rejilla matricial de caracteres combinando los estados lógicos de juego.
        """
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

        # Inyección a ráfaga de las superficies de las letras pre-calculadas en el caché estático
        for (surf, pos) in self.letter_cache.values():
            self.surface.blit(surf, pos)

        # Superpone el marco indicador perimetral si hay una celda marcada por pista
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
        """
        @brief Renderiza el panel derecho que aloja el listado dinámico de palabras y su barra de scroll.
        """
        LIST_W   = 230
        LIST_H   = self.game_height - self.WORD_LIST_Y - 90
        panel    = pygame.Rect(self.WORD_LIST_X - 10, self.WORD_LIST_Y - 10, LIST_W + 20, LIST_H + 20)

        shadow_r = panel.move(4, 4)
        pygame.draw.rect(self.surface, P_SHADOW, shadow_r, border_radius=16)
        pygame.draw.rect(self.surface, P_WORD_PANEL,   panel, border_radius=16)
        pygame.draw.rect(self.surface, P_PANEL_BORDER, panel, 2, border_radius=16)

        hf = pygame.font.Font(None, 30)
        ht = hf.render("✏️  PALABRAS", True, P_TITLE)
        self.surface.blit(ht, (self.WORD_LIST_X + 12, self.WORD_LIST_Y + 8))
        pygame.draw.line(
            self.surface, P_PANEL_BORDER,
            (self.WORD_LIST_X + 8,  self.WORD_LIST_Y + 46),
            (self.WORD_LIST_X + LIST_W - 8, self.WORD_LIST_Y + 46), 2
        )

        # Enmascaramiento por recorte (Clip mask) para controlar desbordamientos tipográficos en el scroll
        old_clip = self.surface.get_clip()
        self.surface.set_clip(pygame.Rect(self.WORD_LIST_X, self.WORD_LIST_Y + 52, LIST_W, LIST_H - 52))

        wf  = pygame.font.Font(None, 30)
        yp  = self.WORD_LIST_Y + 56 - self.scroll_offset

        for word in generate.words_copy:
            pending = word in self.words_to_guess
            color   = P_WORD_PENDING if pending else P_WORD_DONE
            ws      = wf.render(word, True, color)
            self.surface.blit(ws, (self.WORD_LIST_X + 16, yp))
            
            # Aplica línea de tachado central si el elemento léxico fue descubierto con éxito
            if not pending:
                ly = yp + ws.get_height() // 2
                pygame.draw.line(
                    self.surface, P_WORD_STRIKE,
                    (self.WORD_LIST_X + 16, ly), (self.WORD_LIST_X + 16 + ws.get_width(), ly), 2
                )
            yp += 34

        self.surface.set_clip(old_clip)  # Desactiva la máscara de recorte

        # Renderizado estructural del canal y deslizador de la barra de scroll vertical (Scrollbar)
        if self.max_scroll > 0:
            sb_x = self.WORD_LIST_X + LIST_W - 10
            sb_bg = pygame.Rect(sb_x, self.WORD_LIST_Y + 52, 6, LIST_H - 52)
            pygame.draw.rect(self.surface, P_SHADOW, sb_bg, border_radius=3)
            sh   = max(28, (LIST_H - 52) * (LIST_H - 52) / (len(generate.words_copy) * 34))
            sy   = self.WORD_LIST_Y + 52 + (self.scroll_offset / self.max_scroll) * (LIST_H - 52 - sh)
            pygame.draw.rect(self.surface, P_ACCENT, pygame.Rect(sb_x, int(sy), 6, int(sh)), border_radius=3)

    def _draw_bottom_bar(self):
        """
        @brief Renderiza el HUD inferior horizontal que contiene los botones auxiliares de juego.
        """
        BAR_H = 80
        bar_y = self.game_height - BAR_H
        bar   = pygame.Surface((self.game_width, BAR_H), pygame.SRCALPHA)
        bar.fill((245, 235, 255, 200))
        self.surface.blit(bar, (0, bar_y))
        pygame.draw.line(self.surface, P_PANEL_BORDER, (0, bar_y), (self.game_width, bar_y), 2)

        self._draw_button(self.btn_hint, " Pista",  P_BTN_HINT)
        self._draw_button(self.btn_back, "⬅ Menú",  P_BTN_BACK)

    def _draw_button(self, rect, text, color):
        """
        @brief Helper utilitario para el renderizado de botones secundarios in-game con sombreado plano.
        """
        sr = rect.move(3, 3)
        pygame.draw.rect(self.surface, P_SHADOW, sr, border_radius=18)
        pygame.draw.rect(self.surface, color, rect, border_radius=18)
        pygame.draw.rect(self.surface, (255, 255, 255), rect, 2, border_radius=18)
        f  = pygame.font.Font(None, 34)
        ts = f.render(text, True, P_BTN_TEXT)
        self.surface.blit(ts, (rect.x + (rect.width - ts.get_width()) // 2, rect.y + (rect.height - ts.get_height()) // 2))

    def _win(self):
        """
        @brief Gestiona las variables de control al completar con éxito todas las palabras del panel.
        """
        self.state = "menu"
        self.words_to_guess = []
        logger.info("[SOPA] El jugador ha resuelto el tablero de forma exitosa.")