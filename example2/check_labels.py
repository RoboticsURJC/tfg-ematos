import os
import shutil

# Directorios
input_folder = "/home/elisa/uni/tfg-ematos/example2/images"  # Carpeta con las imágenes
label_folder = "/home/elisa/uni/tfg-ematos/example2/labels-cars"  # Carpeta con las etiquetas
output_folder = "/home/elisa/Downloads/non"  # Carpeta para mover las imágenes no etiquetadas

# Asegúrate de que la carpeta de salida exista
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Obtener lista de imágenes en la carpeta de imágenes
image_files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# Recorrer cada imagen
for image in image_files:
    # Obtener el nombre base de la imagen (sin la extensión)
    image_name = os.path.splitext(image)[0]
    
    # Verificar si hay una etiqueta correspondiente en la carpeta de etiquetas
    # Asumimos que las etiquetas son del mismo nombre pero con extensión .xml, .json, etc.
    possible_extensions = ['.xml', '.json', '.txt']  # Añade las extensiones de tus etiquetas
    label_found = False
    
    for ext in possible_extensions:
        label_file = f"{image_name}{ext}"  # Crear el nombre de la etiqueta con la extensión
        if os.path.exists(os.path.join(label_folder, label_file)):
            label_found = True
            break  # Si encontramos la etiqueta, no hace falta seguir buscando
        
    # Si no se encuentra ninguna etiqueta, mover la imagen a la carpeta de descartados
    if not label_found:
        shutil.move(os.path.join(input_folder, image), os.path.join(output_folder, image))
        print(f"Imagen {image} movida a la carpeta de descartados.")

print("¡Proceso completado!")