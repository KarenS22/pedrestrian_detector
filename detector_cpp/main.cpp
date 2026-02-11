/**
 * Detector de Personas - Aplicación Principal
 * Proyecto Integrador - Visión Artificial
 *
 * Detecta personas usando YOLO.onnx y envía resultados al Bot de Telegram
 */

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <opencv2/dnn.hpp>
#include <opencv2/opencv.hpp>
#include <sstream>

#include "config.hpp"
// #include "utils/telegram_sender.hpp" // REMOVED

namespace fs = std::filesystem;

class PersonDetector {
private:
  cv::HOGDescriptor hog_;
  Config::Stats stats_;

  std::chrono::steady_clock::time_point last_detection_time_;
  bool recording_video_;
  cv::VideoWriter video_writer_;
  std::vector<cv::Mat> video_frames_;

public:
  PersonDetector() : recording_video_(false) {

    // Crear directorios necesarios
    fs::create_directories(Config::DETECTIONS_DIR);
    fs::create_directories(Config::LOGS_DIR);

    // Cargar modelo HOG
    loadModel();

    last_detection_time_ = std::chrono::steady_clock::now();
  }

  void loadModel() {
    std::cout << "Cargando modelo SVM (HOG)..." << std::endl;

    std::vector<float> svm_detector;
    std::ifstream file(Config::SVM_MODEL_PATH);

    if (!file.is_open()) {
      std::cerr << "❌ Error: No se pudo abrir " << Config::SVM_MODEL_PATH
                << std::endl;
      exit(1);
    }

    float weight;
    while (file >> weight) {
      svm_detector.push_back(weight);
    }
    file.close();

    std::cout << "✓ Pesos cargados: " << svm_detector.size() << std::endl;

    // Configurar HOG
    hog_ = cv::HOGDescriptor(Config::WIN_SIZE, Config::BLOCK_SIZE,
                             Config::BLOCK_STRIDE, Config::CELL_SIZE,
                             Config::NBINS);
    hog_.setSVMDetector(svm_detector);

    std::cout << "✓ Modelo HOG configurado correctamente" << std::endl;
  }

  std::vector<cv::Rect> detectPersons(const cv::Mat &frame,
                                      std::vector<float> &confidences) {
    std::vector<cv::Rect> boxes;
    confidences.clear();

    auto start = std::chrono::high_resolution_clock::now();

    // Detección HOG (RAW)
    std::vector<cv::Rect> found_locations;
    std::vector<double> found_weights;

    hog_.detectMultiScale(frame, found_locations, found_weights,
                          Config::HIT_THRESHOLD, Config::WIN_STRIDE,
                          Config::PADDING, Config::SCALE,
                          0.0,  // groupThreshold = 0 para obtener RAW boxes
                          false // useMeanshiftGrouping
    );

    // Convertir a formato para NMS
    std::vector<cv::Rect> temp_boxes;
    std::vector<float> temp_confidences;

    for (size_t i = 0; i < found_locations.size(); ++i) {
      cv::Rect r = found_locations[i];
      // Asegurar limites
      r = r & cv::Rect(0, 0, frame.cols, frame.rows);

      if (r.area() >= Config::MIN_PERSON_AREA) {
        temp_boxes.push_back(r);
        temp_confidences.push_back(static_cast<float>(found_weights[i]));
      }
    }

    // Aplicar NMS
    std::vector<int> indices;
    // score_threshold para NMS (usuario usa 0.4)
    cv::dnn::NMSBoxes(
        temp_boxes, temp_confidences,
        0.4f, // hardcoded 0.4 como en script usuario para NMS filter
        static_cast<float>(Config::NMS_THRESHOLD), indices);

    for (int idx : indices) {
      // Filtro final de score (usuario usa > 0.6)
      if (temp_confidences[idx] > Config::SCORE_THRESHOLD) {
        boxes.push_back(temp_boxes[idx]);
        confidences.push_back(temp_confidences[idx]);
      }
    }

    auto end = std::chrono::high_resolution_clock::now();
    auto duration =
        std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    // Actualizar estadísticas (Moving Average)
    if (stats_.avg_inference_time_ms == 0) {
      stats_.avg_inference_time_ms = duration.count();
    } else {
      stats_.avg_inference_time_ms =
          0.9 * stats_.avg_inference_time_ms + 0.1 * duration.count();
    }

    return boxes;
  }

