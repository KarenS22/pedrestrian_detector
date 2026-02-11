"""
Bot de Telegram para Detección de Postura Humana
Recibe imágenes/videos desde la aplicación C++ y realiza análisis de postura
"""
import os
import logging
from pathlib import Path
from datetime import datetime
import asyncio
import cv2
import numpy as np

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import json

BASE_DIR = Path(__file__).resolve().parent
SUBSCRIBERS_FILE = BASE_DIR / "subscribers.json"


def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return []
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f)

def add_subscriber(chat_id):
    subs = load_subscribers()
    if chat_id not in subs:
        subs.append(chat_id)
        save_subscribers(subs)

def remove_subscriber(chat_id):
    subs = load_subscribers()
    if chat_id in subs:
        subs.remove(chat_id)
        save_subscribers(subs)


from config import (
    TELEGRAM_BOT_TOKEN,
    ALLOWED_USER_IDS,
    MESSAGES,
    DETECTIONS_DIR,
    POSES_DIR,
    VIDEOS_DIR
)
from pose_detector import PoseDetector
from video_processor import VideoProcessor

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Inicializar detectores
pose_detector = PoseDetector()
video_processor = VideoProcessor(pose_detector)

# Estadísticas globales
stats = {
    'total_images': 0,
    'total_videos': 0,
    'total_persons_detected': 0,
    'start_time': datetime.now()
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /start"""
    user = update.effective_user
    logger.info(f"Usuario {user.id} - {user.username} inició el bot")
    
    keyboard = [
        [InlineKeyboardButton("📊 Ver Estadísticas", callback_data='stats')],
        [InlineKeyboardButton("❓ Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        MESSAGES['welcome'],
        reply_markup=reply_markup
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /help"""
    help_text = """
📖 **Ayuda - Bot de Detección de Postura**

**¿Cómo usar el bot?**
1. Envía una imagen con personas
2. O envía un video corto
3. El bot detectará automáticamente las posturas humanas

**Formatos soportados:**
• Imágenes: JPG, PNG
• Videos: MP4, AVI

**Recibirás:**
✅ Imagen original
✅ Imagen con posturas detectadas (esqueleto)
✅ Video corto de 5 segundos

**Comandos:**
/start - Iniciar el bot
/help - Mostrar esta ayuda
/stats - Ver estadísticas de uso
    """
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para el comando /stats"""
    uptime = datetime.now() - stats['start_time']
    
    stats_text = f"""
📊 **Estadísticas del Bot**

🖼️ Imágenes procesadas: {stats['total_images']}
🎥 Videos procesados: {stats['total_videos']}
👥 Personas detectadas: {stats['total_persons_detected']}
⏱️ Tiempo activo: {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m

💡 **Información del sistema:**
🤖 Modelo: HRNet-W48 (MMPose)
🎯 Keypoints: 17 puntos COCO
📍 Confianza mínima: 30%
    """
    
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_subscriber(chat_id)
    await update.message.reply_text("✅ Te has suscrito a las notificaciones.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    remove_subscriber(chat_id)
    await update.message.reply_text("❌ Te has desuscrito de las notificaciones.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para imágenes recibidas"""
    user = update.effective_user
    logger.info(f"Imagen recibida de {user.username}")
    
    # Enviar mensaje de confirmación
    status_msg = await update.message.reply_text(MESSAGES['detection_received'])
    
    try:
        # Descargar imagen
        photo = update.message.photo[-1]  # Mejor calidad
        file = await photo.get_file()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = DETECTIONS_DIR / f"detection_{timestamp}.jpg"
        await file.download_to_drive(str(image_path))
        
        # Leer imagen
        image = cv2.imread(str(image_path))
        
        if image is None:
            await status_msg.edit_text("❌ Error al leer la imagen")
            return
        
        # Actualizar estado
        await status_msg.edit_text(MESSAGES['processing'])
        
        # Detectar postura
        detection_result = pose_detector.detect_pose(image)
        num_persons = detection_result['num_persons']
        
        # Actualizar estadísticas
        stats['total_images'] += 1
        stats['total_persons_detected'] += num_persons
        
        # Dibujar postura
        image_with_pose = pose_detector.draw_pose(image, detection_result)
        
        # Guardar imagen con pose
        pose_image_path = POSES_DIR / f"pose_{timestamp}.jpg"
        cv2.imwrite(str(pose_image_path), image_with_pose)
        
        # Analizar posturas
        postures = pose_detector.analyze_posture(detection_result)
        
        # Crear video corto
        await status_msg.edit_text("🎬 Generando video...")
        video_path = video_processor.create_short_clip(image, detection_result)
        
        # Obtener estadísticas
        pose_stats = pose_detector.get_statistics(detection_result)
        
        # Enviar resultados
        await status_msg.edit_text(MESSAGES['sending_results'])
        
        # 1. Imagen original
        with open(image_path, 'rb') as f:
            await update.message.reply_photo(
                photo=f,
                caption="📷 **Imagen Original**",
                parse_mode='Markdown'
            )
        
        # 2. Imagen con posturas
        posture_text = "\n".join([f"Persona {i+1}: {p}" for i, p in enumerate(postures)])
        caption = f"""
🎯 **Detección de Postura Completada**

👥 Personas detectadas: {num_persons}
📊 Confianza promedio: {pose_stats['avg_confidence']:.2%}

**Posturas:**
{posture_text}
        """
        
        with open(pose_image_path, 'rb') as f:
            await update.message.reply_photo(
                photo=f,
                caption=caption,
                parse_mode='Markdown'
            )
        
        # 3. Video corto
        with open(video_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption="🎥 **Video de detección (5 segundos)**",
                parse_mode='Markdown'
            )
        
        # Eliminar mensaje de estado
        await status_msg.delete()
        
        logger.info(f"Procesamiento completado: {num_persons} persona(s)")
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}", exc_info=True)
        await status_msg.edit_text(MESSAGES['error'].format(str(e)))


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para videos recibidos"""
    user = update.effective_user
    logger.info(f"Video recibido de {user.username}")
    
    status_msg = await update.message.reply_text(MESSAGES['detection_received'])
    
    try:
        # Descargar video
        video = update.message.video
        file = await video.get_file()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = DETECTIONS_DIR / f"video_{timestamp}.mp4"
        await file.download_to_drive(str(video_path))
        
        # Actualizar estado
        await status_msg.edit_text("🎬 Procesando video...")
        
        # Procesar video
        original_path, pose_video_path = video_processor.process_video_file(str(video_path))
        
        # Extraer primer frame para estadísticas
        cap = cv2.VideoCapture(str(video_path))
        ret, first_frame = cap.read()
        cap.release()
        
        if ret:
            detection_result = pose_detector.detect_pose(first_frame)
            num_persons = detection_result['num_persons']
            stats['total_persons_detected'] += num_persons
        else:
            num_persons = 0
        
        stats['total_videos'] += 1
        
        # Obtener info del video
        video_info = video_processor.get_video_info(pose_video_path)
        
        await status_msg.edit_text(MESSAGES['sending_results'])
        
        # 1. Video original
        with open(original_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption="📹 **Video Original**",
                parse_mode='Markdown'
            )
        
        # 2. Video con posturas
        caption = f"""
🎯 **Video Procesado con Detección de Postura**

👥 Personas detectadas: {num_persons}
⏱️ Duración: {video_info['duration']:.1f}s
🎞️ Frames: {video_info['total_frames']}
📊 FPS: {video_info['fps']}
        """
        
        with open(pose_video_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption=caption,
                parse_mode='Markdown'
            )
        
        await status_msg.delete()
        
        logger.info(f"Video procesado: {num_persons} persona(s)")
        
    except Exception as e:
        logger.error(f"Error procesando video: {e}", exc_info=True)
        await status_msg.edit_text(MESSAGES['error'].format(str(e)))


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para documentos (videos grandes)"""
    await update.message.reply_text(
        "📎 He recibido un documento. Por favor, envía videos como archivos de video, no como documentos."
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botones inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'stats':
        await stats_command(update, context)
    elif query.data == 'help':
        await help_command(update, context)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de errores"""
    logger.error(f"Error: {context.error}", exc_info=context.error)
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "❌ Ha ocurrido un error. Por favor, intenta nuevamente."
        )


def check_user_permission(user_id: int) -> bool:
    """Verificar si el usuario tiene permiso"""
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS


async def post_init(application: Application):
    """Ejecutar después de inicializar la aplicación"""
    logger.info("Bot iniciado correctamente")
    logger.info(f"Directorio de detecciones: {DETECTIONS_DIR}")
    logger.info(f"Directorio de poses: {POSES_DIR}")
    logger.info(f"Directorio de videos: {VIDEOS_DIR}")


def main():
    """Función principal"""
    # Validar token
    # Validar token
    if not TELEGRAM_BOT_TOKEN:
        logger.error("⚠️ TELEGRAM_BOT_TOKEN no configurado!")
        logger.error("Por favor, configura tu token en el archivo .env o config.py")
        return
    
    # Crear aplicación
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Handlers para multimedia
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    

    
    # Handler para botones
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Handler de errores
    application.add_error_handler(error_handler)
    
    # Post-init
    application.post_init = post_init
    
    # Iniciar bot
    logger.info("🤖 Iniciando bot de Telegram...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
