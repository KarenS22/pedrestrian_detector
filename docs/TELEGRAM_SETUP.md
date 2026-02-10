# 🤖 Guía: Cómo Obtener Credenciales de Telegram

## Paso 1: Crear un Bot en Telegram

1. **Abre Telegram** en tu teléfono o computadora

2. **Busca a BotFather:**
   - En el buscador, escribe: `@BotFather`
   - Es el bot oficial de Telegram para crear bots
   - Tiene una marca de verificación azul ✓

3. **Inicia conversación:**
   - Presiona `START` o envía `/start`

4. **Crea tu bot:**
   - Envía el comando: `/newbot`
   - BotFather te pedirá un **nombre** para tu bot
     - Ejemplo: `Mi Detector de Personas`
   - Luego te pedirá un **username** (debe terminar en 'bot')
     - Ejemplo: `mi_detector_personas_bot`

5. **Guarda el TOKEN:**
   - BotFather te enviará un mensaje como este:
   ```
   Done! Congratulations on your new bot. You will find it at 
   t.me/mi_detector_personas_bot. You can now add a description...
   
   Use this token to access the HTTP API:
   123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   ```
   
   - **COPIA ESE TOKEN** (los números y letras después de "Use this token")
   - Ejemplo: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

---

## Paso 2: Obtener tu Chat ID

### Opción A: Usando el Bot (Método Simple)

1. **Busca tu bot** en Telegram:
   - Busca el username que elegiste (ej: `@mi_detector_personas_bot`)
   - Presiona `START`

2. **Envía cualquier mensaje** a tu bot:
   - Por ejemplo: "Hola"

3. **Usa este comando en tu terminal:**
   ```bash
   curl https://api.telegram.org/bot<TU_TOKEN>/getUpdates
   ```
   
   Reemplaza `<TU_TOKEN>` con el token que obtuviste en el Paso 1.
   
   **Ejemplo completo:**
   ```bash
   curl https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates
   ```

4. **Busca tu Chat ID** en la respuesta:
   ```json
   {
     "ok": true,
     "result": [{
       "update_id": 12345,
       "message": {
         "message_id": 1,
         "from": {
           "id": 987654321,  <-- ESTE ES TU CHAT_ID
           "is_bot": false,
           "first_name": "Tu Nombre"
         },
         "chat": {
           "id": 987654321,  <-- O ESTE
           "first_name": "Tu Nombre",
           "type": "private"
         },
         "text": "Hola"
       }
     }]
   }
   ```
   
   Tu **Chat ID** es el número que aparece en `"chat": {"id": 987654321}`

### Opción B: Usando un Bot Helper

1. **Busca el bot:** `@userinfobot` en Telegram
2. **Presiona START**
3. Te responderá con tu información, incluyendo tu **Chat ID**

### Opción C: Usando Web

1. Abre Telegram Web: https://web.telegram.org
2. Abre conversación con tu bot
3. Mira la URL, verá algo como:
   ```
   https://web.telegram.org/k/#987654321
   ```
   El número después de `#` es tu Chat ID

---

## Paso 3: Configurar el Proyecto

### Opción A: Archivo .env (Recomendado)

Crea un archivo `.env` en la carpeta `bot_telegram/`:

```bash
cd bot_telegram
nano .env
```

Agrega estas líneas:
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

Guarda y cierra (`Ctrl+X`, luego `Y`, luego `Enter`)

### Opción B: Editar config.py

Edita `bot_telegram/config.py`:

```python
TELEGRAM_BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz'
TELEGRAM_CHAT_ID = '987654321'
```

### Opción C: Editar config.hpp (Para C++)

Edita `detector_cpp/config.hpp`:

```cpp
const std::string TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz";
const std::string TELEGRAM_CHAT_ID = "987654321";
```

Luego recompila:
```bash
cd detector_cpp/build
make
```

---

## Verificar Configuración

### Test 1: Probar conexión desde terminal

```bash
curl "https://api.telegram.org/bot<TU_TOKEN>/sendMessage?chat_id=<TU_CHAT_ID>&text=Hola desde la terminal"
```

Si funciona, recibirás un mensaje en Telegram.

### Test 2: Ejecutar el bot

```bash
cd bot_telegram
source venv/bin/activate
python main.py
```

Si ves:
```
✓ Conexión con Telegram establecida
🤖 Iniciando bot de Telegram...
```

¡Todo está bien! 🎉

---

## Solución de Problemas

### Error: "Unauthorized"
- ❌ Token incorrecto
- ✅ Verifica que copiaste el token completo de BotFather

### Error: "Bad Request: chat not found"
- ❌ Chat ID incorrecto
- ✅ Asegúrate de haber enviado un mensaje a tu bot primero
- ✅ Verifica el Chat ID con `getUpdates`

### Error: "Network is unreachable"
- ❌ Sin conexión a internet
- ✅ Verifica tu conexión
- ✅ Intenta: `ping api.telegram.org`

### Bot no responde
- Asegúrate de que el bot esté corriendo (`python main.py`)
- Verifica que no haya errores en la consola
- Intenta enviar `/start` al bot

---

## Seguridad

⚠️ **NUNCA COMPARTAS TU TOKEN**
- No lo subas a GitHub
- No lo compartas en capturas de pantalla
- Agrégalo a `.gitignore`:
  ```bash
  echo ".env" >> .gitignore
  echo "config.hpp" >> .gitignore
  ```

Si tu token se filtra:
1. Ve a @BotFather
2. Envía `/mybots`
3. Selecciona tu bot
4. Presiona "API Token"
5. Presiona "Revoke current token"
6. Obtendrás un nuevo token

---

## Ejemplo Completo

```bash
# 1. Obtener token de @BotFather
# Token: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# 2. Enviar mensaje a tu bot en Telegram
# (cualquier mensaje)

# 3. Obtener Chat ID
curl https://api.telegram.org/bot123456789:ABCdefGHIjklMNOpqrsTUVwxyz/getUpdates

# 4. Copiar Chat ID de la respuesta
# Chat ID: 987654321

# 5. Crear .env
cat > bot_telegram/.env << EOF
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
EOF

# 6. Probar
cd bot_telegram
source venv/bin/activate
python main.py
```

---

## ¿Necesitas Ayuda?

- 📖 [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- 🤖 [@BotFather Commands](https://core.telegram.org/bots#botfather)
- 💬 Consulta con tu docente o compañeros