  void drawDetections(cv::Mat &frame, const std::vector<cv::Rect> &boxes,
                      const std::vector<float> &confidences) {
    for (size_t i = 0; i < boxes.size(); i++) {
      // Dibujar bounding box
      cv::rectangle(frame, boxes[i], Config::BBOX_COLOR,
                    Config::BBOX_THICKNESS);

      // Preparar texto
      std::stringstream ss;
      ss << "Person " << std::fixed << std::setprecision(2) << confidences[i];
      std::string label = ss.str();

      // Calcular tamaño del texto
      int baseline;
      cv::Size text_size = cv::getTextSize(label, cv::FONT_HERSHEY_SIMPLEX,
                                           Config::FONT_SCALE, 2, &baseline);

      // Dibujar fondo del texto
      cv::Point text_pos(boxes[i].x, boxes[i].y - 10);
      cv::rectangle(frame,
                    cv::Point(text_pos.x, text_pos.y - text_size.height - 5),
                    cv::Point(text_pos.x + text_size.width, text_pos.y),
                    Config::TEXT_BG_COLOR, -1);

      // Dibujar texto
      cv::putText(frame, label, text_pos, cv::FONT_HERSHEY_SIMPLEX,
                  Config::FONT_SCALE, Config::TEXT_COLOR, 2);
    }
  }

  void drawStats(cv::Mat &frame, double fps) {
    int y = 30;
    int line_height = 25;

    auto drawStat = [&](const std::string &text) {
      cv::putText(frame, text, cv::Point(10, y), cv::FONT_HERSHEY_SIMPLEX, 0.6,
                  cv::Scalar(0, 255, 0), 2);
      y += line_height;
    };

    std::stringstream ss;
    ss << "FPS: " << std::fixed << std::setprecision(1) << fps;
    drawStat(ss.str());

    ss.str("");
    ss << "Detecciones: " << stats_.total_detections;
    drawStat(ss.str());

    ss.str("");
    ss << "Personas: " << stats_.persons_detected;
    drawStat(ss.str());

    ss.str("");
    ss << "Inference: " << std::fixed << std::setprecision(1)
       << stats_.avg_inference_time_ms << " ms";
    drawStat(ss.str());
  }

  void startVideoRecording(const cv::Mat &first_frame, int fps) {
    if (recording_video_)
      return;

    std::cout << "📹 Iniciando grabación de video..." << std::endl;

    recording_video_ = true;
    video_frames_.clear();
    video_frames_.push_back(first_frame.clone());
  }

  void addVideoFrame(const cv::Mat &frame) {
    if (recording_video_) {
      video_frames_.push_back(frame.clone());
    }
  }

  std::string saveVideo(int fps) {
    if (video_frames_.empty()) {
      return "";
    }

    std::cout << "💾 Guardando video..." << std::endl;

    std::string timestamp = getCurrentTimestamp();
    std::string video_path =
        Config::DETECTIONS_DIR + "video_" + timestamp + ".mp4";

    int fourcc = cv::VideoWriter::fourcc('m', 'p', '4', 'v');
    cv::VideoWriter writer(video_path, fourcc, fps, video_frames_[0].size());

    if (!writer.isOpened()) {
      std::cerr << "Error abriendo VideoWriter" << std::endl;
      return "";
    }

    for (const auto &frame : video_frames_) {
      writer.write(frame);
    }

    writer.release();
    recording_video_ = false;
    video_frames_.clear();

    std::cout << "✓ Video guardado: " << video_path << std::endl;
    return video_path;
  }

