# Zoom & Pan Interactivos - Documentación

## 🔍 Descripción

El sistema de Zoom & Pan Interactivos proporciona navegación avanzada de imágenes para análisis arqueológico detallado. Permite examinar imágenes a diferentes niveles de amplificación y navegar fluidamente por toda la superficie de la imagen.

## 🎯 Características Principales

### Zoom Dinámico
- **Mouse Wheel**: Zoom in/out centrado en la posición del cursor
- **Niveles Predefinidos**: 25%, 50%, 100%, 200%, 400%, 800%
- **Interpolación Adaptativa**: Bicúbica para zoom out, nearest neighbor para zoom in alta magnificación
- **Zoom Inteligente**: Límites automáticos y transiciones suaves

### Pan Fluido
- **Arrastrar con Mouse**: Pan natural arrastrando la imagen
- **Límites Inteligentes**: Previene perder la imagen del área visible
- **Memoria de Posición**: Mantiene posición relativa al cambiar zoom
- **Scrollbars Automáticas**: Aparecen cuando la imagen es mayor que el canvas

### Controles Precisos
- **Toolbar Integrada**: Botones de zoom accesibles
- **Indicador de Zoom**: Muestra porcentaje actual en tiempo real
- **Fit to Window**: Ajusta imagen al tamaño de ventana
- **100% Real Size**: Muestra imagen a tamaño real

## 🖱️ Controles de Navegación

### Mouse
- **Wheel Up/Down**: Zoom in/out centrado en cursor
- **Drag (Left Button)**: Pan/desplazamiento de imagen
- **Click**: Focus para habilitar keyboard shortcuts

### Toolbar
- **🔍-**: Zoom out al nivel anterior
- **🔍+**: Zoom in al siguiente nivel
- **Fit**: Ajustar imagen a ventana
- **100%**: Tamaño real de imagen
- **Dropdown**: Selección directa de zoom level

### Keyboard (Canvas debe tener focus)
- **Ctrl + Plus**: Zoom in
- **Ctrl + Minus**: Zoom out
- **Ctrl + 0**: Fit to window
- **Ctrl + 1**: Zoom 100%

## 📊 Niveles de Zoom

| Nivel | Factor | Uso Recomendado |
|-------|--------|----------------|
| 25%   | 0.25x  | Vista general completa |
| 50%   | 0.5x   | Inspección de áreas grandes |
| 100%  | 1.0x   | Tamaño real, detalle estándar |
| 200%  | 2.0x   | Análisis de detalles finos |
| 400%  | 4.0x   | Inspección de píxeles individuales |
| 800%  | 8.0x   | Máximo detalle, análisis microscópico |

## 🔄 Integración con Inspector Píxeles

### Coordenadas Precisas
- **Transformación Automática**: Coordenadas del inspector se ajustan automáticamente al zoom
- **Precisión Mantenida**: Sampling funciona correctamente en todos los niveles
- **Análisis Multi-escala**: Permite analizar píxeles a diferentes magnificaciones

### Workflow Integrado
1. **Exploración General**: Usar 25%-50% para identificar áreas de interés
2. **Análisis Medio**: 100%-200% para inspección detallada
3. **Análisis Microscópico**: 400%-800% para píxeles individuales
4. **Inspector Continuo**: Valores en tiempo real en cualquier zoom level

## ⚙️ Optimizaciones Técnicas

### Rendering Performance
- **Cache de Imágenes**: Cachea imágenes escaladas para navegación rápida
- **Interpolación Adaptativa**: Algoritmo óptimo según nivel de zoom
- **Rendering Parcial**: Solo renderiza área visible para imágenes grandes
- **Límite de Cache**: Gestión inteligente de memoria

### Coordinate Transformation
- **Precisión Matemática**: Transformaciones exactas canvas ↔ imagen
- **Floating Point**: Cálculos sub-pixel para suavidad
- **Validación de Límites**: Previene acceso fuera de imagen
- **Estado Consistente**: Mantiene coherencia durante operaciones

### Memory Management
- **Cache Limitado**: Máximo 10 imágenes escaladas en cache
- **Limpieza Automática**: Liberación de memoria al cambiar imagen
- **Optimización de Tiles**: Para imágenes extremadamente grandes (futuro)

## 🎨 Aplicaciones Arqueológicas

### Análisis Multi-escala
- **Contexto General**: 25%-50% para ubicación espacial
- **Detalle Medio**: 100%-200% para identificación de elementos
- **Micro-análisis**: 400%-800% para caracterización de pigmentos

### Workflow de Documentación
1. **Vista General**: Capturar contexto completo (Fit)
2. **Áreas de Interés**: Zoom 200% para detalles específicos
3. **Análisis Píxel**: 800% para caracterización exacta
4. **Documentación**: Inspector píxeles para valores precisos

### Control de Calidad
- **Verificación Pre-procesamiento**: Inspeccionar imagen original
- **Validación Post-procesamiento**: Comparar resultados
- **Análisis de Artefactos**: Detectar problemas de procesamiento
- **Calibración**: Ajustar parámetros basándose en zoom detallado

## 🔧 Consideraciones de Uso

### Performance
- **Imágenes Grandes**: >10MP pueden requerir paciencia inicial
- **Cache Warming**: Primera vez en cada zoom level es más lenta
- **Memory Usage**: Zoom alto en imágenes grandes usa más RAM

### Limitaciones
- **Zoom Máximo**: 1600% (16x) límite absoluto
- **Zoom Mínimo**: 10% (0.1x) límite absoluto
- **Cache Size**: Máximo 10 niveles de zoom en memoria
- **Interpolación**: Nearest neighbor puede mostrar pixelación a zoom alto

### Recomendaciones
- **Inicio**: Siempre usar "Fit" al cargar imagen nueva
- **Navegación**: Combinar wheel zoom + drag pan para eficiencia
- **Análisis**: Usar múltiples zoom levels para análisis completo
- **Performance**: Cerrar/reabrir para limpiar cache si necesario

## 📈 Status de Implementación

**✅ Características Completadas:**
- Zoom dinámico con mouse wheel
- Pan con drag de mouse
- Toolbar completa con controles
- Niveles predefinidos (25%-800%)
- Integración con Inspector Píxeles
- Cache optimizado de imágenes
- Coordinate transformation precisa
- Status bar con información de zoom

**🔄 Mejoras Futuras:**
- Keyboard shortcuts avanzados
- Minimap para navegación rápida
- Zoom con selección de área
- Animaciones suaves de transición
- Soporte para tiles en imágenes gigantes

---

## 💡 Tips de Uso Avanzado

### Navegación Eficiente
- **Double-click**: Para zoom rápido a área específica (futuro)
- **Right-click**: Menú contextual con opciones zoom (futuro)
- **Keyboard + Mouse**: Combine shortcuts con wheel para máxima velocidad

### Análisis Sistemático
1. **Fit**: Ver imagen completa
2. **Identify**: Localizar áreas problemáticas
3. **Zoom**: Amplificar área específica
4. **Inspect**: Usar Inspector Píxeles para datos exactos
5. **Document**: Copiar valores para reportes

### Resolución de Problemas
- **Imagen Perdida**: Usar "Fit" para recentrar
- **Zoom Lento**: Reducir resolución de imagen fuente
- **Coordenadas Incorrectas**: Verificar que Inspector tenga zoom controller
- **Memory Issues**: Reiniciar aplicación para limpiar cache
