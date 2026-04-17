import time

##
# @class LLMModel
# @brief Clase base para modelos de lenguaje (LLM).
#
# Define la interfaz común para la generación de texto y evaluación
# de modelos dentro del sistema.
#
class LLMModel:

    ##
    # @brief Constructor de la clase LLMModel.
    #
    # @param name Nombre del modelo.
    #
    def __init__(self, name):
        self.name = name

    ##
    # @brief Genera una respuesta a partir de un prompt.
    #
    # Método abstracto que debe ser implementado por las subclases.
    #
    # @param prompt Texto de entrada.
    # @return tuple(str, dict) Respuesta generada y datos adicionales.
    #
    # @exception NotImplementedError Si no se implementa en una subclase.
    #
    def generate(self, prompt):
        raise NotImplementedError

    ##
    # @brief Ejecuta un benchmark del modelo.
    #
    # Llama al método generate() y devuelve la respuesta junto con
    # información adicional. También imprime información de depuración.
    #
    # @param prompt Texto de entrada para evaluar el modelo.
    # @return tuple(str, dict) Respuesta generada y datos adicionales.
    #
    def benchmark(self, prompt):
        print(f"DEBUG -> {self.__class__.__name__}")
        response, extra = self.generate(prompt)
        return response, extra