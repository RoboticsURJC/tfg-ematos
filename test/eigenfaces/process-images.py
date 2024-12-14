import os
import numpy as np
from skimage.io import imread
from skimage.transform import resize
from sklearn.preprocessing import LabelEncoder

# Configuración
image_dir = "./wicked_dataset"
image_size = (40, 40)  # Tamaño objetivo de las imágenes

# Cargar imágenes y etiquetas
def load_images(image_dir, image_size):
    X = []  # Imágenes
    y = []  # Etiquetas
    for person_name in os.listdir(image_dir):
        person_folder = os.path.join(image_dir, person_name)
        if os.path.isdir(person_folder):
            for file_name in os.listdir(person_folder):
                file_path = os.path.join(person_folder, file_name)
                try:
                    image = imread(file_path, as_gray=True)  # Cargar en escala de grises
                    image_resized = resize(image, image_size, anti_aliasing=True)
                    X.append(image_resized.flatten())  # Aplanar la imagen
                    y.append(person_name)  # Usar el nombre de la carpeta como etiqueta
                except Exception as e:
                    print(f"Error al procesar {file_path}: {e}")
    return np.array(X), np.array(y)

X, y = load_images(image_dir, image_size)

# Convertir etiquetas a números
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)
target_names = label_encoder.classes_

print(f"Datos cargados: {X.shape[0]} imágenes de tamaño {X.shape[1]} píxeles")
print(f"Número de clases: {len(target_names)}")
