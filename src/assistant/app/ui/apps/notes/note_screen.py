# app/ui/apps/notes/notes_screen.py

"""
@file notes_screen.py
@brief Pantalla de gestión de notas optimizada para accesibilidad cognitiva mediante PyQt5.
@details Diseñada con una paleta de alto contraste basada en tonos turquesas y pastel.
Implementa un teclado táctil embebido dinámico que modifica las dimensiones del viewport
al recibir el foco para garantizar la visibilidad de los campos de entrada de texto.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from app.ui.apps.notes.note_store import NotesStore
from app.ui.widgets.keyboard_widget import KeyboardWidget
from app.core.logger import logger

## Hoja de estilos QSS modularizada con colores pastel de alto contraste y esquinas suavizadas hiper-legibles.
STYLE = """
QWidget {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.0 #f0fffe,
        stop:0.5 #d8f8f4,
        stop:1.0 #bff2ec
    );
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QScrollBar:vertical {
    width: 60px;              /*  más gruesa */
    background: rgba(255,255,255,0.3);
    border-radius: 14px;
    margin: 6px 4px 6px 4px;
}

QScrollBar::handle:vertical {
    background: #40c8b8;
    border-radius: 14px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #20a898;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;   /* elimina flechitas */
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}


QLabel#title {
    font-size: 42px;
    font-weight: 900;
    color: #003d36;
    background: #80e0d4;
    border: 3px solid #30b0a0;
    border-radius: 24px;
    padding: 14px 40px;
}

QListWidget {
    background: rgba(255,255,255,0.82);
    border: 4px solid #40c8b8;
    border-radius: 28px;
    font-size: 30px;
    padding: 10px;
    outline: none;
}

QListWidget::item {
    background: #e8faf8;
    border: 2px solid #90ddd6;
    border-radius: 18px;
    padding: 20px 24px;
    margin: 8px 6px;
    color: #003830;
    font-weight: 600;
}

QListWidget::item:selected {
    background: #40c8b8;
    color: white;
    border-color: #20a898;
}

QLineEdit {
    background: rgba(255,255,255,0.88);
    border: 4px solid #40c8b8;
    border-radius: 30px;
    padding: 18px 30px;
    font-size: 30px;
    font-weight: 600;
    color: #003830;
    min-height: 66px;
    selection-background-color: #80e0d4;
}
QLineEdit:focus { border-color: #20a898; background: white; }

QLineEdit#search {
    border-color: #90ddd6;
    font-size: 28px;
    min-height: 62px;
    color: #206858;
}
QLineEdit#search:focus { border-color: #40c8b8; }

QPushButton#btn_add {
    background: #30b8a8;
    border: 4px solid #10988a;
    border-radius: 36px;
    padding: 20px 40px;
    font-size: 32px;
    font-weight: 900;
    color: white;
    min-height: 78px;
}
QPushButton#btn_add:hover   { background: #20a090; border-color: #087870; }
QPushButton#btn_add:pressed { background: #108878; padding-top: 24px; }

QPushButton#btn_delete {
    background: #bff2ec;
    border: 4px solid #60c8be;
    border-radius: 36px;
    padding: 18px 40px;
    font-size: 32px;
    font-weight: 900;
    color: #003d36;
    min-height: 78px;
}
QPushButton#btn_delete:hover   { background: #99e8e0; border-color: #30a898; }
QPushButton#btn_delete:pressed { background: #80d8d0; padding-top: 24px; }

