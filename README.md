# 🎯 Sistema de Detección de Personas y Postura Humana

**Proyecto Integrador Final - Visión Artificial**  
Universidad Politécnica Salesiana

---

## 📋 Descripción

Sistema inteligente de análisis visual que combina:
- **Detector de personas** (C++ + OpenCV + YOLO)
- **Análisis de postura humana** (Python + PyTorch + MMPose)
- **Bot de Telegram** para notificaciones y procesamiento

### Flujo del Sistema

```
┌─────────────────────────┐
│   Cámara Web            │
│   (Aplicación C++)      │
└───────────┬─────────────┘
            │ Detecta persona (YOLO)
            ↓
┌─────────────────────────┐
│   Captura Imagen/Video  │
└───────────┬─────────────┘
            │ Envía a Bot
            ↓
┌─────────────────────────┐
│   Bot Telegram          │
│   (Python + PyTorch)    │
└───────────┬─────────────┘
            │ Análisis de postura
            ↓
┌─────────────────────────┐
│   Resultados:           │
│   1. Imagen original    │
│   2. Imagen con postura │
│   3. Video animado      │
└─────────────────────────┘
```

---

## 🚀 Instalación

### Prerrequisitos

#### Para C++ (Detector):
- Ubuntu 20.04/22.04/24.04
- OpenCV 4.x con soporte DNN
- CMake 3.15+
- g++ 9+
- libcurl4-openssl-dev

#### Para Python (Bot):
- Python 3.8+
- PyTorch 2.x
- MMPose
- OpenCV-Python

---

### Paso 1: Clonar el Repositorio

```bash
git clone <tu-repo>
cd proyecto-vision-artificial
```

---

### Paso 2: Instalación Python (Bot de Telegram)

```bash
cd bot_telegram

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota sobre MMPose:**
Si tienes problemas con MMPose, instala así:

```bash
# Instalar dependencias de MMPose
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0"
mim install "mmpose>=1.0.0"
```

---

### Paso 3: Configurar Bot de Telegram

1. **Crear Bot en Telegram:**
   - Habla con [@BotFather](https://t.me/botfather)
   - Envía `/newbot`
   - Sigue las instrucciones
   - Guarda el **token** que te dan

2. **Obtener tu Chat ID:**
   ```bash
   # Envía un mensaje a tu bot en Telegram, luego:
   curl https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   
   # Busca "chat":{"id":12345678}
   ```

3. **Configurar variables:**
   ```bash
   # Crear archivo .env (recomendado)
   echo "TELEGRAM_BOT_TOKEN=tu_token_aqui" > .env
   echo "TELEGRAM_CHAT_ID=tu_chat_id_aqui" >> .env
   ```

   O editar directamente `bot_telegram/config.py`:
   ```python
   TELEGRAM_BOT_TOKEN = "tu_token_aqui"
   ```

---

### Paso 4: Instalación C++ (Detector)

```bash
cd detector_cpp

# Instalar dependencias
sudo apt update
sudo apt install -y \
    build-essential \
    cmake \
    libopencv-dev \
    libcurl4-openssl-dev
```

**Descargar modelo YOLO:**

```bash
# Crear directorio de modelos
mkdir -p models
cd models

# Opción 1: YOLOv8 Nano (más rápido, 6MB)
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx

# Opción 2: YOLOv8 Small (más preciso, 22MB)
# wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.onnx

cd ..
```

**Compilar:**

```bash
mkdir build
cd build
cmake ..
make -j$(nproc)
```

---

### Paso 5: Configurar Detector C++

Editar `detector_cpp/config.hpp`:

```cpp
// Telegram
const std::string TELEGRAM_BOT_TOKEN = "tu_token_aqui";
const std::string TELEGRAM_CHAT_ID = "tu_chat_id_aqui";

// Modelo (si descargaste otro)
const std::string YOLO_MODEL_PATH = "../models/yolov8n.onnx";
```

---

## ▶️ Ejecución

### Opción 1: Ejecutar ambos componentes

**Terminal 1 - Bot de Telegram:**
```bash
cd bot_telegram
source venv/bin/activate
python main.py
```

**Terminal 2 - Detector C++:**
```bash
cd detector_cpp/build
./person_detector
```

### Opción 2: Ejecutar solo el Bot (para testing)

```bash
cd bot_telegram
source venv/bin/activate
python main.py

