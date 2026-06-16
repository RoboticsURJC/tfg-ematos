# app/core/base.py

import time

##
# @file base.py
# @brief Definición de la interfaz y clase base abstracta para modelos de lenguaje (LLM).
# @details Establece el contrato estructural y de comportamiento para la inferencia,
# pruebas de rendimiento (benchmarking) y extracción de telemetría de los distintos motores de IA.
#

class LLMModel:
    """
    @brief Clase base abstracta para la gestión y abstracción de modelos de lenguaje (LLM).
    @details Define la interfaz común que deben implementar obligatoriamente las subclases 
    (ej: GroqClient, LocalLlama, OpenAIClient) para la generación de texto y evaluación de rendimiento.
    """

    def __init__(self, name):
        """
        @brief Constructor de la clase base LLMModel.
        
        @param name Nombre comercial o identificador técnico del modelo de lenguaje (ej: 'llama-3.1-8b').
        """
        ## Nombre identificativo del modelo cargado o enlazado por el cliente.
        self.name = name

    def generate(self, prompt):
        """
        @brief Genera una respuesta de texto a partir de una instrucción o prompt estructurado.
        @details Este es un método abstracto puro. Las subclases derivadas deben sobrescribir 
        este método para comunicarse con sus respectivos backends o APIs de inferencia.
        
        @param prompt Cadena de texto limpia que contiene las directivas e historial de usuario.
        
        @return tuple Una tupla compuesta por `(response, extra)` donde:
               - `response` (str): El texto plano generado por el modelo.
               - `extra` (dict): Metadatos de la inferencia (tokens por segundo, tiempo de ejecución, etc.).
        
        @exception NotImplementedError Lanzada si se invoca el método directamente desde la clase base sin haber sido sobrescrito.
        """
        raise NotImplementedError

    def benchmark(self, prompt):
        """
        @brief Ejecuta una prueba de rendimiento (benchmark) controlada sobre el método de generación.
        @details Envuelve la llamada al método de inferencia `generate()`, inyecta trazas de depuración 
        en la consola usando metatablas de la clase activa y retorna los datos para auditorías de latencia.
        
        @param prompt Texto de entrada o benchmark estándar para evaluar el comportamiento del modelo.
        
        @return tuple Una tupla `(response, extra)` idéntica a la respuesta del método de generación implementado.
        """
        # Imprime información de depuración dinámica mostrando qué subclase física está ejecutando el test
        print(f"DEBUG -> {self.__class__.__name__}")
        
        response, extra = self.generate(prompt)
        return response, extra