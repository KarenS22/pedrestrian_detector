/**
 * Configuración del Detector de Personas C++
 * Proyecto Integrador - Visión Artificial
 */

#ifndef CONFIG_HPP
#define CONFIG_HPP

#include <opencv2/opencv.hpp>
#include <string>
#include <vector>

namespace Config {

// ============= SERVIDOR PYTHON =============
const std::string PYTHON_SERVER_URL = "http://localhost:8000/detect";

// ============= MODELO YOLO =============
const std::string YOLO_MODEL_PATH = "../models/yolov8n.onnx";
const float CONFIDENCE_THRESHOLD = 0.7f;
const float NMS_THRESHOLD = 0.4f;
const int INPUT_WIDTH = 640;
const int INPUT_HEIGHT = 640;

// Clase "person" en COCO dataset
const int PERSON_CLASS_ID = 0;

// ============= CÁMARA =============
const int CAMERA_INDEX = 2;
const int CAMERA_WIDTH = 1280;
const int CAMERA_HEIGHT = 720;
const int CAMERA_FPS = 30;

// ============= DETECCIÓN =============
const int DETECTION_COOLDOWN_MS = 10000; // Esperar 3s entre detecciones
const int MIN_PERSON_AREA = 5000; // Área mínima para considerar detección
const bool SHOW_PREVIEW = true;   // Mostrar preview en tiempo real

// ============= VIDEO RECORDING =============
const bool RECORD_VIDEO = true;
const int VIDEO_DURATION_SECONDS = 5;
const std::string VIDEO_CODEC = "avc1"; // H.264
const std::string TEMP_VIDEO_PATH = "../../outputs/temp_video.mp4";

// ============= RUTAS =============
const std::string OUTPUTS_DIR = "../../outputs/";
const std::string DETECTIONS_DIR = "../../outputs/detections/";
const std::string LOGS_DIR = "../../outputs/logs/";

// ============= VISUALIZACIÓN =============
const cv::Scalar BBOX_COLOR = cv::Scalar(0, 255, 0); // Verde
const int BBOX_THICKNESS = 2;
const float FONT_SCALE = 0.7f;
const cv::Scalar TEXT_COLOR = cv::Scalar(255, 255, 255); // Blanco
const cv::Scalar TEXT_BG_COLOR = cv::Scalar(0, 0, 0);    // Negro

// ============= ESTADÍSTICAS =============
struct Stats {
  int total_detections = 0;
  int persons_detected = 0;
  int images_sent = 0;
  int videos_sent = 0;
  double avg_fps = 0.0;
  double avg_inference_time_ms = 0.0;
};

// ============= CLASES COCO =============
const std::vector<std::string> COCO_CLASSES = {
    "person",        "bicycle",      "car",
    "motorcycle",    "airplane",     "bus",
    "train",         "truck",        "boat",
    "traffic light", "fire hydrant", "stop sign",
    "parking meter", "bench",        "bird",
    "cat",           "dog",          "horse",
    "sheep",         "cow",          "elephant",
    "bear",          "zebra",        "giraffe",
    "backpack",      "umbrella",     "handbag",
    "tie",           "suitcase",     "frisbee",
    "skis",          "snowboard",    "sports ball",
    "kite",          "baseball bat", "baseball glove",
    "skateboard",    "surfboard",    "tennis racket",
    "bottle",        "wine glass",   "cup",
    "fork",          "knife",        "spoon",
    "bowl",          "banana",       "apple",
    "sandwich",      "orange",       "broccoli",
    "carrot",        "hot dog",      "pizza",
    "donut",         "cake",         "chair",
    "couch",         "potted plant", "bed",
    "dining table",  "toilet",       "tv",
    "laptop",        "mouse",        "remote",
    "keyboard",      "cell phone",   "microwave",
    "oven",          "toaster",      "sink",
    "refrigerator",  "book",         "clock",
    "vase",          "scissors",     "teddy bear",
    "hair drier",    "toothbrush"};

} // namespace Config

#endif // CONFIG_HPP
