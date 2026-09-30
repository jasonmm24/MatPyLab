"""Motor de ejecución del entorno de programación estilo MATLAB.

Este módulo implementa el intérprete principal de MatPyLab. Su responsabilidad es
crear un espacio de trabajo con funciones y objetos de NumPy y Matplotlib, permitir
la ejecución de comandos individuales o scripts completos, interpretar una sintaxis
similar a MATLAB para matrices y gestionar la carga y descarga de toolboxes.

El comportamiento principal es:
- Inicializar un diccionario global con funciones y constantes útiles del entorno.
- Exponer operaciones numéricas y gráficas sin requerir importaciones manuales.
- Traducir expresiones matriciales tipo MATLAB a Python válido.
- Ejecutar sentencias, evaluar expresiones y ejecutar scripts completos.
- Cargar toolboxes externos que agregan nuevas funciones al entorno.
- Limpiar variables definidas por el usuario sin borrar las funciones del sistema.
"""

import numpy as np
import matplotlib.pyplot as plt
import os
import importlib.util
import re
from core.toolbox_manager import ToolboxManager


class ExecutionEngine:
    """Gestiona el entorno de ejecución y la interacción con el usuario.

    Esta clase centraliza todo el comportamiento del entorno de trabajo. Se encarga
    de preparar los nombres disponibles para el usuario, ejecutar comandos, traducir
    sintaxis de MATLAB a Python y administrar toolboxes activos.
    """

    def __init__(self):
        """Inicializa el entorno con funciones auxiliares del sistema.

        Se habilita el modo interactivo de Matplotlib y se crea un diccionario
        `workspace_globals` con los elementos disponibles para evaluar código.
        Además, se registran las claves del sistema para distinguirlas de las
        variables creadas por el usuario.
        """
        plt.ion()
        self.workspace_globals = {'np': np, 'plt': plt}

        for attr in dir(np):
            if not attr.startswith('_'):
                self.workspace_globals[attr] = getattr(np, attr)
        for attr in dir(plt):
            if not attr.startswith('_'):
                self.workspace_globals[attr] = getattr(plt, attr)

        # --- ADAPTADORES EXACTOS DE MATLAB (Deben ir al final para evitar ser sobrescritos) ---
        def matlab_length(v):
            """
            Devuelve la longitud de la dimensión más grande de un arreglo.
            Uso: L = length(X)
            Ejemplo:
                v = [1 2 3 4 5]
                L = length(v)  % Devuelve 5
            """
            if hasattr(v, 'shape'):
                return max(v.shape) if v.shape else 1
            return len(v)

        def matlab_size(v, dim=None):
            """
            Devuelve el tamaño de un arreglo en cada dimensión.
            Uso: d = size(X) o d = size(X, dim)
            Ejemplo:
                M = [1 2; 3 4; 5 6]
                filas = size(M, 1)  % Devuelve 3
            """
            if hasattr(v, 'shape'):
                if dim is not None:
                    # Protección: Si la dimensión solicitada existe (MATLAB usa índice 1)
                    if (dim - 1) < len(v.shape):
                        return v.shape[dim-1]
                    # Si piden una dimensión extra (ej. la 3ra en un array 2D), MATLAB devuelve 1
                    else:
                        return 1
                return v.shape
            return np.shape(v)

        def matlab_help(tema):
            """Muestra la documentación y ejemplos de una función."""
            import inspect
            if isinstance(tema, str) and tema in self.workspace_globals:
                obj = self.workspace_globals[tema]
                nombre = tema
            elif callable(tema):
                obj = tema
                nombre = getattr(obj, '__name__', 'función')
            else:
                print(f"No se encontró ayuda para: {tema}")
                return

            doc = getattr(obj, '__doc__', None)
            print(f"\n{'='*50}\n 📖 Ayuda para: {nombre}\n{'='*50}")
            if doc:
                print(inspect.cleandoc(doc))
            else:
                print("No hay documentación o ejemplos disponibles para esta función.")
            print("="*50 + "\n")

        # Sobrescribir forzosamente cualquier función homónima inyectada previamente
        self.workspace_globals['length'] = matlab_length
        self.workspace_globals['size'] = matlab_size
        self.workspace_globals['help'] = matlab_help
        self.workspace_globals['disp'] = print  # Soporte nativo para imprimir en consola

        self.system_keys = set(self.workspace_globals.keys())
        self.toolboxes_cargados = {}
        self.toolbox_manager = ToolboxManager(self)

    def cargar_toolbox(self, carpeta):
        """Carga un toolbox desde la carpeta `toolboxes`.

        Args:
            carpeta (str): Nombre de la carpeta del toolbox a cargar.

        Este método busca un archivo `toolbox_init.py` dentro de la ruta del
        proyecto y, si existe, lo ejecuta para registrar nuevas funciones.
        Las funciones añadidas se incorporan al entorno global del motor.
        """
        if carpeta in self.toolboxes_cargados:
            return

        ruta_init = os.path.join(os.getcwd(), "toolboxes", carpeta, "toolbox_init.py")
        if os.path.isfile(ruta_init):
            try:
                spec = importlib.util.spec_from_file_location(f"toolbox_{carpeta}", ruta_init)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)

                if hasattr(modulo, 'registrar_toolbox'):
                    funciones_nuevas = modulo.registrar_toolbox()
                    self.workspace_globals.update(funciones_nuevas)
                    self.system_keys.update(funciones_nuevas.keys())
                    self.toolboxes_cargados[carpeta] = list(funciones_nuevas.keys())
                    print(f"\n>> Toolbox activado: {carpeta}")
            except Exception as e:
                print(f"\n>> Error al cargar toolbox {carpeta}: {e}")

    def descargar_toolbox(self, carpeta):
        """Elimina las funciones de un toolbox del entorno actual.

        Args:
            carpeta (str): Nombre del toolbox que se desea desactivar.

        Cuando un toolbox está cargado, este método elimina las funciones que
        añadió de la tabla global del entorno para evitar conflictos o fugas de
        estado entre sesiones.
        """
        if carpeta in self.toolboxes_cargados:
            claves = self.toolboxes_cargados.pop(carpeta)
            for k in claves:
                self.workspace_globals.pop(k, None)
                self.system_keys.discard(k)
            print(f"\n>> Toolbox desactivado: {carpeta}")

    def preprocesar_sintaxis(self, comando: str) -> str:
        """Traduce sintaxis de MATLAB a Python en tiempo real."""
        import re

        strings_protegidos = {}

        def enmascarar(match):
            llave = f"__STR_{len(strings_protegidos)}__"
            strings_protegidos[llave] = match.group(0)
            return llave

        comando = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', enmascarar, comando)

        comando = re.sub(r'\%(.*)', r'#\1', comando)
        comando = re.sub(r'^help\s+([a-zA-Z0-9_]+)(?:\(\))?', r"help('\1')", comando)
        comando = re.sub(r'\bgrid\s+on\b', 'grid(True)', comando)
        comando = re.sub(r'\bgrid\s+off\b', 'grid(False)', comando)
        comando = re.sub(r'\bhold\s+on\b', 'hold(True)', comando)
        comando = re.sub(r'\bhold\s+off\b', 'hold(False)', comando)

        comando = comando.replace('.^', '**')
        comando = comando.replace('.*', '*')
        comando = comando.replace('./', '/')

        def reemplazar_matriz(match):
            contenido = match.group(1)
            if ',' in contenido and ';' not in contenido:
                return match.group(0)
            filas = contenido.split(';')
            filas_python = []
            for fila in filas:
                elementos = [elemento for elemento in fila.strip().split() if elemento]
                if elementos:
                    filas_python.append("[" + ", ".join(elementos) + "]")
            if not filas_python:
                return match.group(0)
            return "np.array([" + ", ".join(filas_python) + "])"

        comando = re.sub(r'(?<![a-zA-Z0-9_])\[(.*?)\]', reemplazar_matriz, comando)

        for llave, valor in strings_protegidos.items():
            comando = comando.replace(llave, valor)

        return comando

    def execute_command(self, command: str):
        """Ejecuta una instrucción única y devuelve su resultado.

        Args:
            command (str): Comando o expresión a evaluar.

        Returns:
            tuple: Una tupla con `(resultado, error)`. Si hay éxito, `error` es
            `None`; si falla, `resultado` es `None` y `error` contiene el mensaje.

        La sintaxis se preprocesa antes de evaluarse. Si la expresión es válida y
        produce un valor, se retorna; si no, se intenta ejecutar como sentencia
        imperativa (por ejemplo, asignaciones o llamadas sin valor de retorno).
        """
        if not command.strip():
            return None, None

        command = self.preprocesar_sintaxis(command)

        try:
            result = eval(command, {}, self.workspace_globals)
            return result, None
        except SyntaxError:
            try:
                exec(command, {}, self.workspace_globals)
                return None, None
            except Exception as e:
                return None, str(e)
        except Exception as e:
            return None, str(e)

    def execute_script(self, codigo: str):
        try:
            lineas = codigo.split('\n')
            codigo_traducido = []

            for linea in lineas:
                if linea.strip().startswith('#'):
                    codigo_traducido.append(linea)
                else:
                    codigo_traducido.append(self.preprocesar_sintaxis(linea))

            codigo_final = "\n".join(codigo_traducido)
            exec(codigo_final, self.workspace_globals)
        except Exception as e:
            return str(e)

    def clear_workspace(self):
        """Elimina las variables creadas por el usuario, conservando el sistema.

        Esta operación no borra funciones internas del entorno ni las importadas por
        toolboxes activos, y solo elimina los nombres que no estaban presentes en la
        inicialización del sistema.
        """
        claves_usuario = [k for k in self.workspace_globals.keys() if k not in self.system_keys]
        for k in claves_usuario:
            del self.workspace_globals[k]