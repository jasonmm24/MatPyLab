# MatPyLab

<div align="center">

  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/Qt-PySide6-41CD52?logo=qt&logoColor=white" alt="Qt - PySide6" />
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License" />
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status active" />

</div>

MatPyLab es un entorno de programación científica y académica inspirado en MATLAB, pero construido sobre Python y librerías modernas de cómputo científico, visualización y aprendizaje automático.

Está pensado para personas que quieren trabajar en análisis numérico, procesamiento de señales, visión por computadora, control, estadística y prototipado rápido con una experiencia de interfaz similar a un IDE de cálculo técnico.

Repositorio oficial: https://github.com/jasonmm24/MatPyLab.git

## ¿Qué es MatPyLab?

MatPyLab combina:

- una interfaz gráfica tipo IDE con PySide6,
- una consola interactiva estilo MATLAB,
- un motor de ejecución basado en Python,
- soporte para scripts y comandos rápidos,
- extensibilidad mediante toolboxes modulares.

La idea principal es ofrecer un entorno accesible para trabajo científico sin abandonar el ecosistema Python.

## ✨ Características principales

- Consola interactiva con sintaxis similar a MATLAB
- Editor de scripts y panel de trabajo visual
- Explorador de archivos y gestión del espacio de trabajo
- Integración con NumPy, Matplotlib, SciPy, OpenCV y más
- Soporte para visualización de gráficos y datos seriales
- Sistema modular de toolboxes para ampliar funcionalidades
- Compatibilidad con tareas de ingeniería, ciencia de datos e investigación

## 🧠 Arquitectura del proyecto

```text
MatPyLab/
├── core/
│   ├── config_manager.py
│   ├── execution_engine.py
│   └── toolbox_manager.py
├── gui/
│   ├── custom_widgets.py
│   ├── main_window.py
│   ├── serial_plotter.py
│   ├── syntax_highlighter.py
│   ├── variable_editor.py
│   ├── variable_inspector.py
│   └── widgets/
├── toolboxes/
│   ├── README_TOOLBOXES.md
│   ├── tb_control_system.py
│   ├── tb_curve_fitting.py
│   ├── tb_deep_learning.py
│   ├── tb_image_processing.py
│   ├── tb_matlab_coder.py
│   ├── tb_parallel_computing.py
│   ├── tb_serial.py
│   ├── tb_signal_processing.py
│   └── tb_stats_ml.py
├── config.json
├── LICENSE
├── main.py
├── README.md
├── requirements.txt
└── .gitignore
```

### Core
La carpeta `core/` contiene la lógica principal de ejecución:

- `execution_engine.py`: motor del entorno, evaluación de expresiones y ejecución de scripts.
- `toolbox_manager.py`: carga y registro de módulos funcionales.
- `config_manager.py`: gestión de configuración de la aplicación.

### GUI
La carpeta `gui/` concentra la interfaz visual:

- ventana principal,
- widgets personalizados,
- editor de código,
- consola interactiva,
- panel de variables,
- trazado de gráficos y datos seriales.

### Toolboxes
Los toolboxes son extensiones modulares que agregan funciones sin modificar el núcleo del sistema. Cada toolbox define funciones que se incorporan al entorno del usuario y pueden usarse directamente desde la consola.

Ejemplos incluidos:

- control automático
- procesamiento de imágenes
- análisis de señales
- estadísticas y machine learning
- ajuste de curvas
- serial y adquisición de datos
- cómputo paralelo

## 🚀 Requisitos

- Python 3.10 o superior
- pip
- entorno compatible con PySide6 / Qt

## ⚙️ Instalación

Clona el repositorio e instala las dependencias:

```bash
git clone https://github.com/jasonmm24/MatPyLab.git
cd MatPyLab
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

En Windows, usa:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Ejecutar la aplicación

Desde la raíz del proyecto:

```bash
python main.py
```

## 🔧 Cómo cargar toolboxes

MatPyLab incluye un sistema modular de toolboxes en la carpeta `toolboxes/`. Para activarlos desde la interfaz:

1. ejecuta la aplicación con `python main.py`;
2. en la barra de herramientas verás un botón llamado `Toolboxes`;
3. haz clic en ese botón y selecciona el toolbox que quieras cargar;
4. las funciones exportadas por ese toolbox quedan disponibles en el workspace para usar en la consola.

También puedes cargar un toolbox desde código:

```python
from core.execution_engine import ExecutionEngine

engine = ExecutionEngine()
engine.toolbox_manager.load_toolbox("tb_image_processing")
```

Cuando el toolbox se carga correctamente, sus funciones se agregan al entorno global, por ejemplo:

```python
img = imread('foto.jpg')
imshow(img)
```

> Importante: los archivos deben estar dentro de la carpeta `toolboxes/` y deben definir una clase que herede de `MatpyLabToolbox` y exponga `export_functions()`.

## 🧪 Ejemplos de uso

### Comandos simples

```python
x = [1 2 3 4 5]
y = x.^2
plot(x, y)

A = [1 2; 3 4]
size(A, 1)
```

### Uso de un toolbox

```python
G = tf([1], [1, 2, 1])
step(G)
```

### Procesamiento de imágenes

```python
img = imread('foto.jpg')
imshow(img)
```

## 🧩 Cómo crear un toolbox

Puedes crear un archivo nuevo dentro de `toolboxes/` y definir una clase que herede de `MatpyLabToolbox`.

```python
from core.toolbox_manager import MatpyLabToolbox

class MiToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Mi Toolbox"

    @property
    def description(self):
        return "Descripción del toolbox"

    def export_functions(self):
        def saludar(nombre="Mundo"):
            print(f"Hola {nombre}!")

        return {"saludar": saludar}
```

Esto permite que la aplicación registre automáticamente las nuevas funciones para que puedan usarse desde la consola o sobre el workspace.

## 📌 Estado del proyecto

MatPyLab se encuentra en desarrollo activo y está orientado a ofrecer una experiencia práctica y educativa de programación científica, con énfasis en extensibilidad y prototipado rápido.

## 🤝 Contribución

Las contribuciones son bienvenidas. Si quieres colaborar:

1. haz un fork del proyecto,
2. crea una rama para tu cambio,
3. realiza tus mejoras o nuevos toolboxes,
4. abre un pull request con una descripción clara.

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

---

Hecho para entornos científicos, educativos y de investigación que buscan una experiencia similar a MATLAB, pero con la flexibilidad del ecosistema Python.