QPushButton#btn_back {
    background: rgba(255,255,255,0.75);
    border: 4px solid #90ddd6;
    border-radius: 36px;
    padding: 16px 40px;
    font-size: 30px;
    font-weight: 900;
    color: #003d36;
    min-height: 72px;
}
QPushButton#btn_back:hover   { background: #e8faf8; border-color: #30b0a0; }
QPushButton#btn_back:pressed { background: #d0f0ec; padding-top: 20px; }
"""


class NotesScreen(QWidget):
    """
    @brief Interfaz gráfica interactiva para la creación, búsqueda y eliminación de notas.
    """

    def __init__(self, controller):
        """
        @brief Constructor de la pantalla de notas.
        @details Inicializa el gestor de almacenamiento e instala los componentes de la interfaz,
        incluyendo las redirecciones táctiles hacia el teclado virtual embebido.
        
        @param controller Instancia del enrutador central de la aplicación.
        """
        super().__init__()
        self.controller = controller
        self.store      = NotesStore()  ##< Componente de persistencia de datos local (JSON wrapper).
        logger.info("[NOTE] Inicializando pantalla de notas NotesScreen.")

        # Configuración inicial del Widget contenedor
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        # ── Layout raíz: Contenido interactivo arriba, teclado táctil abajo ──
        root = QVBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 36, 40, 20)
        content.setLayout(layout)

        # Barra Superior de Cabecera
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        title = QLabel("  Mis notas")
        title.setObjectName("title")

        self.btn_back = QPushButton(" Volver")
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setFixedWidth(240)
        self.btn_back.clicked.connect(self.go_back)

        top_row.addWidget(title, 1)
        top_row.addWidget(self.btn_back)

        # Barra de Búsqueda Dinámica
        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText(" Buscar notas...")
        self.search.textChanged.connect(self.refresh)
        self.search.mousePressEvent = lambda e: self._show_keyboard(self.search)

        # Lista Principal de Notas Guardadas
        self.list = QListWidget()
        self.list.setMinimumHeight(200)

        # Campos de Entrada para Nueva Nota
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("  Título de la nota")
        self.title_input.mousePressEvent = lambda e: self._show_keyboard(self.title_input)

        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText(" Escribe aquí tu nota...")
        self.content_input.mousePressEvent = lambda e: self._show_keyboard(self.content_input)

        # Botonera de Acciones Inferiores
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.btn_add = QPushButton(" Crear nota")
        self.btn_add.setObjectName("btn_add")
        self.btn_add.clicked.connect(self.add_note)

        self.btn_delete = QPushButton("️  Borrar nota")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.clicked.connect(self.delete_note)

        btn_row.addWidget(self.btn_add, 1)
        btn_row.addWidget(self.btn_delete, 1)

        # Ensamblado del Layout del Contenido Principal
        layout.addLayout(top_row)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.title_input)
        layout.addWidget(self.content_input)
        layout.addLayout(btn_row)

        # ── Teclado Embebido Inferior ────────────────────────────────────────
        self.keyboard = KeyboardWidget(self)
        self.keyboard.confirmed.connect(self._hide_keyboard)

        # Integración vertical sobre el layout raíz sin saltos de ventana
        root.addWidget(content, 1)
        root.addWidget(self.keyboard)

        # Carga inicial de elementos persistidos
        self.refresh()

    # =========================================================================
    # LÓGICA DE CONTROL DEL TECLADO EMBEDIDO
    # =========================================================================
    def _show_keyboard(self, target: QLineEdit):
        """
        @brief Acopla el teclado al campo de texto objetivo y reduce las dimensiones de la lista.
        @details **Criterio de Accesibilidad:** Reduce el tamaño máximo de la lista de elementos 
        para evitar que el teclado embebido desplace los campos activos fuera de la pantalla útil.
        
        @param target Widget QLineEdit que recibe el foco de edición actual.
        """
        self.keyboard.set_target(target)
        self.list.setMinimumHeight(60)
        self.list.setMaximumHeight(100)

    def _hide_keyboard(self):
        """
        @brief Desacopla el teclado virtual y restaura las dimensiones originales de la lista.
        """
        self.keyboard.detach()
        self.list.setMinimumHeight(200)
        self.list.setMaximumHeight(16777215)

    # =========================================================================
    # ACCIONES DE PERSISTENCIA Y ACTUALIZACIÓN (CRUD)
    # =========================================================================
    def refresh(self):
        """
        @brief Sincroniza la vista del componente QListWidget con el almacén local persistente.
        @details Filtra los registros en tiempo real basándose en el criterio del campo de búsqueda.
        Cada nota guarda una referencia oculta al diccionario original mediante `Qt.UserRole`.
        """
        self.list.clear()
        query = self.search.text()
        
        # Iteramos sobre el set de notas filtradas por el sub-motor de búsqueda
        for note in self.store.search(query):
            item = QListWidgetItem(f"  {note['title']}\n{note['content']}")
            # Almacenamos la referencia de la nota en el rol de usuario para desvincular el borrado del índice visual
            item.setData(Qt.UserRole, note)
            self.list.addItem(item)

    def add_note(self):
        """
        @brief Extrae los datos de los formularios y registra una nueva nota en el sistema.
        """
        title   = self.title_input.text().strip() or "Sin título"
        content = self.content_input.text().strip()
        
        self.store.add_note(title, content)
        self.title_input.clear()
        self.content_input.clear()
        
        self._hide_keyboard()
        self.refresh()
        logger.info("[NOTE] Nueva nota consolidada y guardada con éxito.")

    def delete_note(self):
        """
        @brief Elimina de forma definitiva la nota seleccionada bajo confirmación del usuario.
        @details **Corrección Lógica:** Utiliza la referencia `Qt.UserRole` para encontrar el elemento
        dentro de la lista global original, evitando corrupciones de borrado erróneo cuando la lista está filtrada.
        """
        current_item = self.list.currentItem()
        if not current_item:
            return

        reply = QMessageBox.question(
            self, "Borrar nota", "¿Eliminar esta nota de forma permanente?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            note_data = current_item.data(Qt.UserRole)
            if note_data in self.store.notes:
                self.store.notes.remove(note_data)
                self.store.save_all()
                self.refresh()
                logger.info("[NOTE] Nota eliminada del almacenamiento local.")

    # =========================================================================
    # EVENTOS DE NAVEGACIÓN Y CICLO DE VIDA
    # =========================================================================
    def hideEvent(self, event):
        """
        @brief Intercepta el evento de ocultación de la pantalla para replegar el teclado.
        
        @param event Instancia del evento nativo de tipo QHideEvent.
        """
        self._hide_keyboard()
        super().hideEvent(event)

    def go_back(self):
        """
        @brief Solicita al enrutador central el retorno seguro hacia el Launcher principal de Qt.
        """
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()
