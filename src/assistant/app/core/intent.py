## @brief Detecta la intención básica del usuario.
#
#  Analiza el texto recibido buscando palabras clave
#  relacionadas con hora o clima.
#
#  Intenciones soportadas:
#   - "time": consultas sobre la hora.
#   - "weather": consultas sobre clima o tiempo.
#   - "llm": cualquier otra consulta general.
#
#  @param texto Texto introducido por el usuario.
#
#  @return str Intención detectada.
def detectar_intencion(texto: str) -> str:
    """
    Detecta intención básica del usuario.
    """
    
    t = texto.lower()

    # Consultas relacionadas con la hora
    if any(x in t for x in [
        "hora",
        "qué hora",
        "que hora",
        "dime la hora"
    ]):
        return "time"

    # Consultas relacionadas con el clima
    if any(x in t for x in [
        "clima",
        "tiempo",
        "qué tiempo",
        "que tiempo"
    ]):
        return "weather"

    # Intención por defecto
    return "llm"