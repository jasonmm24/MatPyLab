"""Punto de entrada principal de MatPyLab.

Este archivo crea la aplicación Qt y despliega la ventana principal de la
aplicación. Es el inicio del programa y coordina la carga de la interfaz gráfica
que a su vez utiliza el motor de ejecución y el sistema de toolboxes.
"""

import sys
from PySide6.QtWidgets import QApplication
from gui.main_window import MatpyLabWindow


def main():
    """Inicializa la app y muestra la ventana principal de MatPyLab."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = MatpyLabWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()