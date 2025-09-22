# DStretch Python

**Inspirado y basado en el plugin DStretch original de Jon Harman (ImageJ).**

**Autor principal:** Víctor Méndez
**Asistido por:** Claude Sonnet 4, Gemini 2.5 Pro, Copilot con GPT-4.1


**DStretch Python** es una implementación avanzada y validada del algoritmo decorrelation stretch para el realce de imágenes arqueológicas, especialmente arte rupestre, en Python. Replica matemáticamente el plugin DStretch de ImageJ (Jon Harman), con arquitectura moderna, interfaces CLI/GUI y 23 espacios de color validados.

## Descripción General

DStretch Python permite revelar pigmentos y detalles invisibles en fotografías de arte rupestre y otros contextos arqueológicos. Utiliza análisis estadístico de color (PCA decorrelation stretch) y matrices predefinidas para separar y realzar colores de interés, facilitando la documentación, análisis y preservación digital.

## Características Principales

- **Replicación exacta** del algoritmo DStretch ImageJ (validación >99.97% SSIM)
- **23 espacios de color** (YDS, CRGB, LRE, LAB, RGB, etc.)
- **CLI y GUI multiplataforma** (Windows, macOS, Linux)
- **Procesamiento batch y scripting Python**
- **Optimización para imágenes grandes** (procesamiento por chunks, uso eficiente de memoria)
- **Extensible y modular** (fácil integración en pipelines científicos)
- **Documentación técnica y científica completa**

## Formatos de Imagen Soportados

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- BMP (`.bmp`)
- TIFF (`.tif`, `.tiff`)
- WebP (`.webp`)

## Instalación

```bash
git clone https://github.com/arqueomendez/dstretch-python.git
cd dstretch-python
uv sync
```
o usando pip:
```bash
pip install dstretch-python
```

## Uso Rápido

### CLI
```bash
# Procesamiento básico (espacio YDS por defecto)
dstretch input.jpg
# Especificar espacio de color e intensidad
dstretch input.jpg --colorspace CRGB --scale 25
# Guardar en archivo específico
dstretch input.jpg --colorspace LRE --scale 30 --output enhanced.jpg
# Listar espacios disponibles
dstretch --list-colorspaces
```

### GUI
```bash
dstretch-gui
# Interfaz gráfica similar a ImageJ DStretch
```

### Python API
```python
from dstretch import DecorrelationStretch
import cv2
image = cv2.imread("input.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
dstretch = DecorrelationStretch()
result = dstretch.process(image, colorspace="YDS", scale=15.0)
enhanced = result.processed_image
cv2.imwrite("output.jpg", cv2.cvtColor(enhanced, cv2.COLOR_RGB2BGR))
```

## Espacios de Color Disponibles

- **Estándar:** RGB, LAB
- **Serie Y (YUV):** YDS, YBR, YBK, YRE, YRD, YWE, YBL, YBG, YUV, YYE
- **Serie L (LAB):** LAX, LDS, LRE, LRD, LBK, LBL, LWE, LYE
- **Predefinidos:** CRGB, RGB0, LABI

## Ejemplos de Aplicación

- **Documentación de pictografías:** realce de pigmentos rojos, amarillos, negros y blancos
- **Análisis de pigmentos:** separación de minerales y composición
- **Registro de sitios:** mejora de fotografías para informes y publicaciones
- **Investigación:** revelado de arte rupestre invisible

### Recomendaciones por Pigmento

- Rojo ocre/hematita: CRGB, LRE, YBR
- Amarillo ocre: YDS, LDS, YYE
- Carbón negro: YBK, LBK
- Caolín blanco: YWE, LWE
- Realce general: YDS, LDS, LAB

## Validación y Precisión

- Validación pixel a pixel contra DStretch ImageJ (SSIM promedio >0.9997)
- 40/40 tests EXCELLENT en suite automática
- 23/23 espacios de color implementados y validados
- Métricas: SSIM, MSE, diferencias por canal

## Arquitectura y Detalles Técnicos

- Núcleo matemático desacoplado de interfaces
- Procesadores independientes (preprocesamiento: flatten, auto-contraste, balance de color, etc.)
- Pipeline configurable y extensible
- Optimización: LUTs precomputadas, procesamiento por chunks, threading en GUI
- Documentación inline y en `docs/`

## Estructura del Proyecto

```
dstretch_python/
├── src/dstretch/           # Paquete principal
│   ├── decorrelation.py    # Algoritmo principal
│   ├── colorspaces.py      # Transformaciones de color
│   ├── cli.py              # Interfaz CLI
│   ├── gui.py              # Interfaz gráfica
│   └── ...
├── tests/                 # Pruebas automáticas
├── examples/              # Ejemplos de uso
├── docs/                  # Documentación técnica
└── validation_results/    # Resultados de validación
```

## Contribución

¡Contribuciones bienvenidas! Puedes ayudar en:
- Nuevos espacios de color o procesadores
- Optimización de rendimiento
- Mejoras en la GUI
- Documentación y tutoriales
- Casos de estudio arqueológicos

## Licencia

Este proyecto está licenciado bajo **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**.

- Puedes usar, modificar y compartir el software libremente **solo para fines no comerciales**.
- Es obligatorio citar el proyecto y a los autores originales.
- Para uso comercial, contacta a los autores.

Ver el archivo LICENSE para detalles completos.

## Cita Recomendada

Si usas DStretch Python en trabajos académicos, por favor cita:

> DStretch Python: Implementación en Python de decorrelation stretch para realce de imágenes arqueológicas. Basado en el plugin DStretch de Jon Harman.

## Reconocimientos

- Jon Harman: Creador del plugin DStretch original para ImageJ
- Comunidad ImageJ y arqueológica: por pruebas y retroalimentación

## Soporte y Comunidad

- Issues: Reporta bugs y solicita mejoras en GitHub Issues
- Documentación: Consulta la documentación técnica en `docs/`
- Comunidad: Únete a foros y discusiones científicas

---