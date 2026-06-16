# assistant_engine.py

"""
@file assistant_engine.py
@brief Motor principal del asistente: integra STT, TTS, LLM y herramientas.
@details Replica fielmente la lógica del asistente_robotico.py original:
- Detección de intenciones (hora, clima, calendario, recordatorios, LLM).
- Memoria conversacional persistente por usuario.
- Llamadas al modelo LLM remoto.
- Fallback a búsqueda web si el modelo falla.
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
"""

# =========================================================
# RUTAS
# =========================================================

## Nombre del fichero JSON local para guardar la persistencia del historial.
MEMORY_FILE = "memoria_usuarios.json"

## Tiempo máximo de espera por defecto (en segundos) para solicitudes de red.
TIMEOUT = 90


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
        
        ## Nombre o ID del perfil de usuario actualmente interactuando.
        self.user = "invitado"
        
        ## Bandera de control para saber si el bucle de escucha asíncrono está encendido.
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

    def _detectar_intencion(self, text):
        """
        @brief Clasifica y mapea el texto del usuario para identificar comandos conocidos o herramientas nativas.
        @param text Transcripción en texto limpio y minúsculas generada por el STT.
        @return str Identificador de la intención ('time', 'weather', 'reminder', 'calendar', o 'llm').
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
        @param query Cadena de términos de búsqueda solicitados por el usuario.
        @return str Resumen de las primeras coincidencias textuales encontradas en la web.
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
        @brief Transforma expresiones complejas de lenguaje natural a un objeto datetime estructurado.
        @param texto Fragmento de la transcripción de voz que describe un tiempo (ej: 'el próximo martes').
        @return datetime Objeto de tiempo interpretado, o None si no se comprende la referencia.
        """
        settings = {
            "PREFER_DATES_FROM": "future",
            "RELATIVE_BASE": datetime.now()
        }
        fecha = dateparser.parse(texto, settings=settings)
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
            
    def _get_calendar_events(self, text):
        """
        @brief Filtra y lee los eventos agendados dentro del rango temporal solicitado por voz.
        @param text Texto con la consulta cronológica sobre la agenda.
        @return str Frase descriptiva conteniendo las citas de la agenda para ser narradas por TTS.
        """
        inicio, fin = self._rango_temporal(text)
        
        if not inicio:
            return "No he entendido bien la fecha que quieres consultar"
 
        resultados = []
        
        for event in self.calendar_store.events:
            try:
                fecha = datetime.strptime(event["date"], "%Y-%m-%d").date()
                if inicio <= fecha <= fin:
                    resultados.append(event)
            except Exception:
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
        @brief Procesa una orden verbal para programar un nuevo recordatorio de alerta.
        @details Extrae mediante expresiones regulares patrones de tiempo numéricos ('minutos', 'horas') 
        y agenda el objeto en el repositorio persistente.
        
        @param texto Transcripción del comando de voz.
        @return str Mensaje de confirmación del éxito de la operación.
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
            
            # Calcular fecha exacta del recordatorio
            when = datetime.now()
        
            if m_min:
               minutos = int(m_min.group(1))
               when += timedelta(minutes=minutos)
            
            if m_h:
               when += timedelta(hours=int(m_h.group(1)))
        
            # Si no se especifica explícitamente el tiempo, aplica salvaguarda de 5 minutos
            if not minutos and not horas:
                when += timedelta(minutes=5)
            else:
                when += timedelta(minutes=5)
        
            mensaje = re.sub(r"\d+\s*(minutos?|horas?) ", "", comando_limpio).strip()
        
            if not mensaje:
                mensaje = "Recordatario sin título"
               
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
        @param prompt Texto formateado completo con el contexto.
        @return str Respuesta generada por la IA o cadena vacía si no hay cliente o falla.
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
        @brief Flujo central y toma de decisiones para resolver un turno de conversación completo.
        @param texto Transcripción de la entrada del usuario.
        @return str Texto de salida generado que el robot debe responder.
        """
        logger.info(f"[USER:{self.user}] {texto}")
        intent = self._detectar_intencion(texto)

        if intent == "time":
            logger.info("Consultado hora")
            respuesta = f"Son las {self._get_time()}."

        elif intent == "weather":
            if self.display:
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

            # Fallback activo si falla la red o el servicio de lenguaje inteligente
            if not respuesta:
                logger.info("[ASSISTANT] fallback a búsqueda web")
                web = self._web_search(texto)
                if web:
                    respuesta = self._ask_model(web + "\n" + prompt)

            if not respuesta:
                respuesta = "Lo siento, no tengo respuesta en este momento."

        # Registrar el turno actual en la estructura persistente
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
            
        self.tts.speak(text, on_done=_fin)
        
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
        """
        def _on_text(text):
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