# En Telegram, envía una imagen manualmente al bot
```

---

## 🎮 Uso

### Detector C++ (Aplicación de Escritorio)

**Controles:**
- `q` o `ESC` - Salir
- `s` - Capturar screenshot manual

**Funcionamiento:**
1. La cámara se inicia automáticamente
2. Cuando detecta una persona:
   - Guarda imagen en `outputs/detections/`
   - Inicia grabación de video (5s)
   - Envía todo al Bot de Telegram

### Bot de Telegram

**Comandos:**
- `/start` - Iniciar bot
- `/help` - Ayuda
- `/stats` - Ver estadísticas

**Uso manual:**
1. Envía una imagen con personas
2. El bot detectará posturas automáticamente
3. Recibirás 3 archivos:
   - Imagen original
   - Imagen con esqueleto de postura
   - Video animado (5s)

---

## 📊 Estructura de Salidas

```
outputs/
├── detections/        # Imágenes capturadas por el detector C++
│   ├── detection_20260209_143052.jpg
│   └── video_20260209_143052.mp4
├── poses/            # Imágenes con posturas detectadas
│   └── pose_20260209_143105.jpg
└── videos/           # Videos generados
    └── clip_20260209_143105.mp4
```

---

## 🔧 Troubleshooting

### Problema: "Error cargando modelo YOLO"
```bash
# Verifica que el archivo existe
ls -lh detector_cpp/models/yolov8n.onnx

# Si no existe, descárgalo
cd detector_cpp/models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx
```

### Problema: "No se pudo conectar con Telegram"
```bash
# Verifica tu token
curl https://api.telegram.org/bot<TU_TOKEN>/getMe

# Si ves "ok":true, el token funciona
```

### Problema: "ModuleNotFoundError: No module named 'mmpose'"
```bash
pip install -U openmim
mim install "mmpose>=1.0.0"
```

### Problema: Cámara no detectada
```bash
# Listar cámaras disponibles
ls /dev/video*

# Cambiar índice en config.hpp
const int CAMERA_INDEX = 0;  // Prueba con 0, 1, 2...
```

### Problema: FPS muy bajo
```bash
# Usar modelo más pequeño
# En config.hpp, cambiar a yolov8n.onnx (nano)

# O reducir resolución de cámara
const int CAMERA_WIDTH = 640;
const int CAMERA_HEIGHT = 480;
```

---

## 📈 Métricas y Evaluación

El sistema genera automáticamente:

### Detector C++:
- FPS en tiempo real
- Tiempo de inferencia promedio
- Total de personas detectadas
- Imágenes y videos enviados

### Bot de Telegram:
- Número de posturas detectadas
- Confianza promedio de keypoints
- Análisis de tipo de postura (erguida, agachada, caída)

---

## 🎓 Para el Informe

### Datos a incluir:

**Precisión del detector:**
- Usar dataset de validación
- Calcular Precision, Recall, F1-Score
- Matriz de confusión

**Rendimiento:**
- FPS promedio
- Tiempo de inferencia (ms)
- Uso de memoria RAM
- Comparación YOLO vs HOG+SVM (si implementaste ambos)

**Detección de Postura:**
- Precisión de keypoints (% correctos)
- Tipos de posturas detectadas correctamente
- Casos fallidos y análisis

### Gráficas recomendadas:
```python
# Ejemplo para generar gráficas
import matplotlib.pyplot as plt

# Gráfica de FPS
plt.plot(fps_values)
plt.title('FPS en el tiempo')
plt.ylabel('FPS')
plt.xlabel('Frame')
plt.savefig('fps_graph.png')
```

---

## 📝 To-Do para Máxima Puntuación

- [x] Detector funcional en C++
- [x] Integración con Bot de Telegram
- [x] Detección de postura con PyTorch
- [x] Generación de 3 archivos (imagen, pose, video)
- [ ] Entrenar HOG+SVM/LBP (opcional, para comparar)
- [ ] Recopilar métricas de rendimiento
- [ ] Generar dataset de pruebas
- [ ] Crear matriz de confusión
- [ ] Video-blog en inglés
- [ ] Informe técnico completo

---

## 📚 Referencias

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [MMPose Documentation](https://mmpose.readthedocs.io/)
- [OpenCV DNN Module](https://docs.opencv.org/4.x/d2/d58/tutorial_table_of_content_dnn.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 👥 Autores

- **Grupo:** [Tu grupo]
- **Integrantes:** [Nombres]
- **Docente:** Ing. Vladimir Robles Bykbaev
- **Materia:** Visión Artificial
- **Período:** Octubre 2025 - Febrero 2026

---

## 📄 Licencia

Este proyecto es para fines académicos - Universidad Politécnica Salesiana
# pedrestrian_detector
