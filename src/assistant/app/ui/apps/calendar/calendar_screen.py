# app/ui/apps/calendar/calendar_screen.py

"""
@file calendar_screen.py
@brief Interfaz gráfica de agenda y calendario táctil optimizada para pantallas integradas.
@details Diseña un entorno visual basado en layouts asimétricos (Izquierda: QCalendarWidget, 
Derecha: QListWidget + Entradas) bajo una estética coral/terracota pastel. Administra un canal de 
comunicación directa con `CalendarStore` e integra controles de escalado dinámico para ocultar o 
mostrar un teclado virtual PyQt5 embebido sin truncar los componentes de texto.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QCalendarWidget, QListWidget,
    QPushButton, QLineEdit, QLabel,
    QMessageBox, QListWidgetItem,
    QTableView
)
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QBrush
from PyQt5.QtCore import Qt, QDate

from app.ui.apps.calendar.calendar_store import CalendarStore
from app.ui.widgets.keyboard_widget import KeyboardWidget
from app.core.logger import logger


## Hoja de estilos QSS global que unifica la paleta de colores terracota pastel, radios de borde y estados táctiles.
STYLE = """
QWidget {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.0 #fff5f0,
        stop:0.5 #ffe4d8,
        stop:1.0 #ffd0bc
    );
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QLabel#header {
    font-size: 40px;
    font-weight: 900;
    color: #5a1200;
    background: rgba(255,255,255,0.75);
    border: 3px solid #f0a090;
    border-radius: 24px;
    padding: 10px 32px;
}

QLabel#panel_title {
    font-size: 32px;
    font-weight: 900;
    color: #5a1200;
    background: #f0a090;
    border: 3px solid #e06850;
    border-radius: 20px;
    padding: 12px 28px;
}

QCalendarWidget {
    background: rgba(255,255,255,0.85);
    border: 4px solid #e8806a;
    border-radius: 28px;
    font-size: 24px;
}

QCalendarWidget QToolButton {
    background: #f0a090;
    border: none;
    border-radius: 12px;
    padding: 8px 14px;
    font-size: 22px;
    font-weight: 800;
    color: #5a1200;
    margin: 4px;
}

QCalendarWidget QToolButton:hover {
    background: #e8806a;
    color: white;
}

QCalendarWidget QAbstractItemView {
    selection-background-color: #e8806a;
    selection-color: white;
    gridline-color: #ffd0bc;
    font-size: 22px;
    color: #3a0a00;
}

QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #ffe4d8;
    border-radius: 16px;
    padding: 4px;
}

QListWidget {
    background: rgba(255,255,255,0.82);
    border: 4px solid #e8806a;
    border-radius: 24px;
    font-size: 28px;
    padding: 8px;
    outline: none;
}

QListWidget::item {
    background: #fff5f0;
    border: 2px solid #f0a090;
    border-radius: 16px;
    padding: 16px 20px;
    margin: 6px 4px;
    color: #5a1200;
    font-weight: 600;
}

QListWidget::item:selected {
    background: #e8806a;
    color: white;
    border-color: #c05030;
}

QLineEdit {
    background: rgba(255,255,255,0.88);
    border: 4px solid #e8806a;
    border-radius: 28px;
    padding: 16px 28px;
    font-size: 30px;
    font-weight: 600;
    color: #3a0a00;
    min-height: 62px;
    selection-background-color: #f0a090;
}
QLineEdit:focus { border-color: #c05030; background: white; }

QPushButton#btn_prev, QPushButton#btn_next {
    background: #f0a090;
    border: 3px solid #e06850;
    border-radius: 28px;
    font-size: 32px;
    font-weight: 900;
    color: #5a1200;
    min-width: 70px;
    min-height: 60px;
}
QPushButton#btn_prev:hover, QPushButton#btn_next:hover { background: #e8806a; color: white; }
QPushButton#btn_prev:pressed, QPushButton#btn_next:pressed { background: #c05030; padding-top: 14px; }

QPushButton#btn_add {
    background: #e8806a;
    border: 4px solid #c05030;
    border-radius: 32px;
    padding: 18px 36px;
    font-size: 30px;
    font-weight: 900;
    color: white;
    min-height: 72px;
}
QPushButton#btn_add:hover   { background: #d86848; border-color: #a03820; }
QPushButton#btn_add:pressed { background: #c05030; padding-top: 22px; }

QPushButton#btn_delete {
    background: #ffd0bc;
    border: 4px solid #e09880;
    border-radius: 32px;
    padding: 18px 36px;
    font-size: 30px;
    font-weight: 900;
    color: #5a1200;
    min-height: 72px;
}
QPushButton#btn_delete:hover   { background: #f0b8a0; border-color: #c07860; }
QPushButton#btn_delete:pressed { background: #e0a080; padding-top: 22px; }

