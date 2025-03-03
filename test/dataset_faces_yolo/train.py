import ultralytics
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

ultralytics.checks()
results = model.train(data="../dataset_faces_yolo/data.yaml", 
                      epochs=10, 
                      imgsz=640, 
                      batch=8,
                      plots=True,
                      ) 