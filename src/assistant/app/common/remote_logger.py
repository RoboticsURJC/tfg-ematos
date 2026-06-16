# handlers/remote_handler.py

import requests
import logging

##
# @file remote_handler.py
# @brief Manejador personalizado de logging para el envío remoto de registros por HTTP.
# @details Permite interceptar los eventos de log de la aplicación y redirigirlos de forma síncrona
# hacia un servidor web o API centralizada.
#

class RemoteHandler(logging.Handler):
    """
    @brief Clase encargada de empaquetar y transmitir los logs hacia un punto de acceso HTTP remoto.
    @details Hereda de logging.Handler y sobreescribe el método fundamental emit para realizar peticiones POST.
    """

    def __init__(self, url):
        """
        @brief Inicializa la instancia del manejador remoto configurando la dirección de destino.
        
        Llama al constructor de la clase base logging.Handler y establece la URL del endpoint receptor.
        
        @param url Dirección base del servidor remoto de logs (ej: 'http://localhost:3000').
        """
        super().__init__()
        
        ## URL del servidor destino donde se enviarán las peticiones JSON con las líneas de log.
        self.url = url

    def emit(self, record):
        """
        @brief Envía de forma activa un registro de log hacia el servidor HTTP remoto.
        
        Este método es invocado automáticamente por el framework de logging de Python cada vez que se genera un evento. 
        Transforma el registro (record) en una carga útil JSON que contiene el nivel y el mensaje formateado.
        
        @note El tiempo de espera (timeout) está limitado estrictamente a 1 segundo para evitar que una caída del 
        servidor remoto bloquee el hilo principal de ejecución de la aplicación o del robot.
        
        @param record Objeto de tipo logging.LogRecord que contiene toda la metadata del evento capturado.
        """
        try:
            requests.post(
                f"{self.url}/log",
                json={
                    "level": record.levelname,
                    "message": self.format(record),
                }, 
                timeout=1
            )

        except Exception:
            # Silenciamos de forma explícita cualquier fallo de conexión para evitar bucles infinitos
            # de logs si el servidor remoto está caído o inalcanzable.
            pass