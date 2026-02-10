# 📝 Guía para el Informe Técnico

## Estructura Recomendada del Informe

### 1. PORTADA
```
- Título del proyecto
- Universidad Politécnica Salesiana
- Carrera de Computación
- Materia: Visión Artificial
- Docente: Ing. Vladimir Robles Bykbaev
- Integrantes del grupo
- Período: Octubre 2025 - Febrero 2026
```

---

### 2. INTRODUCCIÓN (1-2 páginas)

**Qué incluir:**
- Contexto del problema
- Importancia de la detección de personas y análisis de postura
- Aplicaciones en seguridad, medicina, deporte
- Objetivos del proyecto

**Ejemplo:**
```
En el contexto actual de la inteligencia artificial aplicada a la 
seguridad y la salud, existe una creciente necesidad de sistemas que 
integren técnicas clásicas de visión por computador con métodos 
avanzados basados en aprendizaje profundo. Este proyecto busca 
desarrollar un sistema capaz de detectar personas en tiempo real y 
analizar su postura corporal...
```

---

### 3. DESCRIPCIÓN DEL PROBLEMA (1 página)

**Qué incluir:**
- Problema específico que resuelve el proyecto
- Limitaciones de enfoques tradicionales
- Por qué es necesaria la combinación de técnicas clásicas y deep learning

---

### 4. PROPUESTA DE SOLUCIÓN (2-3 páginas)

#### 4.1 Arquitectura del Sistema

**Incluir:**
- Diagrama del sistema completo (usar el de ARQUITECTURA.md)
- Descripción de cada componente:
  - Detector C++ (YOLO)
  - Bot de Telegram (Python)
  - Modelo de postura (MMPose/OpenPose)

#### 4.2 Tecnologías Utilizadas

**Tabla de tecnologías:**

| Componente | Tecnología | Versión | Propósito |
|------------|-----------|---------|-----------|
| Detector | C++ | 17 | Performance y eficiencia |
| Framework CV | OpenCV | 4.x | Procesamiento de imágenes |
| Modelo personas | YOLOv8 | Nano | Detección en tiempo real |
| Backend IA | PyTorch | 2.x | Inferencia de modelos DL |
| Modelo postura | MMPose | 1.3+ | Detección de keypoints |
| Comunicación | Telegram Bot API | 6.x | Notificaciones y UI |

#### 4.3 Flujo de Procesamiento

**Diagrama de flujo con tiempos:**
```
Captura (0ms) → Preprocesamiento (5ms) → 
Inferencia YOLO (10-50ms) → Post-procesamiento (5ms) → 
Detección (SI/NO) → Envío Telegram → 
Bot recibe → Inferencia postura (1-2s) → 
Visualización → Envío al usuario
```

---

### 5. IMPLEMENTACIÓN (3-4 páginas)

#### 5.1 Detector de Personas (C++)

**Explicar:**
- Por qué YOLO vs HOG+SVM
- Configuración del modelo YOLO.onnx
- Preprocesamiento de imágenes
- Post-procesamiento (NMS)
- Criterios de detección

**Código importante (snippets):**
```cpp
// Ejemplo de inferencia YOLO
cv::Mat blob;
cv::dnn::blobFromImage(frame, blob, 1.0/255.0, 
                      cv::Size(640, 640), cv::Scalar(), true);
net_.setInput(blob);
std::vector<cv::Mat> outputs;
net_.forward(outputs);
```

**Gráfica sugerida:**
- Distribución de confianza de detecciones
- Histograma de tamaños de bounding boxes

#### 5.2 Detección de Postura (Python)

**Explicar:**
- Arquitectura de MMPose/OpenPose
- 17 keypoints COCO
- Umbral de confianza
- Análisis de postura (tipos: erguida, agachada, caída)

**Código importante:**
```python
# Ejemplo de detección de postura
detection_result = pose_detector.detect_pose(image)
keypoints = detection_result['keypoints']  # (N, 17, 2)
scores = detection_result['scores']  # (N, 17)
```

**Gráficas sugeridas:**
- Mapa de calor de confianza por keypoint
- Distribución de tipos de postura detectados

#### 5.3 Integración con Telegram

**Explicar:**
- Uso de Telegram Bot API
- Envío de archivos multipart
- Manejo de errores y reintentos

---

### 6. RESULTADOS Y PRUEBAS (4-5 páginas)

#### 6.1 Dataset de Pruebas

**Describir:**
- Número de imágenes/videos utilizados
- Condiciones de iluminación
- Variedad de posturas
- Número de personas por escena

**Ejemplo:**
```
Dataset de pruebas:
- 100 imágenes con personas
- 20 videos (5-10 segundos c/u)
- Condiciones: interior, exterior, luz baja, luz alta
- Posturas: erguida (40%), agachada (30%), caída (20%), otras (10%)
```

