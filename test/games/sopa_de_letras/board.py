"""
@file sopa_letras.py
@brief Sopa de Letras optimizada para Raspberry Pi con interfaz amigable para personas mayores.
@version 2.0 - Con autoajuste dinámico completo y botones funcionales
@author Tu Nombre
@date 2026
"""

import pygame
import generate
import os
import random
import math

# Inicialización de Pygame
try:
    pygame.init()
    pygame.mixer.init()
    print("[OK] Pygame inicializado correctamente")
except Exception as e:
    print(f"[ERROR] Fallo al inicializar Pygame: {e}")
    exit(1)

# ============================================================================
# CONSTANTES DE CONFIGURACIÓN
# ============================================================================

SCREEN_W = 800
SCREEN_H = 600

# Tamaños base (se recalcularán dinámicamente)
BASE_CELL = 45
CELL = BASE_CELL

# Posiciones (se recalcularán dinámicamente)
GRID_POS = (0, 0)
WORD_LIST_X = 0
WORD_LIST_Y = 40

# Colores
COLOR_BACKGROUND = (245, 245, 220)
COLOR_CELL = (255, 255, 255)
COLOR_BORDER = (100, 100, 100)
COLOR_SELECTED = (100, 200, 255)
COLOR_HINT = (255, 215, 0)
COLOR_TITLE = (120, 50, 120)
COLOR_WORD_FOUND = (0, 255, 255)
COLOR_BUTTON = (200, 200, 200)
COLOR_BUTTON_EASY = (173, 216, 230)
COLOR_BUTTON_MEDIUM = (144, 238, 144)
COLOR_BUTTON_HARD = (255, 228, 181)
COLOR_FONT = (0, 0, 0)
COLOR_SCROLLBAR = (180, 180, 180)
COLOR_SCROLLBAR_BG = (220, 220, 220)

# Configuración
FPS = 24
MAX_CLOUDS = 3
MAX_FLOWERS = 6

# ============================================================================
# VARIABLES GLOBALES
# ============================================================================

screen = None
state = "menu"
difficulty = None
selected = []
current_path = []
words_to_guess = []
hint_cell = None
scroll_offset = 0
max_scroll = 0
clock = None
gradient_surf = None
glow_surf = None
clouds = []
flowers = []
letter_cache = {}

# Botones
btn_easy = None
btn_medium = None
btn_hard = None
btn_hint = None
btn_back = None

# ============================================================================
# FUNCIONES DE AUTOAJUSTE
# ============================================================================

def calculate_optimal_layout():
    """
    @brief Calcula el layout óptimo según el tamaño del grid.
    """
    global CELL, GRID_POS, WORD_LIST_X
    
    grid_size = generate.GRID_SIZE
    
    # Calcular tamaño de celda óptimo
    list_width = 230
    margin_left = 20
    margin_right = 20
    
    available_width = SCREEN_W - list_width - margin_left - margin_right
    max_cell_by_width = available_width // grid_size
    
    available_height = SCREEN_H - 120
    max_cell_by_height = available_height // grid_size
    
    optimal_cell = min(max_cell_by_width, max_cell_by_height, BASE_CELL)
    optimal_cell = max(optimal_cell, 25)
    
    CELL = optimal_cell
    
    grid_width = grid_size * CELL
    grid_x = margin_left
    GRID_POS = (grid_x, 60)
    WORD_LIST_X = GRID_POS[0] + grid_width + 20
    
    if WORD_LIST_X + list_width > SCREEN_W - margin_right:
        new_grid_x = max(margin_left, SCREEN_W - list_width - grid_width - 10)
        GRID_POS = (new_grid_x, 60)
        WORD_LIST_X = GRID_POS[0] + grid_width + 15
    
    print(f"[LAYOUT] Grid: {grid_size}x{grid_size}, CELL={CELL}, ListX={WORD_LIST_X}")

def update_scroll_range():
    """Actualiza el rango máximo del scroll."""
    global max_scroll, scroll_offset
    
    if len(generate.words_copy) > 0:
        words_height = len(generate.words_copy) * 32
        list_height = SCREEN_H - 100
        
        if words_height > list_height:
            max_scroll = words_height - list_height
        else:
            max_scroll = 0
        
        scroll_offset = max(0, min(scroll_offset, max_scroll))

