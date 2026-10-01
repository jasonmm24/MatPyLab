import multiprocessing
from joblib import Parallel, delayed
from core.toolbox_manager import MatpyLabToolbox


class ParallelComputingToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Parallel Computing Toolbox"

    @property
    def description(self):
        return "Ejecución de bucles y cálculos masivos aprovechando todos los núcleos del CPU."

    def export_functions(self):
        def matlab_parpool():
            """
            Verifica el pool de trabajadores paralelos.
            Uso: cores = parpool()
            """
            cores = multiprocessing.cpu_count()
            print(f"🚀 Pool paralelo detectado: {cores} núcleos físicos/lógicos disponibles.")
            return cores

        def matlab_parfor(func, iterable, n_jobs=-1):
            """
            Ejecuta un bucle en paralelo.
            Uso: resultados = parfor(mi_funcion, lista_datos)
            """
            print("⚡ Ejecutando parfor en paralelo repartiendo carga...")
            resultados = Parallel(n_jobs=n_jobs)(delayed(func)(item) for item in iterable)
            return resultados

        return {
            'parpool': matlab_parpool,
            'parfor': matlab_parfor
        }
