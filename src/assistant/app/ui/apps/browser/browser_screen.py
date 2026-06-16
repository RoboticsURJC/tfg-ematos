# app/ui/screens/browser_screen.py

"""
@file browser_screen.py
@brief Interfaz de navegación web adaptada para pantallas táctiles en Raspberry Pi.
@details Integra un contenedor PyQt5 que orquesta procesos externos de Chromium en modo quiosco,
controladores de navegación física mediante emulación de pulsaciones (`xdotool`) y un teclado virtual (`wvkbd`).
"""

import os
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QApplication
)
from PyQt5.QtCore import Qt, QTimer
from app.ui.widgets.keyboard_widget import KeyboardWidget
from app.core.logger import logger

## URL del motor de búsqueda DuckDuckGo configurada por defecto en modo simplificado sin JavaScript invasivo.
HOME_URL = (
    "https://duckduckgo.com/?kae=d&k1=-1&kak=-1&kao=-1"
    "&kap=-1&kaq=-1&kar=b&kat=t&kav=1&kp=-2"
)

## Hoja de estilos CSS (QSS) para la personalización y escalado de los elementos táctiles de la barra de navegación.
STYLE = """
QWidget#browser_root {
    background-color: #1e293b;
    font-family: "Segoe UI", sans-serif;
}
QWidget#top_bar_container {
    background-color: #0f172a;
}
QWidget#bottom_bar_container {
    background-color: #0f172a;
}
QLineEdit#url_input {
    background: #1e293b;
    border: 4px solid #4f46e5;
    border-radius: 28px;
    padding: 12px 24px;
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
    min-height: 64px;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
}
QPushButton#btn_nav {
    background: #4f46e5; border: none; border-radius: 24px;
    color: white; font-size: 24px; font-weight: 800;
    min-width: 140px; min-height: 64px; padding: 0 20px;
}
QPushButton#btn_nav:pressed { background: #3730a3; }
QPushButton#btn_back {
    background: #475569; border: none; border-radius: 24px;
    color: white; font-size: 24px; font-weight: 800;
    min-width: 140px; min-height: 64px; padding: 0 20px;
}
QPushButton#btn_back:pressed { background: #334155; }
QPushButton#btn_exit {
    background: #dc2626; border: none; border-radius: 24px;
    color: white; font-size: 24px; font-weight: 800;
    min-width: 140px; min-height: 64px; padding: 0 20px;
}
QPushButton#btn_exit:pressed { background: #991b1b; }
QPushButton#btn_nav_arrow {
    background: #334155; border: none; border-radius: 24px;
    color: white; font-size: 28px; font-weight: 900;
    min-width: 80px; min-height: 64px;
}
QPushButton#btn_nav_arrow:pressed  { background: #1e293b; }
QPushButton#btn_nav_arrow:disabled { color: #64748b; background: #1e293b; }
"""


