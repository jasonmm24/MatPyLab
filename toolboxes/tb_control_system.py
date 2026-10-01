import numpy as np
import matplotlib.pyplot as plt
import control as ct
from core.toolbox_manager import MatpyLabToolbox


class ControlSystemToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Control System Toolbox"

    @property
    def description(self):
        return "Diseño, análisis y sintonización de sistemas de control automático y realimentado."

    def export_functions(self):
        def matlab_tf(num, den):
            """
            Crea una función de transferencia.
            Uso: G = tf([1], [1, 2, 1])
            """
            # Aplanar entradas a 1D para evitar conflictos entre las 
            # matrices 2D del motor (np.array) y las exigencias de la librería control
            num_flat = np.array(num).flatten()
            den_flat = np.array(den).flatten()
            return ct.tf(num_flat, den_flat)

        def matlab_step(sys, T=None):
            """Grafica la respuesta al escalón."""
            t, y = ct.step_response(sys, T)
            plt.figure()
            plt.plot(t, y, 'b-', linewidth=2)
            plt.title('Respuesta al Escalón')
            plt.xlabel('Tiempo (s)')
            plt.ylabel('Amplitud')
            plt.grid(True)
            plt.show()
            return None

        def matlab_bode(sys):
            """Genera el diagrama de Bode."""
            plt.figure()
            ct.bode_plot(sys, dB=True, Hz=False, grid=True)
            plt.show()
            return None

        def matlab_feedback(sys1, sys2=1, sign=-1):
            """
            Conexión en retroalimentación de dos sistemas.
            Uso: T = feedback(G, H)
            """
            return ct.feedback(sys1, sys2, sign)

        def matlab_pid(kp, ki=0, kd=0):
            """
            Crea un controlador PID como función de transferencia.
            Uso: C = pid(Kp, Ki, Kd)
            """
            s = ct.tf('s')
            return kp + (ki / s) + (kd * s)

        def matlab_rlocus(sys):
            """Traza el lugar de las raíces."""
            plt.figure()
            ct.root_locus(sys, grid=True)
            plt.show()
            return None

        return {
            'tf': matlab_tf,
            'step': matlab_step,
            'bode': matlab_bode,
            'feedback': matlab_feedback,
            'pid': matlab_pid,
            'rlocus': matlab_rlocus
        }
