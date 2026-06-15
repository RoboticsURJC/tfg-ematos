# code from server (my pc)

# it will proccess the faces and identify the persons

import os
from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import pickle
import cv2
import base64
import tempfile
import shutil

app = Flask(__name__)

# load "database"
if os.path.exists("known_faces.pkl"):
    with open("known_faces.pkl", "rb") as f:
        known_face_names, known_face_encodings = pickle.load(f)
else:
    known_face_names, known_face_encodings = [], []

@app.route("/recognize", methods=["POST"])
def recognize():
    data = request.get_json()
    image_data = base64.b64decode(data["image"])
    nparr = np.frombuffer(image_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Convert to RGB y proccess
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_frame, model='hog')
    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

    results = []
    for encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, encoding)
        name = "Unknown"
        face_distances = face_recognition.face_distance(known_face_encodings, encoding)
        if len(face_distances) > 0:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
        results.append(name)

    return jsonify({"recognized": results})

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data["name"]
    images = data["images"]  # lista de fotos en base64
    os.makedirs(f"known_persons/{name}", exist_ok=True)
    
    new_encodings = []
    for idx, img_str in enumerate(images):
        img_data = base64.b64decode(img_str)
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_encs = face_recognition.face_encodings(rgb_frame)
        if face_encs:
            new_encodings.append(face_encs[0])
            # save imgs
            cv2.imwrite(f"known_persons/{name}/{name}_{idx+1}.jpg", frame)
    
    if new_encodings:
        known_face_names.extend([name]*len(new_encodings))
        known_face_encodings.extend(new_encodings)
        tmp = tempfile.mktemp()
        with open(tmp, "wb") as f:
            pickle.dump((known_face_names, known_face_encodings), f)
        shutil.move(tmp, "known_faces.pkl")
        
    return jsonify({
        "status": "ok",
        "message": f"{name} registrado con {len(new_encodings)} imágenes válidas"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
    
