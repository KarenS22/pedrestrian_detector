from ultralytics import YOLO

# Load the YOLO26 model
model = YOLO("yolov8n.pt")

# Export the model to ONNX format
model.export(format="onnx")  # creates 'yolov8n.onnx'

# Load the exported ONNX model
onnx_model = YOLO("yolov8n.onnx")

# Run inference
results = onnx_model("https://ultralytics.com/images/bus.jpg")