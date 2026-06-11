
"""
@file assistant_engine.py
@brief Motor principal del asistente: integra STT, TTS, LLM y herramientas.

Replica fielmente la lógica del asistente_robotico.py original:
- Detección de intenciones (hora, clima, LLM)
- Memoria conversacional persistente por usuario
- Llamadas al modelo LLM remoto
- Fallback a búsqueda web si el modelo falla
"""

import os
import re
import json
import socket
import threading
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


# =========================================================
# PROMPT DEL SISTEMA
# =========================================================

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
"""

# =========================================================
# RUTAS
# =========================================================

MEMORY_FILE = "memoria_usuarios.json"
TIMEOUT = 90


# =========================================================
# AssistantEngine
# =========================================================

class AssistantEngine:
    """
    @brief Motor conversacional completo del asistente robótico.

    Orquesta el ciclo completo:
    1. El STT escucha y entrega texto.
    2. Se detecta la intención (hora / clima / LLM).
    3. Se construye el prompt con historial de memoria.
    4. Se llama al modelo LLM remoto.
    5. Si falla, se hace búsqueda web como fallback.
    6. La respuesta se sintetiza con TTS.
    7. La interacción se guarda en memoria persistente.
    """

    def __init__(self, ui_state=None, display=None, calendar_store=None,reminder_store=None, model_path=None, server_url=None, mic_name=None, llm_model='groq', llm_timeout=90):
        """
        @param ui_state    Estado compartido de la interfaz (UIState).
        @param display     Pantalla facial (FaceDisplay).
        @param model_path  Ruta al modelo Vosk para STT.
        @param server_url  URL del servidor LLM (ej: http://192.168.x.x:8000/generate).
        """
        self.ui_state = ui_state
        self.display = display
        self.calendar_store = calendar_store 
        self.reminder_store = reminder_store
        self.reminder_scheduler = None
        self.user = "invitado"
        self.running = False

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

        # ~ Iniciar tts
        self.tts = TTS()
        self.stt = VoskSTT(model_path) if model_path else None
        
        self.memoria = self._cargar_memoria()

        logger.info("[ASSISTANT] listo")

    # =========================================================
    # MEMORIA PERSISTENTE
    # =========================================================

    def _cargar_memoria(self):
        """
        @brief Carga el historial conversacional desde disco.
        @return Diccionario {usuario: [lista de turnos]}.
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
        """@brief Persiste el historial conversacional en disco."""
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.memoria, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[MEMORIA] error al guardar: {e}")

    # =========================================================
    # HERRAMIENTAS LOCALES
    # =========================================================

    def _get_time(self):
        """@brief Devuelve la hora actual en formato HH:MM."""
        return datetime.now().strftime("%H:%M")

    def _get_weather(self, city="Madrid"):
        """
        @brief Consulta el clima actual via open-meteo (sin API key).
        @param city Ciudad a consultar.
        @return Descripción del clima en texto.
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

    def _detectar_intencion(self, text):
        """
        @brief Clasifica el texto del usuario en una intención.

        @param text  Texto en minúsculas.
        @return 'time', 'weather' o 'llm'.
        """
        if any(x in text for x in ["hora", "qué hora", "que hora", "dime la hora"]):
            return "time"
        if any(x in text for x in ["clima", "tiempo", "qué tiempo", "que tiempo", "temperatura"]):
            return "weather"
            
        if any(x in text for x in ["recuerdame", "recuérdame", "avisame", "avísame", 
           "alarma", "medicación", "pastilla", "medicina"
        ]): 
            return "reminder"
            
        if any(x in text for x in [
            "citas", "eventos", "agenda", "calendario", 
            "qué tengo", "que tengo", "mis planes", "mi semana",
            "martes", "lunes", "proximo", "hoy", "mi mes"
        
        ]):
            return "calendar"
        
        return "llm"

    # =========================================================
    # LLM
    # =========================================================

    def _hay_internet(self):
        """@brief Comprueba conectividad básica a internet."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            return True
        except Exception:
            return False

    def _web_search(self, query):
        """
        @brief Búsqueda web de emergencia via DuckDuckGo HTML.
        @param query Consulta a buscar.
        @return Texto con los primeros resultados, o cadena vacía.
        """
        try:
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            results = [a.get_text() for a in soup.find_all("a", class_="result__a", limit=3)]
            return "\n".join(results)
        except Exception as e:
            logger.error(f"[WEB SEARCH] error: {e}")
            return ""


    def _parse_fecha(self, texto):
        """
        Convierte expresiones naturales a fechas reales
        Ej: "mañana", "proximo lunes", "este mes"
        """
        
        settings = {
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
        
        fecha = dateparser.parse(texto, settings=settings)
        
        return fecha
        
    def _rango_temporal(self, texto):
        """
        Devuelve (inico, fin) segun la expresion natural
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
            
           
    def _get_calendar_events(self, text):
                
        inicio, fin = self._rango_temporal(text)
        
        if not inicio:
            return "No he entendido bien la fecha que quieres consultar"
 
        resultados = []
        
        for event in self.calendar_store.events:
            try:
                fecha = datetime.strptime(event["date"], "%Y-%m-%d").date()
                
                if inicio <= fecha <= fin:
                    resultados.append(event)
                    
            except:
                logger.error("[ASSISTANT ENGINE] error creando la fecha del calendario")
                continue
                
        if not resultados:
            return "No tienes eventos en este periodo."
            
        if inicio == fin:
            intro = f"Tiene esto el {inicio.strftime('%d/%m/%Y')}: "
            
        else:
            intro = f"Tienes estos eventos entre el {inicio.strftime('%d/%m/%Y')} y el {fin.strftime('%d/%m/%Y')}: "
            
        return intro + " ".join(
           f"{e['title']} ({e['date']})." for e in resultados
        )  
            
    def _crear_recordatorio(self, texto):
        
        """
        Convierte una orden de voz en un recordatorio
        Ej: Recuerdame tomarme la pastilla en 5 minutos
        """
        
        logger.info("[ASSISTANT ENGINE] Crear recordartorio")
        
        try:


            if not self.reminder_store:
                return "No tengo acceso al sistema de recordatorios"
            
            texto_original = texto.lower()
        
            comando_limpio = re.sub(r"(recu[eé]rdame|recuerdame|av[ií]same|avisame)", "", texto_original).strip()
        
            minutos = None
            horas = None
        
            m_min = re.search(r"(\d+)\s*min", comando_limpio)
            m_h = re.search(r"(\d+)\s*hora", comando_limpio)
            
            # ~ Calcular fecha del recordatorio
            when = datetime.now()
        
            if m_min:
               minutos = int(m_min.group(1))
               when += timedelta(minutes=minutos)
            
            if m_h:
               when += timedelta(hours=int(m_h.group(1)))
        
            # ~ Si no se detecta tiempo
            if not minutos and not horas:
                when += timedelta(minutes=5)
            
            else:
                when += timedelta(minutes=5)
        
            mensaje = re.sub(r"\d+\s*(minutos?|horas?) ", "", comando_limpio).strip()
        
            if not mensaje:
                mensaje = "Recordatario sin título"
            
            # ~ Guardar recordatorio   
            self.reminder_store.add(
                mensaje,
                when.strftime("%Y-%m-%d %H:%M")
            )
        
            logger.info("[ASSISTANT ENGINE] Recordatorio añadido correctamente")
        
            return "Recordatorio añadido correctamente"
        
        except Exception as e:
            logger.info(f"[ASSISTANT ENGINE] Fallo al crear recordatorio {e}")
            return "No he podido crear el recordatorio"
        
            
    def _construir_prompt(self, mensaje):
        """
        @brief Construye el prompt completo con contexto conversacional.

        Incluye el system prompt, los últimos 5 turnos de memoria
        y el mensaje actual del usuario.

        @param mensaje  Texto del usuario en este turno.
        @return Prompt completo como string.
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
        @brief Envía el prompt al LLMClient y devuelve la respuesta.

        @param prompt  Texto completo del prompt.
        @return Respuesta del modelo (str) o cadena vacía si falla.
        """
        if not self.llm:
            logger.warning("[LLM] no hay cliente configurado")
            return ""
        return self.llm.ask(prompt)


    # =========================================================
    # PROCESAMIENTO PRINCIPAL
    # =========================================================

    def _procesar_texto(self, texto):
        """
        @brief Flujo completo de procesamiento de un turno conversacional.

        1. Detecta intención.
        2. Ejecuta herramienta local si procede.
        3. Si es LLM: construye prompt, llama al modelo.
        4. Fallback web si el modelo no responde.
        5. Guarda en memoria persistente.

        @param texto  Texto reconocido del usuario.
        @return Respuesta en texto del asistente.
        """
        logger.info(f"[USER:{self.user}] {texto}")

        intent = self._detectar_intencion(texto)

        if intent == "time":
            logger.info("Consultado hora")
            respuesta = f"Son las {self._get_time()}."

        elif intent == "weather":
            if self.display:
                # ~ self.display.set_talking(False)
                self.display.set_estado("Consultando clima...")
                logger.info("Consultado clima")
            respuesta = self._get_weather()
            
        elif intent == "calendar":
            respuesta = self._get_calendar_events(texto) 
        
        elif intent == "reminder":
            respuesta = self._crear_recordatorio(texto)
        
        else:
            if self.display:
                self.display.set_talking(False)
                self.display.set_estado("Pensando...")

            prompt = self._construir_prompt(texto)
            respuesta = ""

            if self._hay_internet():
                respuesta = self._ask_model(prompt)

            # Fallback: búsqueda web + reintento al modelo
            if not respuesta:
                logger.info("[ASSISTANT] fallback a búsqueda web")
                web = self._web_search(texto)
                if web:
                    respuesta = self._ask_model(web + "\n" + prompt)

            if not respuesta:
                respuesta = "Lo siento, no tengo respuesta en este momento."

        # Guardar en memoria
        self.memoria.setdefault(self.user, []).append({
            "user": texto,
            "bot": respuesta,
            "time": datetime.now().isoformat()
        })
        self._guardar_memoria()

        logger.info(f"[BOT] {respuesta}")
        logger.info("-" * 50)
        return respuesta

    # =========================================================
    # INTERFAZ PÚBLICA
    # =========================================================

    def set_user(self, user):
        """
        @brief Establece el usuario activo y pronuncia el saludo.

        Si el usuario tiene historial previo, el saludo es de reencuentro.

        @param user  Nombre del usuario.
        """
        self.user = user
        historial = self.memoria.get(user, [])
        if historial:
            self.speak(f"Hola de nuevo, {user}. ¿En qué te puedo ayudar?")
        else:
            self.speak(f"Hola {user}, soy tu asistente. ¿En qué te puedo ayudar?")

    def speak(self, text):
        """
        @brief Sintetiza y reproduce texto por voz.
        @param text  Texto a pronunciar.
        """
        if self.display:
            self.display.set_estado("Hablando...")
            self.display.set_talking(True)
         
        def _fin():
            if self.display:
               self.display.set_talking(False)
               self.display.set_estado("Escuchando...") 
            
        self.tts.speak(text, on_done=_fin)
        

    def start(self):
        """
        @brief Arranca el hilo de escucha continua.

        Sólo arranca si hay un modelo STT configurado y
        el asistente no está ya en marcha.
        """
        if self.running:
            logger.warning("[ASSISTANT] ya está en marcha")
            return
        if not self.stt:
            logger.error("[ASSISTANT] no hay STT configurado")
            return
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        logger.info("[ASSISTANT] escucha iniciada")

    def _loop(self):
        """
        @brief Hilo interno de escucha y respuesta.

        Consume texto del STT y genera respuesta para cada frase.
        Gestiona comandos de parada ("calla", "para", "silencio").
        """
        def _on_text(text):
            if self.display:
                # ~ self.display.set_talking(False)
                self.display.set_estado(f"Escuchado: {text[:20]}")

            # Comandos de parada inmediata
            if any(x in text for x in ["calla", "para", "silencio", "cállate"]):
                self.tts.stop()
                if self.display:
                    # ~ self.display.set_talking(False)
                    self.display.set_estado("Escuchando...")
                                        
                return

            try:
                respuesta = self._procesar_texto(text)
            except Exception as e:
                logger.error(f"[ASSISTANT] error procesando: {e}")
                respuesta = "He tenido un problema al procesar tu mensaje."

            self.speak(respuesta)

        self.stt.listen_loop(_on_text, assistant=self, device=self.mic_device)

    def stop(self):
        """@brief Detiene el asistente (STT + TTS)."""
        logger.info("[ASSISTANT] deteniendo")
        self.running = False
        if self.stt:
            self.stt.stop()
        self.tts.stop()
        
        if self.reminder_scheduler:
            self.reminder_scheduler.stop()
        
        
