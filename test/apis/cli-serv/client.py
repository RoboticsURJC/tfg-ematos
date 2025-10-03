# client.py para Raspberry Pi con Picamera2
import base64
import json
import requests
from tkinter import Tk, Label, Button
from PIL import Image, ImageTk
from picamera2 import Picamera2
import cv2

# Cargar configuración
with open("config.json") as f:
    config = json.load(f)
SERVER_URL = config["server_url"]

class ClientApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Face Client")

        # Inicializar Picamera2
        self.picam2 = Picamera2()
        self.picam2.start()
        self.current_frame = None

        # GUI
        self.label = Label(window)
        self.label.pack()

        self.button = Button(window, text="Reconocer", command=self.capture_and_send)
        self.button.pack()

        self.result_label = Label(window, text="", font=("Arial", 16))
        self.result_label.pack()

        self.update_frame()

    def update_frame(self):
        # Capturar frame de la cámara
        frame = self.picam2.capture_array()
        if frame is not None:
            frame = cv2.flip(frame, 1)  # espejo
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.label.config(image=img)
            self.label.image = img
            self.current_frame = frame
        else:
            self.result_label.config(text="Cámara no detectada")

        self.window.after(30, self.update_frame)

    def capture_and_send(self):
        if self.current_frame is None:
            self.result_label.config(text="Cámara no lista")
            return

        # Convertir frame a JPEG y luego a base64
        _, buffer = cv2.imencode('.jpg', self.current_frame)
        img_str = base64.b64encode(buffer).decode("utf-8")

        try:
            response = requests.post(SERVER_URL, json={"image": img_str}, timeout=5)
            if response.ok:
                names = response.json().get("recognized", [])
                self.result_label.config(text=f"Reconocidos: {', '.join(names)}")
            else:
                self.result_label.config(text="Error en el servidor")
        except requests.exceptions.RequestException:
            self.result_label.config(text="No se pudo conectar al servidor")
            
    def start_registration(self):
      from tkinter import simpledialog, messagebox

      name = simpledialog.askstring("Registrar persona", "Introduce el nombre de la persona:")
      if not name:
          return

      images = []
      for i in range(3):  # capturar 3 fotos como ejemplo
          messagebox.showinfo("Registro", f"Prepararse para foto {i+1}")
          frame = self.current_frame
          if frame is not None:
              _, buffer = cv2.imencode('.jpg', frame)
              img_str = base64.b64encode(buffer).decode("utf-8")
              images.append(img_str)
          else:
              messagebox.showerror("Error", "No hay frame de cámara disponible")
      
      # enviar al servidor
      try:
          response = requests.post(f"{SERVER_URL}/register",
                                  json={"name": name, "images": images}, timeout=10)
          if response.ok:
              messagebox.showinfo("Registro", f"{name} registrado correctamente")
          else:
              messagebox.showerror("Error", "No se pudo registrar la persona en el servidor")
      except requests.exceptions.RequestException:
          messagebox.showerror("Error", "No se pudo conectar al servidor")


# Ejecutar aplicación
root = Tk()
app = ClientApp(root)
root.mainloop()
