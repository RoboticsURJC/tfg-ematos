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
        self.window.title("Client")

        # Inicializar Picamera2
        self.picam2 = Picamera2()
        self.picam2.start()
        self.current_frame = None

        # GUI
        self.label = Label(window)
        self.label.pack()

        
        # Boton para iniciar sesion si el usuario ya existiera
        self.button = Button(window, text="Login in", command=self.capture_and_send)
        self.button.pack()
        
        # Boton para registrar nuevo usuario 
        self.button = Button(window, text="Register", command=self.start_registration)
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
            self.result_label.config(text="Camera not detected")

        self.window.after(30, self.update_frame)

    def capture_and_send(self):
        if self.current_frame is None:
            self.result_label.config(text="Camare not ready")
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
                self.result_label.config(text="Server failed")
        except requests.exceptions.RequestException:
            self.result_label.config(text="Could not connect to the server")
            
    def start_registration(self):
      from tkinter import simpledialog, messagebox

      name = simpledialog.askstring("Register user", "Intruce name:")
      if not name:
          return

      images = []
      for i in range(3):  # capturar 3 fotos como ejemplo
          messagebox.showinfo("Register", f"Ready for take {i+1}")
          frame = self.current_frame
          if frame is not None:
              _, buffer = cv2.imencode('.jpg', frame)
              img_str = base64.b64encode(buffer).decode("utf-8")
              images.append(img_str)
          else:
              messagebox.showerror("Error", "Frame failed")
      
      # send to server
      try:
          response = requests.post(f"{SERVER_URL}/register",
                                  json={"name": name, "images": images}, timeout=10)
          if response.ok:
              messagebox.showinfo("Register", f"{name} successfully registered")
          else:
              messagebox.showerror("Error", "The user could not be registered on the server")
      except requests.exceptions.RequestException:
          messagebox.showerror("Error", "Could not connect to the server")


# Ejecutar aplicación
root = Tk()
app = ClientApp(root)
root.mainloop()
