import sys
import asyncio
import cv2
import logging
from pathlib import Path
from telegram import Bot
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, OUTPUTS_DIR, DETECTIONS_DIR, POSES_DIR
from pose_detector import PoseDetector
from video_processor import VideoProcessor

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    if len(sys.argv) < 2:
        logger.error("Uso: python trigger_pose.py <ruta_archivo>")
        return

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        logger.error(f"Archivo no encontrado: {file_path}")
        return

    logger.info(f"Procesando archivo: {file_path}")

    # Inicializar bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    # Inicializar detectores
    pose_detector = PoseDetector()
    video_processor = VideoProcessor(pose_detector)

    try:
        # Determinar si es imagen o video
        extension = file_path.suffix.lower()
        
        if extension in ['.jpg', '.jpeg', '.png']:
            await process_image(bot, file_path, pose_detector, video_processor)
        elif extension in ['.mp4', '.avi', '.mov']:
            await process_video(bot, file_path, pose_detector, video_processor)
        else:
            logger.error(f"Formato no soportado: {extension}")

    except Exception as e:
        logger.error(f"Error procesando archivo: {e}")
        # Intentar notificar error
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"❌ Error en procesamiento: {e}")
        except:
            pass

async def process_image(bot, image_path, pose_detector, video_processor):
    logger.info("Procesando imagen...")
    
    # Leer imagen
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("No se pudo leer la imagen")

    # Detectar postura
    detection_result = pose_detector.detect_pose(image)
    num_persons = detection_result['num_persons']
    
    # Dibujar postura
    image_with_pose = pose_detector.draw_pose(image, detection_result)
    
    # Guardar imagen con pose
    timestamp = image_path.stem.replace('detection_', '')
    pose_image_path = POSES_DIR / f"pose_{timestamp}.jpg"
    cv2.imwrite(str(pose_image_path), image_with_pose)
    
    # Analizar posturas
    postures = pose_detector.analyze_posture(detection_result)
    posture_text = "\n".join([f"Persona {i+1}: {p}" for i, p in enumerate(postures)])

    # Crear video corto (opcional, si se desea generar video de una imagen estática)
    # video_path = video_processor.create_short_clip(image, detection_result)

    # 1. Enviar Imagen Original
    with open(image_path, 'rb') as f:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=f,
            caption="📷 **Detección Original**",
            parse_mode='Markdown'
        )

    # 2. Enviar Imagen con Postura
    caption = f"""
🎯 **Análisis de Postura**

👥 Personas: {num_persons}
🧘 Posturas:
{posture_text}
    """
    with open(pose_image_path, 'rb') as f:
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=f,
            caption=caption,
            parse_mode='Markdown'
        )
    
    logger.info("Procesamiento de imagen completado.")

async def process_video(bot, video_path, pose_detector, video_processor):
    logger.info("Procesando video...")
    
    # Send notification
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🎥 Procesando video de detección...")

    # Procesar video
    # Nota: video_processor.process_video_file espera rutas como str
    original_path, pose_video_path = video_processor.process_video_file(str(video_path))
    
    # Obtener info
    video_info = video_processor.get_video_info(pose_video_path)

    # Enviar Video con Postura
    caption = f"""
🎥 **Video Analizado**

⏱️ Duración: {video_info.get('duration', 0):.1f}s
📊 FPS: {video_info.get('fps', 0)}
    """
    
    with open(pose_video_path, 'rb') as f:
        await bot.send_video(
            chat_id=TELEGRAM_CHAT_ID,
            video=f,
            caption=caption,
            parse_mode='Markdown'
        )
        
    logger.info("Procesamiento de video completado.")

if __name__ == "__main__":
    asyncio.run(main())
