import cv2
import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2, Preview


# Load TFLite model and allocate tensors.
interpreter = tflite.Interpreter(model_path="face_detection_front.tflite",
    experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')])
interpreter.allocate_tensors()

# Get input and output tensors.
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape']

picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()


while True:

    frame = picam2.capture_array()
    h, w, _ = frame.shape

    img_resized = cv2.resize(frame, (input_shape[2], input_shape[1]))

    # Convert the image to numpy array
    input_data = np.expand_dims(img_resized.astype(np.float32), axis=0)

    # normalize 
    input_data = input_data / 255.0

    # Set the tensor to point to the input to be inferred 
    interpreter.set_tensor(input_details[0]['index'], input_data)

    # run the inference
    interpreter.invoke()

    detections = interpreter.get_tensor(output_details[0]['index'])[0]
    confidences = interpreter.get_tensor(output_details[1]['index'])[0]

    print(f"Confidences: {confidences}")
    print(f"Detections: {detections}")
    
    for i in range(len(confidences)):
        if confidences[i] > 0.6:
            print(f"Face Detect")
            ymin, xmin, ymax, xmax = detections[i][:4]
            ymin = max(0.0, min(1.0, ymin))
            xmin = max(0.0, min(1.0, xmin))
            ymax = max(0.0, min(1.0, ymax))
            xmax = max(0.0, min(1.0, xmax))
            x1, y1 = int(xmin * w), int(ymin * h)
            x2, y2 = int(xmax * w), int(ymax * h)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.imshow("Detection", frame)
    if cv2.waitKey(1) == 27:
        break

cv2.destroyAllWindows()