import os
import shutil
import random

# Rutas de las carpetas (ajusta según tu estructura)
input_images = "/home/elisa/uni/tfg-ematos/example2/images"  # Carpeta donde están todas las imágenes
input_labels = "/home/elisa/uni/tfg-ematos/example2/labels-cars"  # Carpeta donde están todas las etiquetas

output_base = "/home/elisa/uni/tfg-ematos/example2/division"  # Carpeta donde se crearán train, val y test

# Proporciones de división
train_ratio = 0.7
val_ratio = 0.2
test_ratio = 0.1  # Lo que queda

# Crear carpetas de salida
for split in ["train", "val", "test"]:
    os.makedirs(os.path.join(output_base, split, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_base, split, "labels"), exist_ok=True)

# Obtener lista de imágenes
images = [f for f in os.listdir(input_images) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
random.shuffle(images)  # Mezclar aleatoriamente las imágenes

# Calcular cantidades
num_train = int(len(images) * train_ratio)
num_val = int(len(images) * val_ratio)

# Dividir en conjuntos
train_images = images[:num_train]
val_images = images[num_train:num_train + num_val]
test_images = images[num_train + num_val:]

# Función para mover archivos
def move_files(image_list, split):
    for image in image_list:
        image_path = os.path.join(input_images, image)
        label_path = os.path.join(input_labels, os.path.splitext(image)[0] + ".txt")  # Asume etiquetas en formato YOLO

        # Mover imagen
        if os.path.exists(image_path):
            shutil.move(image_path, os.path.join(output_base, split, "images", image))

        # Mover etiqueta (si existe)
        if os.path.exists(label_path):
            shutil.move(label_path, os.path.join(output_base, split, "labels", os.path.splitext(image)[0] + ".txt"))

# Mover archivos a sus carpetas correspondientes
move_files(train_images, "train")
move_files(val_images, "val")
move_files(test_images, "test")

print("✅ División completada: Train, Val y Test creados correctamente.")
