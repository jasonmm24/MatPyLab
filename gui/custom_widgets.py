from PySide6.QtWidgets import QPlainTextEdit, QWidget, QLineEdit, QCompleter, QTextEdit
from PySide6.QtGui import QPainter, QColor, QTextFormat, QFont, QTextCursor
from PySide6.QtCore import Qt, QRect, QSize, QStringListModel
import keyword


class ConsoleInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = 0

    def add_to_history(self, command):
        if command.strip():
            if not self.history or self.history[-1] != command:
                self.history.append(command)
            self.history_index = len(self.history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            if self.history and self.history_index > 0:
                self.history_index -= 1
                self.setText(self.history[self.history_index])
        elif event.key() == Qt.Key_Down:
            if self.history and self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.setText(self.history[self.history_index])
            elif self.history_index == len(self.history) - 1:
                self.history_index += 1
                self.clear()
        else:
            super().keyPressEvent(event)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.breakpoints = set()
        self.debug_line = None
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)
        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insertar_completado)
        self.palabras_base = list(keyword.kwlist) + [
            'disp', 'mod', 'serialport', 'read', 'write', 'plot', 'np', 'plt', 'pd', 'time'
        ]
        self.completer_model = QStringListModel(self.palabras_base, self.completer)
        self.completer.setModel(self.completer_model)
        self.actualizar_diccionario(())

    def setCompleter(self, c):
        if self.completer is not c:
            if self.completer:
                self.completer.activated.disconnect()
            self.completer = c
            c.setWidget(self)
            c.setCompletionMode(QCompleter.PopupCompletion)
            c.setCaseSensitivity(Qt.CaseInsensitive)
            c.activated.connect(self.insertar_completado)

    def actualizar_diccionario(self, variables_workspace):
        """Actualiza las sugerencias con las variables disponibles en el motor."""
        palabras = sorted(set(self.palabras_base).union(map(str, variables_workspace)))
        self.completer_model.setStringList(palabras)

    def insertar_completado(self, completion):
        """Inserta la parte de la sugerencia que aún no está escrita."""
        if self.completer.widget() is not self:
            return
        tc = self.textCursor()
        extra = len(completion) - len(self.completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        if extra > 0:
            tc.insertText(completion[-extra:])
        self.setTextCursor(tc)

    def insertCompletion(self, completion):
        """Compatibilidad con el nombre histórico del manejador."""
        self.insertar_completado(completion)

    def actualizar_diccionario_legacy(self, variables_workspace):
        """Compatibilidad con integraciones previas que actualizan el modelo."""
        self.actualizar_diccionario(variables_workspace)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)
        return tc.selectedText()

    def focusInEvent(self, e):
        if self.completer:
            self.completer.setWidget(self)
        super().focusInEvent(e)

    def keyPressEvent(self, e):
        if self.completer and self.completer.popup().isVisible():
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                return

        super().keyPressEvent(e)

        if self.completer is None:
            return

        ctrl_or_shift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if ctrl_or_shift and not e.text():
            return

        caracteres_fin = "~!@#$%^&*()+{}|:\"<>?,./;'[]\\-=\n "
        tiene_modificador = (e.modifiers() != Qt.NoModifier) and not ctrl_or_shift
        prefijo = self.textUnderCursor()

        if tiene_modificador or not e.text() or len(prefijo) < 2 or not prefijo.isidentifier() or e.text()[-1] in caracteres_fin:
            self.completer.popup().hide()
            return

        if prefijo != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(prefijo)
            self.completer.popup().setCurrentIndex(self.completer.completionModel().index(0, 0))

        rect = self.cursorRect()
        rect.setWidth(self.completer.popup().sizeHintForColumn(0) + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        return 27 + self.fontMetrics().horizontalAdvance('9') * digits

    def toggle_breakpoint(self, line_number):
        if line_number in self.breakpoints:
            self.breakpoints.remove(line_number)
            enabled = False
        else:
            self.breakpoints.add(line_number)
            enabled = True
        self.line_number_area.update()
        return enabled

    def set_debug_line(self, line_number):
        self.debug_line = line_number
        self.setExtraSelections([])
        if line_number is None:
            return

        block = self.document().findBlockByNumber(line_number - 1)
        if not block.isValid():
            return

        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(block)
        selection.format.setBackground(QColor("#514719"))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        self.setExtraSelections([selection])
        self.setTextCursor(selection.cursor)
        self.centerCursor()

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2b2b2b"))
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number + 1 in self.breakpoints:
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor("#f14c4c"))
                    marker_y = top + (self.fontMetrics().height() - 8) // 2
                    painter.drawEllipse(3, marker_y, 8, 8)
                painter.setPen(QColor("#858585"))
                painter.setBrush(Qt.NoBrush)
                painter.setFont(self.font())
                painter.drawText(0, top, self.line_number_area.width() - 5, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1