  std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&time_t);

    std::stringstream ss;
    ss << std::put_time(&tm, "%Y%m%d_%H%M%S");
    return ss.str();
  }

  void handleDetection(const cv::Mat &frame,
                       const std::vector<cv::Rect> &boxes) {
    auto now = std::chrono::steady_clock::now();
    auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                       now - last_detection_time_)
                       .count();

    // Cooldown para evitar spam
    if (elapsed < Config::DETECTION_COOLDOWN_MS) {
      std::cout << "Waiting for cooldown " << Config::DETECTION_COOLDOWN_MS
                << "ms" << std::endl;
      return;
    }

    std::cout << "\n🎯 DETECCIÓN ACTIVADA - " << boxes.size() << " persona(s)"
              << std::endl;

    stats_.total_detections++;
    stats_.persons_detected += boxes.size();
    last_detection_time_ = now;

    // Guardar imagen
    std::string timestamp = getCurrentTimestamp();
    std::string image_path =
        Config::DETECTIONS_DIR + "detection_" + timestamp + ".jpg";
    cv::imwrite(image_path, frame);
    std::cout << "✓ Imagen guardada: " << image_path << std::endl;

    // Grabar video si está habilitado
    std::string video_path = "";
    if (Config::RECORD_VIDEO) {
      startVideoRecording(frame, 30);
    }

    // Enviar a Telegram mediante HTTP POST al servidor Python

    // Convertir a ruta absoluta para evitar problemas con CWD del servidor
    std::string abs_image_path = fs::absolute(image_path).string();

    // 1. Enviar Imagen
    // curl -X POST "http://localhost:8000/detect" -H "Content-Type:
    // application/json" -d '{"file_path": "..."}'
    std::string command = "curl -X POST \"http://localhost:8000/detect\" "
                          "-H \"Content-Type: application/json\" "
                          "-d '{\"file_path\": \"" +
                          abs_image_path + "\"}' &";

    // Usamos system para curl (simple y no bloqueante con &)
    system(command.c_str());
    std::cout << "⚡ HTTP Request sent for Image: " << abs_image_path
              << std::endl;

    /*
    // El envío directo se deshabilita para usar el bot de Python
    std::stringstream message;
    message << "🚨 ALERTA: Detección de persona\n"
            << "👥 Personas: " << boxes.size() << "\n"
            << "⏰ " << timestamp;

    telegram_.sendDetectionPackage(image_path, video_path, message.str());
    */

    stats_.images_sent++;
    if (!video_path.empty()) {
      std::string abs_video_path = fs::absolute(video_path).string();

      // 2. Enviar Video
      std::string video_command = "curl -X POST \"" +
                                  Config::PYTHON_SERVER_URL +
                                  "\" "
                                  "-H \"Content-Type: application/json\" "
                                  "-d '{\"file_path\": \"" +
                                  abs_video_path + "\"}' &";

      system(video_command.c_str());
      std::cout << "⚡ HTTP Request sent for Video: " << abs_video_path
                << std::endl;

      stats_.videos_sent++;
    }
  }

  void run() {
    std::cout << "\n🎥 Iniciando cámara..." << std::endl;

    // Construir pipeline de GStreamer para forzar MJPG
    // Esto es necesario porque OpenCV a veces falla al negociar el formato
    // correcto
    std::stringstream pipeline;
    pipeline << "v4l2src device=/dev/video" << Config::CAMERA_INDEX
             << " ! image/jpeg,width=" << Config::CAMERA_WIDTH
             << ",height=" << Config::CAMERA_HEIGHT
             << ",framerate=" << Config::CAMERA_FPS << "/1"
             << " ! jpegdec ! videoconvert ! appsink";

    std::cout << "GStreamer pipeline: " << pipeline.str() << std::endl;

    // cv::VideoCapture cap(pipeline.str(), cv::CAP_GSTREAMER);
    cv::VideoCapture cap("../../test_videos/b4.mp4");

    if (!cap.isOpened()) {
      std::cerr << "❌ No se pudo abrir la cámara con GStreamer" << std::endl;
      std::cerr << "   Intentando fallback a V4L2 estándar..." << std::endl;
      cap.open(Config::CAMERA_INDEX, cv::CAP_V4L2);

      if (!cap.isOpened()) {
        std::cerr << "❌ Fallback también falló. Verifica conexión."
                  << std::endl;
        return;
      }

      // Configuración básica para fallback
      cap.set(cv::CAP_PROP_FRAME_WIDTH, Config::CAMERA_WIDTH);
      cap.set(cv::CAP_PROP_FRAME_HEIGHT, Config::CAMERA_HEIGHT);
      cap.set(cv::CAP_PROP_FPS, Config::CAMERA_FPS);
    }

    // Verificar configuración real
    double width = cap.get(cv::CAP_PROP_FRAME_WIDTH);
    double height = cap.get(cv::CAP_PROP_FRAME_HEIGHT);
    double initial_fps = cap.get(cv::CAP_PROP_FPS);

    std::cout << "✓ Cámara iniciada: " << width << "x" << height << " @ "
              << initial_fps << " FPS" << std::endl;
    std::cout << "\n=== DETECTOR DE PERSONAS ACTIVO ===" << std::endl;
    std::cout << "Presiona 'q' para salir\n" << std::endl;

    cv::Mat frame;
    auto fps_start = std::chrono::steady_clock::now();
    int frame_count = 0;
    double fps = 0.0;

    while (true) {
      cap >> frame;

      if (frame.empty()) {
        std::cerr << "Frame vacío" << std::endl;
        break;
      }

      // Detectar personas
      std::vector<float> confidences;
      std::vector<cv::Rect> boxes = detectPersons(frame, confidences);

      // Dibujar detecciones
      cv::Mat display_frame = frame.clone();
      drawDetections(display_frame, boxes, confidences);

      // Calcular FPS
      frame_count++;
      auto fps_now = std::chrono::steady_clock::now();
      auto fps_elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
                             fps_now - fps_start)
                             .count();

      if (fps_elapsed >= 1000) {
        fps = frame_count * 1000.0 / fps_elapsed;
        stats_.avg_fps = fps;
        frame_count = 0;
        fps_start = fps_now;
      }

      // Dibujar estadísticas
      drawStats(display_frame, fps);

      // Si está grabando video
      std::string finished_video_path = "";
      if (recording_video_) {
        addVideoFrame(display_frame);

        // Detener después de N segundos
        if (video_frames_.size() >= Config::VIDEO_DURATION_SECONDS * 30) {
          finished_video_path = saveVideo(30);
          if (!finished_video_path.empty()) {
            stats_.videos_sent++;
          }
        }
      }

      // Manejar detección
      // Si tenemos un video recién terminado, forzamos el envío aunque no haya
      // caja en este frame exacto? No, la lógica es: si hay cajas, se envía
      // foto. Si ADEMAS hay video listo, se envía video. Pero si el video
      // termina justo cuando no hay cajas, ¿qué pasa? El usuario quiere que
      // "python igual envie el video". Lo mejor es: si hay video, enviarlo
      // independientemente de si hay cajas en ESTE frame.

      if (!finished_video_path.empty()) {
        std::string abs_video_path = fs::absolute(finished_video_path).string();
        std::string video_command = "curl -X POST \"" +
                                    Config::PYTHON_SERVER_URL +
                                    "\" "
                                    "-H \"Content-Type: application/json\" "
                                    "-d '{\"file_path\": \"" +
                                    abs_video_path + "\"}' &";

        system(video_command.c_str());
        std::cout << "⚡ HTTP Request sent for Video: " << abs_video_path
                  << std::endl;
      }

      if (!boxes.empty() && !recording_video_) {
        // Pasamos string vacío para video porque ya lo manejamos arriba si
        // existía
        handleDetection(display_frame, boxes);
      }

      // Mostrar preview
      if (Config::SHOW_PREVIEW) {
        cv::imshow("Detector de Personas", display_frame);
      }

      // Controles de teclado
      char key = cv::waitKey(1);
      if (key == 'q' || key == 27) { // 'q' o ESC
        break;
      } else if (key == 's') { // Screenshot manual
        std::string path =
            Config::DETECTIONS_DIR + "manual_" + getCurrentTimestamp() + ".jpg";
        cv::imwrite(path, display_frame);
        std::cout << "📸 Screenshot: " << path << std::endl;
      }
    }

    cap.release();
    cv::destroyAllWindows();

    printFinalStats();
  }

  void printFinalStats() {
    std::cout << "\n=== ESTADÍSTICAS FINALES ===" << std::endl;
    std::cout << "Total detecciones: " << stats_.total_detections << std::endl;
    std::cout << "Personas detectadas: " << stats_.persons_detected
              << std::endl;
    std::cout << "Imágenes enviadas: " << stats_.images_sent << std::endl;
    std::cout << "Videos enviados: " << stats_.videos_sent << std::endl;
    std::cout << "FPS promedio: " << std::fixed << std::setprecision(1)
              << stats_.avg_fps << std::endl;
    std::cout << "Tiempo inferencia promedio: " << std::fixed
              << std::setprecision(1) << stats_.avg_inference_time_ms << " ms"
              << std::endl;
  }
};

int main() {
  try {
    PersonDetector detector;
    detector.run();
  } catch (const std::exception &e) {
    std::cerr << "Error: " << e.what() << std::endl;
    return 1;
  }

  return 0;
}
