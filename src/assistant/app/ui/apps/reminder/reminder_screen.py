# app/ui/apps/reminders/reminder_screen.py
# app/ui/apps/reminders/reminder_screen.py

"""
@file reminder_screen.py
@brief Interfaz de usuario para la gestión de recordatorios.
@details Proporciona una interfaz basada en PyQt5 para visualizar, crear y 
eliminar recordatorios, integrando un teclado virtual y un selector de fecha/hora.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QMessageBox,
    QCalendarWidget, QSpinBox, QDialog,
    QDialogButtonBox, QFrame
)
from PyQt5.QtCore import Qt, QDate
from app.core.logger import logger
from app.ui.apps.reminder.reminder_store import ReminderStore
from app.ui.widgets.keyboard_widget import KeyboardWidget

# --- Estilos CSS ---
STYLE = """
QWidget {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.0 #f0f8ff,
        stop:0.5 #daeeff,
        stop:1.0 #c4e2ff
    );
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QLabel#title {
    font-size: 44px;
    font-weight: 900;
    color: #002a50;
    background: #7ec8f0;
    border: 3px solid #2a8abf;
    border-radius: 24px;
    padding: 14px 40px;
}

QScrollBar:vertical {
    width: 60px;              /*  más gruesa */
    background: rgba(255,255,255,0.3);
    border-radius: 14px;
    margin: 6px 4px 6px 4px;
}

QScrollBar::handle:vertical {
    background: #2a8abf;
    border-radius: 14px;
    min-height: 40px;
}

QScrollBar::handle:vertical:hover {
    background: #1a6a9f;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;   /* elimina flechitas */
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

QLabel#date_display {
    font-size: 28px;
    font-weight: 700;
    color: #002a50;
    background: rgba(255,255,255,0.82);
    border: 3px solid #4aaad8;
    border-radius: 20px;
    padding: 12px 24px;
}

QListWidget {
    background: rgba(255, 255, 255, 0.82);
    border: 4px solid #4aaad8;
    border-radius: 28px;
    font-size: 30px;
    padding: 10px;
    outline: none;
}

QListWidget::item {
    background: #f0f8ff;
    border: 2px solid #90ccee;
    border-radius: 18px;
    padding: 18px 22px;
    margin: 7px 5px;
    color: #002a50;
    font-weight: 600;
}

QListWidget::item:selected {
    background: #2a8abf;
    color: white;
    border-color: #1a6a9f;
}

QLineEdit {
    background: rgba(255, 255, 255, 0.88);
    border: 4px solid #4aaad8;
    border-radius: 30px;
    padding: 16px 28px;
    font-size: 30px;
    font-weight: 600;
    color: #002a50;
    min-height: 62px;
    selection-background-color: #7ec8f0;
}
QLineEdit:focus { border-color: #1a6a9f; background: white; }

QPushButton#btn_add {
    background-color: #2a8abf;
    border: 4px solid #1a6a9f;
    border-radius: 32px;
    padding: 18px 36px;
    font-size: 32px;
    font-weight: 900;
    color: white;
    min-height: 72px;
}
QPushButton#btn_add:hover   { background-color: #1a7aaf; border-color: #0a5a8f; }
QPushButton#btn_add:pressed { background-color: #1a6a9f; padding-top: 22px; }

QPushButton#btn_pick_date {
    background-color: #7ec8f0;
    border: 4px solid #2a8abf;
    border-radius: 28px;
    padding: 14px 28px;
    font-size: 28px;
    font-weight: 900;
    color: #002a50;
    min-height: 62px;
}
QPushButton#btn_pick_date:hover   { background-color: #5ab8e8; color: white; }
QPushButton#btn_pick_date:pressed { background-color: #2a8abf; color: white; padding-top: 18px; }

QPushButton#btn_delete {
    background-color: #c4e2ff;
    border: 4px solid #7ab8e0;
    border-radius: 32px;
    padding: 18px 36px;
    font-size: 32px;
    font-weight: 900;
    color: #002a50;
    min-height: 72px;
}
QPushButton#btn_delete:hover   { background-color: #a8d4f8; border-color: #4aaad8; }
QPushButton#btn_delete:pressed { background-color: #90c4f0; padding-top: 22px; }

QPushButton#btn_back {
    background-color: rgba(255, 255, 255, 0.75);
    border: 4px solid #90ccee;
    border-radius: 32px;
    padding: 16px 36px;
    font-size: 30px;
    font-weight: 900;
    color: #002a50;
    min-height: 68px;
}
QPushButton#btn_back:hover   { background-color: #f0f8ff; border-color: #2a8abf; }
QPushButton#btn_back:pressed { background-color: #daeeff; padding-top: 20px; }
"""

# ── Diálogo selector de fecha y hora ─────────────────────────────────────────
DATE_DIALOG_STYLE = """
QDialog {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0.0 #f0f8ff, stop:1.0 #c4e2ff
    );
    font-family: "Segoe UI", "Ubuntu", sans-serif;
}

