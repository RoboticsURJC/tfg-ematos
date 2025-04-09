from deepface import DeepFace

img1_path = "/home/elisa/Downloads/Ariana.jpg"
img2_path = "/home/elisa/Downloads/Cythia.jpg"

result = DeepFace.verify(img1_path, img2_path, model_name="ArcFace")

print(result)