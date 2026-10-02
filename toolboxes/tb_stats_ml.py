import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from core.toolbox_manager import MatpyLabToolbox

class StatsMLToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Statistics and Machine Learning Toolbox"

    @property
    def description(self):
        return "Permite analizar datos, crear modelos de aprendizaje automático y realizar análisis estadísticos avanzados."

    def export_functions(self):
        def matlab_fitlm(X, y):
            """
            Ajusta un modelo de regresión lineal.
            Uso: mdl = fitlm(X, y)
            """
            X_arr = np.array(X)
            y_arr = np.array(y)

            # Scikit-learn requiere que X sea 2D (muestras x características)
            if len(X_arr.shape) == 1:
                X_arr = X_arr.reshape(-1, 1)

            modelo = LinearRegression().fit(X_arr, y_arr)
            r2 = modelo.score(X_arr, y_arr)
            print("Modelo lineal ajustado:")
            print(f"   Ecuación: y = {modelo.intercept_:.4f} + {modelo.coef_[0]:.4f}*x")
            print(f"   Precisión (R^2): {r2:.4f}")
            return modelo

        def matlab_kmeans(X, k):
            """
            Agrupamiento K-Means.
            Uso: idx, C = kmeans(X, k)
            """
            X_arr = np.array(X)
            # n_init='auto' para suprimir warnings de versiones recientes
            modelo = KMeans(n_clusters=k, random_state=42, n_init='auto').fit(X_arr)
            print(f"K-Means: datos agrupados en {k} clusters.")
            return np.array(modelo.labels_), np.array(modelo.cluster_centers_)

        def matlab_pca(X, n_components=None):
            """
            Análisis de Componentes Principales.
            Uso: coeff, score = pca(X)
            """
            X_arr = np.array(X)
            modelo = PCA(n_components=n_components).fit(X_arr)
            transformados = modelo.transform(X_arr)
            varianza = modelo.explained_variance_ratio_ * 100
            print(f"PCA completado. Varianza explicada por componente: {np.round(varianza, 2)}%")
            return np.array(modelo.components_), np.array(transformados)

        return {
            'fitlm': matlab_fitlm,
            'kmeans': matlab_kmeans,
            'pca': matlab_pca
        }
