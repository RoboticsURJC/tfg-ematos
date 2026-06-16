# app/ui/screens/launcher_screen.py

"""
@file launcher_screen.py
@brief Lanzador principal (Launcher) del sistema.
@details Interfaz central que permite la navegación entre aplicaciones, control 
rápido de hardware (volumen, energía) y visualización de información del usuario.
"""

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout,
    QToolButton, QSizePolicy, QScrollArea,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QTime, QByteArray
from PyQt5.QtGui import QIcon, QFont, QPixmap
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QApplication
import subprocess
from app.core.logger import logger


_LAUNCHER_QSS = """
QWidget#LauncherMain {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0.00 #fdf6ee,
        stop: 0.50 #fbeede,
        stop: 1.00 #fdf0d8
    );
    font-family: "Segoe UI", "Nunito", "Helvetica Neue", sans-serif;
}
QScrollArea {
    border: none;
    background: transparent;
}
QScrollArea > QWidget { background: transparent; }
QScrollArea > QWidget > QWidget { background: transparent; }
QScrollBar:vertical {
    width: 28px;
    background: rgba(200, 160, 100, 0.15);
    border-radius: 14px;
    margin: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(200, 140, 60, 0.55);
    border-radius: 12px;
    min-height: 80px;
}
QScrollBar::handle:vertical:pressed {
    background: rgba(160, 100, 20, 0.75);
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0px; }
"""


def _svg_icon(svg_bytes, size=72):
    from PyQt5.QtSvg import QSvgRenderer
    from PyQt5.QtGui import QPixmap, QPainter
    from PyQt5.QtCore import QByteArray
    from PyQt5.QtGui import QIcon
    from PyQt5.QtCore import Qt
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


_SVG_VOL_DOWN = b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <polygon points='20,20 34,12 34,52 20,44' fill='#5a3300'/>
  <line x1='38' y1='22' x2='38' y2='42' stroke='#5a3300' stroke-width='4' stroke-linecap='round'/>
  <line x1='44' y1='18' x2='44' y2='46' stroke='#5a3300' stroke-width='4' stroke-linecap='round'/>
  <line x1='50' y1='42' x2='58' y2='50' stroke='#c0392b' stroke-width='5' stroke-linecap='round'/>
  <line x1='50' y1='50' x2='58' y2='42' stroke='#c0392b' stroke-width='5' stroke-linecap='round'/>
</svg>"""

_SVG_VOL_UP = b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <polygon points='20,20 34,12 34,52 20,44' fill='#14532d'/>
  <line x1='38' y1='22' x2='38' y2='42' stroke='#14532d' stroke-width='4' stroke-linecap='round'/>
  <line x1='44' y1='18' x2='44' y2='46' stroke='#14532d' stroke-width='4' stroke-linecap='round'/>
  <line x1='50' y1='14' x2='50' y2='46' stroke='#14532d' stroke-width='4' stroke-linecap='round'/>
  <line x1='42' y1='22' x2='50' y2='14' stroke='#14532d' stroke-width='5' stroke-linecap='round'/>
  <line x1='58' y1='22' x2='50' y2='14' stroke='#14532d' stroke-width='5' stroke-linecap='round'/>
</svg>"""

_SVG_POWER = b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>
  <path d='M32 10 L32 32' stroke='#6b0018' stroke-width='7' stroke-linecap='round'/>
  <path d='M20 18 A16 16 0 1 0 44 18' fill='none' stroke='#6b0018' stroke-width='7' stroke-linecap='round'/>
