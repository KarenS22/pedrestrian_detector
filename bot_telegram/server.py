import logging
import os
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import asyncio

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OUTPUTS_DIR, DETECTIONS_DIR, POSES_DIR
from pose_detector import PoseDetector
from video_processor import VideoProcessor
from telegram import Bot
import json
    

SUBSCRIBERS_FILE = "subscribers.json"

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)


# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pose_detector, video_processor, telegram_bot
    logger.info("Iniciando servidor y cargando modelos...")
    
    pose_detector = PoseDetector()
    video_processor = VideoProcessor(pose_detector)
    telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    logger.info("Servidor listo para recibir peticiones.")
    yield
    logger.info("Cerrando servidor...")

app = FastAPI(title="Pose Detection Server", lifespan=lifespan)

# Modelos y utilidades (se cargan al inicio)
pose_detector = None
video_processor = None
telegram_bot = None

class DetectionRequest(BaseModel):
    file_path: str

@app.get("/")
async def root():
    return {"status": "running", "message": "Pose Detection Server is active"}

@app.post("/detect")
async def detect_pose(request: DetectionRequest):
    file_path = Path(request.file_path)
    
    if not file_path.exists():
        # Incluso si no existe, devolvemos 404 pero queremos asegurarnos que es nuestra lógica
        logger.warning(f"Archivo no encontrado: {file_path}")
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")
    
    logger.info(f"Recibida petición para: {file_path}")
    
    # Procesar en background para no bloquear
    try:
        lower_suffix = file_path.suffix.lower()
        if lower_suffix in ['.jpg', '.jpeg', '.png']:
            await process_image(file_path)
        elif lower_suffix in ['.mp4', '.avi', '.mov', '.mkv']:
            await process_video(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Formato no soportado: {lower_suffix}")
            
        return {"status": "success", "message": "Procesado correctamente"}
        
    except Exception as e:
        logger.error(f"Error procesando: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def process_image(image_path: Path):
    import cv2
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Error leyendo imagen")

    # Detectar
    detection_result = pose_detector.detect_pose(image)
    num_persons = detection_result['num_persons']
    
    # Dibujar y guardar
    image_with_pose = pose_detector.draw_pose(image, detection_result)
    timestamp = image_path.stem.replace('detection_', '')
    pose_image_path = POSES_DIR / f"pose_{timestamp}.jpg"
    cv2.imwrite(str(pose_image_path), image_with_pose)
    
    # Análisis
    postures = pose_detector.analyze_posture(detection_result)
    posture_text = "\n".join([f"Persona {i+1}: {p}" for i, p in enumerate(postures)])

    # Enviar a Telegram
    try:
        with open(image_path, 'rb') as f:
            suscribers = load_subscribers()
            for chat_id in suscribers:
                await telegram_bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption="📷 **Detección Original**",
                    parse_mode='Markdown'
                )
            
        caption = f"🎯 **Análisis de Postura**\n👥 Personas: {num_persons}\n🧘 Posturas:\n{posture_text}"
        
        with open(pose_image_path, 'rb') as f:
            suscribers = load_subscribers()
            for chat_id in suscribers:
                await telegram_bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
    except Exception as e:
        logger.error(f"Error enviando a Telegram: {e}")

async def process_video(video_path: Path):
    try:
        suscribers = load_subscribers()
        for chat_id in suscribers:
            await telegram_bot.send_message(chat_id=chat_id, text="🎥 Procesando video...")
        
        # Procesar
        _, pose_video_path = video_processor.process_video_file(str(video_path))
        video_info = video_processor.get_video_info(pose_video_path)
        
        # Enviar
        caption = f"🎥 **Video Analizado**\n⏱️ Duración: {video_info.get('duration', 0):.1f}s"
        
        with open(pose_video_path, 'rb') as f:
            for chat_id in suscribers:
                await telegram_bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    caption=caption,
                    parse_mode='Markdown'
                )
    except Exception as e:
        logger.error(f"Error procesando video: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
