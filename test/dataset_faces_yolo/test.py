from ultralytics import YOLO

model = YOLO('../dataset_faces_yolo/runs/detect/train3/weights/best.pt')
preds = model('../dataset_faces_yolo/dataset/images/test-pro')
preds[4].show()