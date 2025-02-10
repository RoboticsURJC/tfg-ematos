from deepface.basemodels import Facenet
from deepface.commons import functions
import os
import numpy as np

# Cargar el modelo FaceNet
model = Facenet.loadModel()

def get_embedding(img_path):
    img = functions.preprocess_face(img_path, target_size=(160, 160))
    embedding = model.predict(img)[0]
    return embedding

# Recorrer las imágenes y guardar embeddings
dataset_path = "dataset/"
X = []  # Embeddings
y = []  # Etiquetas

for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)
    if os.path.isdir(person_path):
        for img_name in os.listdir(person_path):
            img_path = os.path.join(person_path, img_name)
            embedding = get_embedding(img_path)
            X.append(embedding)
            y.append(person)

X = np.array(X)
y = np.array(y)

