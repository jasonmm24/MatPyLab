from collections import deque

import pyqtgraph as pg
import serial
from serial.tools import list_ports
from PySide6.QtCore import QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SerialReaderThread(QThread):
    new_data = Signal(float)
    connected = Signal(str)
    error = Signal(str)

    def __init__(self, port, baudrate, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.25)
            self.connected.emit(self.port)

            while not self.isInterruptionRequested():
                line = self.serial_conn.readline()
                if not line:
                    continue
                try:
                    value = float(line.decode("utf-8").strip())
                except (UnicodeDecodeError, ValueError):
                    continue
                self.new_data.emit(value)
        except Exception as error:
            if not self.isInterruptionRequested():
                self.error.emit(str(error))
        finally:
            if self.serial_conn is not None and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except serial.SerialException as error:
                    if not self.isInterruptionRequested():
                        self.error.emit(str(error))
            self.serial_conn = None

    def stop(self):
        self.requestInterruption()
        if self.serial_conn is not None and self.serial_conn.is_open:
            try:
                self.serial_conn.cancel_read()
            except (serial.SerialException, OSError):
                pass


class SerialPlotterWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setWindowTitle("MatpyLab Serial Plotter")
        self.resize(760, 480)

        self.max_points = 200
        self.data_x = deque(maxlen=self.max_points)
        self.data_y = deque(maxlen=self.max_points)
        self.sample_index = 0
        self.reader_thread = None
        self._reader_error = False

        layout = QVBoxLayout(self)
        controls_layout = QHBoxLayout()

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.refresh_button = QPushButton("Actualizar")
        self.refresh_button.clicked.connect(self.refresh_ports)

        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "250000"])
        self.baud_combo.setCurrentText("115200")

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.toggle_connection)
        self.status_label = QLabel("Desconectado")

        controls_layout.addWidget(QLabel("Puerto:"))
        controls_layout.addWidget(self.port_combo, 1)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addWidget(QLabel("Baudios:"))
        controls_layout.addWidget(self.baud_combo)
        controls_layout.addWidget(self.connect_button)

        self.plot_widget = pg.PlotWidget(
            title="Datos del microcontrolador en tiempo real",
            background="w",
            foreground="k",
        )
        self.plot_widget.setLabel("bottom", "Muestra")
        self.plot_widget.setLabel("left", "Valor")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen("b", width=2))
        self.plot_curve.setClipToView(True)
        self.plot_timer = QTimer(self)
        self.plot_timer.setInterval(33)
        self.plot_timer.timeout.connect(self._refresh_plot)

        layout.addLayout(controls_layout)
        layout.addWidget(self.plot_widget)
        layout.addWidget(self.status_label)

        self.refresh_ports()

    def refresh_ports(self):
        current_port = self.port_combo.currentText().strip()
        ports = [port.device for port in list_ports.comports()]
        if not ports:
            ports = ["/dev/ttyUSB0", "/dev/ttyACM0", "COM3"]
        if current_port and current_port not in ports:
            ports.insert(0, current_port)

        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if current_port:
            self.port_combo.setCurrentText(current_port)

    def toggle_connection(self):
        reader = self.reader_thread
        if reader is not None and reader.isRunning():
            self.connect_button.setEnabled(False)
            self.connect_button.setText("Desconectando...")
            reader.stop()
            return

        port = self.port_combo.currentText().strip()
        if not port:
            self._show_error("Selecciona o escribe un puerto serie.")
            return

        try:
            baudrate = int(self.baud_combo.currentText())
        except ValueError:
            self._show_error("La velocidad en baudios no es valida.")
            return

        self.data_x.clear()
        self.data_y.clear()
        self.sample_index = 0
        self.plot_curve.clear()
        self.plot_timer.stop()
        self._reader_error = False

        reader = SerialReaderThread(port, baudrate, self)
        reader.new_data.connect(self.update_plot)
        reader.connected.connect(self._on_connected)
        reader.error.connect(self._show_error)
        reader.finished.connect(self._on_reader_finished)
        self.reader_thread = reader

        self.port_combo.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.baud_combo.setEnabled(False)
        self.connect_button.setText("Desconectar")
        self.connect_button.setEnabled(True)
        self.status_label.setText("Conectando...")
        reader.start()

    def _on_connected(self, port):
        self.status_label.setText(f"Conectado a {port}")

    def _show_error(self, message):
        self._reader_error = True
        self.status_label.setText(f"Error serial: {message}")

    def _on_reader_finished(self):
        reader = self.reader_thread
        if reader is None:
            return

        self.reader_thread = None
        reader.deleteLater()
        self._refresh_plot()
        self.plot_timer.stop()
        self.port_combo.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.baud_combo.setEnabled(True)
        self.connect_button.setEnabled(True)
        self.connect_button.setText("Conectar")
        if not self._reader_error:
            self.status_label.setText("Desconectado")

    def update_plot(self, value):
        self.data_x.append(self.sample_index)
        self.data_y.append(value)
        self.sample_index += 1

        if not self.plot_timer.isActive():
            self.plot_timer.start()

    def _refresh_plot(self):
        self.plot_curve.setData(list(self.data_x), list(self.data_y))

    def closeEvent(self, event):
        reader = self.reader_thread
        if reader is not None and reader.isRunning():
            reader.stop()
            if not reader.wait(1500):
                self.status_label.setText("Esperando a que termine la lectura serie...")
                event.ignore()
                return
            self.reader_thread = None
            reader.deleteLater()
        self.plot_timer.stop()
        event.accept()
