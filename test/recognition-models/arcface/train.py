from deepface import DeepFace
import os
import numpy as np
import pickle
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Paso 1: Extraer los embeddings de las imágenes de entrenamiento
def extract_embeddings(dataset_path):
    embeddings = []
    labels = []

    for person in os.listdir(dataset_path):
        person_path = os.path.join(dataset_path, person)
        if not os.path.isdir(person_path):  # Verifica que sea una carpeta (persona)
            continue

        for img in os.listdir(person_path):
            img_path = os.path.join(person_path, img)
            try:
                # Extraemos el embedding de cada imagen
                embedding = DeepFace.represent(img_path, model_name="ArcFace")[0]["embedding"]
                
                # Asegúrate de que el embedding sea un vector y agregarlo correctamente
                embeddings.append(np.array(embedding))  # Convertir a numpy array para asegurar que es un vector
                labels.append(person)  # La etiqueta es el nombre de la persona
            except Exception as e:
                print(f"Error con la imagen {img_path}: {e}")

    # Convertir a array para usar en el clasificador
    embeddings = np.array(embeddings)
    labels = np.array(labels)

    print(f"Total de embeddings extraídos: {len(embeddings)}")
    return embeddings, labels


# Paso 2: Entrenar el clasificador (SVM)
def train_classifier(embeddings, labels):
    # Verifica si el número de muestras y características está bien
    print(f"Forma de los embeddings: {embeddings.shape}")
    
    # Codificar las etiquetas de las personas (labels) en números
    label_encoder = LabelEncoder()
    labels_encoded = label_encoder.fit_transform(labels)

    # Entrenar el clasificador SVM
    classifier = SVC(kernel="linear", probability=True)
    classifier.fit(embeddings, labels_encoded)

    # Guardamos el clasificador y el codificador de etiquetas
    with open("svm_classifier.pkl", "wb") as f:
        pickle.dump(classifier, f)
    with open("label_encoder.pkl", "wb") as f:
        pickle.dump(label_encoder, f)

    print("✅ Clasificador entrenado y guardado exitosamente.")


# Ruta del dataset (asegúrate de que sea la ruta correcta)
dataset_path = "/home/elisa/uni/tfg-ematos/arcface/dataset"

# Extraemos los embeddings y las etiquetas
embeddings, labels = extract_embeddings(dataset_path)

# Entrenamos el clasificador
train_classifier(embeddings, labels)
