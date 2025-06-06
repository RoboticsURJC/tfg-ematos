import sys
import cv2
import numpy as np
from PyQt5 import QtWidgets
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QStatusBar, QToolBar, QAction, QFileDialog, QLabel
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
import time, libcamera
from picamera2 import Picamera2, Preview
from libcamera import Transform


class CameraThread(QThread):
    image = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (640, 480), "format": "RGB888"})
        self.picam2.configure(config)
        self.frame = None

    def run(self):
        self.picam2.start()
        while True:
            frame = self.picam2.capture_array()
            self.frame = frame
            self.image.emit(frame)

    def stop(self):
        self.picam2.stop()
        super().terminate()

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("WaLLeli")
        self.statusBar().showMessage("Ready")

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(self.label)

        self.camera = CameraThread()
        self.camera.image.connect(self.update_image)
        self.camera.start()

        capture_action = QAction("Capture", self.toolbar)
        capture_action.setShortcut("Space")

        capture_action.triggered.connect(self.capture_photo)
        self.toolbar.addAction(capture_action)

    def update_image(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(image))

    def capture_photo(self):
        frame = self.camera.frame
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = QImage(frame, frame.shape[1], frame.shape[0], QImage.Format_RGB888)
        filename, _ = QFileDialog.getSaveFileName(self, "Save Photo", "", "JPEG Image (*.jpg)")
        if filename:
            image.save(filename, "jpg")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
