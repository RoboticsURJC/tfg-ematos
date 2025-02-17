from ultralytics import YOLO

model = YOLO('runs/detect/train11/weights/best.pt')
preds = model('../dataset_faces_yolo/images/train', conf=0.25)
preds[1].show()