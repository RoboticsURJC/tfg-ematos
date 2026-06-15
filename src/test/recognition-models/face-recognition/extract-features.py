import face_recognition
import os
import pickle

# Función para cargar las imágenes de una persona desde una carpeta y devolver sus codificaciones
def load_face_encodings_from_folder(folder_path):
    face_encodings = []
    person_name = os.path.basename(folder_path)
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".jpg") or filename.endswith(".png"):
            image_path = os.path.join(folder_path, filename)
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            
            if encodings:
                face_encodings.append(encodings[0])
    return person_name, face_encodings

# Función para cargar todas las personas conocidas desde una carpeta principal
def load_known_faces(people_folder):
    known_face_encodings = []
    known_face_names = []
    
    # Itera sobre todas las carpetas dentro de la carpeta principal
    for person_folder in os.listdir(people_folder):
        person_folder_path = os.path.join(people_folder, person_folder)
        
        if os.path.isdir(person_folder_path):
            name, encodings = load_face_encodings_from_folder(person_folder_path)
            
            known_face_names.extend([name] * len(encodings))  # Replicar el nombre tantas veces como encodings haya
            known_face_encodings.extend(encodings)  # Añadir las codificaciones de la persona
    
    return known_face_names, known_face_encodings


# Ruta donde se encuentran las imágenes de todas las personas conocidas
people_folder = "/home/elisa/uni/tfg-ematos/test/recognition-models/face-recognition/known_persons"

# Cargar las personas conocidas
known_face_names, known_face_encodings = load_known_faces(people_folder)

# Guardar las codificaciones y nombres en un archivo pickle
with open("known_faces.pkl", "wb") as f:
    pickle.dump((known_face_names, known_face_encodings), f)

print("Codificaciones faciales guardadas correctamente en 'known_faces.pkl'")
