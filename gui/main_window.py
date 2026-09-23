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
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QTextEdit, QTableWidget,
                               QWidget, QVBoxLayout, QLineEdit, QTableWidgetItem,
                               QToolBar, QTreeView, QFileSystemModel, QFileDialog,
                               QDialog, QListWidget, QDialogButtonBox, QCompleter,
                               QToolTip)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, QObject, Signal, QDir, QStringListModel
from core.execution_engine import ExecutionEngine
from PySide6.QtWidgets import QListWidgetItem
from gui.syntax_highlighter import PythonHighlighter


class StreamRedirector(QObject):
    """Redirige la salida estándar hacia la consola de la aplicación.

    Esta clase actúa como un objeto de tipo `sys.stdout` para capturar texto que se
    imprima en la terminal del proceso y mostrarlo dentro del widget de la consola.
    """

    text_written = Signal(str)

    def write(self, text):
        """Emite el texto recibido como una señal para mostrarlo en la interfaz."""
        self.text_written.emit(text)

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
        self.setWindowTitle("MatpyLab - v0.0")
        self.resize(1200, 800)

        self.editor = QTextEdit()
        self.editor.setPlaceholderText("% Escribe tu script aquí...\n")
        self.editor.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 14px; border: none;")
        self.setCentralWidget(self.editor)

        self.highlighter = PythonHighlighter(self.editor.document())

        self.setup_command_window()

        self.redirector = StreamRedirector()
        self.redirector.text_written.connect(self.imprimir_en_consola)
        sys.stdout = self.redirector

        self.engine = ExecutionEngine()

        self.setup_workspace()
        self.setup_file_explorer()
        self.setup_toolbar()
        self.actualizar_autocompletado()

        self.is_dark_mode = True
        self.aplicar_tema_oscuro()

        self.actualizar_autocompletado()

    def setup_command_window(self):
        """Crea el dock de la consola de comandos y su entrada interactiva."""
        self.dock_console = QDockWidget("Command Window", self)
        self.dock_console.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.RightDockWidgetArea)

        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas, monospace; font-size: 14px;")

        self.console_input = QLineEdit()
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
        self.workspace_table = QTableWidget(0, 3)
        self.workspace_table.setHorizontalHeaderLabels(["Name", "Value", "Type"])
        self.workspace_table.horizontalHeader().setStretchLastSection(True)
        self.dock_workspace.setWidget(self.workspace_table)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_workspace)

    def procesar_comando(self):
        """Procesa la entrada de comando de la consola y la ejecuta en el motor."""
        comando = self.console_input.text()
        if not comando.strip():
            return

        self.console_output.append(f'<span style="color: #4CAF50;">>> {comando}</span>')
        self.console_input.clear()

        if comando.strip() == 'clc':
            self.console_output.clear()
            return

        if comando.strip() == 'clear':
            self.engine.clear_workspace()
            self.actualizar_workspace()
            self.console_output.append('<span style="color: #4CAF50;">>> Workspace limpiado.</span>')
            return

        resultado, error = self.engine.execute_command(comando)

        if error:
            self.console_output.append(f'<span style="color: #F44336;">Error: {error}</span>')
        elif resultado is not None:
            self.console_output.append(str(resultado))

        self.actualizar_workspace()

    def actualizar_workspace(self):
        """Actualiza la tabla del workspace con variables del entorno actual."""
        self.workspace_table.setRowCount(0)

        variables = {k: v for k, v in self.engine.workspace_globals.items() if not k.startswith('__') and k not in self.engine.system_keys}

        self.workspace_table.setRowCount(len(variables))

        for row, (nombre, valor) in enumerate(variables.items()):
            self.workspace_table.setItem(row, 0, QTableWidgetItem(nombre))
            self.workspace_table.setItem(row, 1, QTableWidgetItem(str(valor)[:50]))
            self.workspace_table.setItem(row, 2, QTableWidgetItem(type(valor).__name__))

        self.actualizar_autocompletado()

    def setup_toolbar(self):
        """Configura la barra de herramientas con comandos principales."""
        toolbar = QToolBar("Barra de Herramientas Principal")
        self.addToolBar(toolbar)

        open_action = QAction("📂 Abrir", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.abrir_dialogo_archivo)
        toolbar.addAction(open_action)

        save_action = QAction("💾 Guardar", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.guardar_script)
        toolbar.addAction(save_action)

        toolbox_action = QAction("🧩 Toolboxes", self)
        toolbox_action.triggered.connect(self.abrir_gestor_toolboxes)
        toolbar.addAction(toolbox_action)

        self.theme_action = QAction("☀️ Tema Claro", self)
        self.theme_action.triggered.connect(self.toggle_tema)
        toolbar.addAction(self.theme_action)

        toolbar.addSeparator()

        run_action = QAction("▶ Run Script", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self.ejecutar_script)
        toolbar.addAction(run_action)

    def ejecutar_script(self):
        """Ejecuta el contenido actual del editor como un script completo."""
        script = self.editor.toPlainText()
        self.console_output.append('<span style="color: #2196F3;">>> Ejecutando script...</span><br>')
        error = self.engine.execute_script(script)
        if error:
            self.console_output.append(f'<span style="color: #F44336;">Error: {error}</span>')
        else:
            self.console_output.append('<span style="color: #4CAF50;">Ejecución finalizada.</span>')

    def imprimir_en_consola(self, texto):
        """Muestra salida estándar en la consola de la interfaz."""
        self.console_output.insertPlainText(texto)

        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def setup_file_explorer(self):
        """Configura el panel del explorador de archivos del proyecto."""
        self.dock_files = QDockWidget("Current Folder", self)
        self.dock_files.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self.file_model = QFileSystemModel()
        self.file_model.setRootPath(QDir.currentPath())

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(QDir.currentPath()))

        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setHeaderHidden(True)

        self.dock_files.setWidget(self.tree_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_files)

        self.tree_view.doubleClicked.connect(self.abrir_archivo)

    def abrir_archivo(self, index):
        """Abre un archivo de texto o Python seleccionado en el explorador."""
        ruta = self.file_model.filePath(index)

        if os.path.isfile(ruta):
            if ruta.endswith('.py') or ruta.endswith('.txt'):
                try:
                    with open(ruta, 'r', encoding='utf-8') as f:
                        contenido = f.read()
                    self.editor.setPlainText(contenido)
                    self.console_output.append(f'<span style="color: #2196F3;">>> Archivo cargado: {os.path.basename(ruta)}</span><br>')
                except Exception as e:
                    self.console_output.append(f'<span style="color: #F44336;">Error al leer archivo: {str(e)}</span><br>')
            else:
                self.console_output.append('<span style="color: #FF9800;">>> Formato no soportado. Selecciona un archivo .py</span><br>')

    def abrir_dialogo_archivo(self):
        """Abre el cuadro de diálogo para cargar un script desde disco."""
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir Script", "", "Python Scripts (*.py);;Text Files (*.txt);;All Files (*)")

        if ruta:
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                self.editor.setPlainText(contenido)
                self.console_output.append(f'<span style="color: #2196F3;">>> Archivo cargado: {os.path.basename(ruta)}</span><br>')
            except Exception as e:
                self.console_output.append(f'<span style="color: #F44336;">Error al leer archivo: {str(e)}</span><br>')

    def guardar_script(self):
        """Guarda el contenido del editor en un archivo `.py`."""
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Script", "", "Python Scripts (*.py)")

        if ruta:
            if not ruta.endswith('.py'):
                ruta += '.py'
            try:
                with open(ruta, 'w', encoding='utf-8') as f:
                    f.write(self.editor.toPlainText())
                self.console_output.append(f'<span style="color: #4CAF50;">>> Archivo guardado con éxito: {os.path.basename(ruta)}</span><br>')
            except Exception as e:
                self.console_output.append(f'<span style="color: #F44336;">Error al guardar: {str(e)}</span><br>')

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

    def aplicar_tema_oscuro(self):
        """Aplica la paleta visual oscura a la interfaz."""
        self.theme_action.setText("☀️ Tema Claro")
        self.editor.setStyleSheet("background-color: #1e1e1e; color: #ffffff; font-family: Consolas, monospace; font-size: 14px; border: none;")
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
        self.highlighter.set_theme(is_dark=True)

    def aplicar_tema_claro(self):
        """Aplica la paleta visual clara a la interfaz."""
        self.theme_action.setText("🌙 Tema Oscuro")
        self.editor.setStyleSheet("background-color: #ffffff; color: #000000; font-family: Consolas, monospace; font-size: 14px; border: none;")
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
        self.highlighter.set_theme(is_dark=False)