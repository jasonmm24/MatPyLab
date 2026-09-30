import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt


class VariableInspector(QDialog):
    def __init__(self, var_name, var_value, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Variable Inspector: {var_name}")
        self.resize(600, 400)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        self.cargar_datos(var_value)

    def cargar_datos(self, valor):
        try:
            arr = np.array(valor)

            if arr.ndim == 0:
                arr = arr.reshape(1, 1)
            elif arr.ndim == 1:
                arr = arr.reshape(arr.shape[0], 1)
            elif arr.ndim > 2:
                arr = arr[0]
                self.setWindowTitle(self.windowTitle() + " (Mostrando capa 0 de N-Dimensiones)")

            filas, columnas = arr.shape
            filas_visibles = min(filas, 1000)
            columnas_visibles = min(columnas, 1000)

            self.table.setRowCount(filas_visibles)
            self.table.setColumnCount(columnas_visibles)

            for i in range(filas_visibles):
                for j in range(columnas_visibles):
                    item = QTableWidgetItem(str(arr[i, j]))
                    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(i, j, item)

            self.table.resizeColumnsToContents()

        except Exception as e:
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(f"Formato no soportado: {str(e)}"))