QPushButton#btn_back {
    background: rgba(255,255,255,0.75);
    border: 4px solid #f0a090;
    border-radius: 32px;
    padding: 16px 36px;
    font-size: 28px;
    font-weight: 900;
    color: #5a1200;
    min-height: 68px;
}
QPushButton#btn_back:hover   { background: #fff5f0; border-color: #e06850; }
QPushButton#btn_back:pressed { background: #ffe4d8; padding-top: 20px; }
"""


class CalendarScreen(QWidget):
    """
    @brief Componento de pantalla unificado para la visualización de la agenda táctil del robot.
    """

    def __init__(self, controller):
        """
        @brief Constructor de la pantalla CalendarScreen.
        @details Instancia el motor de almacenamiento de eventos local, modela los layouts relacionales 
        e inicializa las propiedades de los componentes gráficos del calendario y lista de recordatorios.
        
        @param controller Instancia del orquestador central que gestiona las transiciones de pantalla en la interfaz.
        """
        super().__init__()
        
        ## Referencia al controlador de UI general de la aplicación.
        self.controller   = controller
        
        ## Gestor binario/JSON encargado del almacenamiento e indexación física de las tareas en disco.
        self.store        = CalendarStore()
        
        ## Instancia de control de tiempo que almacena de forma activa el día seleccionado por el usuario.
        self.current_date = QDate.currentDate()
        logger.info("[CALENDAR] Iniciando ventana de Calendario")

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        # ── Layout raíz: Contenedor vertical principal ───────────────────────
        root = QVBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        # Contenedor de contenido superior
        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        main = QHBoxLayout()
        main.setSpacing(28)
        main.setContentsMargins(32, 32, 32, 32)
        content.setLayout(main)

        # ── Bloque Izquierdo: Calendario de visualización y navegación ───────
        left = QVBoxLayout()
        left.setSpacing(18)

        nav = QHBoxLayout()
        nav.setSpacing(14)

        self.btn_prev = QPushButton("◀")
        self.btn_prev.setObjectName("btn_prev")
        self.btn_prev.clicked.connect(self.prev_month)

        self.header = QLabel()
        self.header.setObjectName("header")
        self.header.setAlignment(Qt.AlignCenter)

        self.btn_next = QPushButton("▶")
        self.btn_next.setObjectName("btn_next")
        self.btn_next.clicked.connect(self.next_month)

        nav.addWidget(self.btn_prev)
        nav.addWidget(self.header, 1)
        nav.addWidget(self.btn_next)

        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setMinimumHeight(420)
        self.calendar.clicked.connect(self.date_changed)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        
        # Sobrescritura de estilos inline complementaria para customizar sub-paneles del widget Qt nativo
        self.calendar.setStyleSheet("""
