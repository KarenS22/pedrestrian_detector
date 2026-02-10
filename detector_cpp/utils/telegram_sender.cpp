/**
 * Implementación de TelegramSender
 */

#include "telegram_sender.hpp"
#include <curl/curl.h>
#include <iostream>
#include <sstream>
#include <fstream>
#include <thread>
#include <chrono>

TelegramSender::TelegramSender(const std::string& bot_token, const std::string& chat_id)
    : bot_token_(bot_token), chat_id_(chat_id) {
    api_url_ = "https://api.telegram.org/bot" + bot_token_ + "/";
    curl_global_init(CURL_GLOBAL_DEFAULT);
}

TelegramSender::~TelegramSender() {
    curl_global_cleanup();
}

size_t TelegramSender::writeCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

std::string TelegramSender::urlEncode(const std::string& str) {
    CURL* curl = curl_easy_init();
    if (!curl) return str;
    
    char* encoded = curl_easy_escape(curl, str.c_str(), str.length());
    std::string result(encoded);
    curl_free(encoded);
    curl_easy_cleanup(curl);
    
    return result;
}

bool TelegramSender::sendMessage(const std::string& message) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Error inicializando CURL" << std::endl;
        return false;
    }
    
    std::string url = api_url_ + "sendMessage";
    std::string post_data = "chat_id=" + chat_id_ + "&text=" + urlEncode(message);
    
    std::string response;
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_data.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    
    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        std::cerr << "Error enviando mensaje: " << curl_easy_strerror(res) << std::endl;
        return false;
    }
    
    return true;
}

std::string TelegramSender::sendMultipartRequest(const std::string& endpoint,
                                                 const std::string& file_path,
                                                 const std::string& file_field,
                                                 const std::string& caption) {
    CURL* curl = curl_easy_init();
    if (!curl) return "";
    
    std::string url = api_url_ + endpoint;
    std::string response;
    
    struct curl_httppost* formpost = NULL;
    struct curl_httppost* lastptr = NULL;
    
    // Agregar chat_id
    curl_formadd(&formpost, &lastptr,
                 CURLFORM_COPYNAME, "chat_id",
                 CURLFORM_COPYCONTENTS, chat_id_.c_str(),
                 CURLFORM_END);
    
    // Agregar archivo
    curl_formadd(&formpost, &lastptr,
                 CURLFORM_COPYNAME, file_field.c_str(),
                 CURLFORM_FILE, file_path.c_str(),
                 CURLFORM_END);
    
    // Agregar caption si existe
    if (!caption.empty()) {
        curl_formadd(&formpost, &lastptr,
                     CURLFORM_COPYNAME, "caption",
                     CURLFORM_COPYCONTENTS, caption.c_str(),
                     CURLFORM_END);
    }
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPPOST, formpost);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    
    CURLcode res = curl_easy_perform(curl);
    
    curl_formfree(formpost);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        std::cerr << "Error en request: " << curl_easy_strerror(res) << std::endl;
        return "";
    }
    
    return response;
}

bool TelegramSender::sendPhoto(const std::string& image_path, const std::string& caption) {
    // Verificar que el archivo existe
    std::ifstream file(image_path);
    if (!file.good()) {
        std::cerr << "Archivo no encontrado: " << image_path << std::endl;
        return false;
    }
    file.close();
    
    std::cout << "Enviando imagen: " << image_path << std::endl;
    
    std::string response = sendMultipartRequest("sendPhoto", image_path, "photo", caption);
    
    if (response.empty()) {
        std::cerr << "Error enviando imagen" << std::endl;
        return false;
    }
    
    std::cout << "✓ Imagen enviada correctamente" << std::endl;
    return true;
}

bool TelegramSender::sendVideo(const std::string& video_path, const std::string& caption) {
    std::ifstream file(video_path);
    if (!file.good()) {
        std::cerr << "Video no encontrado: " << video_path << std::endl;
        return false;
    }
    file.close();
    
    std::cout << "Enviando video: " << video_path << std::endl;
    
    std::string response = sendMultipartRequest("sendVideo", video_path, "video", caption);
    
    if (response.empty()) {
        std::cerr << "Error enviando video" << std::endl;
        return false;
    }
    
    std::cout << "✓ Video enviado correctamente" << std::endl;
    return true;
}

bool TelegramSender::sendDetectionPackage(const std::string& image_path,
                                         const std::string& video_path,
                                         const std::string& message) {
    // 1. Enviar mensaje inicial
    if (!message.empty()) {
        sendMessage(message);
    }
    
    // 2. Enviar imagen
    std::string img_caption = "🔍 Detección de persona - Imagen capturada";
    if (!sendPhoto(image_path, img_caption)) {
        return false;
    }
    
    // Pequeña pausa
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    
    // 3. Enviar video
    std::string vid_caption = "🎥 Video de detección (5 segundos)";
    if (!sendVideo(video_path, vid_caption)) {
        return false;
    }
    
    return true;
}

bool TelegramSender::testConnection() {
    CURL* curl = curl_easy_init();
    if (!curl) return false;
    
    std::string url = api_url_ + "getMe";
    std::string response;
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    
    CURLcode res = curl_easy_perform(curl);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        std::cerr << "Error de conexión: " << curl_easy_strerror(res) << std::endl;
        return false;
    }
    
    // Verificar si la respuesta contiene "ok":true
    if (response.find("\"ok\":true") != std::string::npos) {
        std::cout << "✓ Conexión con Telegram establecida" << std::endl;
        return true;
    }
    
    std::cerr << "Error: Token inválido" << std::endl;
    return false;
}
