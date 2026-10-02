"""Interfaz gráfica principal de MatPyLab.

Este módulo define la ventana principal de la aplicación, la consola interactiva,
la gestión de toolboxes y el explorador de archivos. Su objetivo es ofrecer una
experiencia visual similar a un entorno MATLAB o IDE científico, con un editor,
una consola de comandos, un panel del espacio de trabajo y un acceso rápido a
funcionalidades como abrir archivos, guardar scripts y cambiar el tema.

La aplicación conecta la GUI con el motor de ejecución a través de
`ExecutionEngine`, permitiendo ejecutar comandos y scripts desde la interfaz.
"""

import sys
import os
import re
import threading
from pathlib import Path
import matplotlib
matplotlib.use('qtagg')  # Forzar a Matplotlib a usar el backend de Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QTextEdit, QTableWidget,
                               QWidget, QVBoxLayout, QTableWidgetItem,
                               QToolBar, QTreeView, QFileSystemModel, QFileDialog,
                               QDialog, QListWidget, QDialogButtonBox, QCompleter,
                               QToolTip, QStyle, QTabWidget)
from PySide6.QtWidgets import QToolButton, QMenu
from PySide6.QtGui import QAction, QTextCursor
from PySide6.QtCore import Qt, QObject, QThread, Signal, QStringListModel, QSize
from core.execution_engine import ExecutionEngine
from core.config_manager import load_config, save_config
from PySide6.QtWidgets import QListWidgetItem
from gui.syntax_highlighter import PythonHighlighter
from gui.custom_widgets import CodeEditor, ConsoleInput
from gui.variable_inspector import VariableInspector
from gui.variable_editor import VariableEditorDialog
from gui.serial_plotter import SerialPlotterWindow


class ExecutionCancelled(BaseException):
    """Señala una cancelación cooperativa del código ejecutado."""


class GuiThreadExecutor(QObject):
    """Ejecuta operaciones que modifican widgets Qt en el hilo de la GUI."""

    call_requested = Signal(object, object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.call_requested.connect(self._execute, Qt.QueuedConnection)

    def invoke(self, callback):
        if QThread.currentThread() == self.thread():
            return callback()

        completed = threading.Event()
        result = {}
        self.call_requested.emit(callback, completed, result)
        while not completed.wait(0.05):
            if QThread.currentThread().isInterruptionRequested():
                raise ExecutionCancelled()

        if "error" in result:
            raise result["error"]
        return result.get("value")

    def _execute(self, callback, completed, result):
        try:
            result["value"] = callback()
        except Exception as error:
            result["error"] = error
        finally:
            completed.set()


class ExecutionWorker(QThread):
    """Ejecuta un comando o script sin bloquear el hilo de la interfaz."""

    result_ready = Signal(object)
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, engine, code, mode="script", parent=None):
        super().__init__(parent)
        self.engine = engine
        self.code = code
        self.mode = mode
        self.outcome = "running"

    def run(self):
        previous_trace = sys.gettrace()

        def check_interruption(frame, event, arg):
            if event == "line" and self.isInterruptionRequested():
                raise ExecutionCancelled()
            return check_interruption

        sys.settrace(check_interruption)
        try:
            if self.mode == "command":
                result, error = self.engine.execute_command(self.code)
                if error:
                    self.outcome = "error"
                    self.error.emit(error)
                elif result is not None:
                    self.result_ready.emit(result)
            else:
                error = self.engine.execute_script(self.code)
                if error:
                    self.outcome = "error"
                    self.error.emit(error)
        except ExecutionCancelled:
            self.outcome = "cancelled"
            self.cancelled.emit()
        except Exception as error:
            self.outcome = "error"
            self.error.emit(str(error))
        else:
            if self.outcome == "running":
                self.outcome = "completed"
        finally:
            sys.settrace(previous_trace)

    def request_stop(self):
        self.requestInterruption()


class StreamRedirector(QObject):
    """Redirige la salida estándar hacia la consola de la aplicación.

    Esta clase actúa como un objeto de tipo `sys.stdout` para capturar texto que se
    imprima en la terminal del proceso y mostrarlo dentro del widget de la consola.
    """

    texto_escrito = Signal(str)

    def write(self, text):
        """Emite el texto recibido como una señal para mostrarlo en la interfaz."""
        self.texto_escrito.emit(text)

    def flush(self):
        """Método obligatorio para compatibilidad con objetos tipo archivo."""
        pass


