import numpy as np
import cv2
import matplotlib.pyplot as plt
from core.toolbox_manager import MatpyLabToolbox


class ImageProcessingToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Image Processing Toolbox"

    @property
    def description(self):
        return "Incluye algoritmos y herramientas para el análisis y procesamiento de imágenes digitales."

    def export_functions(self):
        def matlab_imread(filepath):
            """
            Lee una imagen desde un archivo.
            Uso: img = imread('foto.jpg')
            """
            img = cv2.imread(filepath)
            if img is not None:
                # OpenCV lee en BGR por defecto, MATLAB y Matplotlib usan RGB
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            print(f"Error: no se pudo cargar la imagen en '{filepath}'.")
            return None

        def matlab_imshow(img):
            """
            Muestra la imagen en el panel de gráficas.
            Uso: imshow(img)
            """
            plt.figure()
            # Detectar si es escala de grises (2D) o RGB (3D)
            if len(img.shape) == 2:
                plt.imshow(img, cmap='gray', vmin=0, vmax=255)
            else:
                plt.imshow(img)
            plt.axis('off')  # Ocultar los ejes numéricos para que parezca una foto real
            plt.tight_layout()
            plt.show()
            return None

        def matlab_rgb2gray(img):
            """
            Convierte una imagen RGB a escala de grises.
            Uso: gris = rgb2gray(img)
            """
            if len(img.shape) == 3:
                return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            return img

        def matlab_imbinarize(img, threshold=127):
            """
            Binariza una imagen (blanco y negro puro) basándose en un umbral.
            Uso: bw = imbinarize(gris, 128)
            """
            # Si es RGB, convertir a gris primero
            if len(img.shape) == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

            _, bw = cv2.threshold(img, threshold, 255, cv2.THRESH_BINARY)
            return bw

        return {
            'imread': matlab_imread,
            'imshow': matlab_imshow,
            'rgb2gray': matlab_rgb2gray,
            'imbinarize': matlab_imbinarize
        }
