# app/ui/apps/games/word_search/generate.py

"""
@file generate.py
@brief Motor de generación procedimental de matrices ortogonales para juegos de sopa de letras.
@details Sostiene algoritmos de siembra por fuerza bruta con límites de colisión adaptativos, 
permitiendo un control estricto de dificultad a través de la escala geométrica del tablero.
"""

import random

# =========================================================================
# CONFIGURACIÓN PARAMÉTRICA GLOBAL
# =========================================================================
GRID_SIZE = 10        ##< Dimensión longitudinal de la matriz (N x N). Modificada dinámicamente según dificultad.
num_palabras = 10     ##< Cuota objetivo de palabras que se inyectarán en el lienzo de juego.
grid = []             ##< Estructura bidimensional (matriz de listas) que almacena los caracteres individuales del tablero.
words_copy = []       ##< Subconjunto activo de palabras seleccionadas aleatoriamente para la ronda en curso.
word_positions = {}   ##< Mapa diccionario indexado `{'PALABRA': [(x0,y0), (x1,y1), ...]}` con los vectores de colisión.
MAX_ATTEMPTS = 500    ##< Umbral de iteraciones de fuerza bruta por palabra antes de activar la reducción asíncrona.

# =========================================================================
# MAIZ DE DESPLAZAMIENTOS LINEALES (DIRECCIONES)
# =========================================================================
## Tuplas de dirección matemática elemental `(dx, dy)` que acotan el juego exclusivamente a ejes ortogonales.
possibilites = {
    "h": (1, 0),      # Derecha
    "h_inv": (-1, 0), # Izquierda
    "v": (0, 1),      # Abajo
    "v_inv": (0, -1)  # Arriba
}


def generate_word_list():
    """
    @brief Carga y normaliza el banco de términos lingüísticos desde el sistema de archivos del dispositivo.
    @details Abre el descriptor en modo lectura segura `encoding="utf-8"`. Ante un fallo de entrada/salida (I/O),
    captura la excepción e inyecta un pool alternativo de palabras hardcodeadas para garantizar la resiliencia del software.
    
    @return list Colección de cadenas de texto en mayúsculas listas para su inserción estructural.
    """
    try:
        with open(r"/home/elisa/tfg-ematos/assistant/app/ui/apps/games/words.txt", "r", encoding="utf-8") as file:
            words_list = []
            for line in file.readlines():
                word = line.strip().upper()
                if word:  # Descarte de saltos de línea huérfanos o cadenas vacías
                    words_list.append(word)
            if not words_list:
                raise Exception("El archivo de palabras está vacío")
            return words_list
    except FileNotFoundError:
        print("[ERROR] No se encontró el archivo words.txt en la ruta especificada.")
        # Fallback resiliente ante pérdida de assets en disco
        return ["ARBOL", "BOSQUE", "RIO", "MONTAÑA", "CIELO", "ESTRELLA", "LUNA", "SOL", "FLOR", "HIERBA"]
    except Exception as e:
        print(f"[ERROR] Error imprevisto al procesar la lectura del diccionario: {e}")
        return ["ARBOL", "BOSQUE", "RIO", "MONTAÑA", "CIELO"]


def check_possibility(matrice, word, index, fit_dir):
    """
    @brief Valida mediante proyección lineal si una palabra puede ser sembrada en una coordenada específica.
    @details Evalúa de forma preventiva dos criterios críticos:
             1. Desbordamiento de límites físicos del tablero (Out of Bounds).
             2. Colisión de caracteres (evita sobreescrituras a menos que la celda coincida exactamente con la misma letra).
    
    @param matrice Referencia directa a la matriz bidimensional (`list` de `lists`).
    @param word Cadena de caracteres del término a validar.
    @param index Tupla `(x, y)` con la coordenada propuesta para la primera letra del término.
    @param fit_dir Tupla `(dx, dy)` obtenida del diccionario de posibilidades que rige el crecimiento lineal.
    @return bool True si la región es apta y segura para la siembra de caracteres; False en caso contrario.
    """
    x, y = index
    dx, dy = fit_dir
    for i in range(len(word)):
        nx = x + i * dx
        ny = y + i * dy
        
        # Validación estricta de bordes en el plano cartesiano
        if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
            return False
        
        # Verificación de colisiones de memoria en celdas previamente asignadas ("0" representa celda virgen)
        if matrice[ny][nx] != "0" and matrice[ny][nx] != word[i]:
            return False
    
    return True


