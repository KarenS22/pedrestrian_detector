/**
 * Telegram Sender - Envío de imágenes y videos al Bot
 * Proyecto Integrador - Visión Artificial
 */

#ifndef TELEGRAM_SENDER_HPP
#define TELEGRAM_SENDER_HPP

#include <string>
#include <opencv2/opencv.hpp>

class TelegramSender {
public:
    TelegramSender(const std::string& bot_token, const std::string& chat_id);
    ~TelegramSender();
    
    /**
     * Enviar imagen al bot de Telegram
     * @param image_path Ruta a la imagen
     * @param caption Texto de descripción
     * @return true si se envió correctamente
     */
    bool sendPhoto(const std::string& image_path, const std::string& caption = "");
    
    /**
     * Enviar video al bot de Telegram
     * @param video_path Ruta al video
     * @param caption Texto de descripción
     * @return true si se envió correctamente
     */
    bool sendVideo(const std::string& video_path, const std::string& caption = "");
    
    /**
     * Enviar mensaje de texto
     * @param message Mensaje a enviar
     * @return true si se envió correctamente
     */
    bool sendMessage(const std::string& message);
    
    /**
     * Enviar múltiples archivos (imagen + video)
     * @param image_path Ruta a la imagen
     * @param video_path Ruta al video
     * @param message Mensaje adicional
     * @return true si se envió correctamente
     */
    bool sendDetectionPackage(const std::string& image_path, 
                             const std::string& video_path,
                             const std::string& message);
    
    /**
     * Verificar conexión con Telegram
     * @return true si la conexión es exitosa
     */
    bool testConnection();
    
private:
    std::string bot_token_;
    std::string chat_id_;
    std::string api_url_;
    
    /**
     * Realizar petición HTTP POST multipart
     */
    std::string sendMultipartRequest(const std::string& endpoint,
                                    const std::string& file_path,
                                    const std::string& file_field,
                                    const std::string& caption);
    
    /**
     * Codificar string para URL
     */
    std::string urlEncode(const std::string& str);
    
    /**
     * Callback para libcurl
     */
    static size_t writeCallback(void* contents, size_t size, size_t nmemb, void* userp);
};

#endif // TELEGRAM_SENDER_HPP
