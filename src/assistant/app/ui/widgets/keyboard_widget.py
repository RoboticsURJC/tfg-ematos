# app/ui/widgets/keyboard_widget.py
"""
Teclado software nativo PyQt5.
Diseño de alto contraste con teclas gigantes y descriptivas para personas mayores.
"""

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from app.core.logger import logger


ROWS_LOWER = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l","ñ"],
    ["MAYÚS","z","x","c","v","b","n","m",",","."],
    ["BORRAR","ESPACIO","LISTO"],
]

ROWS_UPPER = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","H","G","H","J","K","L","Ñ"],
    ["MAYÚS","Z","X","C","V","B","N","M",",","."],
    ["BORRAR","ESPACIO","LISTO"],
]

KB_STYLE = """
QWidget#keyboard_root {
    background-color: #e2e8f0;
    border-top: 5px solid #4f46e5;
}

/* Teclas alfabéticas y numéricas (Blancas de alto contraste) */
QPushButton#kb_key {
    background-color: #ffffff;
    color: #0f172a;
    border: none;
    border-bottom: 6px solid #cbd5e1;
    border-radius: 16px;
    font-size: 42px;
    font-weight: 800;
    min-height: 90px;
}
QPushButton#kb_key:pressed {
    background-color: #f1f5f9;
    border-bottom: 2px solid #94a3b8;
    padding-top: 4px;
}

/* Modificadores generales (Azul pastel amigable) */
QPushButton#kb_special {
    background-color: #dbeafe;
    color: #1e40af;
    border: none;
    border-bottom: 6px solid #bfdbfe;
    border-radius: 16px;
    font-size: 28px;
    font-weight: 800;
    min-height: 90px;
}
QPushButton#kb_special:pressed {
    background-color: #bfdbfe;
    border-bottom: 2px solid #93c5fd;
    padding-top: 4px;
}

/* Mayúsculas Activas (Naranja/Ámbar de advertencia clara) */
QPushButton#kb_shift_on {
    background-color: #fef3c7;
    color: #d97706;
    border: none;
    border-bottom: 6px solid #fde68a;
    border-radius: 16px;
    font-size: 28px;
    font-weight: 900;
    min-height: 90px;
}
QPushButton#kb_shift_on:pressed {
    background-color: #fde68a;
    border-bottom: 2px solid #fcd34d;
    padding-top: 4px;
}

/* Barra Espaciadora (Ancha y cómoda) */
QPushButton#kb_space {
    background-color: #f8fafc;
    color: #475569;
    border: none;
    border-bottom: 6px solid #e2e8f0;
    border-radius: 16px;
    font-size: 28px;
    font-weight: 700;
    min-height: 90px;
    letter-spacing: 2px;
}
QPushButton#kb_space:pressed {
    background-color: #e2e8f0;
    border-bottom: 2px solid #cbd5e1;
    padding-top: 4px;
}

/* Botón Borrar (Rojo/Coral suave - ¡Peligro intuitivo!) */
QPushButton#kb_delete {
    background-color: #fee2e2;
    color: #991b1b;
    border: none;
    border-bottom: 6px solid #fca5a5;
    border-radius: 16px;
    font-size: 28px;
    font-weight: 800;
    min-height: 90px;
}
QPushButton#kb_delete:pressed {
    background-color: #fca5a5;
    border-bottom: 2px solid #f87171;
    padding-top: 4px;
}

/* Botón Confirmar / Listo (Verde vitalizante y alegre) */
QPushButton#kb_confirm {
    background-color: #dcfce7;
    color: #166534;
    border: none;
    border-bottom: 6px solid #bbf7d0;
    border-radius: 16px;
    font-size: 30px;
    font-weight: 900;
    min-height: 90px;
}
QPushButton#kb_confirm:pressed {
    background-color: #bbf7d0;
    border-bottom: 2px solid #86efac;
    padding-top: 4px;
}
"""


class KeyboardWidget(QWidget):
    """
    Teclado software interactivo de alta legibilidad para la tercera edad.
    Sincroniza la inserción de texto con instancias QLineEdit.
    """

    confirmed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("keyboard_root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(KB_STYLE)

        self._target = None
        self._upper  = False

        self._grid = QGridLayout()
        self._grid.setSpacing(8)  # Mayor separación entre teclas para evitar pulsaciones erróneas
        self._grid.setContentsMargins(12, 14, 12, 18)
        self.setLayout(self._grid)

        self._build_keys()
        self.hide()

    # ── Construcción de la Interfaz ──────────────────────────────────────────

    def _build_keys(self):
        # Limpieza segura del layout anterior
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        rows = ROWS_UPPER if self._upper else ROWS_LOWER
        font = QFont("Segoe UI", 16, QFont.Bold)

        for r, row in enumerate(rows):
            c = 0
            for key in row:
                btn, span = self._make_button(key, font)
                self._grid.addWidget(btn, r, c, 1, span)
                c += span

    def _make_button(self, key, font):
        btn = QPushButton()
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setFont(font)

        if key == "ESPACIO":
            btn.setText("ESPACIO")
            btn.setObjectName("kb_space")
            span = 4  # Ocupa el centro de la última fila
        elif key == "BORRAR":
            btn.setText("Borrar ⌫")
            btn.setObjectName("kb_delete")
            span = 3  # Lateral izquierdo equilibrado
        elif key == "LISTO":
            btn.setText("Listo ✓")
            btn.setObjectName("kb_confirm")
            span = 3  # Lateral derecho equilibrado
        elif key == "MAYÚS":
            btn.setText("Mayús ⇧")
            btn.setObjectName("kb_shift_on" if self._upper else "kb_special")
            span = 2  # Mantiene alineación armónica en la cuarta fila
        else:
            btn.setText(key)
            btn.setObjectName("kb_key")
            span = 1

        btn.clicked.connect(lambda _, k=key: self._on_key(k))
        return btn, span

    # ── Control de Pulsaciones ───────────────────────────────────────────────

    def _on_key(self, key):
        if key == "BORRAR":
            if self._target:
                self._target.backspace()
        elif key == "ESPACIO":
            if self._target:
                self._target.insert(" ")
        elif key == "MAYÚS":
            self._upper = not self._upper
            self._build_keys()
        elif key == "LISTO":
            self.confirmed.emit()
            self.hide()
        else:
            if self._target:
                self._target.insert(key)
            
            # Desactivar mayúsculas automáticas tras pulsar una letra (comportamiento móvil)
            if self._upper and key not in [",", "."]:
                self._upper = False
                self._build_keys()

    # ── Métodos de Enlace (Target) ───────────────────────────────────────────

    def set_target(self, line_edit):
        """Asocia el teclado a un QLineEdit y lo despliega."""
        self._target = line_edit
        self.show()
        self.raise_()
        logger.info("[KB] Teclado visible adaptado")

    def detach(self):
        """Remueve la referencia del input objetivo y oculta el widget."""
        self._target = None
        self.hide()
        logger.info("[KB] Teclado ocultado")
