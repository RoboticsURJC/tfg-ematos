# app/core/intent.py

##
# @file intent.py
# @brief Módulo analítico para la detección y clasificación de intenciones por palabras clave.
# @details Proporciona un motor de parsing lingüístico básico (Rule-based) para interceptar 
# comandos críticos locales antes de derivar la petición al modelo de lenguaje (LLM).
#

def detectar_intencion(texto: str) -> str:
    """
    @brief Analiza el texto recibido buscando palabras clave para clasificar la intención del usuario.
    @details Pasa toda la cadena a minúsculas para normalizar la entrada y realiza búsquedas de 
    subcadenas (substrings) optimizadas mediante comparaciones booleanas iterativas.
    
    ### Intenciones soportadas en el sistema:
    - `"time"`: Consultas explícitas sobre la hora cronológica local.
    - `"weather"`: Consultas relacionadas con el estado meteorológico, clima o temperatura.
    - `"llm"`: Intención por defecto. Delegación conversacional abierta al modelo de lenguaje.
    
    @param texto Cadena de texto o transcripción de audio limpia introducida de forma verbal por el usuario.
    
    @return str Identificador textual de la intención detectada de acuerdo a las reglas del sistema.
    """
    
    # Normalizar el texto a minúsculas para homogeneizar las búsquedas recursivas
    t = texto.lower()

    # Evaluación de patrones sintácticos para consultas relacionadas con la hora
    if any(x in t for x in [
        "hora",
        "qué hora",
        "que hora",
        "dime la hora"
    ]):
        return "time"

    # Evaluación de patrones sintácticos para consultas relacionadas con el clima
    if any(x in t for x in [
        "clima",
        "tiempo",
        "qué tiempo",
        "que tiempo"
    ]):
        return "weather"

    # Intención por defecto si la entrada no empareja con ninguna regla dura del firmware
    return "llm"