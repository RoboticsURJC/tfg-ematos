# code from server (my pc)

# it will proccess the faces and identify the persons

from flask import Flask, request, jsonify
import face_recognition
import numpy as np
import pickle
import cv2
import base64

app = Flask(__name__)

# load known faces
with open("known_faces.pkl", "rb") as f:
    known_face_names, known_face_encodings = pickle.load(f)


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)