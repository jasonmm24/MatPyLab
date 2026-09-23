"""Toolbox de demostración para control proporcional.

Este módulo sirve como ejemplo de un toolbox extensible para MatPyLab. Al
cargarse, expone funciones útiles en el entorno del usuario para realizar cálculos
simples relacionados con control básico y matrices numéricas.

El patrón esperado por el sistema es que el archivo `toolbox_init.py` defina una
función llamada `registrar_toolbox()`, la cual devuelve un diccionario con los
nombres públicos y las funciones que se añadirán al espacio de trabajo.
"""

import numpy as np


def ganancia_proporcional(error, kp=1.5):
    """Calcula una señal de control proporcional simple.

    Args:
        error: Valor o vector de error de la planta.
        kp (float): Ganancia proporcional. Por defecto es 1.5.

    Returns:
        El valor del error multiplicado por la ganancia proporcional.

    Ejemplo:
        ctrl_kp(2) -> 3.0
    """
    return error * kp


def matriz_identidad_personalizada(n):
    """Genera una matriz identidad multiplicada por pi.

    Args:
        n (int): Tamaño de la matriz identidad.

    Returns:
        np.ndarray: Matriz identidad de dimensión `n x n` multiplicada por pi.

    Ejemplo:
        matriz_pi(3)
        -> [[3.14159, 0, 0], [0, 3.14159, 0], [0, 0, 3.14159]]
    """
    return np.eye(n) * np.pi


def registrar_toolbox():
    """Registra las funciones del toolbox en el entorno del usuario.

    Returns:
        dict: Diccionario donde la clave es el nombre disponible en la consola y el
        valor es la función asociada.

    Este método es obligatorio para que `ExecutionEngine.cargar_toolbox()` pueda
    cargar el toolbox correctamente.
    """
    return {
        "ctrl_kp": ganancia_proporcional,
        "matriz_pi": matriz_identidad_personalizada
    }