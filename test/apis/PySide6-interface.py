from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)
import cv2
import sys
import os
import pickle

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")

        self.create_ui()
        
    
    def create_ui(self):
        toolbar = QToolBar("My main toolbar")
        toolbar.setIconSize(QSize(100, 20))
        self.addToolBar(toolbar)

        button_action = QAction(QIcon("fugue-icons-3.5.6/icons/camera.png"), "Camera button", self)
        button_action.setStatusTip("Take photo")
        button_action.triggered.connect(self.take_photo)
        button_action.setCheckable(True)
        toolbar.addAction(button_action)

        self.setStatusBar(QStatusBar(self))

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Label para mostrar la imagen de la cámara
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Creamos un layout HORIZONTAL para los botones
        button_layout = QHBoxLayout()
        
        # Botón
        self.button_task = QPushButton("Avanzar")
        self.button_task.clicked.connect(self.toolbar_button_task)
        button_layout.addWidget(self.button_task)
        
        
        self.register_person = QPushButton("Register")
        self.register_person.clicked.connect(self.toolbar_button_task)
        button_layout.addWidget(self.register_person)
        
        # Añadimos el layout horizontal al layout principal vertical
        layout.addLayout(button_layout)
        

        # Configurar la cámara
        self.cap = cv2.VideoCapture(0)  # 0 para la cámara predeterminada
        if not self.cap.isOpened():
            print("Error: No se pudo abrir la cámara.")
            sys.exit()

        # Timer para actualizar la imagen
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Actualizar cada 30 ms (~33 fps)

        
        
    # def start_registration(self):
        
        
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convertir el frame de OpenCV (BGR) a QImage (RGB)
            frame = cv2.flip(frame, 1)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(q_img)
            
            # Escalar la imagen para que se ajuste al label manteniendo la relación de aspecto
            self.image_label.setPixmap(pixmap.scaled(
                self.image_label.width(), 
                self.image_label.height(), 
                Qt.AspectRatioMode.KeepAspectRatio
            ))

    def take_photo(self, checked):
        print("Botón de cámara presionado:", checked)

    def toolbar_button_task(self):
        value = self.progress_bar.value()
        if value < 100:
            self.progress_bar.setValue(value + 25)
        else:
            self.button_task.setText("Completado")

    def closeEvent(self, event):
        # Liberar la cámara al cerrar la ventana
        self.cap.release()
        event.accept()

app = QApplication([])
window = MainWindow()
window.show()
app.exec()