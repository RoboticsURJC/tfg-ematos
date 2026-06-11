# app/ui/screens/launcher_screen.py

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout,
    QToolButton, QSizePolicy, QScrollArea,
    QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QTime
from PyQt5.QtGui import QIcon, QFont
from app.core.logger import logger


# ── LAUNCHER — Crema / melocotón cálido (neutro con todos los colores de apps)
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
QScrollArea > QWidget {
    background: transparent;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollBar:vertical {
    width: 8px;
    background: transparent;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: rgba(200, 160, 100, 0.35);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class LauncherScreen(QWidget):

    open_app = pyqtSignal(str)

    def __init__(self, controller):
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
        header_layout.setSpacing(6)

        self.title = QLabel("  Bienvenid@")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 42, QFont.Black))
        self.title.setStyleSheet("color: #5a3300; background: transparent; border: none;")

        self.subtitle = QLabel("¿Qué quieres hacer hoy?")
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setFont(QFont("Segoe UI", 22))
        self.subtitle.setStyleSheet("color: #a06020; background: transparent; border: none;")

        header_layout.addWidget(self.title)
        header_layout.addWidget(self.subtitle)
        
        
        # ~ Reloj 
        
        self.clock = QLabel("00:00:00")
        self.clock.setAlignment(Qt.AlignCenter)
        self.clock.setFont(QFont("Segoe UI", 40, QFont.Bold))
        self.clock.setStyleSheet("""
            color: #7a3d00;
            background: transparent;
            border: none;
        
        """)
        
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

        icon_path_base = "/home/elisa/tfg-ematos/assistant/app/assets/icons/"

        apps = [
            {"label": "Calendario", "id": "calendar", "icon": "calendar_icon_192645.png",
             "bg": "#fef3d0", "border": "#e8b830", "color": "#5a3300"},
            {"label": "Internet",   "id": "browser",  "icon": "apps_web_browser_15742.png",
             "bg": "#ddf0ff", "border": "#60a8e8", "color": "#002860"},
            {"label": "Juegos",     "id": "games",    "icon": "games.png",
             "bg": "#ffe0ea", "border": "#e870a0", "color": "#600030"},
            {"label": "Notas",      "id": "notes",    "icon": "32officeicons-7_89710.png",
             "bg": "#d8f8e8", "border": "#40b870", "color": "#003820"},
            {"label": "Ajustes",    "id": "settings", "icon": "programs_97512.png",
             "bg": "#f0e8d8", "border": "#c09060", "color": "#3a2000"},
            {"label": "Recordatorios",    "id": "reminder", "icon": "reminder.png",
             "bg": "#ede3ff", "border": "#8b6be8", "color": "#2f145f"},
            {"label": "Calculadora",    "id": "calculator", "icon": "calculator.png",
             "bg": "#d8f0ee", "border": "#62d6b9", "color": "#003a3a"}    
              
            
        ]

        for i, app in enumerate(apps):
            btn = QToolButton()
            btn.setIcon(QIcon(icon_path_base + app["icon"]))
            btn.setIconSize(QSize(200, 200))
            btn.setText(app["label"])
            btn.setFont(QFont("Segoe UI", 60, QFont.Black))
            btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            btn.setMinimumSize(290, 320)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {app['bg']};
                    border: 3px solid {app['border']};
                    border-radius: 40px;
                    color: {app['color']};
                    padding: 18px 12px 22px 12px;
                    font-size: 26px;
                    font-weight: 900;
                    font-family: "Segoe UI", "Ubuntu", sans-serif;
                }}
                QToolButton:hover {{
                    background-color: white;
                    border-color: {app['border']};
                }}
                QToolButton:pressed {{
                    background-color: {app['bg']};
                    padding-top: 24px;
                }}
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

        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    # ============================================================
    # USER
    # ============================================================
    def set_user(self, user):
        self.title.setText(f"  Hola =), {user}")
        self.user_label.setText(f"Usuario: {user}")

    # ============================================================
    # RELOJ
    # ============================================================
    def update_clock(self):
        now = QTime.currentTime().toString("HH:mm:ss")
        
        self.clock.setText(now)

    # ============================================================
    # ACTIONS
    # ============================================================
    def launch_app(self, app_id: str):
        logger.info(f"Lanzando app: {app_id}")
        self.open_app.emit(app_id)
        if hasattr(self.controller, "open_app"):
            self.controller.open_app(app_id)

    def logout(self):
        logger.info("Cambio / cierre de usuario")
        if hasattr(self.controller, "logout"):
            self.controller.logout()
