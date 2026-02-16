import pygame
import sys

# --- Configuración de Pantalla ---
# Las pantallas de 10" suelen ser 1280x800 o 1024x600.
# Ajusta el tamaño de la ventana según tu resolución.
WIDTH, HEIGHT = 800, 800 # Un cuadrado grande funciona bien
GRID_SIZE = 9
CELL_SIZE = WIDTH // GRID_SIZE
FPS = 30

# Colores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
BLUE = (50, 50, 255)

# --- Inicialización ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sudoku Táctil - RPi")
font = pygame.font.SysFont("Arial", 40)

# --- Tablero Ejemplo (0 = vacío) ---
board = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9]
]

# --- Funciones de Lógica ---
def draw_grid():
    """Dibuja el tablero de Sudoku."""
    for i in range(GRID_SIZE + 1):
        thickness = 4 if i % 3 == 0 else 1
        # Líneas horizontales
        pygame.draw.line(screen, BLACK, (0, i * CELL_SIZE), (WIDTH, i * CELL_SIZE), thickness)
        # Líneas verticales
        pygame.draw.line(screen, BLACK, (i * CELL_SIZE, 0), (i * CELL_SIZE, HEIGHT), thickness)

def draw_numbers():
    """Dibuja los números en el tablero."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c] != 0:
                text = font.render(str(board[r][c]), True, BLACK)
                # Centrar el número en la celda
                screen.blit(text, (c * CELL_SIZE + CELL_SIZE//3, r * CELL_SIZE + CELL_SIZE//4))

def get_cell_from_pos(pos):
    """Convierte la posición táctil en coordenadas de cuadrícula."""
    x, y = pos
    row = y // CELL_SIZE
    col = x // CELL_SIZE
    return row, col

# --- Bucle Principal ---
def main():
    running = True
    selected_cell = None
    
    while running:
        screen.fill(WHITE)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            # Interacción Táctil (Manejado como mouse)
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                selected_cell = get_cell_from_pos(pos)
                print(f"Celda seleccionada: {selected_cell}") # Depuración
                
            # Entrada de números (aquí se necesitaría un teclado numérico en pantalla)
            if event.type == pygame.KEYDOWN and selected_cell:
                if event.key >= pygame.K_1 and event.key <= pygame.K_9:
                    r, c = selected_cell
                    board[r][c] = event.key - pygame.K_0

        draw_grid()
        draw_numbers()
        
        # Resaltar celda seleccionada
        if selected_cell:
            r, c = selected_cell
            pygame.draw.rect(screen, BLUE, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE), 5)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
