from ultralytics import YOLO
import cv2
from facenet_pytorch import MTCNN
import torch

# Load a pretrained model
model = YOLO("yolo11n.pt")
model.info()

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(select_largest = True, device = device)

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

    # Predict with the model
    results = model(frame)  # predict on camera video

    # Extract bounding boxes,labels and confidence
    boxes = results[0].boxes
    for box in boxes:
      x1, y1, x2, y2 = box.xyxy[0]  # Extract coordinates and confidence
      conf = box.conf[0] # confidence score
      cls = int(box.cls)
      
      if cls == 0 and conf > 0.7:  # label 0 is person
        x1, y1, x2, y2 = map(int, box.xyxy[0]) 

        # get only the person bounding
        person_region = frame[y1:y2, x1:x2]

        # use MTCNN to dectect the faces
        faces, probs = mtcnn.detect(person_region, landmarks=False)

        if faces is not None:
          for face in faces:
            fx1, fy1, fx2, fy2 = map(int, face)
            cv2.rectangle(frame, (x1 + fx1, y1 + fy1), (x1 + fx2, y1 + fy2), (0, 0, 255), 2)
            cv2.putText(frame, "Face", (x1 + fx1, y1 + fy1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


        label = f"{model.names[cls]} {conf:.2f}"  # Get class name and confidence
   
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        # Put label on top of the bounding box
        cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.imshow("Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
    


# free the camera and close windows
cap.release()
cv2.destroyAllWindows()

