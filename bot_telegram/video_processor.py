"""
Módulo de Procesamiento de Video para Detección de Postura
"""
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
import logging
from datetime import datetime

try:
    from moviepy.editor import ImageSequenceClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    logging.warning("MoviePy no disponible. Videos limitados.")
    MOVIEPY_AVAILABLE = False

from config import VIDEO_CONFIG, VIDEOS_DIR

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Procesador de videos con detección de postura"""
    
    def __init__(self, pose_detector):
        self.pose_detector = pose_detector
        self.fps = VIDEO_CONFIG['fps']
        self.duration = VIDEO_CONFIG['duration']
        self.video_format = VIDEO_CONFIG['format']
    
    def process_video_file(self, video_path: str, output_dir: Path = None) -> Tuple[str, str]:
        """
        Procesar archivo de video completo
        
        Args:
            video_path: Ruta al video de entrada
            output_dir: Directorio de salida
        
        Returns:
            (path_original_video, path_pose_video)
        """
        if output_dir is None:
            output_dir = VIDEOS_DIR
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")
        
        # Propiedades del video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Procesando video: {total_frames} frames @ {fps} FPS")
        
        # Preparar output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"pose_detection_{timestamp}.mp4"
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        
        frames_processed = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detectar postura
            detection_result = self.pose_detector.detect_pose(frame)
            
            # Dibujar postura
            frame_with_pose = self.pose_detector.draw_pose(frame, detection_result)
            
            # Escribir frame
            out.write(frame_with_pose)
            frames_processed += 1
            
            if frames_processed % 30 == 0:
                logger.info(f"Procesados {frames_processed}/{total_frames} frames")
        
        cap.release()
        out.release()
        
        logger.info(f"Video procesado: {output_path}")
        
        return video_path, str(output_path)
    
    def create_comparison_video(
        self,
        frames_original: List[np.ndarray],
        frames_pose: List[np.ndarray],
        output_path: str = None
    ) -> str:
        """
        Crear video de comparación lado a lado
        
        Args:
            frames_original: Lista de frames originales
            frames_pose: Lista de frames con posturas
            output_path: Ruta de salida
        
        Returns:
            Ruta al video generado
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(VIDEOS_DIR / f"comparison_{timestamp}.mp4")
        
        if not frames_original or not frames_pose:
            raise ValueError("Las listas de frames no pueden estar vacías")
        
        # Redimensionar si es necesario
        h1, w1 = frames_original[0].shape[:2]
        h2, w2 = frames_pose[0].shape[:2]
        
        target_h = max(h1, h2)
        target_w = w1 + w2
        
        combined_frames = []
        
        for frame_orig, frame_pose in zip(frames_original, frames_pose):
            # Redimensionar frames
            if frame_orig.shape[:2] != (target_h, w1):
                frame_orig = cv2.resize(frame_orig, (w1, target_h))
            if frame_pose.shape[:2] != (target_h, w2):
                frame_pose = cv2.resize(frame_pose, (w2, target_h))
            
            # Combinar lado a lado
            combined = np.hstack([frame_orig, frame_pose])
            
            # Agregar etiquetas
            cv2.putText(combined, "Original", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(combined, "Postura Detectada", (w1 + 10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            combined_frames.append(combined)
        
        # Guardar video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (target_w, target_h))
        
        for frame in combined_frames:
            out.write(frame)
        
        out.release()
        
        logger.info(f"Video de comparación creado: {output_path}")
        
        return output_path
    
    def create_short_clip(
        self,
        image: np.ndarray,
        detection_result: dict,
        duration: float = None
    ) -> str:
        """
        Crear clip corto animado desde una imagen
        (Simula movimiento agregando zoom/desplazamiento)
        
        Args:
            image: Imagen original
            detection_result: Resultado de detección
            duration: Duración en segundos
        
        Returns:
            Ruta al video generado
        """
        if duration is None:
            duration = self.duration
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(VIDEOS_DIR / f"clip_{timestamp}.mp4")
        
        # Generar frames con pose dibujada
        img_with_pose = self.pose_detector.draw_pose(image, detection_result)
        
        h, w = image.shape[:2]
        num_frames = int(duration * self.fps)
        
        frames = []
        
        for i in range(num_frames):
            # Efecto de zoom suave
            scale = 1.0 + 0.1 * np.sin(2 * np.pi * i / num_frames)
            
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            resized = cv2.resize(img_with_pose, (new_w, new_h))
            
            # Centrar
            if new_w > w or new_h > h:
                start_x = (new_w - w) // 2
                start_y = (new_h - h) // 2
                frame = resized[start_y:start_y+h, start_x:start_x+w]
            else:
                frame = cv2.resize(resized, (w, h))
            
            frames.append(frame)
        
        # Guardar video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, self.fps, (w, h))
        
        for frame in frames:
            out.write(frame)
        
        out.release()
        
        logger.info(f"Clip corto creado: {output_path}")
        
        return output_path
    
    def convert_to_gif(self, video_path: str, output_path: str = None) -> str:
        """
        Convertir video a GIF
        
        Args:
            video_path: Ruta al video MP4
            output_path: Ruta de salida del GIF
        
        Returns:
            Ruta al GIF generado
        """
        if not MOVIEPY_AVAILABLE:
            logger.warning("MoviePy no disponible. Retornando video original.")
            return video_path
        
        if output_path is None:
            output_path = video_path.replace('.mp4', '.gif')
        
        try:
            clip = ImageSequenceClip.from_file(video_path, fps=self.fps)
            clip.write_gif(output_path, fps=self.fps, opt='nq')
            logger.info(f"GIF creado: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Error creando GIF: {e}")
            return video_path
    
    def extract_frames(self, video_path: str, max_frames: int = None) -> List[np.ndarray]:
        """
        Extraer frames de un video
        
        Args:
            video_path: Ruta al video
            max_frames: Máximo número de frames a extraer
        
        Returns:
            Lista de frames (numpy arrays)
        """
        cap = cv2.VideoCapture(video_path)
        frames = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames.append(frame)
            
            if max_frames and len(frames) >= max_frames:
                break
        
        cap.release()
        
        logger.info(f"Extraídos {len(frames)} frames de {video_path}")
        
        return frames
    
    def get_video_info(self, video_path: str) -> dict:
        """Obtener información del video"""
        cap = cv2.VideoCapture(video_path)
        
        info = {
            'fps': int(cap.get(cv2.CAP_PROP_FPS)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        
        return info