</svg>"""


class LauncherScreen(QWidget):
    
    """
    @brief Pantalla principal de inicio.
    @details Organiza los accesos directos a las apps mediante un GridView táctil
    y proporciona controles globales de sistema en la cabecera.
    """
    
    ## Señal emitida al seleccionar una aplicación para su ejecución
    open_app = pyqtSignal(str)

    def __init__(self, controller):
        
        """
        @brief Inicializa el launcher y configura el entorno visual.
        @param controller Controlador que gestiona la lógica de navegación y apps.
        """
        
        super().__init__()
        self.controller = controller
        logger.info("[LAUNCHER] Iniciando Launcher Screen")

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("LauncherMain")
        self.setStyleSheet(_LAUNCHER_QSS)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(22)
        main_layout.setContentsMargins(40, 30, 40, 30)

        # ============================================================
        # HEADER
        # ============================================================
        header = QWidget()
        header.setAttribute(Qt.WA_StyledBackground, True)
        header.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.82);
                border-radius: 30px;
                border: 2px solid #f0c878;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 18, 28, 18)
        header_layout.setSpacing(8)

        # ── Fila superior: título + controles rápidos ──
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.title = QLabel("  Bienvenid@")
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.title.setFont(QFont("Segoe UI", 36, QFont.Black))
        self.title.setStyleSheet("color: #5a3300; background: transparent; border: none;")
        top_row.addWidget(self.title)

        top_row.addStretch()

        # ── Controles rápidos (volumen + apagar) ──
        quick = QWidget()
        quick.setStyleSheet("QWidget { background: transparent; border: none; }")
        quick_lay = QHBoxLayout(quick)
        quick_lay.setContentsMargins(0, 0, 0, 0)
        quick_lay.setSpacing(12)

        _big_btn = lambda bg, bg2: f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                border-radius: 24px;
                min-width: 100px;
                min-height: 100px;
                max-width: 110px;
                max-height: 110px;
                padding: 0;
            }}
            QPushButton:pressed {{ background-color: {bg2}; }}
        """

        self.btn_vol_down = QPushButton()
        self.btn_vol_down.setIcon(_svg_icon(_SVG_VOL_DOWN))
        self.btn_vol_down.setIconSize(QSize(72, 72))
        self.btn_vol_down.setStyleSheet(_big_btn("#fde68a", "#f0c840"))
        self.btn_vol_down.clicked.connect(lambda: self._quick_volume(-10))

        self.lbl_vol_quick = QLabel("—")
        self.lbl_vol_quick.setFont(QFont("Segoe UI", 26, QFont.Black))
        self.lbl_vol_quick.setStyleSheet("color: #5a3300; background: transparent; border: none; min-width: 80px;")
        self.lbl_vol_quick.setAlignment(Qt.AlignCenter)

        self.btn_vol_up = QPushButton()
        self.btn_vol_up.setIcon(_svg_icon(_SVG_VOL_UP))
        self.btn_vol_up.setIconSize(QSize(72, 72))
        self.btn_vol_up.setStyleSheet(_big_btn("#fde68a", "#f0c840"))
        self.btn_vol_up.clicked.connect(lambda: self._quick_volume(10))

        sep = QLabel()
        sep.setFixedWidth(3)
        sep.setStyleSheet("background: #d8c0a0; border-radius: 2px; min-height: 70px; border: none;")

        self.btn_quick_power = QPushButton()
        self.btn_quick_power.setIcon(_svg_icon(_SVG_POWER))
        self.btn_quick_power.setIconSize(QSize(72, 72))
        self.btn_quick_power.setStyleSheet(_big_btn("#fda4af", "#f97395"))
        self.btn_quick_power.clicked.connect(self._quick_poweroff)

        quick_lay.addWidget(self.btn_vol_down)
        quick_lay.addWidget(self.lbl_vol_quick)
        quick_lay.addWidget(self.btn_vol_up)
        quick_lay.addWidget(sep)
        quick_lay.addWidget(self.btn_quick_power)

        top_row.addWidget(quick)
        header_layout.addLayout(top_row)

        # ── Subtítulo ──
        self.subtitle = QLabel("¿Qué quieres hacer hoy?")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setFont(QFont("Segoe UI", 22))
        self.subtitle.setStyleSheet("color: #a06020; background: transparent; border: none;")
        header_layout.addWidget(self.subtitle)

        # ── Reloj ──
        self.clock = QLabel("00:00:00")
        self.clock.setAlignment(Qt.AlignCenter)
        self.clock.setFont(QFont("Segoe UI", 40, QFont.Bold))
        self.clock.setStyleSheet("color: #7a3d00; background: transparent; border: none;")
        header_layout.addWidget(self.clock)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        main_layout.addWidget(header)

        # ============================================================
        # BARRA DE USUARIO
        # ============================================================
        user_bar = QWidget()
        user_bar.setAttribute(Qt.WA_StyledBackground, True)
        user_bar.setStyleSheet("QWidget { background: transparent; }")
        user_layout = QHBoxLayout(user_bar)
        user_layout.setContentsMargins(4, 0, 4, 0)
        user_layout.setSpacing(14)

        self.user_label = QLabel("Usuario: -")
        self.user_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.user_label.setStyleSheet("color: #5a3300; background: transparent;")

        self.change_user_btn = QPushButton("Cambiar usuario")
        self.change_user_btn.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.change_user_btn.setStyleSheet("""
            QPushButton {
                background-color: #e8c060;
                color: #4a2800;
                border-radius: 14px;
                padding: 10px 22px;
                border: none;
            }
            QPushButton:hover   { background-color: #d8a840; }
            QPushButton:pressed { background-color: #c09030; padding-top: 14px; }
        """)
        self.change_user_btn.clicked.connect(self.logout)

        self.logout_btn = QPushButton("Cerrar sesión")
        self.logout_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e87060;
                color: white;
                border-radius: 14px;
                padding: 10px 22px;
                border: none;
            }
            QPushButton:hover   { background-color: #d05040; }
            QPushButton:pressed { background-color: #b83020; padding-top: 14px; }
        """)
        self.logout_btn.clicked.connect(self.logout)

        user_layout.addWidget(self.user_label)
        user_layout.addStretch()
        user_layout.addWidget(self.change_user_btn)
        user_layout.addWidget(self.logout_btn)
        main_layout.addWidget(user_bar)

        # ============================================================
        # GRID DE APPS
        # ============================================================
        grid = QGridLayout()
        grid.setSpacing(24)

        icon_path_base = "/home/elisa/tfg-ematos/src/assistant/app/assets/icons/"

        apps = [
            {"label": "Calendario",    "id": "calendar",   "icon": "calendar_icon_192645.png",
             "bg": "#fef3d0", "border": "#e8b830", "color": "#5a3300"},
            {"label": "Internet",      "id": "browser",    "icon": "apps_web_browser_15742.png",
             "bg": "#ddf0ff", "border": "#60a8e8", "color": "#002860"},
            {"label": "Juegos",        "id": "games",      "icon": "games.png",
             "bg": "#ffe0ea", "border": "#e870a0", "color": "#600030"},
            {"label": "Notas",         "id": "notes",      "icon": "32officeicons-7_89710.png",
             "bg": "#d8f8e8", "border": "#40b870", "color": "#003820"},
            {"label": "Ajustes",       "id": "settings",   "icon": "programs_97512.png",
             "bg": "#f0e8d8", "border": "#c09060", "color": "#3a2000"},
            {"label": "Recordatorios", "id": "reminder",   "icon": "reminder.png",
             "bg": "#ede3ff", "border": "#8b6be8", "color": "#2f145f"},
            {"label": "Calculadora",   "id": "calculator", "icon": "calculator.png",
             "bg": "#d8f0ee", "border": "#62d6b9", "color": "#003a3a"},
        ]

        for i, app in enumerate(apps):
            btn = QToolButton()
            btn.setIcon(QIcon(icon_path_base + app["icon"]))
            btn.setIconSize(QSize(90, 90))
            btn.setText(app["label"])
            btn.setFont(QFont("Segoe UI", 60, QFont.Black))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setMinimumSize(260, 260)
            btn.setMaximumSize(320, 320)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {app['bg']};
                    border: 4px solid {app['border']};
                    border-radius: 36px;
                    color: {app['color']};
                    padding: 8px 8px 8px 8px;
                    font-size: 36px;
                    font-weight: 900;
                    font-family: "Segoe UI", "Ubuntu", sans-serif;
                }}
                QToolButton:hover  {{ background-color: white; border-color: {app['border']}; }}
                QToolButton:pressed {{ background-color: {app['bg']}; padding-top: 12px; }}
            """)
            btn.clicked.connect(lambda _, a=app["id"]: self.launch_app(a))
            grid.addWidget(btn, i // 3, i % 3)

        container = QWidget()
        container.setLayout(grid)
        container.setAttribute(Qt.WA_StyledBackground, True)
        container.setStyleSheet("QWidget { background: transparent; }")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # Scrollbar grande para tacto con el dedo
        scroll.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                background: rgba(200, 160, 100, 0.18);
                width: 52px;
                border-radius: 26px;
                margin: 6px 4px 6px 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(180, 120, 40, 0.65);
                border-radius: 22px;
                min-height: 100px;
            }
            QScrollBar::handle:vertical:pressed {
                background: rgba(140, 80, 10, 0.9);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; border: none; }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical { background: none; }
        """)

        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        # Leer volumen inicial
        self._refresh_vol_label()

    # ============================================================
    # CONTROLES RÁPIDOS
    # ============================================================

    def _quick_volume(self, delta: int):
        """
        @brief Ajusta el volumen del sistema mediante comandos de shell.
        @param delta Incremento/decremento porcentual del volumen.
        """
        try:
            sign = "+" if delta > 0 else "-"
            subprocess.run(
                ["amixer", "set", "Master", f"{abs(delta)}%{sign}"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception as e:
            logger.error(f"[LAUNCHER] volumen: {e}")
        self._refresh_vol_label()

    def _refresh_vol_label(self):
        """@brief Sincroniza la etiqueta visual con el estado real del sistema."""
        try:
            out = subprocess.check_output(["amixer", "get", "Master"]).decode()
            if "[" in out and "%]" in out:
                val = int(out.split("[")[1].split("%]")[0])
                self.lbl_vol_quick.setText(f"{val}%")
                return
        except Exception:
            pass
        self.lbl_vol_quick.setText("—")

    def _quick_poweroff(self):
        """@brief Ejecuta un apagado seguro del equipo."""
        self.btn_quick_power.setText("…")
        self.btn_quick_power.setEnabled(False)
        logger.info("[LAUNCHER] Apagado rápido solicitado")
        try:
            subprocess.Popen(["sudo", "poweroff"])
        except Exception as e:
            logger.error(f"[LAUNCHER] poweroff: {e}")
            self.btn_quick_power.setIcon(_svg_icon(_SVG_POWER))
            self.btn_quick_power.setEnabled(True)

    # ============================================================
    # USER
    # ============================================================

    def set_user(self, user):
        self.title.setText(f"  Hola, {user} =)")
        self.user_label.setText(f"Usuario: {user}")

    # ============================================================
    # RELOJ
    # ============================================================

    def update_clock(self):
        """@brief Actualiza la hora mostrada en la interfaz."""
        self.clock.setText(QTime.currentTime().toString("HH:mm:ss"))

    # ============================================================
    # ACTIONS
    # ============================================================

    def launch_app(self, app_id: str):
        """
        @brief Notifica al controlador la apertura de una app específica.
        @param app_id Identificador único de la aplicación (ej: 'reminder').
        """
        logger.info(f"Lanzando app: {app_id}")
        self.open_app.emit(app_id)
        if hasattr(self.controller, "open_app"):
            self.controller.open_app(app_id)

    def logout(self):
        """@brief Vuelve a la ventana de login"""
        logger.info("Cambio / cierre de usuario")
        if hasattr(self.controller, "logout"):
            self.controller.logout()
