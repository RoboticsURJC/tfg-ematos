"""
@file assistant_engine.py
@brief Motor principal del asistente: integra STT, TTS, LLM y herramientas.
@details Replica fielmente la lógica del asistente_robotico.py original:
- Detección de intenciones (hora, clima, calendario, recordatorios, deportes,
  enciclopedia/Wikipedia, LLM).
- Memoria conversacional persistente por usuario.
- Llamadas al modelo LLM remoto.
- Fallback a búsqueda web si el modelo falla, con aviso explícito al LLM para
  que no invente datos cuando el contexto recuperado no los contiene.
"""

import os
import re
import json
import socket
import threading
import concurrent.futures
import requests
import dateparser

from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from app.voice.stt_vosk import VoskSTT
from app.llm.client import LLMClient
from app.voice.audio_stream import encontrar_micro
from app.voice.tts import TTS
from app.ui.apps.reminder.reminder_scheduler import ReminderScheduler
from app.core.logger import logger
from app.tools.sports import get_resultado_equipo
from app.tools.wiki import get_resumen


# =========================================================
# PROMPT DEL SISTEMA
# =========================================================

## Instrucciones de comportamiento base para la Inteligencia Artificial (orientado a ancianos).
PROMPT_DEL_SISTEMA = """
Eres un asistente virtual diseñado para ayudar a personas mayores.

Reglas importantes:
- Siempre responde en español.
- Usa un lenguaje claro, sencillo y amable.
- Explica las cosas paso a paso cuando sea necesario.
- Evita tecnicismos innecesarios.
- Sé paciente, cercano y respetuoso.
- Si no entiendes algo, pide aclaración de forma amable.
- Prioriza respuestas útiles y prácticas.
- Si no tienes datos concretos y verificados para responder algo (una cifra,
  un resultado, un hecho puntual), dilo claramente en vez de inventarlo.
"""

# =========================================================
# RUTAS
# =========================================================

## Nombre del fichero JSON local para guardar la persistencia del historial.
MEMORY_FILE = "memoria_usuarios.json"

## Tiempo máximo de espera por defecto (en segundos) para solicitudes de red.
TIMEOUT = 90

## Cabecera de User-Agent realista para evitar bloqueos al raspar DuckDuckGo.
USER_AGENT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    )
}

## Aviso que se antepone a cualquier contexto recuperado de la web antes de
## pasarlo al LLM, para reducir el riesgo de que el modelo invente datos
## (marcadores, cifras, hechos puntuales) que no estén presentes en el texto.
AVISO_NO_INVENTAR = (
    "A continuación tienes fragmentos de una búsqueda web. Si no encuentras "
    "el dato exacto que se pide (por ejemplo un marcador, una cifra o un "
    "hecho concreto), dilo claramente en vez de inventarlo:\n\n"
)

PALABRAS_EVENTO = [
    "médico", "medico",
    "dentista",
    "hospital",
    "cardiólogo", "cardiologo",
    "enfermera",
    "análisis", "analisis",
    "farmacia",
    "rehabilitación", "rehabilitacion",
    "peluquería", "peluqueria",
    "cumpleaños", "cumpleanos",
    "vacuna",
    "especialista",
    "consulta",
    "boda",
    "comunión", "comunion",
    "operación", "operacion",
    "revisión", "revision",
]

PALABRAS_RECORDATORIO = [
    "pastilla",
    "pastillas",
    "medicina",
    "medicación",
    "medicacion",
    "medicamento",
    "medicamentos",
    "inyección",
    "inyeccion",
    "tomar",
    "llamar"
]

# Pistas léxicas para saber si una frase contiene una referencia temporal,
# sin necesidad de que la frase ENTERA sea "parseable" como fecha (que es
# lo que exige dateparser.parse y por lo que casi nunca detecta nada en
# frases reales con más palabras alrededor).
PISTAS_TEMPORALES = [
    "lunes", "martes", "miércoles", "miercoles", "jueves",
    "viernes", "sábado", "sabado", "domingo",
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
    "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    "hoy", "mañana", "pasado mañana",
    "mediodía", "mediodia", "medianoche",
    "que viene", "próximo", "proximo", "siguiente",
    "esta semana", "este mes", "la semana que viene",
    "a las", "a la una", "en punto",
    "dentro de", "minutos", "horas", "media hora"
]


# =========================================================
# AssistantEngine
# =========================================================

