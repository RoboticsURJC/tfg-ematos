from ultralytics import YOLO

model = YOLO("yolo11n.pt")

results = model.train(data="../dataset_faces_yolo/data.yaml", 
                      epochs=10, 
                      imgsz=640, 
                      plots=True,
                      ) 