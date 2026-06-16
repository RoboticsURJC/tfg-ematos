# app/core/logs_to_server.py

import logging
import requests

##
# @file logs_to_server.py
# @brief Implementación de un manejador de red síncrono para la transmisión de registros de auditoría.
# @details Extiende las capacidades del subsistema nativo logging.Handler para empaquetar eventos 
# en payloads JSON simples y enviarlos de forma directa al Dashboard.
#

class RemoteHandler(logging.Handler):
    """
    @brief Manejador de logs especializado en la persistencia y centralización remota via HTTP POST.
    @details Intercepta cualquier evento emitido en los niveles configurados (ej: DEBUG, INFO) 
    y lo despacha síncronamente por red hacia la base de datos de telemetría.
    """

    def __init__(self, url):
        """
        @brief Inicializa la instancia del manejador vinculando el socket/url de destino.
        
        @param url Dirección URL absoluta del servicio receptor (ej: 'http://192.168.1.96:3000/client-log').
        """
        super().__init__()
        
        ## Dirección de red (endpoint) del servidor remoto de recolección de logs.
        self.url = url

    def emit(self, record):
        """
        @brief Procesa, formatea y transmite el registro de log de forma activa por red.
        @details Extrae las propiedades textuales del evento utilizando los formateadores 
        configurados en el objeto padre, construye un diccionario JSON con la clave 'text' 
        y ejecuta una petición HTTP POST.
        
        @note El tiempo de espera (timeout) está limitado estrictamente a 1 segundo. Si el Dashboard 
        está saturado, desconectado o en una IP errónea en la red local de la Raspberry Pi, el hilo 
        no se quedará colgado de forma indefinida y la ejecución del robot continuará con normalidad.
        
        @param record Instancia de tipo logging.LogRecord que contiene los metadatos inherentes al mensaje generado.
        """
        try:
            # Convierte el LogRecord en una cadena de texto plana utilizando el Formatter asociado
            msg = self.format(record)

            # Envío síncrono de la traza de log formateada hacia la pasarela web
            requests.post(
                self.url,
                json={"text": msg},
                timeout=1
            )

        except Exception as e:
            # Salvaguarda en caso de caída de la infraestructura de red o servidor offline.
            # Se imprime en el canal stdout estándar de la consola del sistema para evitar
            # recursividad infinita del propio manejador de logging.
            print("[REMOTE LOG ERROR]", e)