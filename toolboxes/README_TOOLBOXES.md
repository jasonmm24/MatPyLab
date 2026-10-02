# Desarrollo de toolboxes

Los toolboxes amplían el workspace de MatPyLab con funciones científicas o de ingeniería. La interfaz carga módulos Python ubicados directamente en `toolboxes/`; cada módulo debe definir una clase que herede de `MatpyLabToolbox`.

## Crear una extensión

1. Crea un archivo Python en `toolboxes/`, por ejemplo `tb_mi_modulo.py`.
2. Importa la clase base desde `core.toolbox_manager`.
3. Implementa las propiedades `name` y `description`.
4. Implementa `export_functions()` y devuelve un diccionario que relacione los nombres disponibles en el workspace con sus funciones.
5. Instala y documenta las dependencias externas que el módulo importe.

```python
from core.toolbox_manager import MatpyLabToolbox


class MiToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Mi Toolbox"

    @property
    def description(self):
        return "Funciones de ejemplo para MatPyLab."

    def export_functions(self):
        def saludar(nombre="Mundo"):
            return f"Hola, {nombre}."

        return {"saludar": saludar}
```

## Carga y uso

El menú **Toolboxes** de la ventana principal enumera módulos `.py` dentro de `toolboxes/`, omite `__init__.py` e intenta cargar el módulo seleccionado mediante `ToolboxManager`. El gestor localiza una subclase concreta de `MatpyLabToolbox`, crea una instancia, llama a `export_functions()` e incorpora el resultado al workspace.

También se puede cargar una extensión desde código:

```python
from core.execution_engine import ExecutionEngine

engine = ExecutionEngine()
loaded, message = engine.toolbox_manager.load_toolbox("tb_mi_modulo")
if loaded:
    result, error = engine.execute_command("saludar('MatPyLab')")
```

Los imports opcionales se resuelven al importar el módulo. Si falta una dependencia, la carga falla y el gestor devuelve el mensaje de error. Añade las dependencias necesarias a `requirements-extras.txt` cuando corresponda.

## Consideraciones

- Los nombres devueltos por `export_functions()` pasan a estar disponibles en el workspace y se consideran funciones del sistema.
- Evita reutilizar nombres de funciones ya registradas para no sobrescribir herramientas existentes.
- El motor conserva un método legado para toolboxes organizados como directorios con `toolbox_init.py`; el menú actual utiliza módulos basados en clases. Para extensiones nuevas, usa el formato descrito en esta guía.
- La ejecución de código de terceros puede modificar el entorno del proceso. Carga únicamente extensiones de confianza.
