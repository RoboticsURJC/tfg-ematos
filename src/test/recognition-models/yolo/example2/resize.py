import os
from PIL import Image

# Directorios
input_folder = "/home/elisa/Downloads/images-cars"  # Cambia esta ruta a la carpeta con las imágenes originales
output_folder = "../example2"  # Cambia esta ruta a la carpeta donde guardarás las imágenes redimensionadas

# Asegúrate de que la carpeta de salida exista, si no, créala
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Redimensionar todas las imágenes en la carpeta
for filename in os.listdir(input_folder):
    # Solo procesar archivos de imagen (se puede agregar más extensiones si es necesario)
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        # Ruta completa de la imagen original
        img_path = os.path.join(input_folder, filename)
        
        # Abrir la imagen
        img = Image.open(img_path)
        
        # Nueva dimensión (por ejemplo, reducir a la mitad del tamaño original)
        new_width = 416
        new_height = 416
        
        # Redimensionar la imagen con el algoritmo LANCZOS para alta calidad
        img_resized = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Ruta para guardar la imagen redimensionada
        output_path = os.path.join(output_folder, filename)
        
        # Guardar la imagen redimensionada
        img_resized.save(output_path)

        print(f"Imagen redimensionada guardada en: {output_path}")

print("¡Proceso de redimensionado completado!")