#### 6.2 Métricas de Rendimiento

**Tabla de resultados - Detector C++:**

| Métrica | Valor | Observaciones |
|---------|-------|---------------|
| FPS promedio | 28.5 | Con GPU NVIDIA RTX 3060 |
| Tiempo inferencia | 12 ms | YOLO en CUDA |
| Precisión | 92% | 92 de 100 detecciones correctas |
| Recall | 88% | 88 de 100 personas detectadas |
| Falsos positivos | 8% | Objetos confundidos con personas |
| Uso RAM | 450 MB | Durante operación |

**Tabla de resultados - Bot Python:**

| Métrica | Valor | Observaciones |
|---------|-------|---------------|
| Tiempo inferencia | 1.8 s | MMPose HRNet-W48 |
| Precisión keypoints | 89% | PCK@0.5 |
| Posturas correctas | 85% | 85 de 100 clasificaciones |
| Uso RAM | 2.1 GB | Modelo cargado en memoria |

#### 6.3 Matriz de Confusión

**Detección de Personas (YOLO):**
```
                 Predicho
                Persona | No Persona
Actual Persona     92   |     8
     No Persona     3   |    97

Precisión: 92/95 = 96.8%
Recall: 92/100 = 92%
F1-Score: 94.4%
```

**Clasificación de Posturas:**
```
                 Predicho
              Erguida | Agachada | Caída | Otra
Erguida         36    |    2     |   1   |  1
Agachada         3    |   25     |   1   |  1
Caída            1    |    2     |  17   |  0
Otra             2    |    1     |   0   |  7

Accuracy: 85%
```

#### 6.4 Gráficas de Rendimiento

**Incluir:**

1. **Gráfica de FPS en el tiempo**
   ```python
   import matplotlib.pyplot as plt
   
   fps_values = [28.5, 29.1, 27.8, ...]  # Tus datos
   plt.plot(fps_values)
   plt.title('FPS durante ejecución (30 minutos)')
   plt.xlabel('Segundos')
   plt.ylabel('FPS')
   plt.axhline(y=30, color='r', linestyle='--', label='Target 30 FPS')
   plt.legend()
   plt.savefig('fps_graph.png')
   ```

2. **Gráfica de distribución de confianza**
   ```python
   confidences = [0.92, 0.85, 0.78, ...]
   plt.hist(confidences, bins=20)
   plt.title('Distribución de Confianza de Detecciones')
   plt.xlabel('Confianza')
   plt.ylabel('Frecuencia')
   plt.savefig('confidence_dist.png')
   ```

3. **Gráfica de uso de memoria**
   ```python
   memory_usage = [450, 455, 448, ...]  # MB
   plt.plot(memory_usage)
   plt.title('Uso de Memoria RAM')
   plt.xlabel('Tiempo (s)')
   plt.ylabel('Memoria (MB)')
   plt.savefig('memory_usage.png')
   ```

4. **Comparación YOLO vs HOG** (si implementaste ambos)
   ```python
   methods = ['YOLO', 'HOG+SVM']
   fps = [28.5, 8.2]
   precision = [92, 78]
   
   fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
   ax1.bar(methods, fps)
   ax1.set_title('FPS')
   ax2.bar(methods, precision)
   ax2.set_title('Precisión (%)')
   plt.savefig('comparison.png')
   ```

#### 6.5 Casos de Éxito

**Incluir 3-5 ejemplos con:**
- Imagen original
- Imagen con detección
- Imagen con postura
- Descripción del caso
- Métricas específicas

**Ejemplo:**
```
Caso 1: Persona de pie en interior
- Detección: ✓ Correcta (conf: 0.94)
- Keypoints: 17/17 detectados (avg conf: 0.89)
- Postura: Erguida (correcto)
- Tiempo total: 1.85s
```

#### 6.6 Casos Fallidos

**Importante: Analizar fallos**

**Ejemplo:**
```
Caso Fallido 1: Persona parcialmente oculta
- Problema: Solo se detectó parte superior del cuerpo
- Causa: Oclusión por mueble
- Keypoints detectados: 9/17 (inferior faltante)
- Solución propuesta: Mejorar dataset con oclusiones
```

---

### 7. COMPARACIÓN CON MÉTODOS TRADICIONALES (2 páginas)

**Si implementaste HOG+SVM, comparar:**

| Aspecto | YOLO | HOG+SVM |
|---------|------|---------|
| Velocidad (FPS) | 28.5 | 8.2 |
| Precisión | 92% | 78% |
| Recall | 88% | 72% |
| Detección múltiple | Excelente | Buena |
| Robustez a oclusión | Buena | Regular |
| Complejidad código | Media | Alta |

