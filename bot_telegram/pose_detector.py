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
    from mmpose.apis import init_model, inference_topdown
    from mmpose.structures import merge_data_samples
    MMPOSE_AVAILABLE = True
except ImportError:
    logger.warning("MMPose no disponible. Usando detección simulada.")
    MMPOSE_AVAILABLE = False

from config import (
    POSE_MODEL_CONFIG,
    COCO_KEYPOINTS,
    SKELETON_CONNECTIONS,
    VISUALIZATION_CONFIG
)


class PoseDetector:
    """Detector de postura humana usando MMPose"""
    
    def __init__(self):
        self.device = POSE_MODEL_CONFIG['device']
        self.conf_threshold = POSE_MODEL_CONFIG['conf_threshold']
        self.model = None
        
        # Intentar cargar modelo real
        if MMPOSE_AVAILABLE:
            self._load_model()
        else:
            logger.warning("Usando modo simulado (sin MMPose)")
    
    def _load_model(self):
        """Cargar modelo MMPose"""
        try:
            # Configuración para HRNet
            config_file = 'https://download.openmmlab.com/mmpose/v1/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w48_8xb32-210e_coco-256x192_20220915-a3f6a4c6.py'
            checkpoint_file = 'https://download.openmmlab.com/mmpose/v1/body_2d_keypoint/topdown_heatmap/coco/td-hm_hrnet-w48_8xb32-210e_coco-256x192_20220915-a3f6a4c6.pth'
            
            self.model = init_model(
                config_file,
                checkpoint_file,
                device=self.device
            )
            logger.info(f"Modelo cargado en {self.device}")
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            self.model = None
    
    def detect_pose(self, image: np.ndarray, bboxes: List[List[float]] = None) -> Dict:
        """
        Detectar posturas en la imagen
        
        Args:
            image: Imagen BGR (numpy array)
            bboxes: Lista de bounding boxes [[x1, y1, x2, y2], ...]
                   Si es None, se asume toda la imagen
        
        Returns:
            Dict con keypoints, scores y metadata
        """
        if self.model is None or not MMPOSE_AVAILABLE:
            return self._simulate_detection(image, bboxes)
        
        try:
            # Si no hay bboxes, detectar en toda la imagen
            if bboxes is None or len(bboxes) == 0:
                h, w = image.shape[:2]
                bboxes = [[0, 0, w, h]]
            
            # Preparar datos de entrada
            batch_data = []
            for bbox in bboxes:
                data_info = {
                    'img': image,
                    'bbox': np.array(bbox, dtype=np.float32),
                    'bbox_score': 1.0
                }
                batch_data.append(data_info)
            
            # Inferencia
            results = inference_topdown(self.model, image, bboxes)
            
            # Procesar resultados
            keypoints_list = []
            scores_list = []
            
            for result in results:
                keypoints = result.pred_instances.keypoints[0]  # (17, 2)
                scores = result.pred_instances.keypoint_scores[0]  # (17,)
                
                keypoints_list.append(keypoints)
                scores_list.append(scores)
            
            return {
                'keypoints': keypoints_list,
                'scores': scores_list,
                'num_persons': len(keypoints_list),
                'image_shape': image.shape[:2]
            }
            
        except Exception as e:
            logger.error(f"Error en detección: {e}")
            return self._simulate_detection(image, bboxes)
    
    def _simulate_detection(self, image: np.ndarray, bboxes: List = None) -> Dict:
        """Simulación de detección para testing sin MMPose"""
        h, w = image.shape[:2]
        
        if bboxes is None or len(bboxes) == 0:
            num_persons = 1
            # Simular keypoints en el centro
            keypoints = np.array([
                [w*0.5, h*0.2],   # nose
                [w*0.48, h*0.18], # left_eye
                [w*0.52, h*0.18], # right_eye
                [w*0.46, h*0.2],  # left_ear
                [w*0.54, h*0.2],  # right_ear
                [w*0.45, h*0.35], # left_shoulder
                [w*0.55, h*0.35], # right_shoulder
                [w*0.42, h*0.5],  # left_elbow
                [w*0.58, h*0.5],  # right_elbow
                [w*0.40, h*0.65], # left_wrist
                [w*0.60, h*0.65], # right_wrist
                [w*0.46, h*0.6],  # left_hip
                [w*0.54, h*0.6],  # right_hip
                [w*0.45, h*0.75], # left_knee
                [w*0.55, h*0.75], # right_knee
                [w*0.44, h*0.9],  # left_ankle
                [w*0.56, h*0.9],  # right_ankle
            ], dtype=np.float32)
            keypoints_list = [keypoints]
        else:
            num_persons = len(bboxes)
            keypoints_list = []
            for bbox in bboxes:
                x1, y1, x2, y2 = bbox
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                # Simular keypoints relativos al bbox
                keypoints = np.array([
                    [cx, y1 + (y2-y1)*0.1],
                    [cx - (x2-x1)*0.05, y1 + (y2-y1)*0.08],
                    [cx + (x2-x1)*0.05, y1 + (y2-y1)*0.08],
                    # ... (simplificado para simulación)
                ] + [[cx, cy]] * 14, dtype=np.float32)
                keypoints_list.append(keypoints)
        
        scores_list = [np.ones(17) * 0.9 for _ in range(num_persons)]
        
        return {
            'keypoints': keypoints_list,
            'scores': scores_list,
            'num_persons': num_persons,
            'image_shape': (h, w)
        }
    
    def draw_pose(self, image: np.ndarray, detection_result: Dict) -> np.ndarray:
        """
        Dibujar posturas detectadas en la imagen
        
        Args:
            image: Imagen original
            detection_result: Resultado de detect_pose()
        
        Returns:
            Imagen con posturas dibujadas
        """
        img_pose = image.copy()
        
        keypoints_list = detection_result['keypoints']
        scores_list = detection_result['scores']
        
        for keypoints, scores in zip(keypoints_list, scores_list):
            # Dibujar conexiones (esqueleto)
            for connection in SKELETON_CONNECTIONS:
                idx1, idx2 = connection
                if scores[idx1] > self.conf_threshold and scores[idx2] > self.conf_threshold:
                    pt1 = tuple(map(int, keypoints[idx1]))
                    pt2 = tuple(map(int, keypoints[idx2]))
                    cv2.line(
                        img_pose,
                        pt1,
                        pt2,
                        VISUALIZATION_CONFIG['skeleton_color'],
                        VISUALIZATION_CONFIG['line_thickness']
                    )
            
            # Dibujar keypoints
            for idx, (keypoint, score) in enumerate(zip(keypoints, scores)):
                if score > self.conf_threshold:
                    pt = tuple(map(int, keypoint))
                    cv2.circle(
                        img_pose,
                        pt,
                        VISUALIZATION_CONFIG['keypoint_radius'],
                        VISUALIZATION_CONFIG['keypoint_color'],
                        -1
                    )
                    # Opcional: agregar etiquetas
                    # cv2.putText(img_pose, COCO_KEYPOINTS[idx], pt, ...)
        
        # Agregar contador de personas
        num_persons = detection_result['num_persons']
        text = f"Personas detectadas: {num_persons}"
        cv2.putText(
            img_pose,
            text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            VISUALIZATION_CONFIG['font_scale'],
            VISUALIZATION_CONFIG['text_color'],
            2
        )
        
        return img_pose
    
    def analyze_posture(self, detection_result: Dict) -> List[str]:
        """
        Analizar tipo de postura (erguida, agachada, caída, etc.)
        
        Returns:
            Lista de descripciones de postura para cada persona
        """
        postures = []
        
        for keypoints, scores in zip(
            detection_result['keypoints'],
            detection_result['scores']
        ):
            # Calcular ángulos y posiciones
            nose = keypoints[0]
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]
            right_hip = keypoints[12]
            left_ankle = keypoints[15]
            right_ankle = keypoints[16]
            
            # Centro de hombros y caderas
            shoulder_center = (left_shoulder + right_shoulder) / 2
            hip_center = (left_hip + right_hip) / 2
            
            # Altura relativa
            torso_height = np.linalg.norm(shoulder_center - hip_center)
            total_height = np.linalg.norm(nose - (left_ankle + right_ankle) / 2)
            
            # Clasificación simple de postura
            if total_height < 100:  # Muy bajo
                posture = "Caída o agachada"
            elif torso_height / total_height > 0.4:
                posture = "Erguida"
            elif torso_height / total_height > 0.25:
                posture = "Inclinada"
            else:
                posture = "Agachada"
            
            postures.append(posture)
        
        return postures
    
    def get_statistics(self, detection_result: Dict) -> Dict:
        """Obtener estadísticas de la detección"""
        keypoints_list = detection_result['keypoints']
        scores_list = detection_result['scores']
        
        total_keypoints = sum(len(kp) for kp in keypoints_list)
        avg_confidence = np.mean([s.mean() for s in scores_list]) if scores_list else 0
        
        return {
            'num_persons': detection_result['num_persons'],
            'total_keypoints': total_keypoints,
            'avg_confidence': float(avg_confidence),
            'keypoints_per_person': 17
        }
