# Inspector Píxeles Básico - Documentación

## 📊 Descripción

El Inspector Píxeles Básico es una herramienta integrada en DStretch Python que proporciona análisis en tiempo real de los valores de color bajo el cursor del mouse. Es esencial para el análisis arqueológico detallado de pigmentos y texturas.

## 🎯 Características Principales

### Análisis en Tiempo Real
- **Coordenadas**: Posición exacta (x, y) del píxel
- **RGB**: Valores de Rojo, Verde, Azul (0-255)
- **HSV**: Matiz (0-360°), Saturación (0-100%), Valor (0-100%)
- **LAB**: Luminancia (0-100), componentes a* y b* (-128 a +127)
- **Hexadecimal**: Código de color #RRGGBB
- **Intensidad**: Promedio de canales RGB

### Funcionalidades Avanzadas
- **Freeze/Unfreeze**: Congela valores para análisis detallado
- **Sampling**: Análisis de 1x1, 3x3, o 5x5 píxeles
- **Copy to Clipboard**: Copia todos los valores analizados
- **Color Preview**: Vista previa visual del color

## 🖱️ Uso

### Inspección Básica
1. Carga una imagen en DStretch
2. Mueve el cursor sobre la imagen
3. Observa los valores en tiempo real en el panel derecho

### Análisis Detallado
1. **Seleccionar Sampling**: Elige 1x1 para píxel único, 3x3 o 5x5 para promedio de área
2. **Freeze Values**: Haz clic en la imagen o botón "Freeze" para congelar valores
3. **Copy Data**: Usa "Copy" para copiar análisis completo al portapapeles

### Integración con Workflow
- **Pre-análisis**: Inspecciona colores antes de aplicar decorrelation stretch
- **Post-análisis**: Compara valores antes y después del procesamiento
- **Documentación**: Copia valores para reportes arqueológicos

## 📋 Formato de Salida (Clipboard)

```
Pixel Analysis:
Position: (245, 189)
RGB: 156, 134, 98
HSV: 28°, 37%, 61%
LAB: 58.2, 12.4, 31.7
Hex: #9C8662
Sampling: 1x1
```

## 🔧 Controles

### Panel Inspector
- ☑️ **Enable**: Activa/desactiva el inspector
- **Sample**: Selecciona tamaño de muestreo (1x1, 3x3, 5x5)
- **Freeze**: Congela valores actuales
- **Copy**: Copia análisis al portapapeles

### Interacción Mouse
- **Movimiento**: Actualización en tiempo real
- **Clic**: Congela/descongela valores
- **Salir del área**: Limpia valores (si no está congelado)

## 🎨 Aplicaciones Arqueológicas

### Análisis de Pigmentos
- **Identificación**: Determina tipos de pigmento por valores LAB
- **Comparación**: Compara pigmentos similares en diferentes áreas
- **Documentación**: Registra valores exactos para publicaciones

### Control de Calidad
- **Verificación**: Confirma que el procesamiento preserva información crítica
- **Calibración**: Ajusta parámetros basándose en valores específicos
- **Validación**: Compara resultados con referencias conocidas

## ⚙️ Consideraciones Técnicas

### Performance
- Actualización optimizada en cada movimiento del mouse
- Threading para no bloquear la interfaz
- Conversiones de color precisas usando estándares CIE

### Precisión
- Conversiones RGB↔LAB usando matriz sRGB estándar
- Iluminante D65 para máxima precisión
- Corrección gamma para valores lineales

### Limitaciones
- Requiere imagen cargada para funcionar
- Coordenadas limitadas a dimensiones de imagen
- Sampling máximo 5x5 píxeles
