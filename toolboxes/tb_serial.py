import serial
import serial.tools.list_ports
from core.toolbox_manager import MatpyLabToolbox


class SerialToolbox(MatpyLabToolbox):
    @property
    def name(self):
        return "Hardware & Serial Toolbox"

    @property
    def description(self):
        return "Comunicación nativa con microcontroladores (ESP32, Arduino) vía puerto serial."

    def export_functions(self):
        # Diccionario interno para mantener vivas las conexiones
        self.active_connections = {}

        def descartar_conexion(port):
            connection = self.active_connections.pop(port, None)
            if connection is not None:
                try:
                    connection.close()
                except Exception:
                    pass

        def serial_ports():
            """
            Lista los puertos seriales disponibles.
            Uso: puertos = serial_ports()
            """
            ports = serial.tools.list_ports.comports()
            print("\n🔌 Puertos Seriales Detectados:")
            for port in ports:
                print(f"  - {port.device} : {port.description}")
            print("-" * 30)
            return [port.device for port in ports]

        def serial_open(port, baudrate=115200):
            """
            Abre una conexión serial.
            Uso: serial_open('COM3', 115200) o serial_open('/dev/ttyUSB0', 9600)
            """
            try:
                # Si ya estaba abierto, cerrarlo primero
                if port in self.active_connections:
                    self.active_connections[port].close()

                connection = serial.Serial(port, baudrate, timeout=1, write_timeout=1)
                self.active_connections[port] = connection
                print(f"✅ Puerto {port} abierto a {baudrate} baudios.")
                return True
            except Exception as error:
                print(f"❌ Error al abrir {port}: {error}")
                return False

        def serial_read(port):
            """
            Lee la última línea disponible en el búfer serial.
            Uso: datos = serial_read('COM3')
            """
            if port in self.active_connections:
                try:
                    data = self.active_connections[port].readline().decode("utf-8").strip()
                    return data
                except Exception as error:
                    print(f"⚠️ Error de conexión en {port}: {error}. Cerrando puerto.")
                    descartar_conexion(port)
                    return ""
            print(f"⚠️ El puerto {port} no está abierto.")
            return ""

        def serial_write(port, data):
            """
            Escribe una cadena de texto en el puerto serial.
            Uso: serial_write('COM3', 'START\\n')
            """
            if port in self.active_connections:
                try:
                    if isinstance(data, str):
                        data = data.encode("utf-8")
                    self.active_connections[port].write(data)
                    return True
                except Exception as error:
                    print(f"⚠️ Error de conexión en {port}: {error}. Cerrando puerto.")
                    descartar_conexion(port)
                    return False
            print(f"⚠️ El puerto {port} no está abierto.")
            return False

        def serial_close(port):
            """
            Cierra la conexión serial activa.
            Uso: serial_close('COM3')
            """
            if port in self.active_connections:
                self.active_connections[port].close()
                del self.active_connections[port]
                print(f"🛑 Puerto {port} cerrado.")
            else:
                print(f"El puerto {port} no estaba abierto.")

        def serial_close_all():
            """Cierra todos los puertos seriales abiertos."""
            ports = list(self.active_connections.keys())
            for port in ports:
                serial_close(port)

        # Retornamos el diccionario de funciones que se inyectarán al Workspace
        return {
            "serial_ports": serial_ports,
            "serial_open": serial_open,
            "serial_read": serial_read,
            "serial_write": serial_write,
            "serial_close": serial_close,
            "serial_close_all": serial_close_all,
        }
