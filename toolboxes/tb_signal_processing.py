import numpy as np
from scipy import signal
from scipy.fft import fft as scipy_fft
from core.toolbox_manager import MatpyLabToolbox


class SignalProcessingToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Signal Processing Toolbox"

    @property
    def description(self):
        return "Proporciona funciones para filtrar, medir y analizar señales digitales y de sensores."

    def export_functions(self):
        def matlab_butter(N, Wn, btype='low'):
            """
            Diseña un filtro digital Butterworth.
            Uso: b, a = butter(orden, freq_corte, 'low')
            Nota: Wn debe estar entre 0.0 y 1.0 (donde 1.0 es la frecuencia de Nyquist).
            """
            b, a = signal.butter(N, Wn, btype=btype)
            return b, a

        def matlab_filtfilt(b, a, x):
            """
            Aplica un filtro digital hacia adelante y hacia atrás (cero distorsión de fase).
            Uso: y_filtrada = filtfilt(b, a, x)
            """
            # Convertir a array de numpy aplanado
            x_arr = np.array(x).flatten()
            y = signal.filtfilt(b, a, x_arr)
            return y

        def matlab_fft(x):
            """
            Calcula la Transformada Rápida de Fourier (FFT) discreta de 1D.
            Uso: Y = fft(x)
            """
            x_arr = np.array(x).flatten()
            return scipy_fft(x_arr)

        return {
            'butter': matlab_butter,
            'filtfilt': matlab_filtfilt,
            'fft': matlab_fft
        }
