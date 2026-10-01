import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from core.toolbox_manager import MatpyLabToolbox


class DeepLearningToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Deep Learning Toolbox"

    @property
    def description(self):
        return "Ofrece un entorno para diseñar, entrenar y simular redes neuronales profundas."

    def export_functions(self):
        def matlab_feedforwardnet(input_size, hidden_sizes, output_size):
            """
            Crea una red neuronal perceptrón multicapa (MLP).
            Uso: net = feedforwardnet(1, [10, 10], 1)
            """
            layers = []
            in_features = input_size

            for h in hidden_sizes:
                layers.append(nn.Linear(in_features, h))
                layers.append(nn.ReLU())
                in_features = h

            layers.append(nn.Linear(in_features, output_size))
            net = nn.Sequential(*layers)
            print(f"🧠 Red Neuronal creada: {input_size} entradas -> capas ocultas {hidden_sizes} -> {output_size} salidas.")
            return net

        def matlab_trainNetwork(X, y, net, epochs=1000, lr=0.01):
            """
            Entrena la red neuronal (Regresión MSE por defecto).
            Uso: net_entrenada = trainNetwork(X, y, net)
            """
            # Convertir datos a tensores de PyTorch
            X_tensor = torch.tensor(X, dtype=torch.float32)
            y_tensor = torch.tensor(y, dtype=torch.float32)

            # Ajustar dimensiones si es necesario (espera matrices 2D)
            if len(X_tensor.shape) == 1:
                X_tensor = X_tensor.unsqueeze(1)
            if len(y_tensor.shape) == 1:
                y_tensor = y_tensor.unsqueeze(1)

            criterion = nn.MSELoss()
            optimizer = optim.Adam(net.parameters(), lr=lr)

            print(f"⚙️ Entrenando red por {epochs} épocas...")
            for epoch in range(epochs):
                optimizer.zero_grad()
                outputs = net(X_tensor)
                loss = criterion(outputs, y_tensor)
                loss.backward()
                optimizer.step()

                if (epoch + 1) % (epochs // 10) == 0 or epoch == 0:
                    print(f"   Época [{epoch+1}/{epochs}], Pérdida: {loss.item():.6f}")

            print("✅ Entrenamiento completado.")
            return net

        def matlab_predict(net, X):
            """
            Realiza predicciones con la red entrenada.
            Uso: y_pred = predict(net, X_nuevo)
            """
            net.eval()  # Modo evaluación
            X_tensor = torch.tensor(X, dtype=torch.float32)
            if len(X_tensor.shape) == 1:
                X_tensor = X_tensor.unsqueeze(1)

            with torch.no_grad():
                pred = net(X_tensor)
            return pred.numpy()

        return {
            'feedforwardnet': matlab_feedforwardnet,
            'trainNetwork': matlab_trainNetwork,
            'predict': matlab_predict
        }