# ============================================================================
# FUNCIONES DE INICIALIZACIÓN
# ============================================================================

def init_screen():
    """Inicializa la pantalla."""
    global screen, clock
    try:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Sopa de Letras - Juego para Mayores")
        clock = pygame.time.Clock()
        print(f"[OK] Pantalla: {SCREEN_W}x{SCREEN_H}")
        return True
    except Exception as e:
        print(f"[ERROR] Pantalla: {e}")
        return False

def init_buttons():
    """Inicializa botones."""
    global btn_easy, btn_medium, btn_hard, btn_hint, btn_back
    
    btn_easy = pygame.Rect(SCREEN_W//2 - 125, 200, 250, 60)
    btn_medium = pygame.Rect(SCREEN_W//2 - 125, 280, 250, 60)
    btn_hard = pygame.Rect(SCREEN_W//2 - 125, 360, 250, 60)
    btn_hint = pygame.Rect(SCREEN_W - 150, SCREEN_H - 70, 130, 50)
    btn_back = pygame.Rect(20, SCREEN_H - 70, 130, 50)

def init_gradient_background():
    """Crea fondo degradado."""
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    start_color = (255, 248, 225)
    end_color = (230, 240, 255)
    
    for i in range(SCREEN_H):
        ratio = i / SCREEN_H
        r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
        g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
        b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
        pygame.draw.line(surf, (r, g, b), (0, i), (SCREEN_W, i))
    
    return surf

def init_decorations():
    """Inicializa decoraciones."""
    global clouds, flowers
    
    if generate.GRID_SIZE > 0:
        grid_width = generate.GRID_SIZE * CELL
        
        clouds = []
        for _ in range(MAX_CLOUDS):
            cloud = {
                'x': random.randint(GRID_POS[0], GRID_POS[0] + grid_width),
                'y': random.randint(GRID_POS[1], GRID_POS[1] + grid_width // 2),
                'r': random.randint(20, 30),
                'speed': random.uniform(0.05, 0.15),
                'offset': random.uniform(0, 2 * math.pi)
            }
            clouds.append(cloud)
        
        flowers = []
        for _ in range(MAX_FLOWERS):
            flower = {
                'x': random.randint(GRID_POS[0], GRID_POS[0] + grid_width),
                'y': random.randint(GRID_POS[1], GRID_POS[1] + grid_width),
                'r': random.randint(3, 5),
                'color': (random.randint(220, 255), random.randint(180, 220), random.randint(200, 255))
            }
            flowers.append(flower)

def init_glow_effect():
    """Crea efecto de brillo."""
    surf = pygame.Surface((CELL, CELL), pygame.SRCALPHA)
    center = CELL // 2
    max_radius = CELL // 2
    
    for radius in range(max_radius, 0, -2):
        alpha = int(100 * (1 - radius / max_radius))
        pygame.draw.circle(surf, (0, 200, 255, alpha), (center, center), radius)
    
    return surf

def cache_letters():
    """Pre-renderiza letras."""
    global letter_cache, glow_surf
    
    letter_cache = {}
    font_size = max(int(CELL * 0.65), 20)
    font = pygame.font.Font(None, font_size)
    
    glow_surf = init_glow_effect()
    
    for y, row in enumerate(generate.grid):
        for x, letter in enumerate(row):
            text_surf = font.render(letter.upper(), True, COLOR_FONT)
            text_x = GRID_POS[0] + x * CELL + (CELL - text_surf.get_width()) // 2
            text_y = GRID_POS[1] + y * CELL + (CELL - text_surf.get_height()) // 2
            letter_cache[(x, y)] = (text_surf, (text_x, text_y))

def init_game_resources():
    """Inicializa recursos."""
    global gradient_surf
    
    if not init_screen():
        return False
    
    init_buttons()
    gradient_surf = init_gradient_background()
    
    print("[OK] Recursos inicializados")
    return True

# ============================================================================
# FUNCIONES DE DIBUJO
# ============================================================================

def draw_button(rect, text, bg_color, border_color=(100, 100, 100), font_size=32):
    """Dibuja botón redondeado."""
    pygame.draw.rect(screen, bg_color, rect, border_radius=12)
    pygame.draw.rect(screen, border_color, rect, 3, border_radius=12)
    
    font = pygame.font.Font(None, font_size)
    text_surf = font.render(text, True, COLOR_FONT)
    text_x = rect.x + (rect.width - text_surf.get_width()) // 2
    text_y = rect.y + (rect.height - text_surf.get_height()) // 2
    screen.blit(text_surf, (text_x, text_y))

def draw_menu():
    """Dibuja menú principal."""
    screen.blit(gradient_surf, (0, 0))
    
    title_font = pygame.font.Font(None, 64)
    title_text = "SOPA DE LETRAS"
    title_shadow = title_font.render(title_text, True, (200, 200, 200))
    title_surf = title_font.render(title_text, True, COLOR_TITLE)
    
    screen.blit(title_shadow, (SCREEN_W//2 - title_shadow.get_width()//2 + 3, 55))
    screen.blit(title_surf, (SCREEN_W//2 - title_surf.get_width()//2, 50))
    
    subtitle_font = pygame.font.Font(None, 28)
    subtitle_text = "Selecciona la dificultad"
    subtitle_surf = subtitle_font.render(subtitle_text, True, (100, 100, 100))
    screen.blit(subtitle_surf, (SCREEN_W//2 - subtitle_surf.get_width()//2, 130))
    
    draw_button(btn_easy, "FÁCIL", COLOR_BUTTON_EASY)
    draw_button(btn_medium, "MEDIO", COLOR_BUTTON_MEDIUM)
    draw_button(btn_hard, "DIFÍCIL", COLOR_BUTTON_HARD)


def draw_game_board():
    """Dibuja el tablero."""
    for y in range(generate.GRID_SIZE):
        for x in range(generate.GRID_SIZE):
            rect = pygame.Rect(
                GRID_POS[0] + x * CELL,
                GRID_POS[1] + y * CELL,
                CELL, CELL
            )
            
            cell_selected = [x * CELL, y * CELL] in selected
            
            if cell_selected:
                pygame.draw.rect(screen, COLOR_SELECTED, rect, 0, border_radius=6)
            elif (x, y) in current_path:
                if glow_surf:
                    screen.blit(glow_surf, rect.topleft)
                else:
                    pygame.draw.rect(screen, (200, 230, 255), rect, 0, border_radius=6)
            else:
                pygame.draw.rect(screen, COLOR_CELL, rect, 0, border_radius=6)
            
            pygame.draw.rect(screen, COLOR_BORDER, rect, 2, border_radius=6)
    
    # Dibujar todas las letras
    for (text_surf, pos) in letter_cache.values():
        screen.blit(text_surf, pos)
    
    # Dibujar la celda de pista
    if hint_cell is not None:
        x, y = hint_cell
        # Verificar que las coordenadas sean válidas
        if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
            hint_rect = pygame.Rect(
                GRID_POS[0] + x * CELL,
                GRID_POS[1] + y * CELL,
                CELL, CELL
            )
            # Dibujar un borde amarillo más grueso para la pista
            pygame.draw.rect(screen, COLOR_HINT, hint_rect, 5, border_radius=6)
            # Opcional: dibujar un efecto de brillo
            if glow_surf:
                screen.blit(glow_surf, hint_rect.topleft)

def draw_word_list():
    """Dibuja lista de palabras con scroll."""
    if WORD_LIST_X <= 0:
        return
    
    list_width = 230
    list_height = SCREEN_H - 100
    list_rect = pygame.Rect(WORD_LIST_X, WORD_LIST_Y, list_width, list_height)
    pygame.draw.rect(screen, (255, 250, 205), list_rect, border_radius=12)
    pygame.draw.rect(screen, COLOR_BORDER, list_rect, 2, border_radius=12)
    
    title_font = pygame.font.Font(None, 24)
    title_surf = title_font.render("PALABRAS:", True, COLOR_TITLE)
    screen.blit(title_surf, (WORD_LIST_X + 15, WORD_LIST_Y + 10))
    
    pygame.draw.line(screen, COLOR_BORDER,
                    (WORD_LIST_X + 10, WORD_LIST_Y + 40),
                    (WORD_LIST_X + list_width - 10, WORD_LIST_Y + 40), 2)
    
    list_area = pygame.Rect(WORD_LIST_X, WORD_LIST_Y + 45, list_width, list_height - 45)
    old_clip = screen.get_clip()
    screen.set_clip(list_area)
    
    word_font = pygame.font.Font(None, 26)
    y_pos = WORD_LIST_Y + 45 - scroll_offset
    
    for word in generate.words_copy:
        if WORD_LIST_Y + 40 <= y_pos <= WORD_LIST_Y + list_height:
            if word in words_to_guess:
                word_surf = word_font.render(word, True, COLOR_FONT)
                screen.blit(word_surf, (WORD_LIST_X + 15, y_pos))
            else:
                word_surf = word_font.render(word, True, (150, 150, 150))
                screen.blit(word_surf, (WORD_LIST_X + 15, y_pos))
                line_y = y_pos + word_surf.get_height() // 2
                pygame.draw.line(screen, COLOR_WORD_FOUND,
                               (WORD_LIST_X + 15, line_y),
                               (WORD_LIST_X + 15 + word_surf.get_width(), line_y), 2)
        
        y_pos += 32
    
    screen.set_clip(old_clip)
    
    if max_scroll > 0:
        scroll_bg = pygame.Rect(WORD_LIST_X + list_width - 15, WORD_LIST_Y + 45, 8, list_height - 45)
        pygame.draw.rect(screen, COLOR_SCROLLBAR_BG, scroll_bg, border_radius=4)
        
        scroll_height = (list_height - 45) * (list_height - 45) / (len(generate.words_copy) * 32)
        scroll_height = max(30, min(scroll_height, list_height - 45))
        scroll_y = WORD_LIST_Y + 45 + (scroll_offset / max_scroll) * (list_height - 45 - scroll_height)
        scroll_bar = pygame.Rect(WORD_LIST_X + list_width - 15, scroll_y, 8, scroll_height)
        pygame.draw.rect(screen, COLOR_SCROLLBAR, scroll_bar, border_radius=4)

def draw_decorations():
    """Dibuja decoraciones."""
    for cloud in clouds:
        pygame.draw.circle(screen, (255, 255, 240), 
                          (int(cloud['x']), int(cloud['y'])), 
                          cloud['r'])
    
    for flower in flowers:
        pygame.draw.circle(screen, flower['color'], 
                          (int(flower['x']), int(flower['y'])), 
                          flower['r'])

def draw_game_ui():
    """Dibuja UI del juego."""
    draw_button(btn_hint, "PISTA", (255, 215, 0), font_size=28)
    draw_button(btn_back, "MENÚ", COLOR_BUTTON, font_size=28)

# ============================================================================
# FUNCIONES DE LÓGICA
# ============================================================================

def update_decorations():
    """Actualiza decoraciones."""
    if not clouds:
        return
    
    time_ms = pygame.time.get_ticks() / 1000.0
    grid_width = generate.GRID_SIZE * CELL
    
    for cloud in clouds:
        cloud['x'] += cloud['speed']
        cloud['y'] += 0.5 * math.sin(time_ms + cloud['offset'])
        
        if cloud['x'] - cloud['r'] > GRID_POS[0] + grid_width:
            cloud['x'] = GRID_POS[0] - cloud['r']
            cloud['y'] = random.randint(GRID_POS[1], GRID_POS[1] + grid_width // 2)

def get_hint_cell():
    """
    @brief Obtiene la primera celda de la primera palabra no encontrada.
    @return Tupla (x, y) con coordenadas de celda o None si no hay pista.
    """
    if words_to_guess and len(words_to_guess) > 0:
        # Buscar la primera palabra que aún no ha sido encontrada
        for word in words_to_guess:
            # Normalizar la palabra para comparación
            word_upper = word.upper()
            if word_upper in generate.word_positions:
                # Obtener la primera posición de la palabra
                positions = generate.word_positions[word_upper]
                if positions and len(positions) > 0:
                    # Devolver coordenadas de celda (x, y) en índices de grid
                    x, y = positions[0]
                    print(f"[DEBUG] Pista para palabra '{word}' en celda ({x}, {y})")
                    return (x, y)  # Devolver índices, no píxeles
    
    print("[DEBUG] No hay pista disponible")
    return None

def handle_grid_click(pos):
    """Maneja clic en grid."""
    global current_path
    
    grid_rect = pygame.Rect(GRID_POS[0], GRID_POS[1], 
                           generate.GRID_SIZE * CELL, 
                           generate.GRID_SIZE * CELL)
    
    if grid_rect.collidepoint(pos):
        x = (pos[0] - GRID_POS[0]) // CELL
        y = (pos[1] - GRID_POS[1]) // CELL
        
        if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
            current_path = [(x, y)]
            return True
    
    return False

def handle_grid_drag(pos):
    """Maneja arrastre."""
    grid_rect = pygame.Rect(GRID_POS[0], GRID_POS[1],
                           generate.GRID_SIZE * CELL,
                           generate.GRID_SIZE * CELL)
    
    if grid_rect.collidepoint(pos):
        x = (pos[0] - GRID_POS[0]) // CELL
        y = (pos[1] - GRID_POS[1]) // CELL
        
        if 0 <= x < generate.GRID_SIZE and 0 <= y < generate.GRID_SIZE:
            cell = (x, y)
            if cell not in current_path:
                # Verificar que sea línea recta antes de añadir
                temp_path = current_path + [cell]
                if is_straight_line(temp_path):
                    current_path.append(cell)

def handle_scroll(event):
    """Maneja scroll del mouse."""
    global scroll_offset
    
    if event.type == pygame.MOUSEWHEEL:
        list_rect = pygame.Rect(WORD_LIST_X, WORD_LIST_Y, 230, SCREEN_H - 100)
        if list_rect.collidepoint(pygame.mouse.get_pos()):
            scroll_offset -= event.y * 30
            scroll_offset = max(0, min(scroll_offset, max_scroll))

def validate_selection():
    """Valida selección."""
    global selected, words_to_guess, hint_cell
    
    if len(current_path) < 2:
        return False
    
    # Obtener la palabra formada
    word = "".join(generate.grid[y][x] for (x, y) in current_path)
    
    # Verificar si es válida (o su inversa)
    found_word = None
    if word in words_to_guess:
        found_word = word
    elif word[::-1] in words_to_guess:
        found_word = word[::-1]
    
    if found_word:
        # Marcar celdas como encontradas
        for (x, y) in current_path:
            selected.append([x * CELL, y * CELL])
        
        # Eliminar palabra de la lista
        words_to_guess.remove(found_word)
        
        # Limpiar pista si era esta palabra
        if hint_cell is not None:
            # Verificar si la celda de pista está en el path encontrado
            for (x, y) in current_path:
                if hint_cell == (x, y):  # Comparar con tupla, no con rectángulo
                    hint_cell = None
                    print("[DEBUG] Pista limpiada - palabra encontrada")
                    break
        
        update_scroll_range()
        print(f"[DEBUG] Palabra encontrada: {found_word}")
        return True
    
    return False


def is_straight_line(path):
    """Verifica si una ruta es línea recta horizontal o vertical."""
    if len(path) < 2:
        return True
    
    # Obtener dirección del primer paso
    dx = path[1][0] - path[0][0]
    dy = path[1][1] - path[0][1]
    
    # Solo permitir horizontal (dx != 0, dy == 0) o vertical (dx == 0, dy != 0)
    if dx != 0 and dy != 0:
        return False
    
    # Normalizar dirección
    if dx != 0:
        dx = dx // abs(dx)
    if dy != 0:
        dy = dy // abs(dy)
    
    # Verificar que todos los pasos sigan la misma dirección
    for i in range(1, len(path)):
        step_x = path[i][0] - path[i-1][0]
        step_y = path[i][1] - path[i-1][1]
        
        # Normalizar paso
        if step_x != 0:
            step_x = step_x // abs(step_x)
        if step_y != 0:
            step_y = step_y // abs(step_y)
        
        if step_x != dx or step_y != dy:
            return False
    
    return True

def check_victory():
    """Verifica victoria."""
    return len(words_to_guess) == 0

def show_victory_screen():
    """Muestra pantalla de victoria."""
    screen.fill((255, 240, 245))
    
    font_big = pygame.font.Font(None, 72)
    win_text = font_big.render("¡HAS GANADO!", True, (180, 50, 180))
    screen.blit(win_text, (SCREEN_W//2 - win_text.get_width()//2, SCREEN_H//2 - 50))
    
    font_small = pygame.font.Font(None, 36)
    congrats_text = font_small.render("¡Felicidades!", True, (100, 100, 100))
    screen.blit(congrats_text, (SCREEN_W//2 - congrats_text.get_width()//2, SCREEN_H//2 + 20))
    
    pygame.display.flip()
    pygame.time.delay(1500)
    
    # Regenerar tablero
    generate.generate_board()
    global words_to_guess, selected, current_path, hint_cell, scroll_offset
    words_to_guess = generate.words_copy[:]
    selected = []
    current_path = []
    hint_cell = None
    scroll_offset = 0
    
    # Recalcular layout
    calculate_optimal_layout()
    cache_letters()
    init_decorations()
    update_scroll_range()

def start_game(selected_difficulty):
    """Inicia un nuevo juego con la dificultad seleccionada."""
    global state, difficulty, words_to_guess, selected, current_path, hint_cell, scroll_offset
    
    difficulty = selected_difficulty
    generate.set_difficulty(difficulty)
    generate.generate_board()
    
    words_to_guess = generate.words_copy[:]
    selected = []
    current_path = []
    hint_cell = None
    scroll_offset = 0
    
    # Calcular layout óptimo
    calculate_optimal_layout()
    cache_letters()
    init_decorations()
    update_scroll_range()
    
    state = "game"

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def run_game():
    """Bucle principal."""
    global state
    
    running = True
    frame_count = 0
    
    while running:
        clock.tick(FPS)
        frame_count += 1
        
        screen.blit(gradient_surf, (0, 0))
        
        if frame_count % 2 == 0 and state == "game":
            update_decorations()
        
        draw_decorations()
        
        if state == "menu":
            draw_menu()
        elif state == "game":
            draw_game_board()
            draw_word_list()
            draw_game_ui()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Scroll en juego (siempre procesar)
            if event.type == pygame.MOUSEWHEEL and state == "game":
                list_rect = pygame.Rect(WORD_LIST_X, WORD_LIST_Y, 230, SCREEN_H - 100)
                if list_rect.collidepoint(pygame.mouse.get_pos()):
                    scroll_offset -= event.y * 30
                    scroll_offset = max(0, min(scroll_offset, max_scroll))
            
            # Eventos del menú
            elif state == "menu" and event.type == pygame.MOUSEBUTTONDOWN:
                if btn_easy.collidepoint(event.pos):
                    start_game("facil")
                elif btn_medium.collidepoint(event.pos):
                    start_game("medio")
                elif btn_hard.collidepoint(event.pos):
                    start_game("dificil")
            
            # Eventos del juego
            elif state == "game":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_hint.collidepoint(event.pos):
                        hint_cell = get_hint_cell()
                    elif btn_back.collidepoint(event.pos):
                        state = "menu"
                    else:
                        handle_grid_click(event.pos)
                
                elif event.type == pygame.MOUSEMOTION:
                    if pygame.mouse.get_pressed()[0] and not btn_hint.collidepoint(event.pos):
                        handle_grid_drag(event.pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if current_path:
                        if validate_selection():
                            pass
                        current_path.clear()
        
        if state == "game" and check_victory():
            show_victory_screen()
        
        pygame.display.flip()
    
    pygame.quit()

# ============================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("SOPA DE LETRAS - Versión para Raspberry Pi")
    print("Optimizado para personas mayores con autoajuste")
    print("=" * 50)
    
    if init_game_resources():
        run_game()
    else:
        print("[ERROR] No se pudo iniciar el juego")
        exit(1)