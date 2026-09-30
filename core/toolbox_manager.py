"""Carga toolboxes basados en clases e incorpora sus funciones al motor."""

import importlib
import sys
from pathlib import Path


class MatpyLabToolbox:
    """Clase base que todos los toolboxes deben heredar."""

    @property
    def name(self):
        return "Generic Toolbox"

    @property
    def description(self):
        return "Descripción del toolbox."

    def export_functions(self):
        """Devuelve las funciones que se inyectarán en el workspace."""
        return {}


class ToolboxManager:
    """Importa toolboxes y registra sus funciones en el motor."""

    def __init__(self, engine):
        self.engine = engine
        self.loaded_toolboxes = {}
        self.toolboxes_dir = Path(__file__).parent.parent / "toolboxes"
        if str(self.toolboxes_dir) not in sys.path:
            sys.path.append(str(self.toolboxes_dir))

    def load_toolbox(self, module_name):
        """Carga un toolbox desde la carpeta `toolboxes/`."""
        if module_name in self.loaded_toolboxes:
            return True, "El toolbox ya está cargado."

        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, MatpyLabToolbox)
                        and attr is not MatpyLabToolbox):
                    toolbox_instance = attr()
                    functions = toolbox_instance.export_functions()

                    self.engine.workspace_globals.update(functions)
                    self.engine.system_keys.update(functions.keys())
                    self.loaded_toolboxes[module_name] = toolbox_instance

                    return True, f"{toolbox_instance.name} cargado exitosamente."
            return False, "No se encontró una clase Toolbox válida en el módulo."
        except Exception as error:
            return False, f"Error al cargar {module_name}: {str(error)}"