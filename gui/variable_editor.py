import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


class VariableEditorDialog(QDialog):
    def __init__(self, var_name, var_value, parent=None):
        super().__init__(parent)
        self.var_name = var_name
        self.original_value = var_value
        self.setWindowTitle(f"Editando Variable: {var_name}")
        self.resize(400, 300)

        self.layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.layout.addWidget(self.table)

        self.btn_save = QPushButton("Guardar Cambios")
        self.btn_save.clicked.connect(self.save_data)
        self.layout.addWidget(self.btn_save)

        self._array = None
        self.load_data()

    def load_data(self):
        value = self.original_value
        if isinstance(value, (int, float, str, np.number, np.bool_)):
            self.table.setRowCount(1)
            self.table.setColumnCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(str(value)))
            return

        if isinstance(value, (np.ndarray, list)):
            array = np.asarray(value)
            if array.dtype.kind not in "biufc":
                self._show_unsupported("Solo se pueden editar arreglos numéricos.")
                return
            if array.ndim > 2:
                self._show_unsupported("No se pueden editar arreglos de más de 2 dimensiones.")
                return

            self._array = array
            rows = array.shape[0] if array.ndim else 1
            columns = array.shape[1] if array.ndim == 2 else 1
            self.table.setRowCount(rows)
            self.table.setColumnCount(columns)
            for row in range(rows):
                for column in range(columns):
                    value = array[row] if array.ndim == 1 else array[row, column] if array.ndim == 2 else array.item()
                    self.table.setItem(row, column, QTableWidgetItem(str(value)))
            return

        self._show_unsupported("Este tipo de variable no se puede editar.")

    def _show_unsupported(self, message):
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        item = QTableWidgetItem(message)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(0, 0, item)
        self.btn_save.setEnabled(False)

    def _cell_text(self, row, column):
        item = self.table.item(row, column)
        if item is None:
            raise ValueError(f"La celda ({row + 1}, {column + 1}) está vacía.")
        return item.text().strip()

    @staticmethod
    def _parse_bool(text):
        normalized = text.lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        raise ValueError("Los valores booleanos deben ser true/false o 1/0.")

    def save_data(self):
        try:
            original = self.original_value
            if isinstance(original, str):
                new_value = self._cell_text(0, 0)
            elif isinstance(original, (int, float, np.number, np.bool_)):
                text = self._cell_text(0, 0)
                if isinstance(original, (bool, np.bool_)):
                    new_value = self._parse_bool(text)
                else:
                    new_value = type(original)(text)
            else:
                dtype = self._array.dtype
                values = []
                for row in range(self.table.rowCount()):
                    row_values = []
                    for column in range(self.table.columnCount()):
                        text = self._cell_text(row, column)
                        row_values.append(self._parse_bool(text) if dtype.kind == "b" else dtype.type(text))
                    values.append(row_values)

                new_array = np.asarray(values, dtype=dtype).reshape(self._array.shape)
                if isinstance(original, list):
                    new_value = new_array.tolist()
                else:
                    new_value = new_array

            self.new_value = new_value
            self.accept()
        except (TypeError, ValueError, OverflowError) as error:
            QMessageBox.critical(self, "Error", f"Valor inválido: {error}")