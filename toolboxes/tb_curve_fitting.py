import numpy as np
from scipy import interpolate
from core.toolbox_manager import MatpyLabToolbox


class CurveFittingToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Curve Fitting Toolbox"

    @property
    def description(self):
        return "Ajuste de curvas, interpolación polinomial y suavizado de datos."

    def export_functions(self):
        def matlab_polyfit(x, y, n):
            """
            Ajuste polinomial por mínimos cuadrados de grado n.
            Uso: p = polyfit(x, y, 2)
            """
            return np.polyfit(x, y, n)

        def matlab_polyval(p, x):
            """
            Evalúa un polinomio.
            Uso: y_est = polyval(p, x)
            """
            return np.polyval(p, x)

        def matlab_interp1(x, y, x_new, kind='linear'):
            """
            Interpolación 1D.
            Uso: y_new = interp1(x, y, x_new, 'cubic')
            """
            f = interpolate.interp1d(x, y, kind=kind, fill_value="extrapolate")
            return f(x_new)

        return {
            'polyfit': matlab_polyfit,
            'polyval': matlab_polyval,
            'interp1': matlab_interp1
        }
