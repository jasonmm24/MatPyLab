/*
 * Módulo de cálculo rápido para MatPyLab.
 *
 * Este archivo define una función de ejemplo escrita en C++ y exportada con
 * convenios de enlace C para poder ser invocada desde Python u otros módulos del
 * proyecto. Sirve como demostración de cómo integrar código nativo con la lógica
 * del entorno de ejecución.
 *
 * La función implementada realiza un cálculo tipo controlador proporcional-derivativo
 * simplificado:
 *
 *     salida = error * kp + kd * 0.5
 */
extern "C" {
    // Calcula una salida tipo PID simplificada basada en el error y dos ganancias.
    double calcular_pid(double error, double kp, double kd) {
        return (error * kp) + (kd * 0.5);
    }
}