class ToolboxManager(QDialog):
    """Diálogo para activar o desactivar toolboxes disponibles en el proyecto.

    Muestra una lista de carpetas dentro de `toolboxes`, permitiendo al usuario
    marcar las que desea cargar en el entorno actual del programa.
    """

    def __init__(self, engine, parent=None):
        """Inicializa el gestor de toolboxes y construye la interfaz del diálogo."""
        super().__init__(parent)
        self.engine = engine
        self.setWindowTitle("Gestor de Toolboxes")
        self.resize(350, 300)

        layout = QVBoxLayout(self)
        self.lista = QListWidget()
        self.lista.setStyleSheet("font-size: 14px; padding: 5px;")
        layout.addWidget(self.lista)

        self.cargar_lista()

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.aplicar_cambios)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def cargar_lista(self):
        """Carga la lista de toolboxes disponibles en el directorio del proyecto."""
        ruta_toolboxes = os.path.join(os.getcwd(), "toolboxes")
        if os.path.exists(ruta_toolboxes):
            for carpeta in sorted(os.listdir(ruta_toolboxes)):
                ruta_carpeta = os.path.join(ruta_toolboxes, carpeta)
                if os.path.isdir(ruta_carpeta) and not carpeta.startswith("__"):
                    item = QListWidgetItem(f"📦 {carpeta}")
                    item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

                    if carpeta in self.engine.toolboxes_cargados:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)

                    item.setData(Qt.UserRole, carpeta)
                    self.lista.addItem(item)

    def aplicar_cambios(self):
        """Aplica los cambios seleccionados en los toolboxes activos."""
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            carpeta = item.data(Qt.UserRole)

            if item.checkState() == Qt.Checked:
                self.engine.cargar_toolbox(carpeta)
            else:
                self.engine.descargar_toolbox(carpeta)
        self.accept()


