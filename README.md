# MatPyLab

MatPyLab es un entorno gráfico de programación científica construido con Python y PySide6. Integra una consola interactiva, un editor de scripts, visualización de datos y extensiones para tareas de ingeniería y análisis numérico.

[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![Licencia MIT](https://img.shields.io/badge/Licencia-MIT-green.svg)](LICENSE)

Repositorio: [github.com/jasonmm24/MatPyLab](https://github.com/jasonmm24/MatPyLab)

## Características

- Consola interactiva y editor con pestañas para scripts Python y archivos `.m`.
- Ejecución de comandos, scripts y selecciones en un hilo de trabajo, con opción de detener la ejecución.
- Depuración básica mediante puntos de interrupción, continuación y ejecución paso a paso.
- Workspace inspeccionable y editable para variables escalares y arreglos numéricos de hasta dos dimensiones.
- Gráficas Matplotlib integradas en la ventana y paneles acoplables.
- Importación y exportación del workspace en formatos MATLAB `.mat` y NumPy `.npz`.
- Toolboxes opcionales que incorporan funciones al workspace.
- Visualizador de datos seriales en tiempo real.

## Alcance de la sintaxis MATLAB

MatPyLab ejecuta Python. El motor aplica una traducción limitada para matrices numéricas sencillas, operadores elemento a elemento (`.^`, `.*`, `./`), comentarios `%`, `grid on/off`, `hold on/off` y el comando `help nombre`. Los archivos `.m` se pueden abrir y guardar, pero no se interpretan mediante un runtime MATLAB ni se admite el lenguaje MATLAB completo. La ejecución de scripts usa `exec`; ejecuta únicamente código de fuentes confiables.

## Requisitos

- Una versión de Python compatible con las dependencias instaladas. El proyecto no declara actualmente una versión mínima en sus metadatos.
- pip y un entorno de escritorio compatible con PySide6/Qt.
- Las dependencias base de [requirements.txt](requirements.txt).

Los toolboxes avanzados requieren dependencias adicionales. Consulta [requirements-extras.txt](requirements-extras.txt); el toolbox de aprendizaje profundo también requiere instalar PyTorch por separado. Las librerías específicas solo son necesarias cuando se carga el toolbox que las importa.

## Instalación y ejecución

```bash
git clone https://github.com/jasonmm24/MatPyLab.git
cd MatPyLab
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

En Windows, activa el entorno con `.venv\Scripts\activate` antes de instalar las dependencias y ejecutar `python main.py`.

Para habilitar las dependencias de los toolboxes:

```bash
python -m pip install -r requirements-extras.txt
python -m pip install torch
```

La segunda orden es necesaria para cargar `tb_deep_learning.py`. No instales dependencias opcionales si no vas a usar sus toolboxes.

## Uso de la consola

Las funciones incluidas en el motor están disponibles al iniciar. Por ejemplo:

```python
A = [1 2; 3 4]
B = A.^2
plot(B)
```

Las funciones de toolbox no están disponibles hasta cargar la extensión. En la aplicación, usa el menú **Toolboxes**. También se pueden cargar desde Python:

```python
from core.execution_engine import ExecutionEngine

engine = ExecutionEngine()
ok, message = engine.toolbox_manager.load_toolbox("tb_control_system")
if ok:
    result, error = engine.execute_command("G = tf([1], [1, 2, 1])")
```

Un toolbox que depende de un paquete no instalado no podrá cargarse. Cada módulo documenta sus funciones en sus docstrings; los nombres exportados están enumerados más abajo.

## Toolboxes incluidos

| Archivo | Funciones exportadas | Dependencia específica |
| --- | --- | --- |
| `tb_control_system.py` | `tf`, `step`, `bode`, `feedback`, `pid`, `rlocus` | `control` |
| `tb_curve_fitting.py` | `polyfit`, `polyval`, `interp1` | SciPy |
| `tb_deep_learning.py` | `feedforwardnet`, `trainNetwork`, `predict` | PyTorch |
| `tb_image_processing.py` | `imread`, `imshow`, `rgb2gray`, `imbinarize` | OpenCV |
| `tb_matlab_coder.py` | `codegen` | Ninguna adicional |
| `tb_parallel_computing.py` | `parpool`, `parfor` | joblib |
| `tb_serial.py` | `serialport`, `write`, `readline`, `clear` | pyserial |
| `tb_signal_processing.py` | `butter`, `filtfilt`, `fft` | SciPy |
| `tb_stats_ml.py` | `fitlm`, `kmeans`, `pca` | scikit-learn |

La carga y el diseño de extensiones se describen en [toolboxes/README_TOOLBOXES.md](toolboxes/README_TOOLBOXES.md). `codegen` genera archivos fuente C, un encabezado y un Makefile; no transpila automáticamente código Python o MATLAB.

## Pruebas

Las dependencias de desarrollo incluyen Pytest. Instálalas y ejecuta la suite desde la raíz:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

La suite actual cubre el motor de ejecución, las operaciones básicas, la disponibilidad de NumPy, los errores y la limpieza del workspace.

## Estructura del proyecto

```text
MatPyLab/
├── core/                     Motor, configuración y carga de toolboxes
├── gui/                      Ventana, editores, visualización y widgets
│   └── widgets/               Widgets adicionales de la interfaz
├── tests/                    Pruebas automatizadas
├── toolboxes/                Extensiones científicas opcionales
├── config.json               Preferencias de usuario
├── main.py                   Punto de entrada
├── requirements.txt          Dependencias base
├── requirements-dev.txt      Dependencias de desarrollo y pruebas
├── requirements-extras.txt   Dependencias opcionales de toolboxes
├── LICENSE                   Licencia MIT
└── README.md                 Documentación del proyecto
```

## Catálogo de módulos

### Aplicación

- [main.py](main.py): inicializa Qt, crea la ventana principal y arranca el bucle de eventos.
- [core/config_manager.py](core/config_manager.py): lee y guarda `config.json`; completa las claves ausentes con valores predeterminados.
- [core/execution_engine.py](core/execution_engine.py): crea el workspace, registra funciones de NumPy y Matplotlib, traduce la sintaxis admitida, ejecuta comandos y scripts, y limpia variables de usuario. También conserva un cargador legado de toolboxes basados en carpetas.
- [core/toolbox_manager.py](core/toolbox_manager.py): define la clase base `MatpyLabToolbox` y carga módulos de toolbox basados en clases; incorpora sus funciones exportadas al workspace.
- [gui/main_window.py](gui/main_window.py): implementa la ventana, consola, editor por pestañas, explorador de archivos, panel de variables, gráficas, importación y exportación de workspaces, acciones de ejecución y depuración, y el menú actual de toolboxes.
- [gui/custom_widgets.py](gui/custom_widgets.py): proporciona entrada de consola con historial y un editor con números de línea, autocompletado y puntos de interrupción.
- [gui/serial_plotter.py](gui/serial_plotter.py): ofrece una ventana independiente para leer valores numéricos de un puerto serie y graficarlos en tiempo real.
- [gui/syntax_highlighter.py](gui/syntax_highlighter.py): aplica resaltado de sintaxis al editor y permite cambiar entre paletas clara y oscura.
- [gui/variable_editor.py](gui/variable_editor.py): permite editar valores escalares y arreglos numéricos de hasta dos dimensiones.
- [gui/variable_inspector.py](gui/variable_inspector.py): presenta variables en una tabla de solo lectura; para arreglos de más de dos dimensiones muestra la primera capa.
- `core/__init__.py`, `gui/__init__.py` y `toolboxes/__init__.py`: marcadores de paquete Python sin lógica adicional.
- `gui/widgets/__init__.py`: marcador del subpaquete de widgets.
- `gui/widgets/command_window.py`: archivo reservado, actualmente vacío; la consola activa está implementada en `gui/main_window.py`.

### Extensiones

- [toolboxes/tb_control_system.py](toolboxes/tb_control_system.py): funciones de transferencia, respuesta al escalón, diagramas de Bode, realimentación, control PID y lugar de raíces.
- [toolboxes/tb_curve_fitting.py](toolboxes/tb_curve_fitting.py): ajuste polinomial, evaluación de polinomios e interpolación unidimensional.
- [toolboxes/tb_deep_learning.py](toolboxes/tb_deep_learning.py): creación de redes MLP, entrenamiento con PyTorch y predicción.
- [toolboxes/tb_image_processing.py](toolboxes/tb_image_processing.py): lectura, visualización, conversión a escala de grises y binarización de imágenes.
- [toolboxes/tb_matlab_coder.py](toolboxes/tb_matlab_coder.py): genera los archivos C, header y Makefile a partir de una firma y una expresión proporcionadas.
- [toolboxes/tb_parallel_computing.py](toolboxes/tb_parallel_computing.py): consulta el número de procesadores y ejecuta funciones en paralelo con joblib.
- [toolboxes/tb_serial.py](toolboxes/tb_serial.py): abre puertos serie y ofrece operaciones de escritura, lectura de líneas y cierre.
- [toolboxes/tb_signal_processing.py](toolboxes/tb_signal_processing.py): diseña filtros Butterworth, filtra señales y calcula la FFT unidimensional.
- [toolboxes/tb_stats_ml.py](toolboxes/tb_stats_ml.py): regresión lineal, agrupamiento K-Means y análisis de componentes principales.
- [toolboxes/README_TOOLBOXES.md](toolboxes/README_TOOLBOXES.md): instrucciones para implementar y cargar toolboxes.

### Pruebas y configuración

- [tests/test_engine.py](tests/test_engine.py): pruebas de regresión del motor de ejecución.
- [config.json](config.json): tema y última carpeta seleccionada. Si no existe o no se puede leer, la aplicación utiliza valores predeterminados.
- [requirements.txt](requirements.txt), [requirements-dev.txt](requirements-dev.txt) y [requirements-extras.txt](requirements-extras.txt): dependencias base, de desarrollo y opcionales.
- [.gitignore](.gitignore): excluye cachés de Python, entornos virtuales y archivos locales de Qt y VS Code.
- [LICENSE](LICENSE): términos de distribución MIT.

## Contribuciones y licencia

Las contribuciones pueden proponerse mediante pull requests. Para cambios funcionales, incluye pruebas y actualiza la documentación afectada.

MatPyLab se distribuye bajo la licencia MIT. Consulta [LICENSE](LICENSE) para ver el texto completo.
