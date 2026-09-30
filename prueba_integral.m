# ==========================================
# SCRIPT DE PRUEBA INTEGRAL - MATPYLAB v0.1
# ==========================================

# 1. Prueba de Parser de MATLAB (Matrices nativas)
print(">> Generando matrices...")
A = [1 2 3; 4 5 6; 7 8 9]
B = eye(3)
C = zeros(3)

# 2. Prueba de adaptadores de tamaño (length y size)
filas_A = size(A, 1)
columnas_A = size(A, 2)
elementos_totales = length(A)

# 3. Prueba de vectores y estadística básica
t = linspace(0, 4*np.pi, 200)
senal_1 = np.sin(t) * np.exp(-0.1 * t)
senal_2 = np.cos(t) * 0.5

promedio_s1 = mean(senal_1)
maximo_s1 = max(senal_1)

# 4. Prueba de Graficación y comandos traducidos (grid on)
print(">> Generando gráficas...")
figure()
plot(t, senal_1, 'b-', linewidth=2, label='Senoidal Amortiguada')
plot(t, senal_2, 'r--', linewidth=2, label='Coseno')

# Este comando es de MATLAB puro, nuestro motor debería traducirlo:
grid on

title('Prueba de Rendimiento - MatpyLab')
xlabel('Tiempo (s)')
ylabel('Amplitud')
legend()

print(">> ¡Prueba finalizada con éxito!")