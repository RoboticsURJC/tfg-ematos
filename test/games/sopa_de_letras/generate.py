"""
@file generate.py
@brief Generador de sopa de letras para board.py
@details Soporta diferentes dificultades, posiciones de palabras y tablero listo para mostrar.
"""

import random

# =========================
# CONFIGURACIÓN POR DEFECTO
# =========================
GRID_SIZE = 10        # tamaño base, se puede cambiar por dificultad
num_palabras = 10
grid = []
words_copy = []
word_positions = {}   # palabra: lista de coordenadas [(x,y),...]
MAX_ATTEMPTS = 500    # Límite de intentos para colocar cada palabra

# =========================
# DIRECCIONES (SOLO HORIZONTAL Y VERTICAL)
# =========================
possibilites = {
    "h": (1, 0),      # derecha
    "h_inv": (-1, 0), # izquierda
    "v": (0, 1),      # abajo
    "v_inv": (0, -1)  # arriba
}

# =========================
# PALABRAS
# =========================
def generate_word_list():
    """Lee las palabras desde el archivo words.txt"""
    try:
        with open(r"/home/elisa/uni/tfg-ematos/test/games/sopa_de_letras/words.txt", "r", encoding="utf-8") as file:
            words_list = []
            for line in file.readlines():
                word = line.strip().upper()
                if word:  # Ignorar líneas vacías
                    words_list.append(word)
            if not words_list:
                raise Exception("El archivo de palabras está vacío")
            return words_list
    except FileNotFoundError:
        print("[ERROR] No se encontró el archivo words.txt")
        # Lista de palabras por defecto
        return ["ARBOL", "BOSQUE", "RIO", "MONTAÑA", "CIELO", "ESTRELLA", "LUNA", "SOL", "FLOR", "HIERBA"]
    except Exception as e:
        print(f"[ERROR] Error al leer palabras: {e}")
        return ["ARBOL", "BOSQUE", "RIO", "MONTAÑA", "CIELO"]

# =========================
# COMPROBACIONES DE POSICIÓN
# =========================
def check_possibility(matrice, word, index, fit_dir):
    """Verifica si se puede colocar una palabra en la posición indicada"""
    x, y = index
    dx, dy = fit_dir
    for i in range(len(word)):
        nx = x + i * dx
        ny = y + i * dy
        
        # Verificar límites
        if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
            return False
        
        # Verificar si la celda está vacía o tiene la misma letra
        if matrice[ny][nx] != "0" and matrice[ny][nx] != word[i]:
            return False
    
    return True

def put_in_word(matrice, word, index, fit_dir):
    """Coloca una palabra en la matriz y guarda sus posiciones"""
    x, y = index
    dx, dy = fit_dir
    positions = []
    for i, c in enumerate(word):
        nx = x + i * dx
        ny = y + i * dy
        # Asegurar que la letra está en mayúscula
        matrice[ny][nx] = c.upper()
        positions.append((nx, ny))
    # Guardar con la palabra en mayúsculas
    word_positions[word.upper()] = positions
    print(f"[DEBUG] Palabra '{word}' colocada en posiciones: {positions}")

# =========================
# GENERAR TABLERO
# =========================
def generate_board():
    """Genera un tablero nuevo según dificultad"""
    global grid, words_copy, word_positions
    
    # Obtener lista de palabras
    lst_words = generate_word_list()
    
    # Asegurar que todas las palabras estén en mayúsculas
    lst_words = [word.upper() for word in lst_words]
    
    # Seleccionar palabras aleatorias
    words_copy = random.sample(lst_words, min(num_palabras, len(lst_words)))
    word_positions = {}
    
    # Inicializar grid vacío
    grid = [["0" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    # Colocar cada palabra
    for word in words_copy:
        placed = False
        attempts = 0
        
        while not placed and attempts < MAX_ATTEMPTS:
            # Elegir dirección aleatoria (solo horizontal o vertical)
            dir_key = random.choice(list(possibilites.keys()))
            dx, dy = possibilites[dir_key]
            
            # Elegir posición inicial
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            
            if check_possibility(grid, word, (x, y), (dx, dy)):
                put_in_word(grid, word, (x, y), (dx, dy))
                placed = True
            
            attempts += 1
        
        # Si no se pudo colocar la palabra, reintentar con menos palabras
        if not placed:
            print(f"[WARNING] No se pudo colocar la palabra '{word}' después de {MAX_ATTEMPTS} intentos")
            # Intentar con menos palabras
            if len(words_copy) > 4:
                words_copy = random.sample(lst_words, min(len(words_copy) - 1, len(lst_words)))
                return generate_board()  # Reintentar con menos palabras
    
    # Llenar espacios vacíos con letras aleatorias
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            if grid[y][x] == "0":
                grid[y][x] = random.choice(alphabet)
    
    print(f"[OK] Tablero generado con {len(words_copy)} palabras en grilla {GRID_SIZE}x{GRID_SIZE}")
    print(f"[OK] Direcciones permitidas: Horizontal y Vertical (sin diagonales)")
    print(f"[DEBUG] Palabras colocadas: {words_copy}")
    for word, positions in word_positions.items():
        print(f"[DEBUG] '{word}': {positions}")
    return True

# =========================
# AJUSTAR DIFICULTAD
# =========================
def set_difficulty(level):
    """Configura tamaño de tablero y número de palabras"""
    global GRID_SIZE, num_palabras
    
    if level == "facil":
        GRID_SIZE = 10
        num_palabras = 6
    elif level == "medio":
        GRID_SIZE = 12
        num_palabras = 8
    elif level == "dificil":
        GRID_SIZE = 14
        num_palabras = 10
    else:
        # Valor por defecto
        GRID_SIZE = 10
        num_palabras = 6
    
    print(f"[DEBUG] Dificultad configurada: {level} -> Grid {GRID_SIZE}x{GRID_SIZE}, {num_palabras} palabras")