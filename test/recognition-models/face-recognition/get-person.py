import os
import time
import pickle
import cv2
import face_recognition


# Load known person from pickle file
def load_known_faces(pickle_file):
    if os.path.exists(pickle_file):
        with open(pickle_file, "rb") as f:
            return pickle.load(f)
    return [], []

# Save the face encodings to the pickle file
def save_known_faces(pickle_file, known_face_names, known_face_encodings):
    with open(pickle_file, "wb") as f:
        pickle.dump((known_face_names, known_face_encodings), f)

# Save the photos taken
def save_face_image(frame, name, idx, person_folder):
    filename = f"{name}{idx+1}.jpg"
    save_path = os.path.join(person_folder, filename)
    cv2.imwrite(save_path, frame)
    print(f" Saved photo {filename}")



# Initial setup
pickle_file = "known_faces.pkl"
people_folder = "known_persons"
known_face_names, known_face_encodings = load_known_faces(pickle_file)

video_capture = cv2.VideoCapture(0)
frame_resize_factor = 0.25

print(" Starting Face Recognition (Press 'q' to exit)")

process_this_frame = True

while True:
    ret, frame = video_capture.read()
    if not ret:
        print(" Capture failed")
        continue    
    
    small_frame = cv2.resize(frame, (0, 0), fx=frame_resize_factor, fy=frame_resize_factor)
    rgb_small_frame = cv2.cvtColor(small_frame[:, :, ::-1], cv2.COLOR_BGR2RGB)

    if process_this_frame:
        # use hog because cnn is slowly
        face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            if len(face_distances) > 0:
                best_match_index = face_distances.argmin()
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

            top, right, bottom, left = [v * 4 for v in face_location]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

            if name == "Unknown":
                print(" Unknown person detected.")
                print(" Press 'r' to register this person.")

    cv2.imshow('Video', frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print(" Exiting...")
        break

    elif key == ord('r'):
        print(" Register process started.")

        num_photos = int(input(" How many photos do you want? (Example: 3): "))

        captured_images = []
        for i in range(num_photos):
            print(f"\n Get ready for photo {i+1}/{num_photos}.")
            print("▶ Press key 'p' to take the photo.")

            while True:
                ret, live_frame = video_capture.read()
                if not ret:
                    continue
                cv2.imshow('Video', live_frame)

                key_pressed = cv2.waitKey(1) & 0xFF
                if key_pressed == ord('p'):
                    print(f" Photo {i+1}/{num_photos} captured.")
                    break

            ret, final_frame = video_capture.read()
            if not ret:
                print(" Capture failed.")
                continue

            small_frame = cv2.resize(final_frame, (0, 0), fx=frame_resize_factor, fy=frame_resize_factor)
            rgb_small_frame = cv2.cvtColor(small_frame[:, :, ::-1], cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame, model='hog')
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            if not face_encodings:
                print(" No face detected. Please try again.")
                continue

            face_encoding = face_encodings[0]
            top, right, bottom, left = [v * 4 for v in face_locations[0]]
            face_image = final_frame[top:bottom, left:right]
            captured_images.append((face_image, face_encoding))

        if captured_images:
            new_name = input(" Enter name: ").strip()
            person_folder = os.path.join(people_folder, new_name)
            os.makedirs(person_folder, exist_ok=True)

            for idx, (img, encoding) in enumerate(captured_images):
                save_face_image(img, new_name, idx, person_folder)
                known_face_names.append(new_name)
                known_face_encodings.append(encoding)

            save_known_faces(pickle_file, known_face_names, known_face_encodings)
            print(" Person registered successfully.")

    process_this_frame = not process_this_frame

video_capture.release()
cv2.destroyAllWindows()
