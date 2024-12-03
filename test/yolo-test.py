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

    # Extract bounding boxes,labels and confidence
    boxes = results[0].boxes
    for box in boxes:
      x1, y1, x2, y2 = box.xyxy[0]  # Extract coordinates and confidence
      conf = box.conf[0] # confidence score
      cls = int(box.cls)
      
      if conf > 0.5:
        print("Detect somthing")
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

