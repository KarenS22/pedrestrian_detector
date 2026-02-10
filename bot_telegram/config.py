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
ALLOWED_USER_IDS = []  # Lista de IDs de usuarios permitidos (vacío = todos)

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

# ============= DETECCIÓN DE POSTURA =============
# Keypoints COCO (17 puntos)
COCO_KEYPOINTS = [
    'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
    'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
    'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
]

# Conexiones para dibujar el esqueleto
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # Cabeza
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # Brazos
    (5, 11), (6, 12), (11, 12),  # Torso
    (11, 13), (13, 15), (12, 14), (14, 16)  # Piernas
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