**Análisis:**
```
YOLO demuestra ser superior en velocidad (3.5x más rápido) y 
precisión (14% mejor). HOG+SVM requiere configuración manual 
de parámetros mientras que YOLO es end-to-end...
```

---

### 8. DIFICULTADES ENCONTRADAS (1-2 páginas)

**Ser honestos, mencionar:**
- Problemas de instalación
- Compatibilidad de librerías
- Dificultad en configuración de Telegram
- Problemas de rendimiento
- Cómo se resolvieron

**Ejemplo:**
```
Dificultad 1: Instalación de MMPose
- Error: Incompatibilidad con PyTorch 2.2
- Solución: Downgrade a PyTorch 2.1 y MMPose 1.3.0
- Tiempo perdido: 3 horas
```

---

### 9. CONCLUSIONES (1 página)

**Incluir:**
- Logros del proyecto
- Cumplimiento de objetivos
- Aprendizajes técnicos
- Aplicabilidad real
- Trabajo futuro

**Ejemplo:**
```
1. Se logró implementar un sistema de detección en tiempo real 
   con precisión del 92%

2. La combinación de técnicas clásicas (YOLO) y deep learning 
   (MMPose) demostró ser efectiva

3. Se aprendió el uso de:
   - OpenCV DNN module para inferencia
   - PyTorch para modelos preentrenados
   - Telegram Bot API para interfaces de usuario
   - Integración C++ ↔ Python

4. El sistema es aplicable en:
   - Vigilancia inteligente
   - Monitoreo de pacientes
   - Análisis deportivo
   - Seguridad industrial
```

---

### 10. TRABAJO FUTURO (1 página)

**Ideas para mejorar:**
- Tracking multi-objeto (seguimiento temporal)
- Detección de acciones (caminar, correr, caer)
- Alertas inteligentes (ej: detectar caída y llamar emergencia)
- Optimización para edge devices (Raspberry Pi, Jetson Nano)
- Base de datos de eventos
- Dashboard web para monitoreo

---

### 11. BIBLIOGRAFÍA

**Formato IEEE o APA, incluir:**

```
[1] Redmon, J., & Farhadi, A. (2018). YOLOv3: An Incremental 
    Improvement. arXiv preprint arXiv:1804.02767.

[2] Cao, Z., Simon, T., Wei, S. E., & Sheikh, Y. (2017). 
    Realtime multi-person 2D pose estimation using part affinity 
    fields. In CVPR (pp. 7291-7299).

[3] Contributors, MMPose. (2020). OpenMMLab Pose Estimation 
    Toolbox and Benchmark. 
    https://github.com/open-mmlab/mmpose

[4] OpenCV Team. (2023). OpenCV: Open Source Computer Vision 
    Library. https://opencv.org/

[5] Telegram. (2023). Telegram Bot API. 
    https://core.telegram.org/bots/api
```

---

## ANEXOS

### Anexo A: Código Fuente Relevante

**Incluir snippets importantes:**
- Función de detección YOLO
- Función de análisis de postura
- Handler de Telegram Bot

### Anexo B: Configuración de Entorno

- Versiones exactas de librerías
- Comandos de instalación
- Configuración de hardware

### Anexo C: Dataset

- Descripción de imágenes de prueba
- Condiciones de captura
- Anotaciones (si las hay)

---

## CHECKLIST FINAL

Antes de entregar, verificar:

- [ ] Todas las secciones completas
- [ ] Al menos 5 gráficas/diagramas
- [ ] Matriz de confusión incluida
- [ ] Tabla de métricas con valores reales
- [ ] Código fuente comentado
- [ ] Bibliografía en formato correcto
- [ ] Screenshots de resultados
- [ ] Análisis de casos fallidos
- [ ] Conclusiones sustentadas en datos
- [ ] Ortografía y redacción revisadas
- [ ] Formato consistente (fuente, márgenes)
- [ ] Numeración de páginas
- [ ] Índice de contenidos
- [ ] Índice de figuras y tablas

---

## RÚBRICA DE AUTOEVALUACIÓN

Califica tu informe (1-5):

| Criterio | Puntos |
|----------|--------|
| Descripción clara del problema | __/5 |
| Propuesta de solución detallada | __/5 |
| Resultados con datos reales | __/5 |
| Gráficas y tablas informativas | __/5 |
| Análisis crítico (incluye fallos) | __/5 |
| Conclusiones sustentadas | __/5 |
| Calidad de redacción | __/5 |
| Formato profesional | __/5 |
| **TOTAL** | __/40 |

**Meta: > 32/40 (80%)**

---

¡Éxito en tu informe! 🚀
