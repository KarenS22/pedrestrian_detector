"""
Configuración del Bot de Telegram para Detección de Postura Humana
"""
import os
from pathlib import Path

# ============= TELEGRAM =============
from dotenv import load_dotenv

load_dotenv()

# ============= TELEGRAM =============
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = "1623681551"  # ID del usuario principal
ALLOWED_USER_IDS = [int(TELEGRAM_CHAT_ID)]  # Lista de IDs de usuarios permitidos

# ============= RUTAS =============
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / 'models'
OUTPUTS_DIR = BASE_DIR.parent / 'outputs'
DETECTIONS_DIR = OUTPUTS_DIR / 'detections'
POSES_DIR = OUTPUTS_DIR / 'poses'
VIDEOS_DIR = OUTPUTS_DIR / 'videos'

# Crear directorios si no existen
for directory in [OUTPUTS_DIR, DETECTIONS_DIR, POSES_DIR, VIDEOS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============= MODELO DE POSTURA =============
POSE_MODEL_CONFIG = {
    'model_name': 'hrnet_w48_coco_256x192',  # Opciones: hrnet, openpose, etc.
    'checkpoint': str(MODELS_DIR / 'pose_hrnet_w48.pth'),
    'device': 'cuda',  # 'cuda' o 'cpu'
    'conf_threshold': 0.3,  # Umbral de confianza para keypoints
}

# ============= DETECCIÓN DE POSTURA (MEDIAPIPE) =============
# Keypoints MediaPipe (33 puntos)
COCO_KEYPOINTS = [
    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer', 
    'right_eye_inner', 'right_eye', 'right_eye_outer',
    'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
    'left_index', 'right_index', 'left_thumb', 'right_thumb',
    'left_hip', 'right_hip', 'left_knee', 'right_knee',
    'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
    'left_foot_index', 'right_foot_index'
]

# Conexiones para dibujar el esqueleto (MediaPipe)
SKELETON_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), # Cara
    (9, 10), (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), # Brazo Izq
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), # Brazo Der
    (11, 23), (12, 24), (23, 24), # Torso
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31), # Pierna Izq
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32)  # Pierna Der
]

# ============= VIDEO =============
VIDEO_CONFIG = {
    'fps': 15,
    'duration': 5,  # segundos
    'format': 'mp4',  # 'mp4' o 'gif'
    'quality': 8,  # 1-10 (10 = mejor calidad)
}

# ============= VISUALIZACIÓN =============
VISUALIZATION_CONFIG = {
    'skeleton_color': (0, 255, 0),  # Verde (BGR)
    'keypoint_color': (0, 0, 255),  # Rojo (BGR)
    'line_thickness': 2,
    'keypoint_radius': 4,
    'text_color': (255, 255, 255),  # Blanco
    'font_scale': 0.6,
}

# ============= MENSAJES =============
MESSAGES = {
    'detection_received': '✅ Detección recibida. Analizando postura...',
    'processing': '⏳ Procesando imagen/video...',
    'pose_detected': '🎯 Postura detectada: {} persona(s)',
    'sending_results': '📤 Enviando resultados...',
    'error': '❌ Error: {}',
    'welcome': '''
🤖 Bot de Detección de Postura Humana

Envía una imagen o video con personas y analizaré su postura.

Comandos disponibles:
/start - Iniciar el bot
/help - Ayuda
/stats - Estadísticas
''',
}
