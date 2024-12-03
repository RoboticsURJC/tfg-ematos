from ultralytics import YOLO
import cv2


# Load a pretrained model
model = YOLO("yolo11n.pt")
model.info()

# Check camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera unavailable")
    exit()


while True:
    ret, frame = cap.read()

    if not ret:
      print("Not capture")
      break

    # Show original frame
    cv2.imshow("Original", frame)


    # Predict with the model
    results = model(frame)  # predict on camera video
    

    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
    


# Liberar la cámara y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()

