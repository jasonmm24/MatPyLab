# Toolboxes de MatPyLab

Los toolboxes son extensiones modulares que agregan nuevas funciones al entorno de ejecución de MatPyLab sin modificar el núcleo del programa. Permiten separar funcionalidades por categoría, como control, matemáticas rápidas o utilidades específicas.

## ¿Qué es un toolbox?

Un toolbox es una carpeta dentro de `toolboxes/` que contiene un archivo `toolbox_init.py` y, opcionalmente, otros archivos auxiliares como librerías compiladas, módulos adicionales o scripts de soporte.

Cuando el usuario activa un toolbox desde la interfaz, MatPyLab ejecuta ese archivo `toolbox_init.py` y obtiene un diccionario de funciones que se incorporan al espacio de trabajo global.

## Estructura típica

```text
toolboxes/
├── demo_control/
│   └── toolbox_init.py
├── fast_math/
│   ├── fast_math.cpp
│   ├── fast_math.so
│   ├── Makefile
│   └── toolbox_init.py
└── README_TOOLBOXES.md
```

## Cómo se registra un toolbox

El archivo `toolbox_init.py` debe implementar una función llamada `registrar_toolbox()`. Esa función debe devolver un diccionario con el siguiente formato:

```python
return {
    "nombre_funcion": funcion_python,
    "otra_funcion": otra_funcion
}
```

La clave del diccionario será el nombre visible para el usuario dentro de la consola o el entorno de ejecución, y el valor será la función real que se ejecutará.

### Ejemplo básico

```python
import numpy as np


def sumar_matrices(a, b):
    return np.array(a) + np.array(b)


def registrar_toolbox():
    return {
        "sumar_matrices": sumar_matrices
    }
```

Cuando ese toolbox es cargado, `sumar_matrices` quedará disponible en el entorno como si fuera una función nativa.

## Cómo los carga MatPyLab

El motor principal de ejecución se encarga de buscar la carpeta del toolbox y ejecutar ese archivo:

- Si existe `toolboxes/<nombre>/toolbox_init.py`
- Se importa el módulo
- Se llama a `registrar_toolbox()`
- Las funciones devueltas se agregan a `workspace_globals`

Esto permite que el usuario use esas funciones directamente en la Command Window.

## Toolboxes nativos y toolboxes Python

Hay dos tipos principales de extensiones:

### 1. Toolbox en Python puro

Se usa cuando la lógica puede implementarse directamente en Python.

Ejemplo:
- cálculos matemáticos
- transformaciones de matrices
- utilidades de análisis

### 2. Toolbox con biblioteca compilada

Se usa cuando se requiere mayor rendimiento o se integra código C/C++.

En ese caso el patrón es:
- compilar una librería compartida (.so)
- cargarla con `ctypes` desde Python
- envolver la llamada en una función Python
- devolver esa función desde `registrar_toolbox()`

## Ejemplo del toolbox `demo_control`

Este toolbox expone funciones como:

- `ctrl_kp`
- `matriz_pi`

Estas funciones sirven como demostración de cómo un toolbox puede ampliar el entorno con funciones útiles para control y cálculo matricial.

## Ejemplo del toolbox `fast_math`

Este toolbox muestra cómo integrar código C++ con Python:

- `fast_math.cpp` define una función nativa
- `Makefile` compila la librería
- `toolbox_init.py` usa `ctypes` para cargarla
- `pid_rapido` queda disponible en la consola

## Recomendaciones para crear un nuevo toolbox

1. Crea una carpeta nueva dentro de `toolboxes/`
2. Agrega un archivo `toolbox_init.py`
3. Define una función `registrar_toolbox()`
4. Devuelve un diccionario con las funciones que quieras exponer
5. Si necesitas rendimiento, compila una biblioteca nativa y cárgala con `ctypes`
6. Prueba el toolbox desde la interfaz de MatPyLab

## Convención importante

El nombre del archivo debe ser siempre:

```python
toolbox_init.py
```

Y la función de registro debe existir obligatoriamente:

```python
def registrar_toolbox():
    ...
```

## Beneficios

Los toolboxes permiten:

- mantener el núcleo más limpio
- extender MatPyLab sin tocar código central
- organizar funciones por dominio
- agregar optimizaciones nativas cuando sea necesario

## Resumen

Un toolbox es una extensión modular de MatPyLab que se activa desde la interfaz y añade funciones al entorno del usuario. Para funcionar, solo necesita:

- una carpeta dentro de `toolboxes/`
- un archivo `toolbox_init.py`
- una función `registrar_toolbox()` que devuelva un diccionario de funciones

Con esa estructura, MatPyLab puede ampliar su funcionalidad de forma sencilla y reutilizable.