QCalendarWidget {
    background-color: #f7f3ff;
}
QCalendarWidget QHeaderView::section {
    background-color: #efe3ff;
    color: #4b2a6b;
    font-size: 22px;
    font-weight: bold;
    padding: 8px;
    border: none;
}
QCalendarWidget QTableView {
    background-color: #f7f3ff;
    gridline-color: orange;
    selection-background-color: #c8a0f0;
    selection-color: #2b1b3f;
    font-size: 34px;
    font-weight: bold;
}
QCalendarWidget QTableView::item {
    padding: 6px;
    font-size: 20px;
    font-weight: bold;
    color: #2b1b3f;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: transparent;
}
QCalendarWidget QToolButton {
    border: none;
    background: transparent;
}
QCalendarWidget QAbstractItemView {
    outline: 0;
}
""")

        left.addLayout(nav)
        left.addWidget(self.calendar)

        # ── Bloque Derecho: Gestión de eventos de la fecha e inputs ──────────
        right = QVBoxLayout()
        right.setSpacing(16)

        self.panel_title = QLabel(" Eventos del día")
        self.panel_title.setObjectName("panel_title")
        self.panel_title.setAlignment(Qt.AlignCenter)

        self.list = QListWidget()
        self.list.setMinimumHeight(300)

        self.input = QLineEdit()
        self.input.setPlaceholderText("️  Nuevo evento...")
        self.input.mousePressEvent = lambda e: self._show_keyboard(self.input)

        self.btn_add = QPushButton("➕  Añadir evento")
        self.btn_add.setObjectName("btn_add")
        self.btn_add.clicked.connect(self.add_event)

        self.btn_delete = QPushButton("  Eliminar evento")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.clicked.connect(self.delete_event)

        self.btn_back = QPushButton("⬅  Volver al inicio")
        self.btn_back.setObjectName("btn_back")
        self.btn_back.clicked.connect(self.go_back)

        right.addWidget(self.panel_title)
        right.addWidget(self.list, 1)
        right.addWidget(self.input)
        right.addWidget(self.btn_add)
        right.addWidget(self.btn_delete)
        right.addWidget(self.btn_back)

        # Distribución proporcional de pesos en el espacio horizontal (60% izquierda - 40% derecha)
        main.addLayout(left, 3)
        main.addLayout(right, 2)

        # ── Teclado Virtual Embebido ─────────────────────────────────────────
        self.keyboard = KeyboardWidget(self)
        self.keyboard.confirmed.connect(self._hide_keyboard)

        root.addWidget(content, 1)
        root.addWidget(self.keyboard)

        # Inicialización de textos y renderizado de la cuadrícula
        self.update_header()
        self.refresh()

    # ── Rutinas de Control del Teclado Táctil ─────────────────────────────────

    def _show_keyboard(self, target: QLineEdit):
        """
        @brief Despliega el teclado táctil en pantalla y encoge proporcionalmente la lista de eventos.
        @details Modifica dinámicamente los límites de altura de `QListWidget` para posibilitar la 
        completitud visual del teclado en resoluciones limitadas de Raspberry Pi sin ocultar los campos de entrada.
        
        @param target Puntero al control de texto `QLineEdit` que recibirá los caracteres inyectados.
        """
        self.keyboard.set_target(target)
        self.list.setMinimumHeight(60)
        self.list.setMaximumHeight(100)

    def _hide_keyboard(self):
        """
        @brief Oculta de la interfaz el teclado virtual y restaura las dimensiones originales de la lista de eventos.
        """
        self.keyboard.detach()
        self.list.setMinimumHeight(300)
        self.list.setMaximumHeight(16777215)

    # ── Orquestación de Navegación Temporal ────────────────────────────────────

    def update_header(self):
        """
        @brief Sincroniza el texto del encabezado principal con el mes y año bajo visualización.
        """
        self.header.setText(self.current_date.toString("MMMM yyyy").capitalize())
        self.calendar.setCurrentPage(self.current_date.year(), self.current_date.month())

    def prev_month(self):
        """
        @brief Retrocede una página en el calendario correspondiente a un mes atrás de la fecha actual.
        """
        self.current_date = self.current_date.addMonths(-1)
        self.update_header()

    def next_month(self):
        """
        @brief Avanza una página en el calendario correspondiente a un mes adelante de la fecha actual.
        """
        self.current_date = self.current_date.addMonths(1)
        self.update_header()

    def date_changed(self, date):
        """
        @brief Slot asíncrono que se dispara cuando el usuario presiona un día en la cuadrícula.
        
        @param date Instancia de objeto `QDate` del día pulsado.
        """
        self.current_date = date
        self.update_header()
        self.refresh()

    # ── Gestión del Historial de Tareas y Marcadores ──────────────────────────

    def refresh(self):
        """
        @brief Sincroniza la lista visual de tareas y repinta los días destacados.
        @details Limpia la instancia de `QListWidget`, consulta las cadenas correspondientes en 
        el `CalendarStore`, inyecta los nuevos registros físicos y actualiza las marcas estéticas del calendario.
        """
        self.list.clear()
        date_str = self.current_date.toString("yyyy-MM-dd")
        for e in self.store.get_events(date_str):
            self.list.addItem(QListWidgetItem(f"  {e['title']}"))
        self.panel_title.setText(f"  {self.current_date.toString('d MMMM yyyy')}")
        self.mark_events_on_calendar()

    def add_event(self):
        """
        @brief Da de alta un nuevo evento en el día en curso.
        @details Sanea la cadena ingresada por el usuario. Si contiene caracteres válidos, confirma el registro 
        en la persistencia del Store, oculta el teclado virtual táctil y refresca la vista.
        """
        text = self.input.text().strip()
        if not text:
            return
        self.store.add_event(self.current_date.toString("yyyy-MM-dd"), text)
        self.input.clear()
        self._hide_keyboard()
        self.refresh()
        logger.info("[CALENDAR] Evento añadido")

    def delete_event(self):
        """
        @brief Remueve el evento seleccionado de la agenda bajo confirmación de diálogo.
        @details Recupera el índice de fila activo en el widget gráfico. Si existe una selección válida, 
        despliega un cuadro modal de advertencia (`QMessageBox`). Tras la aprobación, sincroniza el borrado 
        con el Store utilizando un contador de offset.
        """
        row = self.list.currentRow()
        if row < 0:
            return
        date_str = self.current_date.toString("yyyy-MM-dd")
        reply = QMessageBox.question(self, "Eliminar evento", "¿Borrar este evento?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            count = 0
            for i, e in enumerate(self.store.events):
                if e["date"] == date_str:
                    if count == row:
                        self.store.delete_event(i)
                        break
                    count += 1
            self.refresh()
            logger.info("[CALENDAR] Evento eliminado")

    def mark_events_on_calendar(self):
        """
        @brief Resalta visualmente las casillas del calendario que contienen recordatorios agendados.
        @details Genera un pincel y formato de celda personalizado (`QTextCharFormat`) con fondo coral 
        y texto blanco, barriendo el listado global para estampar el formato en las celdas del mes actual.
        """
        fmt = QTextCharFormat()
        fmt.setBackground(QBrush(QColor("#e8806a")))
        fmt.setForeground(QBrush(QColor("#ffffff")))
        for e in self.store.events:
            self.calendar.setDateTextFormat(QDate.fromString(e["date"], "yyyy-MM-dd"), fmt)

    def hideEvent(self, event):
        """
        @brief Intercepta la ocultación de la ventana para replegar el teclado de forma segura.
        
        @param event Objeto del evento nativo de tipo QHideEvent.
        """
        self._hide_keyboard()
        super().hideEvent(event)

    def go_back(self):
        """
        @brief Cierra el módulo de agenda actual regresando la interfaz al menú principal (Launcher).
        """
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()