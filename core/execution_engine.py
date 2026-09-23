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

        self.system_keys = set(self.workspace_globals.keys())
        self.toolboxes_cargados = {}

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
        """Convierte sintaxis matricial tipo MATLAB a una expresión válida en Python.

        Ejemplo:
            '[1 2; 3 4]' -> 'array([[1, 2], [3, 4]])'

        Esta función detecta bloques entre corchetes y los transforma en llamadas a
        `array(...)` para que NumPy entienda el formato MATLAB.

        Args:
            comando (str): Expresión a procesar.

        Returns:
            str: Comando transformado con la sintaxis de matrices convertida.
        """
        def reemplazar_matriz(match):
            """Transforma una matriz interna en la forma de NumPy."""
            contenido = match.group(1)
            filas = contenido.split(';')
            filas_py = []
            for fila in filas:
                # Reemplazar múltiples espacios o comas por una sola coma
                fila_limpia = re.sub(r'[,\s]+', ',', fila.strip())
                fila_limpia = fila_limpia.strip(',')
                filas_py.append(f"[{fila_limpia}]")
            return f"array([{', '.join(filas_py)}])"

        if '[' in comando and ']' in comando:
            return re.sub(r'\[(.*?)\]', reemplazar_matriz, comando)
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

    def execute_script(self, script_text: str):
        """Ejecuta un bloque completo de código en el entorno actual.

        Args:
            script_text (str): Script o conjunto de instrucciones a ejecutar.

        Returns:
            str | None: El mensaje de error si ocurre una excepción; de lo
            contrario, `None`.

        Este método es útil para correr varias líneas, definiciones de funciones o
        secuencias de comandos que no necesitan devolver un valor inmediato.
        """
        if not script_text.strip():
            return None
        try:
            exec(script_text, {}, self.workspace_globals)
            return None
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