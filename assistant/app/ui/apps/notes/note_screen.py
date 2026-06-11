# app/ui/apps/notes/notes_screen.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PyQt5.QtCore import Qt
from app.ui.apps.notes.note_store import NotesStore
from app.core.logger import logger


# ── NOTAS — Verde menta / turquesa pastel ────────────────────────────────────
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

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.store      = NotesStore()
        logger.info("[NOTE] Iniciada de ventana Notes")

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 36, 40, 36)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        title = QLabel("  Mis notas")
        title.setObjectName("title")

        self.btn_back = QPushButton("⬅  Volver")
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setFixedWidth(240)
        self.btn_back.clicked.connect(self.go_back)

        top_row.addWidget(title, 1)
        top_row.addWidget(self.btn_back)

        self.search = QLineEdit()
        self.search.setObjectName("search")
        self.search.setPlaceholderText(" Buscar notas...")
        self.search.textChanged.connect(self.refresh)

        self.list = QListWidget()
        self.list.setMinimumHeight(420)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("  Título de la nota")

        self.content_input = QLineEdit()
        self.content_input.setPlaceholderText("✏️  Escribe aquí tu nota...")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.btn_add = QPushButton("➕  Crear nota")
        self.btn_add.setObjectName("btn_add")
        self.btn_add.clicked.connect(self.add_note)

        self.btn_delete = QPushButton("️  Borrar nota")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.clicked.connect(self.delete_note)

        btn_row.addWidget(self.btn_add, 1)
        btn_row.addWidget(self.btn_delete, 1)

        layout.addLayout(top_row)
        layout.addWidget(self.search)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.title_input)
        layout.addWidget(self.content_input)
        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        self.list.clear()
        for note in self.store.search(self.search.text()):
            self.list.addItem(QListWidgetItem(f"  {note['title']}\n{note['content']}"))

    def add_note(self):
        title   = self.title_input.text().strip() or "Sin título"
        content = self.content_input.text().strip()
        self.store.add_note(title, content)
        self.title_input.clear()
        self.content_input.clear()
        self.refresh()
        logger.info("[NOTE] Nota añadido")


    def delete_note(self):
        row = self.list.currentRow()
        if row < 0:
            return
        reply = QMessageBox.question(self, "Borrar nota", "¿Eliminar esta nota?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.store.notes[row]
            self.store.save_all()
            self.refresh()
            
            
        logger.info("[CALENDAR] Nota eliminada")


    def go_back(self):
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()