class MatpyLabWindow(QMainWindow):
    """Ventana principal de la aplicación MatPyLab.

    Esta clase encapsula la interfaz gráfica completa: editor, consola, explorador
    de archivos, panel del workspace y controles principales para ejecutar código y
    manipular el entorno de trabajo.
    """

    def __init__(self):
        """Configura la ventana principal, los docks, la consola y el motor de ejecución."""
        super().__init__()
        self.config = load_config()
        self.setWindowTitle("MatpyLab - v0.1")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.cerrar_pestana)
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #3c3f41; }
            QTabBar::tab { background: #2b2b2b; color: #888888; padding: 8px 15px; border-right: 1px solid #3c3f41; }
            QTabBar::tab:selected { background: #1e1e1e; color: #ffffff; font-weight: bold; border-top: 2px solid #00BFFF; }
        """)
        self.setCentralWidget(self.tabs)

        self.setup_command_window()

        self.engine = ExecutionEngine()
        self.worker = None
        self.gui_executor = GuiThreadExecutor(self)
        self.plotter_window = None

        self.setup_workspace()
        self.setup_file_explorer()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_files)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_workspace)
        self.splitDockWidget(self.dock_files, self.dock_workspace, Qt.Vertical)
        self.setup_plots_dock()
        self.setup_toolbar()
        self.actualizar_autocompletado()

        self.is_dark_mode = self.config.get("theme") != "light"
        if self.is_dark_mode:
            self.aplicar_tema_oscuro()
        else:
            self.aplicar_tema_claro()

        self.actualizar_autocompletado()

    def setup_command_window(self):
        """Crea el dock de la consola de comandos y su entrada interactiva."""
        self.dock_console = QDockWidget("Command Window", self)
        self.dock_console.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)

        self.console_output = QTextEdit()
        self.console_output.document().setMaximumBlockCount(5000)
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 14px;")

        self.stdout_redirector = StreamRedirector()
        self.stdout_redirector.texto_escrito.connect(self.escribir_en_consola)
        sys.stdout = self.stdout_redirector
        sys.stderr = self.stdout_redirector

        mensaje_inicio = (
            '<div style="font-family: Consolas, monospace; margin-bottom: 10px;">'
            '<span style="font-weight: bold;">MatpyLab v0.1 (R2026a)</span><br>'
            '<span>Para uso académico y desarrollo de ingeniería.</span><br>'
            '<span style="color: #888888;">Escribe tus comandos a continuación o presiona F5 para ejecutar un script.</span>'
            '</div><br>'
        )
        self.console_output.setHtml(mensaje_inicio)

        self.console_input = ConsoleInput()
        self.console_input.setPlaceholderText(">> Ingresa un comando y presiona Enter...")
        self.console_input.setStyleSheet("background-color: #2d2d2d; color: #ffffff; font-family: Consolas, monospace; font-size: 14px; padding: 4px;")

        console_layout.addWidget(self.console_output)
        console_layout.addWidget(self.console_input)
        self.dock_console.setWidget(console_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_console)

        self.console_input.returnPressed.connect(self.procesar_comando)

        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.console_input.setCompleter(self.completer)

        self.console_input.textChanged.connect(self.mostrar_ayuda_funcion)

    def setup_workspace(self):
        """Crea el panel donde se muestran las variables activas del entorno."""
        self.dock_workspace = QDockWidget("Workspace", self)
        self.dock_workspace.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.workspace_table = QTableWidget()
        self.workspace_table.cellDoubleClicked.connect(self.editar_variable)
        self.workspace_table.setColumnCount(4)
        self.workspace_table.setHorizontalHeaderLabels(["Name", "Value", "Size", "Class"])
        self.workspace_table.horizontalHeader().setStretchLastSection(True)
        self.dock_workspace.setWidget(self.workspace_table)

    def setup_plots_dock(self):
        self.dock_plots = QDockWidget("📈 Plots", self)
        self.dock_plots.setAllowedAreas(Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.dock_plots.setWidget(container)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_plots)
        self.dock_plots.hide()

        self.ax = self.figure.add_subplot(111)

        import matplotlib.pyplot as plt

        self._original_figure = plt.figure
        self._original_show = plt.show
        self._original_gcf = plt.gcf
        self._original_gca = plt.gca

        def figura_integrada(*args, **kwargs):
            """Redirige pyplot a la figura embebida y limpia el lienzo."""
            self.dock_plots.show()
            if args and args[0] is self.figure:
                return self.figure
            self.figure.clear()
            self.ax = None
            return self.figure

        def eje_integrado():
            """Devuelve el eje activo de la figura embebida, creándolo si hace falta."""
            if self.ax not in self.figure.axes:
                self.ax = self.figure.gca()
            return self.ax

        def mostrar_integrada(*args, **kwargs):
            """Actualiza el canvas integrado en lugar de abrir una ventana."""
            self.dock_plots.show()
            self.canvas.draw()

        plt.figure = figura_integrada
        plt.show = mostrar_integrada
        plt.gcf = lambda: self.figure
        plt.gca = eje_integrado

        def custom_figure(*args, **kwargs):
            self.dock_plots.show()
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            self.canvas.draw()

        def custom_plot(*args, **kwargs):
            """
            Crea una gráfica lineal en 2D.
            Uso: plot(X, Y, 'estilo')
            Ejemplo:
                t = linspace(0, 2*np.pi, 100)
                y = np.sin(t)
                plot(t, y, 'b-', linewidth=2)
                grid on
            """
            self.dock_plots.show()
            if self.ax not in self.figure.axes or self.ax.name != 'rectilinear':
                self.figure.clear()
                self.ax = self.figure.add_subplot(111)
            result = self.ax.plot(*args, **kwargs)
            self.canvas.draw()
            return result

        def custom_plot3(*args, **kwargs):
            """
            Crea una gráfica de líneas en 3D.
            Uso: plot3(X, Y, Z, 'estilo')
            Ejemplo:
                t = linspace(0, 10*np.pi, 200)
                plot3(np.sin(t), np.cos(t), t)
                grid on
            """
            self.dock_plots.show()
            if self.ax not in self.figure.axes or self.ax.name != '3d':
                self.figure.clear()
                self.ax = self.figure.add_subplot(111, projection='3d')
            result = self.ax.plot(*args, **kwargs)
            self.canvas.draw()
            return result

        def custom_grid(state=True):
            eje_integrado().grid(state)
            self.canvas.draw()

        def custom_hold(state=True):
            # Matplotlib superpone las gráficas nativamente; absorbe el comando de MATLAB.
            pass

        def custom_title(label, *args, **kwargs):
            eje_integrado().set_title(label, *args, **kwargs)
            self.canvas.draw()

        def custom_xlabel(xlabel, *args, **kwargs):
            eje_integrado().set_xlabel(xlabel, *args, **kwargs)
            self.canvas.draw()

        def custom_ylabel(ylabel, *args, **kwargs):
            eje_integrado().set_ylabel(ylabel, *args, **kwargs)
            self.canvas.draw()

        def custom_zlabel(zlabel, *args, **kwargs):
            eje = eje_integrado()
            if hasattr(eje, 'set_zlabel'):
                eje.set_zlabel(zlabel, *args, **kwargs)
                self.canvas.draw()

        def custom_legend(*args, **kwargs):
            eje_integrado().legend(*args, **kwargs)
            self.canvas.draw()

        def ejecutar_en_gui(funcion):
            def wrapper(*args, **kwargs):
                return self.gui_executor.invoke(lambda: funcion(*args, **kwargs))
            return wrapper

        funciones_graficas = {
            'figure': ejecutar_en_gui(custom_figure),
            'plot': ejecutar_en_gui(custom_plot),
            'plot3': ejecutar_en_gui(custom_plot3),
            'grid': ejecutar_en_gui(custom_grid),
            'title': ejecutar_en_gui(custom_title),
            'legend': ejecutar_en_gui(custom_legend),
            'xlabel': ejecutar_en_gui(custom_xlabel),
            'ylabel': ejecutar_en_gui(custom_ylabel),
            'zlabel': ejecutar_en_gui(custom_zlabel),
            'hold': ejecutar_en_gui(custom_hold)
        }
        self.engine.workspace_globals.update(funciones_graficas)
        self.engine.system_keys.update(funciones_graficas.keys())

    def closeEvent(self, event):
        """Restaura pyplot para no dejar el monkey patch activo al cerrar la GUI."""
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_stop()
            self.escribir_en_consola("Solicitud de detención enviada; cierra MatpyLab cuando termine la ejecución.\n")
            event.ignore()
            return

        import matplotlib.pyplot as plt

        plt.figure = self._original_figure
        plt.show = self._original_show
        plt.gcf = self._original_gcf
        plt.gca = self._original_gca
        super().closeEvent(event)

    def procesar_comando(self):
        """Procesa la entrada de comando de la consola y la ejecuta en el motor."""
        comando = self.console_input.text()
        self.console_input.add_to_history(comando)
        if not comando.strip():
            return

        self.escribir_en_consola(f">> {comando}\n")
        self.console_input.clear()

        if comando.strip() == 'clc':
            self.console_output.clear()
            return

        if comando.strip() == 'clear':
            self.limpiar_workspace_interfaz()
            return

        self.ejecutar_codigo(comando, mode="command")

    def limpiar_workspace_interfaz(self):
        self.engine.clear_workspace()
        self.actualizar_workspace()
        self.console_output.append('<span style="color: #4CAF50;">>> Workspace limpiado.</span>')

    def actualizar_workspace(self):
        """Actualiza la tabla del workspace con variables del entorno actual."""
        self.workspace_table.setRowCount(0)

        variables = {k: v for k, v in self.engine.workspace_globals.items() if not k.startswith('__') and k not in self.engine.system_keys}

        self.workspace_table.setRowCount(len(variables))

        for row, (nombre, valor) in enumerate(variables.items()):
            self.workspace_table.setItem(row, 0, QTableWidgetItem(nombre))

            # Limpieza visual para la columna "Value"
            clase_nombre = type(valor).__name__
            if clase_nombre == 'TransferFunction':
                str_valor = "[Función de Transferencia]"
            elif hasattr(valor, 'shape') and getattr(valor, 'size', 0) > 10:
                str_valor = f"[{valor.shape[0]}x{valor.shape[1]} double]" if len(valor.shape) == 2 else f"[{valor.size} elements]"
            else:
                str_valor = str(valor).replace('\n', ' ')
                if len(str_valor) > 40:
                    str_valor = str_valor[:37] + "..."
            self.workspace_table.setItem(row, 1, QTableWidgetItem(str_valor))

            size_str = "1x1"
            if hasattr(valor, "shape"):
                size_str = "x".join(map(str, valor.shape)) if valor.shape else "1x1"
            elif isinstance(valor, (list, str, dict)):
                size_str = f"1x{len(valor)}"
            self.workspace_table.setItem(row, 2, QTableWidgetItem(size_str))
            self.workspace_table.setItem(row, 3, QTableWidgetItem(type(valor).__name__))

        self.actualizar_autocompletado()
        self.canvas.draw()

    def abrir_inspector_variables(self, item):
        """Abre el inspector visual para la variable seleccionada con doble clic."""
        fila = item.row()
        nombre_item = self.workspace_table.item(fila, 0)

        if nombre_item:
            nombre_var = nombre_item.text()
            if nombre_var in self.engine.workspace_globals:
                valor = self.engine.workspace_globals[nombre_var]
                inspector = VariableInspector(nombre_var, valor, self)

                if getattr(self, 'is_dark_mode', True):
                    inspector.setStyleSheet("""
                        QDialog { background-color: #2b2b2b; color: #ffffff; }
                        QTableWidget { background-color: #1e1e1e; color: #ffffff; gridline-color: #3c3f41; }
                        QHeaderView::section { background-color: #3c3f41; color: #ffffff; }
                    """)
                else:
                    inspector.setStyleSheet("""
                        QDialog { background-color: #f0f0f0; color: #000000; }
                        QTableWidget { background-color: #ffffff; color: #000000; gridline-color: #d0d0d0; }
                        QHeaderView::section { background-color: #e0e0e0; color: #000000; }
                    """)

                inspector.exec()

    def editar_variable(self, row, column):
        """Edita una variable compatible y actualiza el namespace del motor."""
        if self.worker is not None and self.worker.isRunning():
            self.escribir_en_consola("No se pueden editar variables durante una ejecución.\n")
            return

        nombre_item = self.workspace_table.item(row, 0)
        if nombre_item is None:
            return

        nombre_var = nombre_item.text()
        if nombre_var in {"np", "pd", "plt"} or nombre_var.startswith("__"):
            return

        if nombre_var not in self.engine.workspace_globals:
            return

        valor_actual = self.engine.workspace_globals[nombre_var]
        if callable(valor_actual) or isinstance(valor_actual, type(sys)):
            return

        dialog = VariableEditorDialog(nombre_var, valor_actual, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.engine.workspace_globals[nombre_var] = dialog.new_value
            self.escribir_en_consola(f"Variable '{nombre_var}' actualizada manualmente.\n")
            self.actualizar_workspace()

    def setup_toolbar(self):
        """Configura la barra de herramientas con comandos principales."""
        toolbar = QToolBar("Barra de Herramientas Principal")
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        estilo = self.style()

        self.theme_action = QAction(estilo.standardIcon(QStyle.SP_DesktopIcon), "Tema", self)
        self.theme_action.triggered.connect(self.toggle_tema)
        toolbar.addAction(self.theme_action)

        new_action = QAction(estilo.standardIcon(QStyle.SP_FileIcon), "Nuevo", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(lambda: self.nuevo_script())
        toolbar.addAction(new_action)

        open_action = QAction(estilo.standardIcon(QStyle.SP_DialogOpenButton), "Abrir", self)
        open_action.triggered.connect(self.open_folder)
        toolbar.addAction(open_action)

        open_script_action = QAction(estilo.standardIcon(QStyle.SP_FileIcon), "Abrir Script", self)
        open_script_action.setShortcut("Ctrl+O")
        open_script_action.triggered.connect(self.abrir_dialogo_archivo)
        toolbar.addAction(open_script_action)

        save_action = QAction(estilo.standardIcon(QStyle.SP_DialogSaveButton), "Guardar", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.guardar_script)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        clear_workspace_act = QAction(estilo.standardIcon(QStyle.SP_TrashIcon), "Clear\nWorkspace", self)
        clear_workspace_act.triggered.connect(self.limpiar_workspace_interfaz)
        toolbar.addAction(clear_workspace_act)
        self.clear_workspace_action = clear_workspace_act

        toolbar.addSeparator()

        clear_cmd_act = QAction(estilo.standardIcon(QStyle.SP_BrowserReload), "Clear\nCommands", self)
        clear_cmd_act.triggered.connect(lambda: self.console_output.clear())
        toolbar.addAction(clear_cmd_act)

        run_action = QAction(estilo.standardIcon(QStyle.SP_MediaPlay), "Run\nScript", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.ejecutar_script)
        toolbar.addAction(run_action)
        self.run_action = run_action

        run_sel_action = QAction(estilo.standardIcon(QStyle.SP_MediaSkipForward), "Run\nSelection", self)
        run_sel_action.setShortcut("F9")
        run_sel_action.triggered.connect(self.ejecutar_seleccion)
        toolbar.addAction(run_sel_action)
        self.run_selection_action = run_sel_action

        self.stop_action = QAction(estilo.standardIcon(QStyle.SP_BrowserStop), "Stop", self)
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.detener_ejecucion)
        toolbar.addAction(self.stop_action)

        serial_plotter_action = QAction(
            estilo.standardIcon(QStyle.SP_ComputerIcon), "Serial Plotter", self
        )
        serial_plotter_action.triggered.connect(self.abrir_serial_plotter)
        toolbar.addAction(serial_plotter_action)

        toolbar.addSeparator()

        toolboxes_btn = QToolButton(self)
        toolboxes_btn.setText("Toolboxes")
        toolboxes_btn.setIcon(estilo.standardIcon(QStyle.SP_DirOpenIcon))
        toolboxes_btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        toolboxes_btn.setPopupMode(QToolButton.InstantPopup)

        self.toolbox_menu = QMenu(toolboxes_btn)

        def generar_loader(modulo):
            def loader():
                exito, msj = self.engine.toolbox_manager.load_toolbox(modulo)
                self.escribir_en_consola(f">> {msj}\n")
                self.actualizar_workspace()
            return loader

        def actualizar_menu_toolboxes():
            self.toolbox_menu.clear()

            tb_dir = Path(__file__).parent.parent / "toolboxes"
            toolboxes_encontrados = 0

            if tb_dir.exists():
                for archivo in tb_dir.glob("*.py"):
                    if not archivo.name.startswith("__"):
                        modulo = archivo.stem
                        if modulo not in self.engine.toolbox_manager.loaded_toolboxes:
                            act = QAction(f"📦 Cargar {modulo}", self)
                            act.triggered.connect(generar_loader(modulo))
                            self.toolbox_menu.addAction(act)
                            toolboxes_encontrados += 1

            if toolboxes_encontrados == 0:
                act_vacio = QAction("No hay toolboxes nuevos...", self)
                act_vacio.setEnabled(False)
                self.toolbox_menu.addAction(act_vacio)

            self.toolbox_menu.addSeparator()

            act_crear = QAction("➕ Crear nuevo Toolbox (Plantilla)...", self)
            act_crear.triggered.connect(self.crear_plantilla_toolbox)
            self.toolbox_menu.addAction(act_crear)

        self.toolbox_menu.aboutToShow.connect(actualizar_menu_toolboxes)
        toolboxes_btn.setMenu(self.toolbox_menu)
        toolbar.addWidget(toolboxes_btn)
        self.toolboxes_button = toolboxes_btn

    def abrir_serial_plotter(self):
        if self.plotter_window is None:
            self.plotter_window = SerialPlotterWindow(self)
        self.plotter_window.show()
        self.plotter_window.activateWindow()
        self.plotter_window.raise_()

    def nuevo_script(self, contenido="", titulo="Untitled.m"):
        editor = CodeEditor()
        editor.setPlaceholderText("% Escribe tu script aquí...\n")
        highlighter = PythonHighlighter(editor.document())
        highlighter.set_theme(getattr(self, 'is_dark_mode', True))
        editor.highlighter = highlighter

        completer = QCompleter(self.completer_model, self)
        if getattr(self, 'is_dark_mode', True):
            completer.popup().setStyleSheet("background-color: #2b2b2b; color: #ffffff; border: 1px solid #3c3f41;")
        else:
            completer.popup().setStyleSheet("background-color: #ffffff; color: #000000; border: 1px solid #d0d0d0;")
        editor.setCompleter(completer)

        if getattr(self, 'is_dark_mode', True):
            editor.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Consolas, monospace; font-size: 14px; border: none;")
        else:
            editor.setStyleSheet("background-color: #ffffff; color: #000000; font-family: Consolas, monospace; font-size: 14px; border: none;")

        if contenido:
            editor.setPlainText(contenido)

        idx = self.tabs.addTab(editor, titulo)
        self.tabs.setCurrentIndex(idx)

    def cerrar_pestana(self, index):
        self.tabs.removeTab(index)

    def obtener_editor_actual(self):
        """Devuelve el editor activo, o None si no hay pestañas abiertas."""
        if self.tabs.count() > 0:
            return self.tabs.currentWidget()
        return None

    def ejecutar_script(self):
        """Ejecuta el contenido actual del editor como un script completo."""
        editor = self.obtener_editor_actual()
        if editor is None:
            self.console_output.append('<span style="color: #FF9800;">>> No hay ningún script abierto para ejecutar.</span><br>')
            return

        script = editor.toPlainText()
        self.console_output.append('<span style="color: #2196F3;">>> Ejecutando script...</span><br>')
        self.ejecutar_codigo(script)

    def ejecutar_seleccion(self):
        editor = self.obtener_editor_actual()
        if editor is None:
            return

        cursor = editor.textCursor()
        if cursor.hasSelection():
            codigo = cursor.selectedText().replace('\u2029', '\n')
            self.console_output.append('<span style="color: #2196F3;">>> Ejecutando selección...</span><br>')
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            codigo = cursor.selectedText()
            self.console_output.append('<span style="color: #2196F3;">>> Ejecutando línea actual...</span><br>')

        self.ejecutar_codigo(codigo)

    def ejecutar_codigo(self, codigo, mode="script"):
        """Inicia una ejecución asíncrona única y bloquea acciones incompatibles."""
        if self.worker is not None and self.worker.isRunning():
            self.escribir_en_consola("Ya hay una ejecución activa; deténla antes de iniciar otra.\n")
            return

        self.worker = ExecutionWorker(self.engine, codigo, mode, self)
        self.worker.error.connect(self.mostrar_error_consola)
        self.worker.result_ready.connect(self.mostrar_resultado_comando)
        self.worker.cancelled.connect(self.mostrar_ejecucion_cancelada)
        self.worker.finished.connect(self.restaurar_interfaz)

        self.run_action.setEnabled(False)
        self.run_selection_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.console_input.setEnabled(False)
        self.clear_workspace_action.setEnabled(False)
        self.toolboxes_button.setEnabled(False)
        self.worker.start()

    def mostrar_resultado_comando(self, resultado):
        self.escribir_en_consola(f"{resultado}\n")

    def mostrar_error_consola(self, mensaje_error):
        self.escribir_en_consola(f"Error: {mensaje_error}\n")

    def mostrar_ejecucion_cancelada(self):
        self.escribir_en_consola("Ejecución detenida por el usuario.\n")

    def detener_ejecucion(self):
        if self.worker is not None and self.worker.isRunning():
            self.worker.request_stop()
            self.stop_action.setEnabled(False)
            self.escribir_en_consola("Solicitando detener la ejecución...\n")

    def restaurar_interfaz(self):
        """Actualiza el workspace y restaura los controles tras la ejecución."""
        worker = self.worker
        if worker is None:
            return

        if worker.outcome == "completed":
            self.escribir_en_consola("Ejecución finalizada.\n")
        self.actualizar_workspace()
        self.run_action.setEnabled(True)
        self.run_selection_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.console_input.setEnabled(True)
        self.clear_workspace_action.setEnabled(True)
        self.toolboxes_button.setEnabled(True)
        worker.deleteLater()
        self.worker = None

    def crear_plantilla_toolbox(self):
        plantilla = '''import numpy as np
from core.toolbox_manager import MatpyLabToolbox

class MiToolboxPersonalizado(MatpyLabToolbox):
    @property
    def name(self):
        return "Mi Primer Toolbox"
        
    @property
    def description(self):
        return "Un toolbox de prueba creado por la comunidad."
        
    def export_functions(self):
        # 1. Define tus funciones personalizadas aquí
        def saludar(nombre="Mundo"):
            """Imprime un saludo en la consola."""
            print(f"¡Hola {nombre} desde tu nuevo Toolbox!")
            
        def calcular_magia(x):
            """Calcula el cuadrado del valor y le suma 42."""
            return (x ** 2) + 42

        # 2. Devuelve el diccionario de funciones a inyectar en el Workspace
        return {
            'saludar': saludar,
            'magia': calcular_magia
        }
'''
        self.nuevo_script(plantilla, "tb_mi_modulo.py")
        self.console_output.append('<span style="color: #2196F3;">&gt;&gt; Plantilla generada. Guárdala en la carpeta "toolboxes/" para usarla.</span><br>')

    def escribir_en_consola(self, texto):
        cursor = self.console_output.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.console_output.setTextCursor(cursor)
        self.console_output.insertPlainText(texto)
        self.console_output.ensureCursorVisible()

    def setup_file_explorer(self):
        """Configura el panel del explorador de archivos del proyecto."""
        current_path = self.config.get("last_folder", os.path.expanduser("~"))
        try:
            current_path = os.path.abspath(current_path)
            os.chdir(current_path)
        except Exception as error:
            print(f"No se pudo acceder a {current_path}; se usará la carpeta personal: {error}")
            current_path = os.path.expanduser("~")
            os.chdir(current_path)
            self.config["last_folder"] = current_path
            save_config(self.config)

        self.dock_files = QDockWidget("Current Folder", self)
        self.dock_files.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(current_path)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(current_path))

        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setHeaderHidden(True)

        self.dock_files.setWidget(self.tree_view)

        self.tree_view.doubleClicked.connect(self.abrir_archivo)

    def open_folder(self):
        """Selecciona la carpeta de trabajo y sincroniza la aplicación."""
        current_path = self.config.get("last_folder", os.path.expanduser("~"))
        folder_path = QFileDialog.getExistingDirectory(
            self, "Seleccionar Carpeta de Proyecto", current_path
        )

        if not folder_path:
            return

        try:
            os.chdir(folder_path)
        except OSError as error:
            self.escribir_en_consola(f"No se pudo cambiar a {folder_path}: {error}\n")
            return

        self.file_model.setRootPath(folder_path)
        self.tree_view.setRootIndex(self.file_model.index(folder_path))
        self.config["last_folder"] = folder_path
        save_config(self.config)
        self.escribir_en_consola(f">> Workspace actualizado a: {folder_path}\n")

    def abrir_archivo(self, index):
        """Abre un archivo de texto o Python seleccionado en el explorador."""
        ruta = self.file_model.filePath(index)

        if os.path.isfile(ruta):
            if ruta.endswith('.py') or ruta.endswith('.m') or ruta.endswith('.txt'):
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    self.nuevo_script(contenido, os.path.basename(ruta))
                    self.escribir_en_consola(f">> Archivo cargado: {os.path.basename(ruta)}\n")
                except Exception as e:
                    self.escribir_en_consola(f"Error al leer archivo: {e}\n")
            else:
                self.console_output.append('<span style="color: #FF9800;">>> Formato no soportado. Selecciona un archivo .py o .m</span><br>')

    def abrir_dialogo_archivo(self):
        """Abre el cuadro de diálogo para cargar un script desde disco."""
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Script", "", "MatpyLab/MATLAB Scripts (*.py *.m);;All Files (*)")

        if ruta:
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                self.nuevo_script(contenido, os.path.basename(ruta))
                self.escribir_en_consola(f">> Archivo cargado: {os.path.basename(ruta)}\n")
            except Exception as e:
                self.escribir_en_consola(f"Error al leer archivo: {e}\n")

    def guardar_script(self):
        """Guarda el contenido del editor en un archivo `.py`."""
        editor = self.obtener_editor_actual()
        if editor is None:
            return

        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Script", "", "Python Script (*.py);;MATLAB Script (*.m)")

        if ruta:
            if not (ruta.endswith('.py') or ruta.endswith('.m')):
                ruta += '.py'
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    f.write(editor.toPlainText())
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(ruta))
                self.escribir_en_consola(f">> Guardado: {os.path.basename(ruta)}\n")
            except Exception as e:
                self.escribir_en_consola(f"Error: {e}\n")

    def abrir_gestor_toolboxes(self):
        """Abre el diálogo que permite activar o desactivar toolboxes."""
        dialogo = ToolboxManager(self.engine, self)
        dialogo.exec()
        self.actualizar_autocompletado()

    def actualizar_autocompletado(self):
        """Actualiza la lista de palabras conocidas para el autocompleter."""
        palabras = list(self.engine.workspace_globals.keys())
        palabras.extend(['clc', 'clear'])

        self.completer_model.setStringList(palabras)

    def mostrar_ayuda_funcion(self, texto):
        """Muestra una pista rápida con la documentación de una función escrita."""
        if '(' in texto:
            parte = texto.rsplit('(', 1)[0]

            palabras = re.split(r'[^a-zA-Z0-9_]', parte)
            if palabras:
                nombre_func = palabras[-1]

                if nombre_func in self.engine.workspace_globals:
                    func = self.engine.workspace_globals[nombre_func]

                    if callable(func) and func.__doc__:
                        doc = func.__doc__.strip().split('\n')[0]

                        QToolTip.showText(
                            self.console_input.mapToGlobal(self.console_input.rect().topLeft()),
                            f"{nombre_func}: {doc}",
                            self.console_input
                        )
                        return

        QToolTip.hideText()

    def toggle_tema(self):
        """Alterna entre modo oscuro y claro de la aplicación."""
        self.is_dark_mode = not getattr(self, 'is_dark_mode', True)
        if self.is_dark_mode:
            self.aplicar_tema_oscuro()
        else:
            self.aplicar_tema_claro()
        self.config["theme"] = "dark" if self.is_dark_mode else "light"
        save_config(self.config)

    def aplicar_tema_oscuro(self):
        """Aplica la paleta visual oscura a la interfaz."""
        self.theme_action.setText("Tema Claro")
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Consolas, monospace; font-size: 14px;")
        self.console_input.setStyleSheet("background-color: #2d2d2d; color: #ffffff; font-family: Consolas, monospace; font-size: 14px; padding: 4px;")

        self.setStyleSheet("""
            QMainWindow, QDialog { background-color: #2b2b2b; color: #ffffff; }
            QDockWidget { color: #ffffff; font-weight: bold; }
            QDockWidget::title { background: #3c3f41; padding: 8px; }
            QTreeView, QTableWidget, QListWidget { background-color: #252526; color: #ffffff; border: 1px solid #3c3f41; gridline-color: #3c3f41; }
            QTreeView::item:selected, QTableWidget::item:selected, QListWidget::item:selected { background-color: #094771; }
            QHeaderView::section { background-color: #3c3f41; color: #ffffff; border: 1px solid #2b2b2b; padding: 4px; }
            QToolBar { background-color: #3c3f41; border: none; padding: 2px; }
            QToolBar QToolButton { color: #ffffff; padding: 6px; border-radius: 4px; }
            QToolBar QToolButton:hover { background-color: #505355; }
        """)
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            editor.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Consolas, monospace; font-size: 14px; border: none;")
            editor.highlighter.set_theme(is_dark=True)

    def aplicar_tema_claro(self):
        """Aplica la paleta visual clara a la interfaz."""
        self.theme_action.setText("Tema Oscuro")
        self.console_output.setStyleSheet("background-color: #f5f5f5; color: #000000; font-family: Consolas, monospace; font-size: 14px;")
        self.console_input.setStyleSheet("background-color: #ffffff; color: #000000; font-family: Consolas, monospace; font-size: 14px; padding: 4px; border: 1px solid #ccc;")

        self.setStyleSheet("""
            QMainWindow, QDialog { background-color: #f0f0f0; color: #000000; }
            QDockWidget { color: #000000; font-weight: bold; }
            QDockWidget::title { background: #e0e0e0; padding: 8px; }
            QTreeView, QTableWidget, QListWidget { background-color: #ffffff; color: #000000; border: 1px solid #d0d0d0; gridline-color: #d0d0d0; }
            QTreeView::item:selected, QTableWidget::item:selected, QListWidget::item:selected { background-color: #cce8ff; color: #000000; }
            QHeaderView::section { background-color: #e0e0e0; color: #000000; border: 1px solid #c0c0c0; padding: 4px; }
            QToolBar { background-color: #e0e0e0; border: none; padding: 2px; }
            QToolBar QToolButton { color: #000000; padding: 6px; border-radius: 4px; }
            QToolBar QToolButton:hover { background-color: #d0d0d0; }
        """)
        for index in range(self.tabs.count()):
            editor = self.tabs.widget(index)
            editor.setStyleSheet("background-color: #ffffff; color: #000000; font-family: Consolas, monospace; font-size: 14px; border: none;")
            editor.highlighter.set_theme(is_dark=False)