class AssistantEngine:
    """
    @brief Motor conversacional completo del asistente robótico.
    @details Orquesta el ciclo completo: Listen -> Detect -> Process -> Speak.
    """

    def __init__(self, ui_state=None, display=None, calendar_store=None, reminder_store=None, model_path=None, server_url=None, mic_name=None, llm_model='groq', llm_timeout=90):
        """
        @brief Inicializa los módulos de voz, interfaz, almacenamiento y clientes de IA.
        
        @param ui_state        Estado compartido de la interfaz gráfica (UIState).
        @param display         Controlador de la pantalla facial (FaceDisplay).
        @param calendar_store  Repositorio o base de datos de eventos del calendario.
        @param reminder_store  Repositorio o base de datos de los recordatorios de medicación/alertas.
        @param model_path      Ruta local hacia la carpeta del modelo Vosk para STT.
        @param server_url      URL del API Gateway o servidor LLM externo.
        @param mic_name        Nombre específico del micrófono a capturar en hardware.
        @param llm_model       Identificador del backend/modelo LLM (ej: 'groq', 'ollama').
        @param llm_timeout     Límite de tiempo en segundos para las consultas al LLM.
        """
        self.ui_state = ui_state
        self.display = display
        self.calendar_store = calendar_store 
        self.reminder_store = reminder_store
        self.reminder_scheduler = None
        self.on_reminder_created = None
        self.on_calendar_created = None
        
        ## Nombre o ID del perfil de usuario actualmente interactuando.
        self.user = "invitado"
        
        ## Bandera de control para saber si el bucle de escucha asíncrono está encendido.
        self.running = False

        ## Tiempo máximo (segundos) que se espera a la respuesta del LLM antes de
        ## abandonar y devolver fallback, para evitar cuelgues silenciosos.
        self.llm_timeout = llm_timeout or TIMEOUT

        # Cliente LLM (None si no hay URL configurada)
        if server_url:
            self.llm = LLMClient(server_url=server_url, model=llm_model, timeout=llm_timeout)
            logger.info(f"[ASSISTANT] LLM configurado: {server_url} | modelo: {llm_model}")
        else:
            self.llm = None
            logger.warning("[ASSISTANT] server_url vacío — LLM desactivado")

        # Buscar micrófono por nombre si se proporciona
        if mic_name:
            self.mic_device = encontrar_micro(mic_name)
            if self.mic_device is None:
                logger.warning(f"[ASSISTANT] micro '{mic_name}' no encontrado, usando default")
        else:
            self.mic_device = None

        # Iniciar síntesis de voz y reconocedor
        self.tts = TTS()
        self.stt = VoskSTT(model_path) if model_path else None
        
        ## Estructura en memoria con el historial cargado por perfiles.
        self.memoria = self._cargar_memoria()
        
        if self.display:
            self.display.set_estado("Esperando activación...")

        logger.info("[ASSISTANT] listo")

    # =========================================================
    # MEMORIA PERSISTENTE
    # =========================================================

    def _cargar_memoria(self):
        """
        @brief Carga el historial conversacional desde el almacenamiento en disco.
        @return dict Diccionario estructurado `{usuario: [lista de turnos]}` o dict vacío ante fallos.
        """
        if not os.path.exists(MEMORY_FILE):
            return {}
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[MEMORIA] no se pudo cargar: {e}")
            return {}

    def _guardar_memoria(self):
        """
        @brief Persiste el historial conversacional actual estructurado en formato JSON a disco.
        """
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[MEMORIA] error al guardar: {e}")

    # =========================================================
    # HERRAMIENTAS LOCALES
    # =========================================================

    def _get_time(self):
        """
        @brief Devuelve la hora actual del sistema operativo.
        @return str Cadena de texto formateada en "HH:MM".
        """
        return datetime.now().strftime("%H:%M")

    def _get_weather(self, city="Madrid"):
        """
        @brief Consulta el pronóstico del tiempo meteorológico mediante Open-Meteo sin API key.
        @param city Nombre textual de la localidad o ciudad a buscar mediante geolocalización.
        @return str Mensaje resumido con los grados y velocidad del viento listo para ser locutado.
        """
        try:
            geo = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1",
                timeout=10
            ).json()
            lat = geo["results"][0]["latitude"]
            lon = geo["results"][0]["longitude"]

            weather = requests.get(
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}&current_weather=true",
                timeout=10
            ).json()

            temp = weather["current_weather"]["temperature"]
            wind = weather["current_weather"]["windspeed"]
            return f"En {city} ahora hay {temp}°C y viento de {wind} km/h."
        except Exception as e:
            logger.error(f"[WEATHER] error: {e}")
            return "No he podido obtener el clima ahora mismo."

    # =========================================================
    # DETECCIÓN DE INTENCIÓN
    # =========================================================

    def _contiene_referencia_temporal(self, text):
        """
        @brief Comprueba si la frase contiene alguna pista de fecha/hora.
        @details A diferencia de dateparser.parse() (que exige que casi toda la
        cadena sea una fecha y por eso nunca detecta nada en frases reales como
        "tengo cita el martes a las diez"), esta función solo busca pistas
        léxicas dentro de la frase, sin importar qué más se diga alrededor.
        @param text Texto en minúsculas.
        @return bool True si se detecta alguna referencia temporal.
        """
        if any(p in text for p in PISTAS_TEMPORALES):
            return True
        # Patrón numérico de hora suelto, ej. "a las 9", "9:30"
        if re.search(r"\b\d{1,2}[:h]\d{2}\b", text):
            return True
        return False

    def _detectar_intencion(self, text):
        """
        @brief Clasifica y mapea el texto del usuario para identificar comandos conocidos o herramientas nativas.
        @param text Transcripción en texto limpio y minúsculas generada por el STT.
        @return str Identificador de la intención ('time', 'weather', 'reminder',
        'calendar', 'sports', 'wiki' o 'llm').
        """
        
        text = text.lower().strip()

        # Hora
        if any(x in text for x in [
            "qué hora",
            "que hora",
            "dime la hora",
            "hora es"
        ]):
            return "time"

        # Tiempo
        if any(x in text for x in [
            "clima",
            "tiempo",
            "temperatura",
            "llover",
            "lluvia"
        ]):
            return "weather"

        # Resultados deportivos (debe ir antes de "calendar"/"llm" genéricos,
        # ya que frases como "cómo quedó el Madrid" no tienen verbo disparador
        # de calendario ni de recordatorio).
        if any(x in text for x in [
            "resultado del",
            "resultado de",
            "cómo quedó",
            "como quedo",
            "cómo ha quedado",
            "como ha quedado",
            "ganó el",
            "gano el",
            "perdió el",
            "perdio el",
            "partido del",
            "marcador"
        ]):
            return "sports"

        # Consultar recordatorios
        if any(x in text for x in [
            "mis recordatorios",
            "qué recordatorios",
            "que recordatorios",
            "tengo recordatorios",
            "recordatorios pendientes",
            "mis alarmas",
            "qué alarmas",
            "que alarmas"
        ]):
            return "reminder_query"

        # Crear recordatorio
        if any(x in text for x in [
            "recuérdame",
            "recuerdame",
            "avísame",
            "avisame"
        ]):
            return "reminder_add"

        # Consultar calendario
        if any(x in text for x in [
            "qué tengo",
            "que tengo",
            "mis citas",
            "mis eventos",
            "mi agenda",
            "esta semana",
            "este mes",
            "la semana que viene"
        ]):
            return "calendar"

        # Frases naturales con fecha/hora (ej. "el martes tengo cita con el médico",
        # "el sábado tomar la pastilla a las nueve"), sin necesidad de un verbo
        # disparador explícito como "recuérdame" o "apunta".
        if self._contiene_referencia_temporal(text):

            if any(x in text for x in PALABRAS_EVENTO):
                return "calendar_add"

            if any(x in text for x in PALABRAS_RECORDATORIO):
                return "reminder_add"

        # Añadir evento explícito
        if any(x in text for x in [
            "añade cita",
            "añade evento",
            "agrega cita",
            "agrega evento",
            "apunta",
            "pon una cita",
            "pon un evento",
            "crear evento",
            "calendario"
        ]):
            return "calendar_add"

        # Añadir recordatorio explícito
        if any(x in text for x in [
            "recordatorio",
            "alarma"
        ]):
            return "reminder_add"

        # Preguntas de tipo enciclopédico: personas, lugares, temas generales.
        # Va al final, justo antes del fallback a "llm" puro, porque es una
        # red de captura amplia y conviene que las intenciones más
        # específicas (hora, clima, deportes, calendario...) se evalúen antes.
        if any(x in text for x in [
            "quién es",
            "quien es",
            "qué es",
            "que es",
            "dónde está",
            "donde esta",
            "cuéntame sobre",
            "cuentame sobre",
            "háblame de",
            "hablame de",
            "sabes quién es",
            "sabes quien es"
        ]):
            return "wiki"

        return "llm"

    # =========================================================
    # LLM Y BÚSQUEDA
    # =========================================================

    def _hay_internet(self):
        """
        @brief Comprueba de forma rápida la conectividad TCP a Internet mediante el DNS de Google.
        @return bool True si hay conexión activa, False en caso de corte de red.
        """
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except Exception:
            return False

    def _web_search(self, query):
        """
        @brief Realiza un escrapeo de emergencia via DuckDuckGo HTML ante caídas de la IA.
        @details Usa un User-Agent de navegador real (sin esto DuckDuckGo suele
        bloquear o devolver una página distinta, dejando los resultados
        siempre vacíos) y captura también el snippet/descripción de cada
        resultado, no solo el título, para dar más contexto útil al LLM.
        @param query Cadena de términos de búsqueda solicitados por el usuario.
        @return str Resumen de las primeras coincidencias textuales encontradas en la web.
        """
        try:
            url = "https://html.duckduckgo.com/html/"
            r = requests.post(
                url,
                data={"q": query},
                headers=USER_AGENT_HEADERS,
                timeout=10
            )
            logger.info(f"[WEB SEARCH] status={r.status_code} len={len(r.text)}")

            soup = BeautifulSoup(r.text, "html.parser")
            bloques = soup.find_all("div", class_="result", limit=5)

            resultados = []
            for b in bloques:
                titulo_tag = b.find("a", class_="result__a")
                snippet_tag = b.find("a", class_="result__snippet") or b.find(
                    "div", class_="result__snippet"
                )
                titulo = titulo_tag.get_text(strip=True) if titulo_tag else ""
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                if titulo or snippet:
                    resultados.append(f"{titulo}: {snippet}".strip(": "))

            if not resultados:
                logger.warning(
                    "[WEB SEARCH] sin resultados parseables "
                    "(posible bloqueo o cambio de HTML)"
                )
                return ""

            return "\n".join(resultados[:3])

        except Exception as e:
            logger.error(f"[WEB SEARCH] error: {e}")
            return ""

    def _parse_fecha(self, texto):
        """
        @brief Transforma expresiones complejas de lenguaje natural a un objeto datetime estructurado.
        @param texto Fragmento de la transcripción de voz que describe un tiempo (ej: 'el próximo martes').
        @return datetime Objeto de tiempo interpretado, o None si no se comprende la referencia.
        """
        settings = {
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
        fecha = dateparser.parse(texto, languages=["es"], settings=settings)
        return fecha
        
    def _rango_temporal(self, texto):
        """
        @brief Determina los límites temporales (fecha de inicio y fin) según los adverbios utilizados.
        @param texto Transcripción del habla en minúsculas.
        @return tuple Una tupla `(date_inicio, date_fin)` o `(None, None)` si es inclasificable.
        """
        texto = texto.lower()
        hoy = datetime.now().date()
        
        if "hoy" in texto:
            logger.info("Pregunta por hoy")
            return hoy, hoy
            
        if "mañana" in texto:
            logger.info("Pregunta por mañana")
            mañana = hoy + timedelta(days=1)
            return mañana, mañana
            
        if "semana" in texto:
            logger.info("Pregunta la semana")
            inicio = hoy - timedelta(days=hoy.weekday())
            fin = inicio + timedelta(days=6)
            return inicio, fin
                 
        if "mes" in texto:
            logger.info("Pregunta por el mes")
            inicio = hoy.replace(day=1)
            
            if inicio.month == 12:
                fin = inicio.replace(year=inicio.year+1, month=1, day=1) - timedelta(days=1)
            else:
                fin = inicio.replace(month=inicio.month+1, day=1) - timedelta(days=1)
            return inicio, fin
            
        fecha = self._parse_fecha(texto)
        if fecha:
             f = fecha.date()
             return f, f
         
        return None, None
    
    def _palabras_a_numeros(self, texto):
        """
        @brief Convierte números en letra a dígitos para facilitar el parsing temporal.
        """
         
        tabla = {
        "cero": "0", "una": "1", "uno": "1", "dos": "2", "tres": "3",
        "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8",
        "nueve": "9", "diez": "10", "once": "11", "doce": "12", "trece": "13",
        "catorce": "14", "quince": "15", "dieciséis": "16", "dieciseis": "16",
        "diecisiete": "17", "dieciocho": "18", "diecinueve": "19",
        "veinte": "20", "veintiuna": "21", "veintiuno": "21", "veintidós": "22",
        "veintidos": "22", "veintitrés": "23", "veintitres": "23",
        }
        
        for palabra, numero in tabla.items():
            texto = re.sub(rf"\b{palabra}\b", numero, texto)
        
        return texto
    
         
    
    def _normalizar_hora(self, texto):
        """
        @brief Convierte expresiones como 'las tres de la tarde' a 'las 15:00',
        y formas coloquiales como 'y media'/'y cuarto'/'menos cuarto' a minutos.
        """
        # "X y media" / "X y cuarto" / "X menos cuarto" → "X:30" / "X:15" / "(X-1):45"
        # Se hace ANTES de las conversiones de tarde/noche para que estas últimas
        # puedan capturar también los minutos.
        texto = re.sub(r"\b(\d{1,2})\s*y\s*media\b", lambda m: f"{m.group(1)}:30", texto)
        texto = re.sub(r"\b(\d{1,2})\s*y\s*cuarto\b", lambda m: f"{m.group(1)}:15", texto)
        texto = re.sub(
            r"\b(\d{1,2})\s*menos\s*cuarto\b",
            lambda m: f"{int(m.group(1)) - 1 if int(m.group(1)) > 1 else 12}:45",
            texto
        )

        # "a las X de la tarde/noche" → suma 12 si < 12
        def _tarde(m):
            h = int(m.group(1))
            mins = m.group(2) if m.group(2) else "00"
            if h != 12:
                h += 12
            return f"a las {h}:{mins}"

        def _manana_franja(m):
            h = int(m.group(1))
            mins = m.group(2) if m.group(2) else "00"
            if h == 12:
                h = 0
            return f"a las {h}:{mins}"

        def _mediodia(m):
            mins = m.group(1) if m.group(1) else "00"
            return f"a las 12:{mins}"

        # "a las X de la tarde/noche"
        texto = re.sub(r"a las (\d{1,2})(?::(\d{2}))?\s*de la tarde", _tarde, texto)
        texto = re.sub(r"a las (\d{1,2})(?::(\d{2}))?\s*de la noche", _tarde, texto)
        texto = re.sub(r"a las (\d{1,2})(?::(\d{2}))?\s*de la mañana", _manana_franja, texto)
        texto = re.sub(r"a las (\d{1,2})(?::(\d{2}))?\s*del mediodía", _mediodia, texto)
        texto = re.sub(r"a las (\d{1,2})(?::(\d{2}))?\s*del mediodia", _mediodia, texto)

        # "las ocho de la tarde" sin "a"
        texto = re.sub(r"\blas (\d{1,2})(?::(\d{2}))?\s*de la tarde", _tarde, texto)
        texto = re.sub(r"\blas (\d{1,2})(?::(\d{2}))?\s*de la noche", _tarde, texto)
        texto = re.sub(r"\blas (\d{1,2})(?::(\d{2}))?\s*de la mañana", _manana_franja, texto)

        return texto


    def _extraer_hora(self, texto):
        """
        @brief Extrae hora del texto y devuelve (hora_dt, texto_sin_hora).
        @return (None, texto) si no encuentra hora.
        """
        now = datetime.now()

        # Patrón "mañana a las HH"
        m = re.search(r"mañana\s+a las\s+(\d{1,2})(?::(\d{2}))?", texto)
        if m:
            h, mn = int(m.group(1)), int(m.group(2)) if m.group(2) else 0
            when = (now + timedelta(days=1)).replace(hour=h, minute=mn, second=0, microsecond=0)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "dentro de X minutos" / "en X minutos"
        m = re.search(r"(?:en|dentro de)\s+(\d+)\s*minutos?", texto)
        if m:
            when = now + timedelta(minutes=int(m.group(1)))
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "dentro de X horas" / "en X horas"
        m = re.search(r"(?:en|dentro de)\s+(\d+)\s*horas?", texto)
        if m:
            when = now + timedelta(hours=int(m.group(1)))
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "media hora" / "en media hora" / "dentro de media hora"
        m = re.search(r"(?:en\s+|dentro de\s+)?media hora", texto)
        if m:
            when = now + timedelta(minutes=30)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "a mediodía" / "a mediodia"
        m = re.search(r"a (?:mediodía|mediodia)", texto)
        if m:
            when = now.replace(hour=12, minute=0, second=0, microsecond=0)
            if when <= now:
                when += timedelta(days=1)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "a medianoche"
        m = re.search(r"a medianoche", texto)
        if m:
            when = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if when <= now:
                when += timedelta(days=1)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # "a la una[:MM]" (caso especial sin plural; si la 1 de la madrugada ya
        # pasó, se interpreta como la 1 de la tarde, que es lo más natural)
        m = re.search(r"a la una(?::(\d{2}))?", texto)
        if m:
            mn = int(m.group(1)) if m.group(1) else 0
            when = now.replace(hour=1, minute=mn, second=0, microsecond=0)
            if when <= now:
                when = when.replace(hour=13)
                if when <= now:
                    when += timedelta(days=1)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        # Patrón "a las HH:MM" o "a las HH"
        m = re.search(r"a las\s+(\d{1,2})(?::(\d{2}))?", texto)
        if m:
            h, mn = int(m.group(1)), int(m.group(2)) if m.group(2) else 0
            when = now.replace(hour=h, minute=mn, second=0, microsecond=0)
            if when <= now:
                when += timedelta(days=1)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return when, texto_limpio.strip()

        return None, texto

    def _extraer_fecha(self, texto):
        """
        @brief Extrae fecha del texto y devuelve (fecha_dt, texto_sin_fecha).
        @return (None, texto) si no encuentra fecha.
        """
        now = datetime.now()

        dias = {
            "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
            "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6
        }
        meses = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
            "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
            "octubre": 10, "noviembre": 11, "diciembre": 12
        }

        # "el 5 de julio", "el 12 de marzo"
        m = re.search(
            r"el\s+(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|"
            r"agosto|septiembre|octubre|noviembre|diciembre)", texto
        )
        if m:
            dia_n = int(m.group(1))
            mes_n = meses[m.group(2)]
            año = now.year
            fecha = datetime(año, mes_n, dia_n)
            if fecha.date() < now.date():
                fecha = datetime(año + 1, mes_n, dia_n)
            texto_limpio = texto[:m.start()] + texto[m.end():]
            return fecha, texto_limpio.strip()

        # "pasado mañana" (debe comprobarse ANTES que "mañana" a solas,
        # porque la contiene como subcadena)
        if re.search(r"\bpasado\s+mañana\b", texto):
            fecha = now + timedelta(days=2)
            texto_limpio = re.sub(r"\bpasado\s+mañana\b", "", texto).strip()
            return fecha, texto_limpio

        # "hoy"
        if re.search(r"\bhoy\b", texto):
            fecha = now
            texto_limpio = re.sub(r"\bhoy\b", "", texto).strip()
            return fecha, texto_limpio

        # "mañana" (sin hora asociada, ya gestionado en _extraer_hora)
        if re.search(r"\bmañana\b", texto):
            fecha = now + timedelta(days=1)
            texto_limpio = re.sub(r"\bmañana\b", "", texto).strip()
            return fecha, texto_limpio

        # Día de la semana
        for dia, num in dias.items():
            if re.search(rf"\b{dia}\b", texto):
                dias_hasta = (num - now.weekday()) % 7
                if dias_hasta == 0:
                    dias_hasta = 7
                fecha = now + timedelta(days=dias_hasta)
                texto_limpio = re.sub(rf"\b{dia}\b", "", texto).strip()
                # "próximo lunes" → eliminar también "próximo"
                texto_limpio = re.sub(r"\b(próximo|proximo|siguiente|el|que viene)\b", "", texto_limpio).strip()
                return fecha, texto_limpio

        # Fallback dateparser
        fecha = self._parse_fecha(texto)
        if fecha:
            return fecha, texto

        return None, texto

    def _limpiar_titulo(self, texto):
        """ @brief Elimina preposiciones y palabras residuales del título."""
        texto = texto.lower()

        basura = [

            "recuérdame",
            "recuerdame",
            "avísame",
            "avisame",

            "añade",
            "agrega",
            "pon",
            "apunta",

            "recordatorio",
            "alarma",

            "mañana",
            "hoy",

            "a las",
            "las",

            "para",
            "de",
            "del",
            "el",
            "la",
            "los",
            "las",

            "que",
            "sobre",

            "tengo",
            "que viene",
        ]

        for palabra in basura:
            texto = re.sub(rf"\b{re.escape(palabra)}\b", " ", texto)

        texto = re.sub(r"\d{1,2}:\d{2}", " ", texto)
        texto = re.sub(r"\d+", " ", texto)

        meses = (
            "enero febrero marzo abril mayo junio julio agosto "
            "septiembre octubre noviembre diciembre"
        ).split()

        for mes in meses:
            texto = re.sub(rf"\b{mes}\b", " ", texto)

        texto = re.sub(r"\s+", " ", texto)

        return texto.strip()

               
    def _crear_recordatorio(self, texto):
        """
        @brief Procesa una orden verbal para programar un nuevo recordatorio de alerta.
        @details Extrae tanto la FECHA ("el martes", "mañana", "el 5 de julio"...)
        como la HORA ("a las nueve", "en 20 minutos"...) y combina ambas, igual
        que se hace para los eventos de calendario. Si solo se da una de las dos,
        se usa esa; si no se da ninguna, se programa para dentro de 5 minutos.

        @param texto Transcripción del comando de voz.
        @return str Mensaje de confirmación del éxito de la operación.
        """
        logger.info("[ASSISTANT ENGINE] Crear recordartorio")
    
        try:
            if not self.reminder_store:
                return "No tengo acceso al sistema de recordatorios"
            
            t = texto.lower().strip()
            
            # Eliminar palabras clave de activación
            for kw in ["recuérdame", "recuerdame", "avísame", "avisame",
                    "pon un recordatorio", "añade un recordatorio",
                    "pon recordatorio", "alarma", "medicina", "medicación"]:
                t = t.replace(kw, "").strip()
            
            t = self._palabras_a_numeros(t)
            t = self._normalizar_hora(t)
            
            logger.info(f"[ASSISTANT ENGINE] Texto normalizado {t}")

            # Extraer fecha y hora por separado y combinarlas (antes este método
            # llamaba dos veces a _extraer_hora y nunca a _extraer_fecha, por lo
            # que cualquier fecha mencionada ("el martes"...) se ignoraba siempre).
            fecha, t_sin_fecha = self._extraer_fecha(t)
            hora_dt, titulo = self._extraer_hora(t_sin_fecha)

            if fecha and hora_dt:
                when = fecha.replace(
                    hour=hora_dt.hour, minute=hora_dt.minute,
                    second=0, microsecond=0
                )
            elif fecha and not hora_dt:
                when = fecha
            elif hora_dt and not fecha:
                when = hora_dt
            else:
                when = None

            if not when:
                when = datetime.now() + timedelta(minutes=5)

            # Limpiar título
            titulo = self._limpiar_titulo(titulo)
            if not titulo:
                if "pastilla" in texto:
                    titulo = "Tomar pastilla"
                elif "medicina" in texto:
                    titulo = "Tomar medicina"
                elif "medicamento" in texto:
                    titulo = "Tomar medicamento"
                else:
                    titulo = "Recordatorio"

            self.reminder_store.add(titulo, when.strftime("%Y-%m-%d %H:%M"))

            if self.on_reminder_created:
                self.on_reminder_created()

            logger.info(f"[REMINDER] '{titulo}' → {when.strftime('%H:%M %d/%m')}")
            return f"Recordatorio '{titulo}' añadido para las {when.strftime('%H:%M')} del {when.strftime('%d/%m')}."

        except Exception as e:
            logger.error(f"[REMINDER] Fallo: {e}")
            return "No he podido crear el recordatorio."

        
    def _consultar_recordatorios(self, texto):
        """
        @brief Consulta los recordatorios pendientes y los narra por voz.
        @param texto Transcripción de la consulta del usuario.
        @return str Frase con los recordatorios pendientes.
        """
        if not self.reminder_store:
            return "No tengo acceso al sistema de recordatorios."

        # Recargar desde disco por si hay cambios recientes
        self.reminder_store.reminders = self.reminder_store.load()
        pendientes = self.reminder_store.get_pending()

        if not pendientes:
            return "No tienes recordatorios pendientes."

        # Filtrar por rango temporal si se menciona
        inicio, fin = self._rango_temporal(texto)

        if inicio:
            filtrados = []
            for r in pendientes:
                try:
                    fecha = datetime.strptime(r["time"], "%Y-%m-%d %H:%M").date()
                    if inicio <= fecha <= fin:
                        filtrados.append(r)
                except Exception:
                    continue
            if not filtrados:
                return "No tienes recordatorios en ese periodo."
            pendientes = filtrados

        if len(pendientes) == 1:
            r = pendientes[0]
            partes = r["time"].split()
            return f"Tienes un recordatorio: {r['title']} a las {partes[1]} del {partes[0]}."

        resultado = f"Tienes {len(pendientes)} recordatorios pendientes: "
        items = []
        for r in pendientes[:5]:
            partes = r["time"].split()
            items.append(f"{r['title']} a las {partes[1]}")
        resultado += ", ".join(items)
        if len(pendientes) > 5:
            resultado += f" y {len(pendientes) - 5} más"
        return resultado + "."


    def _get_calendar_events(self, texto):
        """
        @brief Consulta los eventos pendientes y los narra por voz.
        @param texto Transcripción de la consulta del usuario.
        @return str Frase con los eventos pendientes.
        """

        if not self.calendar_store:
            return "No tengo acceso al calendario."

        # Recargar desde disco
        self.calendar_store.events = self.calendar_store.load()

        inicio, fin = self._rango_temporal(texto)

        if not inicio:
            # Sin rango → hoy
            inicio = fin = datetime.now().date()

        resultados = []
        for event in self.calendar_store.events:
            try:
                fecha = datetime.strptime(event["date"], "%Y-%m-%d").date()
                if inicio <= fecha <= fin:
                    resultados.append(event)
            except Exception:
                continue

        if not resultados:
            if inicio == fin:
                return f"No tienes eventos el {inicio.strftime('%d/%m/%Y')}."
            return f"No tienes eventos entre el {inicio.strftime('%d/%m/%Y')} y el {fin.strftime('%d/%m/%Y')}."

        if inicio == fin:
            intro = f"El {inicio.strftime('%d/%m/%Y')} tienes: "
        else:
            intro = f"Entre el {inicio.strftime('%d/%m/%Y')} y el {fin.strftime('%d/%m/%Y')} tienes: "

        eventos_str = ", ".join(e["title"] for e in resultados)
        return intro + eventos_str + "."
        
    def _añadir_evento_calendario(self, texto):
        """
        @brief Añade evento al calendario que escucha.
        @param texto Transcripción de la consulta del usuario.
        """
        if not self.calendar_store:
            return "No tengo acceso al calendario."

        try:
            t = texto.lower().strip()

            for kw in ["añade", "agrega", "pon", "apunta", "añadir", "agregar",
                    "un evento", "una cita", "al calendario", "en el calendario",
                    "nueva cita", "nuevo evento"]:
                t = t.replace(kw, "").strip()

            t = self._palabras_a_numeros(t)
            t = self._normalizar_hora(t)

            logger.info(f"[ASSISTANT ENGINE] Texto calendario normalizado {t}")

            # Extraer fecha y hora por separado
            fecha, t_sin_fecha = self._extraer_fecha(t)
            hora_dt, titulo = self._extraer_hora(t_sin_fecha)

            # Si encontramos hora, combinar con la fecha
            if fecha and hora_dt:
                fecha = fecha.replace(
                    hour=hora_dt.hour,
                    minute=hora_dt.minute,
                    second=0, microsecond=0
                )
            elif not fecha and hora_dt:
                fecha = hora_dt

            if not fecha:
                return ("No he entendido la fecha. Puedes decir por ejemplo: "
                        "añade al calendario médico el martes a las diez, "
                        "o cita médico el 5 de julio.")

            # Limpiar título
            titulo = self._limpiar_titulo(titulo)

            if titulo.startswith("tengo "):
                titulo = titulo[6:]

            if titulo.startswith("voy al "):
                titulo = titulo[7:]

            if titulo.startswith("ir al "):
                titulo = titulo[6:]

            titulo = titulo.strip()

            if not titulo:
                titulo = "Evento"

            self.calendar_store.add_event(fecha.strftime("%Y-%m-%d"), titulo)

            if self.on_calendar_created:
                self.on_calendar_created()

            fecha_str = fecha.strftime("%d/%m/%Y")
            hora_str = fecha.strftime("%H:%M") if hora_dt else ""
            respuesta = f"Evento '{titulo}' añadido para el {fecha_str}"
            if hora_str:
                respuesta += f" a las {hora_str}"
            return respuesta + "."

        except Exception as e:
            logger.error(f"[CALENDAR] Fallo: {e}")
            return "No he podido añadir el evento al calendario."
        
    def _construir_prompt(self, mensaje):
        """
        @brief Prepara el prompt consolidado inyectando el System Prompt, memoria de corto plazo y el mensaje actual.
        @param mensaje Texto de la entrada actual remitida por el usuario.
        @return str Bloque de texto final formateado para el modelo LLM.
        """
        historial = self.memoria.get(self.user, [])[-5:]
        contexto = ""
        for h in historial:
            contexto += f"Usuario: {h['user']}\nAsistente: {h['bot']}\n"

        return (
            f"{PROMPT_DEL_SISTEMA}\n\n"
            f"Historial de conversación:\n{contexto}\n"
            f"Usuario: {mensaje}\nAsistente:"
        )

    def _ask_model(self, prompt):
        """
        @brief Realiza la invocación de red hacia la interfaz de inferencia del LLMClient.
        @details Se ejecuta con un techo de tiempo duro (self.llm_timeout). Si el
        cliente LLM se queda colgado por cualquier motivo (DNS, socket, etc. que
        no respete su propio timeout interno), esto evita que el asistente se
        quede esperando indefinidamente sin responder nada.
        @param prompt Texto formateado completo con el contexto.
        @return str Respuesta generada por la IA o cadena vacía si no hay cliente o falla.
        """
        if not self.llm:
            logger.warning("[LLM] no hay cliente configurado")
            return ""

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(self.llm.ask, prompt)
                resultado = future.result(timeout=self.llm_timeout)

            # Algunos backends de LLMClient.ask devuelven (texto, metadata)
            # en vez de un string plano. Si llega así, nos quedamos solo con
            # el texto para no acabar narrando/registrando la tupla entera
            # (p. ej. "['hola', {}]") como si fuera la respuesta.
            if isinstance(resultado, (tuple, list)):
                if resultado and isinstance(resultado[0], str):
                    resultado = resultado[0]
                else:
                    logger.warning(f"[LLM] respuesta con formato inesperado: {resultado!r}")
                    resultado = ""

            return resultado or ""
        except concurrent.futures.TimeoutError:
            logger.error("[LLM] tiempo de espera agotado, sin respuesta")
            return ""
        except Exception as e:
            logger.error(f"[LLM] error: {e}")
            return ""

    def _responder_con_llm_y_fallback_web(self, texto):
        """
        @brief Flujo común de "pregunta libre": intenta el LLM directamente y,
        si falla o no hay respuesta, recurre a _web_search como contexto
        adicional antes de reintentar con el LLM.
        @details Centraliza la lógica que antes estaba duplicada entre el
        intent "llm" y los fallbacks de "sports"/"wiki" cuando esas
        herramientas específicas no encuentran nada. Siempre antepone
        AVISO_NO_INVENTAR al contexto web para reducir el riesgo de que el
        modelo rellene huecos con datos inventados.
        @param texto Transcripción original del usuario.
        @return str Respuesta generada, o mensaje de disculpa si todo falla.
        """
        prompt = self._construir_prompt(texto)
        respuesta = ""

        if self._hay_internet():
            respuesta = self._ask_model(prompt)

        if not respuesta:
            logger.info("[ASSISTANT] fallback a búsqueda web")
            web = self._web_search(texto)
            if web:
                respuesta = self._ask_model(AVISO_NO_INVENTAR + web + "\n\n" + prompt)

        if not respuesta:
            respuesta = "Lo siento, no tengo respuesta en este momento."

        return respuesta

    # =========================================================
    # PROCESAMIENTO PRINCIPAL
    # =========================================================

    def _procesar_texto(self, texto):
        """
        @brief Flujo central y toma de decisiones para resolver un turno de conversación completo.
        @param texto Transcripción de la entrada del usuario.
        @return str Texto de salida generado que el robot debe responder.
        """
        logger.info(f"[ASSISTANT ENGINE] USER:{self.user} {texto}")
        intent = self._detectar_intencion(texto)
        logger.info(f"[ASSISTANT ENGINE] {intent} ")

        if intent == "time":
            logger.info("Consultado hora")
            respuesta = f"Son las {self._get_time()}."

        elif intent == "weather":
            if self.display:
                self.display.set_estado("Consultando clima...")
                logger.info("[ASSISTANT ENGINE] Consultado clima")
            respuesta = self._get_weather()

        elif intent == "sports":
            if self.display:
                self.display.set_estado("Consultando resultado...")
                logger.info("[ASSISTANT ENGINE] Consultado resultado deportivo")

            respuesta = get_resultado_equipo(texto.lower())
            if not respuesta:
                # No reconocemos el equipo o la API ha fallado: caemos al
                # flujo normal de LLM + búsqueda web.
                logger.info("[ASSISTANT ENGINE] Sports sin resultado, fallback a LLM/web")
                respuesta = self._responder_con_llm_y_fallback_web(texto)

        elif intent == "wiki":
            if self.display:
                self.display.set_estado("Buscando información...")
                logger.info("[ASSISTANT ENGINE] Consultando Wikipedia")

            respuesta = get_resumen(texto)
            if not respuesta:
                # Wikipedia no tiene artículo (p. ej. algo muy reciente/viral):
                # caemos al flujo normal de LLM + búsqueda web.
                logger.info("[ASSISTANT ENGINE] Wikipedia sin resultado, fallback a LLM/web")
                respuesta = self._responder_con_llm_y_fallback_web(texto)

        elif intent == "calendar":
            if self.display:
                self.display.set_estado("Consultando calendario...")
                logger.info("[ASSISTANT ENGINE] Consultado calendario")
            respuesta = self._get_calendar_events(texto) 
        
        elif intent == "calendar_add": 
            if self.display:
                self.display.set_estado("Añadiendo al calendario...")
                logger.info("[ASSISTANT ENGINE] Añadiendo al calendario")
                
            respuesta = self._añadir_evento_calendario(texto) 
        
        elif intent == "reminder_add":
            if self.display:
                self.display.set_estado("Añadiendo a recordatorios...")
                logger.info("[ASSISTANT ENGINE] Añadiendo a recordatorios")
            
            respuesta = self._crear_recordatorio(texto)
                        
        elif intent == "reminder_query":
            if self.display:
                self.display.set_estado("Consultando recordatorios...")
                logger.info("[ASSISTANT ENGINE] Consultado recordatorios")
                
            respuesta = self._consultar_recordatorios(texto)
        
        else:
            if self.display:
                self.display.set_talking(False)
                self.display.set_estado("Pensando...")

            respuesta = self._responder_con_llm_y_fallback_web(texto)

        # Registrar el turno actual en la estructura persistente
        self.memoria.setdefault(self.user, []).append({
            "user": texto,
            "bot": respuesta,
            "time": datetime.now().isoformat()
        })
        self._guardar_memoria()

        logger.info(f"[ASSISTANT ENGINE] (ROJAZZ) {respuesta}")
        logger.info("-" * 50)
        return respuesta

    # =========================================================
    # INTERFAZ PÚBLICA
    # =========================================================

    def set_user(self, user):
        """
        @brief Modifica el perfil de usuario activo y genera un saludo adaptado por voz (TTS).
        @param user Nombre de pila o identificador del usuario detectado (ej: por reconocimiento facial).
        """
        self.user = user
        historial = self.memoria.get(user, [])
        if historial:
            self.speak(f"Hola de nuevo, {user}. ¿En qué te puedo ayudar?")
        else:
            self.speak(f"Hola {user}, soy tu asistente. ¿En qué te puedo ayudar?")

    def speak(self, text):
        """
        @brief Envía una cadena de texto al sintetizador de audio (TTS) y sincroniza los estados gráficos de la cara.
        @param text Mensaje completo de respuesta que será transformado a audio.
        """
        if self.display:
            self.display.set_estado("Hablando...")
            self.display.set_talking(True)
         
        def _fin():
            if self.display:
               self.display.set_talking(False)
               if self.stt and self.stt.awake:
                   self.display.set_estado("Escuchando...") 
               else:
                   self.display.set_estado("Esperando activación...") 

        try:
            self.tts.speak(text, on_done=_fin)
        except Exception as e:
            # Si el TTS falla aquí sin protección, el hilo de escucha (daemon)
            # muere en silencio y el asistente se queda "colgado" sin avisar.
            logger.error(f"[TTS] error al hablar: {e}")
            if self.display:
                self.display.set_talking(False)
                self.display.set_estado("Escuchando...")
        
    def start(self):
        """
        @brief Levanta e inicializa el hilo daemon encargado del bucle infinito de escucha por micrófono.
        """
        if self.running:
            logger.warning("[ASSISTANT] ya está en marcha")
            return
        if not self.stt:
            logger.error("[ASSISTANT] no hay STT configurado")
            return
            
        if self.display: 
            self.display.set_estado("Esperando activación")
            logger.warning("[ASSISTANT] Esperando activación")
            
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("[ASSISTANT] escucha iniciada")

    def _loop(self):
        """
        @brief Bucle de consumo interno para procesar el texto obtenido del transcriptor de audio.
        @details Intercepta comandos de parada en tiempo real antes de procesar intenciones complejas.
        Todo el cuerpo va envuelto en try/except: al ser un hilo daemon, una
        excepción sin capturar lo mata en silencio (sin log visible para el
        usuario) y el asistente se queda "escuchando" para siempre sin
        responder nunca más. Esa es la causa más probable de los cuelgues.
        """
        def _on_text(text):
            try:
                if not text or not isinstance(text, str) or not text.strip():
                    return

                if self.display:
                    self.display.set_estado(f"Escuchado: {text[:20]}")

                # Interrupción inmediata por comandos de pánico o parada de locución
                if any(x in text for x in ["calla", "para", "silencio", "cállate"]):
                    self.tts.stop()
                    if self.display:
                        self.display.set_estado("Escuchando...")
                    return

                try:
                    respuesta = self._procesar_texto(text)
                except Exception as e:
                    logger.error(f"[ASSISTANT] error procesando: {e}")
                    respuesta = "He tenido un problema al procesar tu mensaje."

                self.speak(respuesta)

            except Exception as e:
                # Red de seguridad final: nunca dejar morir el hilo en silencio.
                logger.error(f"[ASSISTANT] error inesperado en _on_text: {e}")
                if self.display:
                    self.display.set_estado("Escuchando...")

        self.stt.listen_loop(_on_text, assistant=self, device=self.mic_device)

    def stop(self):
        """
        @brief Detiene y cancela de forma controlada el ciclo de vida del motor de escucha y voz.
        """
        logger.info("[ASSISTANT] deteniendo")
        self.running = False
        if self.stt:
            self.stt.stop()
        self.tts.stop()
        
        if self.reminder_scheduler:
            self.reminder_scheduler.stop()


