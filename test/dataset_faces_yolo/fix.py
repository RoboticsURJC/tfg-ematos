import os
import shutil
import random

# Configuración
IMAGES_DIR = "Will"  # Carpeta de imágenes original
LABELS_DIR = "labels_will"  # Carpeta de etiquetas original
OUTPUT_DIR = "dataset_will"  # Carpeta donde se guardarán train, val y test
TRAIN_RATIO = 0.8
VAL_RATIO = 0.1
TEST_RATIO = 0.1

# Crear las carpetas de salida
for folder in ["train", "val", "test"]:
    os.makedirs(os.path.join(OUTPUT_DIR, "images", folder), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, "labels", folder), exist_ok=True)

# Obtener lista de imágenes
image_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))]
random.shuffle(image_files)  # Mezclar aleatoriamente

# Calcular tamaños de los conjuntos
total = len(image_files)
train_size = int(total * TRAIN_RATIO)
val_size = int(total * VAL_RATIO)
test_size = total - train_size - val_size  # El resto va a test

# Dividir archivos
train_files = image_files[:train_size]
val_files = image_files[train_size:train_size + val_size]
test_files = image_files[train_size + val_size:]

# Función para mover archivos
def move_files(files, split):
    for file in files:
        image_path = os.path.join(IMAGES_DIR, file)
        label_path = os.path.join(LABELS_DIR, file.replace(".jpg", ".txt").replace(".png", ".txt").replace(".jpeg", ".txt"))

        if os.path.exists(label_path):  # Asegurar que la etiqueta existe
            shutil.move(image_path, os.path.join(OUTPUT_DIR, "images", split, file))
            shutil.move(label_path, os.path.join(OUTPUT_DIR, "labels", split, file.replace(".jpg", ".txt").replace(".png", ".txt").replace(".jpeg", ".txt")))

# Mover los archivos a sus carpetas
move_files(train_files, "train")
move_files(val_files, "val")
move_files(test_files, "test")

print(f"Dataset dividido: {train_size} train, {val_size} val, {test_size} test")
