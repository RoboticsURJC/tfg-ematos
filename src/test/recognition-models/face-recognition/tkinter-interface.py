import cv2
import time
import os
import pickle
import face_recognition
import threading
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk 
from tkinter import Label, Button, Tk, PhotoImage, Frame

class FaceRegistrationApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Face Registration System")
        self.window.geometry("800x600")
        self.window.configure(bg="black")
        
        # Window can be resized
        self.window.resizable(1, 1)
        
        # Face recognition variables
        self.pickle_file = "known_faces.pkl"
        self.people_folder = "known_persons"
        self.known_face_names, self.known_face_encodings = self.load_known_faces()
        self.frame_resize_factor = 0.25
        self.captured_images = []
        self.current_photo_index = 0
        self.registration_mode = False
        
        # Create UI elements
        self.create_ui()
        
        # Start camera thread
        self.Main()

    def create_ui(self):
        # Create a frame for the Exit button at the top of the window
        self.button_top_frame = Frame(self.window, bg="black")
        self.button_top_frame.pack(side="top", fill="x")
        
        # Create the main frame for video
        self.main_frame = Frame(self.window)
        self.main_frame.pack(fill="both", expand=True)

        # Show the video
        self.ImageLabel = Label(self.main_frame, bg="black")
        self.ImageLabel.pack(fill="both", expand=True)

        # Create the bottom buttons frame (initial state)
        self.button_bottom_frame = Frame(self.window, bg="white")
        self.button_bottom_frame.pack(fill="x")

        # Initial buttons
        self.Register = Button(self.button_bottom_frame, text="Register New Person", 
                             font=("Times", 15), bg="green", fg="white", 
                             relief='flat', command=self.start_registration)
        self.Register.pack(side="bottom", expand=True, fill="x", padx=10, pady=10)
        
        # Registration buttons (hidden initially)
        self.TakePhoto_b = Button(self.button_bottom_frame, text="Take Photo", 
                                font=("Times", 15), bg="blue", fg="white", 
                                relief='flat', command=self.take_photo)
        self.RepeatPhoto_b = Button(self.button_bottom_frame, text="Repeat Photo", 
                                   font=("Times", 15), bg="orange", fg="white", 
                                   relief='flat', command=self.repeat_photo)
        self.FinishRegistration_b = Button(self.button_bottom_frame, text="Finish Registration", 
                                         font=("Times", 15), bg="purple", fg="white", 
                                         relief='flat', command=self.finish_registration)
        
        self.hide_registration_buttons()

    def start_registration(self):
        self.registration_mode = True
        self.captured_images = []
        self.current_photo_index = 0
        self.register_person()
        
        # advertise of the registration action
        messagebox.showinfo("Registration", "Please take photos of the person to register.")

    def hide_registration_buttons(self):
      
        # With pack_forget hide the buttons
        self.TakePhoto_b.pack_forget()
        self.RepeatPhoto_b.pack_forget()
        self.FinishRegistration_b.pack_forget()
        self.Register.pack(side="bottom", expand=True, fill="x", padx=10, pady=10)

    def register_person(self):
        self.Register.pack_forget()  # hide the register botton
        self.TakePhoto_b.pack(side="left", expand=True, fill="x", padx=10, pady=10)
        self.RepeatPhoto_b.pack(side="left", expand=True, fill="x", padx=10, pady=10)
        self.FinishRegistration_b.pack(side="left", expand=True, fill="x", padx=10, pady=10)

    def take_photo(self):
        if self.current_frame is not None:
            # Convert frame to RGB for face recognition
            small_frame = cv2.resize(self.current_frame, (0, 0), fx=self.frame_resize_factor, fy=self.frame_resize_factor)
            rgb_small_frame = cv2.cvtColor(small_frame[:, :, ::-1], cv2.COLOR_BGR2RGB)
            
            # Detect faces (model could be cnn or hog (cnn is more precise))
            face_locations = face_recognition.face_locations(rgb_small_frame, model='cnn')
            
            if len(face_locations) == 0:
                messagebox.showerror("Error", "No face detected. Please try again.")
                return
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            # Save the first face found
            face_location = face_locations[0]
            top, right, bottom, left = [v * (1/self.frame_resize_factor) for v in face_location]
            face_image = self.current_frame[int(top):int(bottom), int(left):int(right)]
            
            self.captured_images.append((face_image, face_encodings[0]))
            self.current_photo_index += 1
            
            messagebox.showinfo("Advise", "Take at least 3 photos (fronta, right and left) ")            
            messagebox.showinfo("Success", f"Photo {self.current_photo_index} taken successfully!")

            if len(self.captured_images) >= 3:  # Example: require 3 photos
                self.FinishRegistration_b.config(state="normal")

    def repeat_photo(self):
        if self.captured_images:
            self.captured_images.pop()
            self.current_photo_index = max(0, self.current_photo_index - 1)
            messagebox.showinfo("Info", "Last photo discarded. Please take a new one.")

    def finish_registration(self):
        if not self.captured_images:
            messagebox.showerror("Error", "No photos taken to register.")
            return
            
        new_name = simpledialog.askstring("Registration", "Please enter the name for this person:")
        if not new_name:
            messagebox.showinfo("Cancelled", "Registration cancelled.")
            self.cancel_registration()
            return
            
        # Create folder for the person
        person_folder = os.path.join(self.people_folder, new_name)
        os.makedirs(person_folder, exist_ok=True)

        # Save all captured images
        for idx, (img, encoding) in enumerate(self.captured_images):
            self.save_face_image(img, new_name, idx, person_folder)
            self.known_face_names.append(new_name)
            self.known_face_encodings.append(encoding)

        # Save to pickle file
        self.save_known_faces()
        
        messagebox.showinfo("Success", f"Person {new_name} registered successfully!")
        self.cancel_registration()

    def cancel_registration(self):
        self.registration_mode = False
        self.captured_images = []
        self.current_photo_index = 0
        self.hide_registration_buttons()

    @staticmethod
    def load_camera():
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            ret, frame = camera.read()
        while ret:
            ret, frame = camera.read()
            if ret:
                yield frame
            else:
                yield False

    def Main(self):
        self.render_thread = threading.Thread(target=self.start_camera)
        self.render_thread.daemon = True
        self.render_thread.start()

    def start_camera(self):
        frame_generator = self.load_camera()
        self.current_frame = None
        
        while True:
            frame = next(frame_generator)
            if frame is False:
                continue
                
            self.current_frame = frame.copy()
            
            # Flip frame for more intuitive viewing
            frame = cv2.flip(frame, 1)
            
            if self.registration_mode:
                # Show just the camera feed during registration
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # Perform face recognition when not in registration mode
                small_frame = cv2.resize(frame, (0, 0), fx=self.frame_resize_factor, fy=self.frame_resize_factor)
                rgb_small_frame = cv2.cvtColor(small_frame[:, :, ::-1], cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                for face_encoding, face_location in zip(face_encodings, face_locations):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Unknown"

                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = face_distances.argmin()
                        if matches[best_match_index]:
                            name = self.known_face_names[best_match_index]

                    top, right, bottom, left = [v * 4 for v in face_location]
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Convert to PhotoImage and display
            picture = Image.fromarray(rgb_frame)
            picture = picture.resize((700, 500), resample=Image.BILINEAR)
            picture = ImageTk.PhotoImage(picture)
            
            self.ImageLabel.configure(image=picture)
            self.ImageLabel.image = picture  # Keep reference
            
            time.sleep(0.01)

    # Face database methods
    def load_known_faces(self):
        if os.path.exists(self.pickle_file):
            with open(self.pickle_file, "rb") as f:
                return pickle.load(f)
        return [], []

    def save_known_faces(self):
        with open(self.pickle_file, "wb") as f:
            pickle.dump((self.known_face_names, self.known_face_encodings), f)

    @staticmethod
    def save_face_image(frame, name, idx, person_folder):
        filename = f"{name}_{idx+1}.jpg"
        save_path = os.path.join(person_folder, filename)
        cv2.imwrite(save_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        print(f"Saved photo {filename}")

# Main application
if __name__ == "__main__":
    root = Tk()
    app = FaceRegistrationApp(root)
    root.mainloop()