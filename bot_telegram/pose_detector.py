"""
Módulo de Detección de Postura Humana usando MMPose
"""
import cv2
import numpy as np
import torch
from typing import List, Tuple, Dict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MMPOSE_AVAILABLE = True
except ImportError:
    logger.warning("MediaPipe no disponible. Usando detección simulada.")
    MMPOSE_AVAILABLE = False

from config import (
    POSE_MODEL_CONFIG,
    COCO_KEYPOINTS,
    SKELETON_CONNECTIONS,
    VISUALIZATION_CONFIG
)


class PoseDetector:
    """Detector de postura humana usando MediaPipe"""
    
    def __init__(self):
        self.device = POSE_MODEL_CONFIG['device']
        self.conf_threshold = POSE_MODEL_CONFIG['conf_threshold']
        
        # Inicializar MediaPipe Pose
        if MMPOSE_AVAILABLE:
            import mediapipe as mp # Importar aquí para evitar error si no está instalado
            self.mp_pose = mp.solutions.pose
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
            
            # Inicializar detector
            # static_image_mode=True para imágenes, False para video (más fluido)
            # Aquí usaremos True por simplicidad y porque procesamos frames individuales a veces
            self.pose_model = self.mp_pose.Pose(
                static_image_mode=True,
                model_complexity=1, # 0=Lite, 1=Full, 2=Heavy
                enable_segmentation=False,
                min_detection_confidence=0.5
            )
            logger.info("Modelo MediaPipe inicializado")
        else:
            logger.warning("MediaPipe no disponible. Usando modo simulado.")
            self.pose_model = None
    
    def detect_pose(self, image: np.ndarray, bboxes: List[List[float]] = None) -> Dict:
        """
        Detectar posturas en la imagen usando MediaPipe
        Nota: MediaPipe Standard detecta solo a la persona más prominente por defecto.
        """
        if self.pose_model is None or not MMPOSE_AVAILABLE:
            return self._simulate_detection(image, bboxes)
            
        try:
            # MediaPipe requiere RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Inferencia
            results = self.pose_model.process(image_rgb)
            
            keypoints_list = []
            scores_list = []
            
            if results.pose_landmarks:
                # Convertir landmarks a formato similar para compatibilidad
                h, w, _ = image.shape
                keypoints = []
                scores = []
                
                for landmark in results.pose_landmarks.landmark:
                    # Convertir coordenadas normalizadas a píxeles
                    px, py = landmark.x * w, landmark.y * h
                    keypoints.append([px, py])
                    scores.append(landmark.visibility) # Usamos visibilidad como score
                
                keypoints_list.append(np.array(keypoints))
                scores_list.append(np.array(scores))
            
            return {
                'keypoints': keypoints_list,
                'scores': scores_list,
                'num_persons': len(keypoints_list),
                'image_shape': image.shape[:2],
                'raw_results': results # Guardar objeto original para dibujo fácil
            }
            
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return self._simulate_detection(image, bboxes)

    def _simulate_detection(self, image: np.ndarray, bboxes: List = None) -> Dict:
        # Simplificado para mantener compatibilidad si falla MP
        return {
            'keypoints': [],
            'scores': [],
            'num_persons': 0,
            'image_shape': image.shape[:2]
        }
    
    def draw_pose(self, image: np.ndarray, detection_result: Dict) -> np.ndarray:
        """Dibujar usando utilidades de MediaPipe"""
        if 'raw_results' not in detection_result or not MMPOSE_AVAILABLE:
            return image.copy()
            
        img_pose = image.copy()
        results = detection_result['raw_results']
        
        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                img_pose,
                results.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
            )
            
        # Agregar contador
        num_persons = detection_result['num_persons']
        cv2.putText(img_pose, f"MediaPipe: {num_persons} persona", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                   
        return img_pose

    def analyze_posture(self, detection_result: Dict) -> List[str]:
        """Analizar postura basado en landmarks de MediaPipe (33 puntos)"""
        if detection_result['num_persons'] == 0:
            return []
            
        postures = []
        for keypoints in detection_result['keypoints']:
            # Índices MediaPipe:
            # 0: Nariz
            # 11, 12: Hombros
            # 23, 24: Caderas
            # 27, 28: Tobillos
            
            nose = keypoints[0]
            shoulder_y = (keypoints[11][1] + keypoints[12][1]) / 2
            hip_y = (keypoints[23][1] + keypoints[24][1]) / 2
            ankle_y = (keypoints[27][1] + keypoints[28][1]) / 2
            
            # Alturas relativas
            torso_height = abs(hip_y - shoulder_y)
            leg_height = abs(ankle_y - hip_y)
            
            # Lógica simple
            if torso_height < 20: # Muy comprimido
                posture = "Agachada/Caída"
            elif leg_height < torso_height * 0.8: # Piernas dobladas
                posture = "Sentada/Agachada"
            else:
                posture = "Erguida"
                
            postures.append(posture)
            
        return postures

    def get_statistics(self, detection_result: Dict) -> Dict:
        return {
            'num_persons': detection_result['num_persons'],
            'total_keypoints': 33,
            'avg_confidence': 1.0 # Placeholder
        }