QCalendarWidget {
    background: white;
    border: 3px solid #4aaad8;
    border-radius: 20px;
    font-size: 20px;
    min-width: 800px;
    min-height: 500px;
}
QCalendarWidget QToolButton {
    background: #7ec8f0;
    border: none;
    border-radius: 10px;
    padding: 6px 12px;
    font-size: 20px;
    font-weight: 800;
    color: #002a50;
    margin: 3px;
}
QCalendarWidget QToolButton:hover { background: #2a8abf; color: white; }
QCalendarWidget QAbstractItemView {
    background-color: white;
    selection-background-color: #2a8abf;
    selection-color: white;
    font-size: 20px;
    color: #002a50;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #daeeff;
    border-radius: 12px;
    padding: 4px;
}

QLabel#time_label {
    font-size: 26px;
    font-weight: 900;
    color: #002a50;
    background: transparent;
    padding: 8px 0;
}

QSpinBox {
    background: white;
    border: 3px solid #4aaad8;
    border-radius: 16px;
    padding: 10px 18px;
    font-size: 32px;
    font-weight: 900;
    color: #002a50;
    min-width: 90px;
    min-height: 56px;
}
QSpinBox:focus { border-color: #1a6a9f; }
QSpinBox::up-button, QSpinBox::down-button {
    width: 38px;
    border-radius: 8px;
    background: #7ec8f0;
    border: none;
    margin: 3px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #2a8abf; }
QSpinBox::up-arrow  { image: none; width: 0; }
QSpinBox::down-arrow { image: none; width: 0; }

QLabel#sep {
    font-size: 36px;
    font-weight: 900;
    color: #2a8abf;
    background: transparent;
    padding: 0 4px;
}

QDialogButtonBox QPushButton {
    background-color: #2a8abf;
    border: 3px solid #1a6a9f;
    border-radius: 20px;
    padding: 12px 32px;
    font-size: 26px;
    font-weight: 900;
    color: white;
    min-height: 52px;
    min-width: 140px;
}
QDialogButtonBox QPushButton:hover   { background-color: #1a7aaf; }
QDialogButtonBox QPushButton:pressed { background-color: #1a6a9f; padding-top: 16px; }
"""


class DateTimePickerDialog(QDialog):
    """
    @brief Diálogo modal para la selección precisa de fecha y hora.
    """
    
    def __init__(self, parent=None):
        
        """@brief Inicializa el calendario y los selectores de tiempo (spinboxes)."""
        
        super().__init__(parent)
        self.setWindowTitle("Elegir fecha y hora")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(DATE_DIALOG_STYLE)

        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(28, 28, 28, 28)

        # Calendario
        self.calendar = QCalendarWidget()        
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setGridVisible(True)
        layout.addWidget(self.calendar)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background: #90ccee; border: none; min-height: 2px; max-height: 2px;")
        layout.addWidget(line)

        # Selector de hora
        time_label = QLabel("  Hora del recordatorio")
        time_label.setObjectName("time_label")
        time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(time_label)

        time_row = QHBoxLayout()
        time_row.setSpacing(8)
        time_row.setAlignment(Qt.AlignCenter)

        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(9)
        self.hour_spin.setWrapping(True)
        self.hour_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        self.hour_spin.setAlignment(Qt.AlignCenter)

        sep = QLabel(":")
        sep.setObjectName("sep")
        sep.setAlignment(Qt.AlignCenter)

        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 59)
        self.min_spin.setValue(0)
        self.min_spin.setWrapping(True)
        self.min_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        self.min_spin.setAlignment(Qt.AlignCenter)
        self.min_spin.setSingleStep(5)

        time_row.addWidget(self.hour_spin)
        time_row.addWidget(sep)
        time_row.addWidget(self.min_spin)
        layout.addLayout(time_row)

        # Botones OK / Cancelar
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("  Confirmar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_datetime_str(self):
        """@brief Formatea la selección a 'YYYY-MM-DD HH:MM'."""
        date = self.calendar.selectedDate()
        h    = self.hour_spin.value()
        m    = self.min_spin.value()
        return f"{date.toString('yyyy-MM-dd')} {h:02d}:{m:02d}"


# ── Pantalla principal ────────────────────────────────────────────────────────
class ReminderScreen(QWidget):

    def __init__(self, controller):
        
        """
        @brief Inicializa la pantalla de recordatorios.
        @param controller Controlador principal que gestiona el flujo de UI y datos.
        """
        
        super().__init__()
        self.controller   = controller
        self.store        = controller.reminder_store
        self._selected_dt = None

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout()
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)
        self.setLayout(root)

        content = QWidget()
        content.setAttribute(Qt.WA_StyledBackground, True)
        
        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(40, 36, 40, 36)

        content.setLayout(layout)

        # Cabecera
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.title = QLabel(" Recordatorios")
        self.title.setObjectName("title")

        self.btn_back = QPushButton(" Volver")
        self.btn_back.setObjectName("btn_back")
        self.btn_back.setFixedWidth(220)
        self.btn_back.clicked.connect(self.go_back)

        top_row.addWidget(self.title, 1)
        top_row.addWidget(self.btn_back)

        # Lista
        self.list = QListWidget()
        self.list.setMinimumHeight(340)

        # Input texto
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText(" Ej: Tomar pastilla")
        
        self.input_text.mousePressEvent = (
            lambda e: self._show_keyboard(self.input_text)
        )

        # Fila fecha: display + botón
        date_row = QHBoxLayout()
        date_row.setSpacing(14)

        # Selector de fecha
        self.date_display = QLabel(" Sin fecha seleccionada")
        self.date_display.setObjectName("date_display")

        self.btn_pick_date = QPushButton("  Elegir fecha y hora")
        self.btn_pick_date.setObjectName("btn_pick_date")
        self.btn_pick_date.setFixedWidth(300)
        self.btn_pick_date.clicked.connect(self.open_date_picker)

        date_row.addWidget(self.date_display, 1)
        date_row.addWidget(self.btn_pick_date)

        # Botones acción
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.btn_add = QPushButton("  Añadir recordatorio")
        self.btn_add.setObjectName("btn_add")
        self.btn_add.clicked.connect(self.add_reminder)

        self.btn_delete = QPushButton("  Eliminar")
        self.btn_delete.setObjectName("btn_delete")
        self.btn_delete.clicked.connect(self.delete_reminder)

        btn_row.addWidget(self.btn_add, 2)
        btn_row.addWidget(self.btn_delete, 1)

        layout.addLayout(top_row)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.input_text)
        layout.addLayout(date_row)
        layout.addLayout(btn_row)

        # Integración teclado
        self.keyboard = KeyboardWidget(self)
        self.keyboard.confirmed.connect(self._hide_keyboard)
        
        root.addWidget(content, 1)
        root.addWidget(self.keyboard)
        
        self.refresh()

    
    def _show_keyboard(self, target):
        """@brief Despliega el teclado y ajusta el layout."""
        self.keyboard.set_target(target)
        
        self.list.setMinimumHeight(80)
        self.list.setMaximumHeight(120)
     
    
    def _hide_keyboard(self):
        """@brief Oculta el teclado y restaura el tamaño de la lista."""
        self.keyboard.detach()
        
        self.list.setMinimumHeight(340)
        self.list.setMaximumHeight(16777215)
     
     
    def hideEvent(self, event):
        """@brief Garantiza el cierre del teclado al ocultar el widget."""
        self._hide_keyboard()
        super().hideEvent(event)


    def open_date_picker(self):
        """@brief Lanza el selector de fecha y hora."""
        dialog = DateTimePickerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self._selected_dt = dialog.get_datetime_str()
            self.date_display.setText(f"  {self._selected_dt}")

    def refresh(self):
        """@brief Refresca la lista desde el store."""
        self.list.clear()
        for r in self.store.reminders:
            logger.info(f"[REMINDER SCREEN] Encontrado: {r}")
            estado = "O" if r.get("done") else "X"
            self.list.addItem(
                QListWidgetItem(f"{estado}  {r['time']}  —  {r['title']}")
            )

    def add_reminder(self):
        """@brief Valida entrada y guarda el recordatorio."""
        title = self.input_text.text().strip()
        if not title or not self._selected_dt:
            return
            
        self.store.add(title, self._selected_dt)
        self.input_text.clear()
        self._selected_dt = None
        self.date_display.setText("  Sin fecha seleccionada")
        
        self._hide_keyboard()
        
        self.refresh()

    def delete_reminder(self):
        """@brief Elimina el item seleccionado."""
        row = self.list.currentRow()
        if row < 0:
            return
        reply = QMessageBox.question(
            self, "Eliminar", "¿Eliminar este recordatorio?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            del self.store.reminders[row]
            self.store.save()
            self.refresh()

    def go_back(self):
        """@brief Navegación hacia atrás."""
        if hasattr(self.controller, "ui"):
            self.controller.ui.show_launcher()
