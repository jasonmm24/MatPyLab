"""Carga y expone la biblioteca nativa de cálculo rápido.

Este archivo actúa como puente entre MatPyLab y la función compilada en C++
`calcular_pid`. Su tarea es localizar la librería compartida `fast_math.so`,
cargarla con `ctypes` y exponer una función Python de alto nivel que el usuario
pueda invocar desde la consola o desde scripts del entorno.

La idea es combinar rendimiento nativo con un interfaz amigable para el usuario.
"""

import ctypes
import os


def registrar_toolbox():
    """Carga la librería compartida y registra una función pública del toolbox.

    Returns:
        dict: Diccionario con la función `pid_rapido` disponible en el entorno.

    Si la librería no ha sido compilada aún, se imprime un mensaje de error y se
    devuelve un diccionario vacío para evitar fallos del sistema.
    """
    ruta_lib = os.path.join(os.path.dirname(__file__), "fast_math.so")

    if not os.path.exists(ruta_lib):
        print(f"\n>> Falla: Librería no compilada en {ruta_lib}")
        return {}

    try:
        # 1. Cargar la librería dinámica compilada.
        lib_cpp = ctypes.CDLL(ruta_lib)

        # 2. Configurar estrictamente los tipos de datos (doble precisión).
        lib_cpp.calcular_pid.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
        lib_cpp.calcular_pid.restype = ctypes.c_double

        # 3. Envolver la llamada en una función limpia para el usuario.
        def pid_rapido(error, kp, kd):
            """Ejecuta la función nativa `calcular_pid` con argumentos del usuario.

            Args:
                error (float): Señal de error.
                kp (float): Ganancia proporcional.
                kd (float): Ganancia derivativa.

            Returns:
                float: Resultado calculado por la implementación C++.
            """
            return lib_cpp.calcular_pid(error, kp, kd)

        return {
            "pid_rapido": pid_rapido
        }
    except Exception as e:
        print(f"\n>> Error al cargar ctypes: {e}")
        return {}