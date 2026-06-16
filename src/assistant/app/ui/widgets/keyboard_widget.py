"""
Teclado software nativo PyQt5.
Diseño corregido y alineado: Borrar abajo a la derecha, Listo abajo a la izquierda.
Matriz matemática perfecta de 10 columnas por fila.
"""

from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from app.core.logger import logger


# Cada fila suma exactamente 10 en su 'span' total para evitar descuadres
ROWS_LOWER = [
    ["1","2","3","4","5","6","7","8","9","0"], # 10 teclas (span 1x10 = 10)
    ["q","w","e","r","t","y","u","i","o","p"], # 10 teclas (span 1x10 = 10)
    ["a","s","d","f","g","h","j","k","l","ñ"], # 10 teclas (span 1x10 = 10)
    ["MAYÚS","z","x","c","v","b","n","m",",","."], # MAYÚS(2) + 8 teclas(8) = 10
    ["LISTO", "ESPACIO", "BORRAR"],                # LISTO(2) + ESPACIO(6) + BORRAR(2) = 10
]

ROWS_UPPER = [
    ["1","2","3","4","5","6","7","8","9","0"],
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L","Ñ"],
    ["MAYÚS","Z","X","C","V","B","N","M",",","."],
    ["LISTO", "ESPACIO", "BORRAR"],
]

KB_STYLE = """
QWidget#keyboard_root {
    background-color: #e2e8f0;
    border-top: 5px solid #4f46e5;
}

/* Teclas alfabéticas y numéricas */
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

/* Modificadores generales (Mayús inactivo) */
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

/* Mayúsculas Activas */
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

/* Barra Espaciadora Centrada */
QPushButton#kb_space {
    background-color: #f8fafc;
    color: #475569;
    border: none;
    border-bottom: 6px solid #e2e8f0;
    border-radius: 16px;
    font-size: 32px;
    font-weight: 800;
    min-height: 90px;
    letter-spacing: 2px;
}
QPushButton#kb_space:pressed {
    background-color: #e2e8f0;
    border-bottom: 2px solid #cbd5e1;
    padding-top: 4px;
}

/* Botón Borrar (Abajo a la derecha) */
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

/* Botón Confirmar / Listo (Abajo a la izquierda) */
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
    @brief Teclado software interactivo diseñado para alta legibilidad.
    @details Proporciona una interfaz táctil de teclado con disposición QWERTY,
    soporte para mayúsculas y una matriz matemática fija de 10 columnas para
    garantizar una alineación consistente en diferentes resoluciones de pantalla.
    
    @attr confirmed Señal emitida cuando el usuario presiona el botón 'Listo'.
    """

    confirmed = pyqtSignal()

    def __init__(self, parent=None):
        
        """
        @brief Inicializa el teclado, configura el estilo y construye la matriz de teclas.
        @param parent Widget padre (opcional).
        """
        
        super().__init__(parent)
        self.setObjectName("keyboard_root")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(KB_STYLE)

        self._target = None
        self._upper  = False

        self._grid = QGridLayout()
        self._grid.setSpacing(10)
        self._grid.setContentsMargins(14, 16, 14, 20)
        self.setLayout(self._grid)

        self._build_keys()
        self.hide()

    # ── Construcción de la Interfaz ──────────────────────────────────────────

    def _build_keys(self):
        
        """
        @brief Reconstruye la matriz del teclado al cambiar de estado (Mayús).
        @details Limpia el layout actual y redibuja los botones según ROWS_UPPER o ROWS_LOWER.
        """
        
        # Limpieza del layout
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
        
        
        """
        @brief Crea y configura un botón del teclado basándose en su función.
        @param key String con el carácter o acción a asignar.
        @param font QFont configurada para el texto del botón.
        @return Tupla (QPushButton, int) con el botón y el espacio que ocupa (span).
        """
        
        btn = QPushButton()
        btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        btn.setFont(font)

        if key == "ESPACIO":
            btn.setText("ESPACIO")
            btn.setObjectName("kb_space")
            span = 6  # Columnas centrales (de la 2 a la 7)
        elif key == "BORRAR":
            btn.setText("Borrar ⌫")
            btn.setObjectName("kb_delete")
            span = 2  # Columnas 8 y 9 (Esquina inferior derecha)
        elif key == "LISTO":
            btn.setText("Listo ✓")
            btn.setObjectName("kb_confirm")
            span = 2  # Columnas 0 y 1 (Esquina inferior izquierda)
        elif key == "MAYÚS":
            btn.setText("Mayús ⇧")
            btn.setObjectName("kb_shift_on" if self._upper else "kb_special")
            span = 2  # Ocupa 2 columnas en la fila 4
        else:
            btn.setText(key)
            btn.setObjectName("kb_key")
            span = 1

        btn.clicked.connect(lambda _, k=key: self._on_key(k))
        return btn, span

    # ── Control de Pulsaciones ───────────────────────────────────────────────

    def _on_key(self, key):
        
        """
        @brief Slot principal para gestionar eventos de clic en las teclas.
        @details Realiza la acción correspondiente (borrado, espacio, shift, inserción).
        @param key El identificador de la tecla pulsada.
        """
        
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
            
            # Desactivación móvil del Shift tras pulsar una letra
            if self._upper and key not in [",", "."]:
                self._upper = False
                self._build_keys()

    # ── Métodos de Enlace (Target) ───────────────────────────────────────────

    def set_target(self, line_edit):
        
        """
        @brief Asigna el widget de texto (target) donde se escribirán los caracteres.
        @param line_edit Instancia de QLineEdit o similar.
        """
        
        self._target = line_edit
        self.show()
        self.raise_()
        logger.info("[KB] Teclado visible adaptado")

    def detach(self):
        """@brief Desvincula el target actual y oculta el teclado."""
        self._target = None
        self.hide()
        logger.info("[KB] Teclado ocultado")
