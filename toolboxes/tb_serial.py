import serial
import time
from core.toolbox_manager import MatpyLabToolbox


class SerialToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Serial Toolbox"

    @property
    def description(self):
        return "Comunicación bidireccional por puerto serie para leer sensores y controlar microcontroladores."

    def export_functions(self):
        def matlab_serialport(port, baudrate):
            """
            Abre un puerto serie.
            Uso: s = serialport("COM3", 115200) o s = serialport("/dev/ttyUSB0", 115200)
            """
            try:
                s = serial.Serial(port, baudrate, timeout=1)
                print(f"Conectado al puerto {port} a {baudrate} baudios.")
                return s
            except Exception as e:
                print(f"Error al conectar con {port}: {e}")
                return None

        def matlab_write(s, data, tipo='string'):
            """
            Escribe datos en el puerto serie.
            Uso: write(s, "Hola Arduino") o write(s, [255, 0, 128, 255], 'uint8')
            """
            if s is None or not s.is_open:
                print("El puerto serie no está abierto.")
                return

            if tipo == 'string':
                s.write((str(data) + '\n').encode('utf-8'))
            elif tipo == 'uint8':
                s.write(bytearray(data))

            # Pausa microscópica para asegurar que el buffer del SO haga el volcado
            time.sleep(0.05)

        def matlab_readline(s):
            """
            Lee una línea de texto del puerto serie hasta encontrar un salto de línea.
            Uso: dato = readline(s)
            """
            if s is None or not s.is_open:
                return ""

            if s.in_waiting > 0:
                try:
                    return s.readline().decode('utf-8').strip()
                except UnicodeDecodeError:
                    return "[Error de decodificación]"
            return ""

        def matlab_clear(s):
            """Limpia el buffer y cierra el puerto de forma segura."""
            if s is not None and s.is_open:
                s.flush()
                s.close()
                print("Puerto serie cerrado y liberado.")

        return {
            'serialport': matlab_serialport,
            'write': matlab_write,
            'readline': matlab_readline,
            'clear': matlab_clear
        }