# Toolboxes de MatpyLab

Los toolboxes son extensiones modulares que agregan nuevas capacidades al entorno de ejecución de MatpyLab sin modificar el núcleo del programa. Permiten emular la experiencia de los toolboxes oficiales de MATLAB y crear paquetes personalizados para hardware, visión, control, etc.

## Nueva Arquitectura (v0.2+)

A partir de la versión 0.2, MatpyLab utiliza un sistema basado en clases gestionado por el `ToolboxManager` para cargar módulos de manera dinámica. Atrás quedó la antigua estructura de carpetas con `toolbox_init.py`.

Ahora, un toolbox es simplemente un archivo Python (`.py`) dentro de la carpeta `toolboxes/` que contiene una clase que hereda de `MatpyLabToolbox`.

## Estructura del Directorio

```text
toolboxes/
├── tb_control_system.py
├── tb_image_processing.py
├── tb_serial.py
└── README_TOOLBOXES.md
```

## Cómo crear un nuevo Toolbox
Para que MatpyLab reconozca un toolbox automáticamente en el menú dinámico de la interfaz, debes seguir estas 5 reglas:

1. **Crear un archivo `.py`** en la carpeta `toolboxes/` (ej. `tb_mi_modulo.py`).
2. **Importar la clase base:** `from core.toolbox_manager import MatpyLabToolbox`.
3. **Crear una clase** que herede de `MatpyLabToolbox`.
4. **Definir las propiedades** `name` y `description`.
5. **Implementar el método `export_functions(self)`** que devuelva un diccionario con las funciones que se inyectarán a la Command Window.

### Plantilla Básica
Python

```
from core.toolbox_manager import MatpyLabToolbox

class MiToolboxPersonalizado(MatpyLabToolbox):
    @property
    def name(self):
        return "Mi Primer Toolbox"
        
    @property
    def description(self):
        return "Descripción de lo que hace el paquete."
        
    def export_functions(self):
        # 1. Definir funciones locales o importar librerías (ej. numpy, cv2)
        def saludar(nombre="Mundo"):
            print(f"¡Hola {nombre} desde el nuevo Toolbox!")

        # 2. Retornar diccionario de funciones exportadas al Workspace
        return {
            'saludar': saludar
        }
```

## Cómo los carga MatpyLab
El `ToolboxManager` (ubicado en `core/toolbox_manager.py`) se encarga de:

1. Escanear la carpeta `toolboxes/` en tiempo real.
2. Listar los archivos `.py` disponibles en el menú superior de la GUI.
3. Al hacer clic, instanciar la clase y llamar al método `export_functions()`.
4. Inyectar esas funciones directamente en el `workspace_globals` del motor, permitiendo su uso inmediato en la consola o en scripts `.m`.