def put_in_word(matrice, word, index, fit_dir):
    """
    @brief Modifica físicamente las celdas de la matriz e inyecta los caracteres de la palabra validada.
    @details Almacena de forma indexada en el diccionario global `word_positions` la secuencia exacta 
    de tuplas de coordenadas discretas ocupadas, permitiendo que la interfaz táctil realice comprobaciones instantáneas.
    
    @param matrice Referencia directa a la matriz bidimensional activa de caracteres.
    @param word Cadena de caracteres del término a inyectar.
    @param index Tupla `(x, y)` inicial de siembra.
    @param fit_dir Tupla `(dx, dy)` que gobierna la dirección de escritura en la memoria matricial.
    """
    x, y = index
    dx, dy = fit_dir
    positions = []
    for i, c in enumerate(word):
        nx = x + i * dx
        ny = y + i * dy
        matrice[ny][nx] = c.upper()
        positions.append((nx, ny))
    
    word_positions[word.upper()] = positions
    print(f"[DEBUG] Palabra '{word}' colocada en posiciones: {positions}")


def generate_board():
    """
    @brief Genera procedimentalmente un nuevo mapa completo de sopa de letras bajo criterios de optimización espacial.
    @details **Algoritmo de escape por recursividad adaptativa:** Si el factor de empaquetamiento espacial colapsa 
    y una palabra no logra situarse tras superar el umbral de seguridad `MAX_ATTEMPTS`, el motor captura el bloqueo, 
    reduce de forma dinámica la cuota de palabras deseadas en una unidad y reinicia el proceso de generación de forma 
    recursiva para mitigar bucles infinitos de procesamiento en la CPU de la Raspberry Pi. Tras la siembra limpia, 
    rellena el ruido residual con caracteres pseudoaleatorios extraídos del alfabeto anglosajón.
    
    @return bool True cuando el tablero logra estructurarse de forma integral y queda listo para el render.
    """
    global grid, words_copy, word_positions
    
    lst_words = generate_word_list()
    lst_words = [word.upper() for word in lst_words]
    
    # Muestreo aleatorio sin reemplazo acotado a la disponibilidad del pool
    words_copy = random.sample(lst_words, min(num_palabras, len(lst_words)))
    word_positions = {}
    
    # Inicialización del tablero con caracteres nulos de control "0"
    grid = [["0" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    
    for word in words_copy:
        placed = False
        attempts = 0
        
        while not placed and attempts < MAX_ATTEMPTS:
            dir_key = random.choice(list(possibilites.keys()))
            dx, dy = map_dir = possibilites[dir_key]
            
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            
            if check_possibility(grid, word, (x, y), map_dir):
                put_in_word(grid, word, (x, y), map_dir)
                placed = True
            
            attempts += 1
        
        # Disparador del algoritmo de escape adaptativo ante colisiones masivas cíclicas
        if not placed:
            print(f"[WARNING] Densidad crítica: No se pudo colocar '{word}' tras {MAX_ATTEMPTS} intentos.")
            if len(words_copy) > 4:
                # Se reduce la presión espacial eliminando un elemento del pool y relanzando el generador de forma recursiva
                words_copy = random.sample(lst_words, min(len(words_copy) - 1, len(lst_words)))
                return generate_board()
    
    # Inyección de ruido tipográfico aleatorio sobre las celdas vacías residuales
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


def set_difficulty(level):
    """
    @brief Configura y altera dinámicamente las dimensiones estructurales de la grilla según el grado de complejidad deseado.
    
    @param level Cadena de texto identificadora de la dificultad ("facil" | "medio" | "dificil").
    """
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
        # Configuración defensiva por defecto ante parámetros de entrada alterados o nulos
        GRID_SIZE = 10
        num_palabras = 6
    
    print(f"[DEBUG] Dificultad configurada: {level} -> Grid {GRID_SIZE}x{GRID_SIZE}, {num_palabras} palabras")