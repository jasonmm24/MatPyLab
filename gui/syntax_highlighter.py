"""Resaltador de sintaxis para el editor de MatPyLab.

Este módulo aplica colores y estilos visuales a los scripts escritos en el editor,
mejorando la legibilidad del código. Se encarga de destacar palabras clave,
funciones, cadenas, comentarios y números según el tema activo (oscuro o claro).
"""

import re
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class PythonHighlighter(QSyntaxHighlighter):
    """Clase que resalta sintaxis del código dentro del editor de texto.

    Hereda de `QSyntaxHighlighter` y define una serie de expresiones regulares para
    aplicar formato visual a diferentes elementos del lenguaje, como palabras clave,
    funciones, números y cadenas.
    """

    def __init__(self, document):
        """Inicializa el resaltador y prepara la paleta de colores del tema oscuro."""
        super().__init__(document)
        self.rules = []

        self.keywords = [
            r'\bdef\b', r'\bclass\b', r'\bimport\b', r'\bfrom\b',
            r'\bif\b', r'\belif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\breturn\b', r'\bpass\b', r'\bbreak\b', r'\bcontinue\b',
            r'\band\b', r'\bor\b', r'\bnot\b', r'\bin\b', r'\bis\b',
            r'\bTrue\b', r'\bFalse\b', r'\bNone\b', r'\bclc\b', r'\bclear\b'
        ]
        self.set_theme(is_dark=True)

    def set_theme(self, is_dark):
        """Define el esquema de colores según el tema activo.

        Args:
            is_dark (bool): Si es `True`, usa colores oscuros; si es `False`, usa
            una paleta clara.
        """
        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setFontWeight(QFont.Bold)

        number_format = QTextCharFormat()
        string_format = QTextCharFormat()
        func_format = QTextCharFormat()

        comment_format = QTextCharFormat()
        comment_format.setFontItalic(True)

        if is_dark:
            keyword_format.setForeground(QColor("#00BFFF"))
            number_format.setForeground(QColor("#00FF00"))
            string_format.setForeground(QColor("#FF8C00"))
            comment_format.setForeground(QColor("#00FA9A"))
            func_format.setForeground(QColor("#FFD700"))
        else:
            keyword_format.setForeground(QColor("#0000CD"))
            number_format.setForeground(QColor("#228B22"))
            string_format.setForeground(QColor("#B22222"))
            comment_format.setForeground(QColor("#008080"))
            func_format.setForeground(QColor("#8B008B"))

        for word in self.keywords:
            self.rules.append((re.compile(word), keyword_format))

        self.rules.append((re.compile(r'\b[A-Za-z0-9_]+(?=\()'), func_format))
        self.rules.append((re.compile(r'\b[0-9]+(?:\.[0-9]+)?\b'), number_format))
        self.rules.append((re.compile(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((re.compile(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))
        self.rules.append((re.compile(r'#[^\n]*'), comment_format))

        self.rehighlight()

    def highlightBlock(self, text):
        """Aplica formato a cada bloque de texto del documento.

        Args:
            text (str): Línea actual del editor que se está resaltando.
        """
        for regex, fmt in self.rules:
            for match in regex.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)