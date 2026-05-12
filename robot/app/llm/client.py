import requests
import logging

logger = logging.getLogger("llm")


## @file client.py
#  @brief Cliente genérico para interacción con modelos LLM.
#
#  Este módulo implementa un wrapper para:
#   - servidores LLM locales o remotos
#   - envío de prompts
#   - manejo de contexto adicional
#   - fallback seguro ante errores


## @class LLMClient
#  @brief Cliente genérico para modelos LLM.
#
#  Permite comunicarse con:
#   - APIs propias
#   - servidores locales
#   - modelos remotos tipo Groq, etc.
class LLMClient:
    """
    Cliente genérico para modelos LLM (servidor propio o API).
    """

    ## @brief Inicializa el cliente LLM.
    #
    #  @param server_url URL del servidor LLM.
    #  @param model Nombre del modelo a usar.
    #  @param timeout Tiempo máximo de espera en segundos.
    def __init__(
        self,
        server_url: str,
        model: str = "groq",
        timeout: int = 90
    ):

        ## @brief URL del servidor LLM.
        self.server_url = server_url

        ## @brief Modelo seleccionado.
        self.model = model

        ## @brief Timeout de peticiones HTTP.
        self.timeout = timeout

    # =========================
    # PETICIÓN BASE
    # =========================

    ## @brief Envía un prompt al servidor LLM.
    #
    #  Realiza una petición HTTP POST y devuelve la respuesta.
    #
    #  @param prompt Texto de entrada al modelo.
    #
    #  @return str Respuesta del modelo.
    #  @retval "" Si ocurre un error.
    def ask(self, prompt: str) -> str:
        """
        Envía un prompt al servidor LLM.
        """

        try:

            r = requests.post(
                self.server_url,
                json={
                    "model": self.model,
                    "prompt": prompt
                },
                timeout=self.timeout
            )

            data = r.json()

            output = data.get("output", "")

            # Normalizar salida lista
            if isinstance(output, list):
                output = output[0]

            return str(output)

        except Exception as e:

            logger.error(f"LLM ERROR: {e}")
            return ""

    # =========================
    # CONTEXTO
    # =========================

    ## @brief Envía prompt con contexto adicional.
    #
    #  Permite incluir memoria, historial o datos externos.
    #
    #  @param prompt Prompt principal.
    #  @param context Contexto adicional.
    #
    #  @return str Respuesta del modelo.
    def ask_with_context(
        self,
        prompt: str,
        context: str = ""
    ) -> str:

        full_prompt = (
            f"{context}\n\n{prompt}"
            if context else prompt
        )

        return self.ask(full_prompt)

    # =========================
    # FALLBACK SEGURO
    # =========================

    ## @brief Consulta segura con fallback.
    #
    #  Si el modelo falla o devuelve vacío,
    #  retorna un mensaje alternativo.
    #
    #  @param prompt Texto de entrada.
    #  @param fallback Mensaje por defecto.
    #
    #  @return str Respuesta del modelo o fallback.
    def safe_ask(
        self,
        prompt: str,
        fallback: str = "No tengo respuesta."
    ) -> str:

        response = self.ask(prompt)

        if not response or response.strip() == "":
            return fallback

        return response