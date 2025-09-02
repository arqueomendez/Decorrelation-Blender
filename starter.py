"""
Script para crear la estructura de archivos del proyecto DStretch Python.
Ejecutar desde el directorio raíz donde quieres crear el proyecto.
"""

import os
from pathlib import Path

def create_dstretch_structure():
    """Crea toda la estructura de carpetas y archivos del proyecto."""
    
    # Definir estructura del proyecto
    structure = {
        # Archivos raíz
        "pyproject.toml": "",
        "README.md": "",
        
        # Código fuente
        "src/dstretch/__init__.py": "",
        "src/dstretch/decorrelation.py": "",
        "src/dstretch/colorspaces.py": "",
        "src/dstretch/cli.py": "",
        "src/dstretch/gui.py": "",
        
        # Tests
        "tests/__init__.py": "",
        "tests/test_decorrelation.py": "",
        
        # Ejemplos
        "examples/basic_usage.py": "",
        
        # Directorio para imágenes de prueba (opcional)
        "test_images/.gitkeep": "",
    }
    
    print("Creando estructura del proyecto DStretch Python...")
    print("=" * 50)
    
    # Crear directorio base del proyecto
    project_root = Path("dstretch_python")
    project_root.mkdir(exist_ok=True)
    
    # Cambiar al directorio del proyecto
    os.chdir(project_root)
    
    # Crear cada archivo y directorio
    for file_path, content in structure.items():
        path = Path(file_path)
        
        # Crear directorios padre si no existen
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Crear archivo vacío
        if not path.exists():
            path.touch()
            print(f"✓ Creado: {file_path}")
        else:
            print(f"- Ya existe: {file_path}")
    
    print("=" * 50)
    print("Estructura creada exitosamente!")
    print(f"Directorio del proyecto: {project_root.absolute()}")
    print("\nPróximos pasos:")
    print("1. cd dstretch_python")
    print("2. uv init")
    print("3. uv add numpy scipy opencv-python pillow")
    print("4. uv add --dev pytest pytest-cov black flake8")
    print("5. Llenar los archivos con el código proporcionado")
    
    # Crear archivo de instrucciones
    instructions_file = Path("INSTRUCTIONS.md")
    instructions_content = "# Instrucciones para completar DStretch Python\n\n"
    instructions_content += "## Archivos a rellenar con código:\n\n"
    instructions_content += "### 1. Configuración del proyecto\n"
    instructions_content += "- `pyproject.toml` - Configuración del proyecto y dependencias\n\n"
    instructions_content += "### 2. Código principal\n"
    instructions_content += "- `src/dstretch/__init__.py` - Inicialización del paquete\n"
    instructions_content += "- `src/dstretch/decorrelation.py` - Algoritmo principal\n"
    instructions_content += "- `src/dstretch/colorspaces.py` - Espacios de color\n"
    instructions_content += "- `src/dstretch/cli.py` - Interfaz de línea de comandos\n"
    instructions_content += "- `src/dstretch/gui.py` - Interfaz gráfica\n\n"
    instructions_content += "### 3. Tests y ejemplos\n"
    instructions_content += "- `tests/test_decorrelation.py` - Suite de pruebas\n"
    instructions_content += "- `examples/basic_usage.py` - Ejemplos de uso\n\n"
    instructions_content += "### 4. Documentación\n"
    instructions_content += "- `README.md` - Documentación principal\n\n"
    instructions_content += "## Comando para inicializar proyecto:\n\n"
    instructions_content += "```bash\n"
    instructions_content += "uv init\n"
    instructions_content += "uv add numpy scipy opencv-python pillow\n"
    instructions_content += "uv add --dev pytest pytest-cov black flake8\n"
    instructions_content += "```\n\n"
    instructions_content += "## Orden recomendado de desarrollo:\n\n"
    instructions_content += "1. Completar `pyproject.toml`\n"
    instructions_content += "2. Completar `src/dstretch/__init__.py`\n"
    instructions_content += "3. Completar `src/dstretch/colorspaces.py`\n"
    instructions_content += "4. Completar `src/dstretch/decorrelation.py`\n"
    instructions_content += "5. Completar `src/dstretch/cli.py`\n"
    instructions_content += "6. Completar `src/dstretch/gui.py`\n"
    instructions_content += "7. Completar tests y ejemplos\n"
    instructions_content += "8. Completar README.md\n\n"
    instructions_content += "¡Todos los archivos están listos para ser llenados con el código!\n"
    
    instructions_file.write_text(instructions_content, encoding='utf-8')
    print(f"✓ Creado: {instructions_file}")

if __name__ == "__main__":
    try:
        create_dstretch_structure()
    except Exception as e:
        print(f"Error creando estructura: {e}")
        print("Asegúrate de tener permisos de escritura en el directorio actual.")