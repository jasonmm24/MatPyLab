"""Pruebas de regresión para el motor de ejecución de MatPyLab."""

import os
import sys

import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.execution_engine import ExecutionEngine


class TestExecutionEngine:
    def setup_method(self):
        """Crear un motor nuevo para cada prueba."""
        self.engine = ExecutionEngine()

    def test_script_asigna_variable_al_workspace(self):
        error = self.engine.execute_script("var_prueba = 42")

        assert error is None
        assert self.engine.workspace_globals["var_prueba"] == 42

    def test_script_ejecuta_operaciones_matematicas(self):
        error = self.engine.execute_script("a = 10\nb = 5\nc = a * b")

        assert error is None
        assert self.engine.workspace_globals["c"] == 50

    def test_numpy_esta_disponible_en_el_workspace(self):
        error = self.engine.execute_script("matriz = np.zeros((2, 2))")

        assert error is None
        assert self.engine.workspace_globals["matriz"].shape == (2, 2)

    def test_comando_inexistente_devuelve_error(self):
        resultado, error = self.engine.execute_command("variable_inexistente + 10")

        assert resultado is None
        assert error is not None
        assert "variable_inexistente" in error

    def test_script_con_division_por_cero_devuelve_error(self):
        error = self.engine.execute_script("resultado = 10 / 0")

        assert isinstance(error, str)
        assert "division by zero" in error.lower()

    def test_clear_workspace_elimina_variables_de_usuario_y_preserva_sistema(self):
        self.engine.execute_script("variable_usuario = 123")
        nombres_sistema = set(self.engine.system_keys)

        self.engine.clear_workspace()

        assert "variable_usuario" not in self.engine.workspace_globals
        assert nombres_sistema.issubset(self.engine.workspace_globals)