class BrowserScreen(QWidget):
    """
    @brief Pantalla contenedora encargada de inicializar y supervisar el ciclo de vida del navegador Chromium.
    """

    def __init__(self, controller):
        """
        @brief Constructor de la pantalla BrowserScreen.
        @details Inicializa la interfaz gráfica, distribuye los botones táctiles en layouts
        e inyecta el widget de teclado inicial de PyQt5.
        
        @param controller Instancia del orquestador o gestor central de la UI de la aplicación.
        """
        super().__init__()
        
        ## Instancia del controlador central de pantallas.
        self.controller = controller
        
        ## Referencia al subproceso del navegador externo Chromium.
        self._chromium  = None
        
        ## Referencia al subproceso del teclado virtual táctil wvkbd.
        self._wvkbd     = None

        self.setObjectName("browser_root")
        self.setStyleSheet(STYLE)

        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # ── Barra superior de controles ───────────────────────────────────────
        bar_container = QWidget()
        bar_container.setObjectName("top_bar_container")
        top_bar = QHBoxLayout(bar_container)
        top_bar.setSpacing(10)
        top_bar.setContentsMargins(16, 10, 16, 10)

        self.btn_home = QPushButton("⬅ Volver")
        self.btn_home.setObjectName("btn_back")
        self.btn_home.clicked.connect(self.go_back_to_launcher)

        self.btn_prev = QPushButton("◀")
        self.btn_nav_arrow = self.btn_prev  # Mapeo implícito para compatibilidad semántica
        self.btn_prev.setObjectName("btn_nav_arrow")
        self.btn_prev.clicked.connect(self._go_back)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("btn_nav_arrow")
        self.btn_next.clicked.connect(self._go_forward)

        self.input_url = QLineEdit()
        self.input_url.setObjectName("url_input")
        self.input_url.setPlaceholderText("Escribe aquí para buscar…")
        self.input_url.setAlignment(Qt.AlignCenter)
        self.input_url.returnPressed.connect(self._on_buscar)
        self.input_url.mousePressEvent = lambda e: self._show_initial_keyboard()

        self.btn_go = QPushButton("Buscar")
        self.btn_go.setObjectName("btn_nav")
        self.btn_go.clicked.connect(self._launch_from_bar)

        top_bar.addWidget(self.btn_home)
        top_bar.addWidget(self.btn_prev)
        top_bar.addWidget(self.btn_next)
        top_bar.addStretch(1)
        top_bar.addWidget(self.input_url, 5)
        top_bar.addStretch(1)
        top_bar.addWidget(self.btn_go)
        root_layout.addWidget(bar_container)

        root_layout.addStretch(1)

        # Teclado en pantalla nativo de PyQt5 utilizado únicamente en la pantalla de inicio del módulo
        self.initial_keyboard = KeyboardWidget(self)
        self.initial_keyboard.confirmed.connect(self._launch_from_bar)
        root_layout.addWidget(self.initial_keyboard)

        # ── Barra inferior ────────────────────────────────────────────────────
        bottom_bar = QWidget()
        bottom_bar.setObjectName("bottom_bar_container")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(16, 10, 16, 10)

        self.btn_exit = QPushButton("✕ Salir")
        self.btn_exit.setObjectName("btn_exit")
        self.btn_exit.clicked.connect(self.go_back_to_launcher)

        bottom_layout.addStretch(1)
        bottom_layout.addWidget(self.btn_exit)
        root_layout.addWidget(bottom_bar)

        # Inicialización diferida del enfoque del teclado virtual
        QTimer.singleShot(100, self._show_initial_keyboard)

    # ── Métodos de soporte del Teclado Inicial ────────────────────────────────

    def _show_initial_keyboard(self):
        """
        @brief Enlaza el widget del teclado virtual interno de PyQt5 con la barra de entrada de texto.
        """
        self.initial_keyboard.set_target(self.input_url)

    # ── Rutinas de Navegación y Saneo ─────────────────────────────────────────

    def _resolve_url(self, text):
        """
        @brief Analiza y sanea la cadena de texto de entrada para determinar si es una dirección URL o un término de búsqueda.
        
        @param text Cadena de texto en bruto extraída de la barra de direcciones.
        @return str Dirección URL absoluta formateada y sanitizada.
        """
        url = text.strip()
        if not url:
            return HOME_URL
        if "://" not in url:
            # Si contiene espacios o carece de un punto, se interpreta de manera automática como una búsqueda en DuckDuckGo
            if " " in url or "." not in url:
                return f"https://duckduckgo.com/?q={url.replace(' ', '+')}&kae=d&k1=-1"
            return "https://" + url
        return url

    def _on_buscar(self):
        """
        @brief Slot asíncrono para el evento de retorno de la barra de direcciones (`Return Pressed`).
        """
        self.initial_keyboard.detach()
        url = self._resolve_url(self.input_url.text())
        self._launch_chromium(url)

    def _launch_from_bar(self):
        """
        @brief Slot asíncrono asignado a la acción del botón físico táctil de 'Buscar'.
        """
        self.initial_keyboard.detach()
        url = self._resolve_url(self.input_url.text())
        self._launch_chromium(url)

    def _go_back(self):
        """
        @brief Emula el comando de hardware 'Atrás' en el historial de navegación.
        @details Invoca a la herramienta de Linux `xdotool` para inyectar de forma directa 
        la combinación de teclas `Alt + Flecha Izquierda` dentro del servidor de ventanas gráfico X11.
        """
        if self._chromium:
            subprocess.Popen(["xdotool", "key", "alt+Left"])

    def _go_forward(self):
        """
        @brief Emula el comando de hardware 'Adelante' en el historial de navegación.
        @details Utiliza `xdotool` para inyectar la combinación de teclas `Alt + Flecha Derecha`.
        """
        if self._chromium:
            subprocess.Popen(["xdotool", "key", "alt+Right"])

    # ── Gestión de Procesos Externos (Chromium + wvkbd) ───────────────────────

    def _launch_chromium(self, url):
        """
        @brief Configura y levanta el subproceso independiente de Chromium optimizado para sistemas integrados.
        @details Cierra de forma preventiva instancias zombis concurrentes y parametriza un array masivo de flags 
        de aceleración de hardware, omisión de diálogos de error por cuelgues (`--noerrdialogs`) y perfiles de color 
        estables para mitigar la fatiga gráfica en pantallas de Raspberry Pi.
        
        @param url Dirección web absoluta que cargará el navegador en su arranque inicial.
        """
        self._kill_all()
        logger.info(f"[BROWSER] Lanzando Chromium: {url}")

        cmd = [
            "chromium",
            "--start-maximized",
            "--disable-infobars",
            "--noerrdialogs",
            "--disable-translate",
            "--disable-features=TranslateUI,WebContentsForceDark",
            "--disable-session-crashed-bubble",
            "--disable-restore-session-state",
            "--password-store=basic",
            "--use-mock-keychain",
            "--disable-sync",
            "--no-first-run",
            "--no-default-browser-check",
            "--force-color-profile=srgb",
            url,
        ]

        try:
            self._chromium = subprocess.Popen(cmd)
        except FileNotFoundError:
            try:
                # Intento de resolución adaptativa para sistemas operativos con nombres alternativos de binario
                cmd[0] = "chromium-browser"
                self._chromium = subprocess.Popen(cmd)
            except FileNotFoundError:
                logger.error("[BROWSER] Binario de Chromium no localizado en las rutas del sistema operativo.")
                return

        # Retraso controlado de 3 segundos para posibilitar la renderización de la ventana de Chromium antes de inyectar el teclado
        QTimer.singleShot(3000, self._launch_wvkbd)

    def _launch_wvkbd(self):
        """
        @brief Despliega el teclado virtual en pantalla compatible con Wayland/X11 `wvkbd-mobintl`.
        @details Inyecta explícitamente el descriptor del display primario (`DISPLAY: ":0"`) en el 
        entorno de ejecución para asegurar la correcta superposición geométrica del teclado.
        """
        try:
            self._wvkbd = subprocess.Popen(
                ["wvkbd-mobintl", "-L", "300", "--fn", "Sans 22"],
                env={**os.environ, "DISPLAY": ":0"}
            )
            logger.info("[BROWSER] wvkbd lanzado con éxito.")
        except FileNotFoundError:
            logger.error("[BROWSER] Teclado wvkbd no instalado en el sistema operativo.")

    def _kill_all(self):
        """
        @brief Detiene y purga de forma atómica todos los procesos e instancias zombis del navegador y teclados auxiliares.
        @details Emplea una política de terminación gradual benigna (`terminate`), escalando a interrupción 
        forzada de kernel (`kill`) si el proceso bloquea los descriptores de archivos tras una ventana de 2 segundos.
        """
        if self._wvkbd:
            try:
                self._wvkbd.terminate()
                self._wvkbd.wait(timeout=2)
            except Exception:
                pass
            self._wvkbd = None
            
        try:
            subprocess.run(["pkill", "-f", "wvkbd"], check=False)
        except Exception:
            pass
            
        if self._chromium:
            try:
                self._chromium.terminate()
                self._chromium.wait(timeout=2)
            except Exception:
                try:
                    self._chromium.kill()
                except Exception:
                    pass
            self._chromium = None
            logger.info("[BROWSER] Instancia activa de Chromium purgada de memoria.")

    # ── Sobrescritura de Eventos Nativos PyQt5 ─────────────────────────────────

    def showEvent(self, event):
        """
        @brief Intercepta el evento de visualización del Widget principal.
        
        @param event Objeto del evento nativo de tipo QShowEvent.
        """
        super().showEvent(event)
        if not self._chromium:
            QTimer.singleShot(100, self._show_initial_keyboard)

    def hideEvent(self, event):
        """
        @brief Intercepta la ocultación de la pantalla para desactivar y liberar recursos.
        
        @param event Objeto del evento nativo de tipo QHideEvent.
        """
        self._kill_all()
        self.initial_keyboard.detach()
        super().hideEvent(event)

    def closeEvent(self, event):
        """
        @brief Asegura la limpieza total de subprocesos cuando el widget es destruido de forma explícita.
        
        @param event Objeto del evento nativo de tipo QCloseEvent.
        """
        self._kill_all()
        super().closeEvent(event)

    # ── Rutina de Retorno al Launcher ─────────────────────────────────────────

    def go_back_to_launcher(self):
        """
        @brief Cierra de forma ordenada los componentes del navegador y cede el foco al menú principal (Launcher).
        """
        self._kill_all()
        self.initial_keyboard.detach()
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()