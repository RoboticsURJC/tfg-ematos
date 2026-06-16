# app/core/results_manager.py

import json
import os
import time
from datetime import datetime

##
# @file results_manager.py
# @brief Gestor de persistencia para el histórico de resultados, benchmarks y métricas de juegos.
# @details Implementa funciones de lectura y escritura incremental utilizando el formato de texto 
# estructurado JSON Lines (.jsonl), optimizando las operaciones de E/S en sistemas embebidos.
#

## Ruta absoluta del directorio base donde se encuentra alojado este script de persistencia.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

## Ruta absoluta construida de forma dinámica que apunta al fichero físico de almacenamiento JSONL.
FILE = os.path.join(BASE_DIR, "..", "results", "results.jsonl")


def load_results():
    """
    @brief Carga y deserializa recursivamente el histórico completo de resultados guardados en disco.
    @details Lee de forma secuencial línea por línea el archivo JSONL. Cada línea física representa 
    un objeto JSON independiente, evitándole al sistema tener que parsear arrays masivos en memoria.
    
    @return list Una lista de diccionarios Python, donde cada elemento es una interacción o métrica de test.
    @retval [] Retorna una lista vacía si el archivo físico aún no ha sido creado en el sistema de archivos.
    """
    if not os.path.exists(FILE):
        return []

    results = []
    with open(FILE, "r", encoding="utf-8") as f:
        for line in f:
            # Limpia espacios en blanco residuales y parsea la línea como un diccionario JSON
            if line.strip():
                results.append(json.loads(line))
                
    return results


def save_result(result):
    """
    @brief Acumula e inyecta de forma permanente un nuevo registro de rendimiento al final del archivo.
    @details Estampa de manera automática una marca de tiempo con formato internacional ISO 8601, 
    asegura la existencia del directorio contenedor `../results/` y realiza un volcado atómico en modo append (`'a'`).
    
    @note Se fuerza el parámetro `ensure_ascii=False` en la serialización. Esto garantiza que caracteres 
    del idioma español con tildes (como 'ejecución', 'puntuación') o la letra 'ñ' se escriban en formato 
    UTF-8 legible en lugar de secuencias de escape Unicode complejas de auditar en texto plano.
    
    @param result Diccionario con la metadata de la partida, métrica de inferencia o rendimiento del juego.
    """
    # Estampar la fecha y hora exacta de la ejecución en formato ISO extendido (AAAA-MM-DDTHH:MM:SS.ffffff)
    result["timestamp"] = datetime.now().isoformat()

    # Asegurar de forma tolerante a fallos que la carpeta contenedora 'results' exista en disco
    os.makedirs(os.path.dirname(FILE), exist_ok=True)

    # Apertura en modo append para concatenar la nueva línea al final del fichero existente
    with open(FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")