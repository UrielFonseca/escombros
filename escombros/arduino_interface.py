import serial
import threading
import time

class ArduinoInterface:
    def __init__(self, port='COM3', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.latest_sensor_value = None
        self.latest_voltage = None
        self.running = False
        self.thread = None

    def start(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self.read_loop, daemon=True)
            self.thread.start()
            print(f"Connected to Arduino on {self.port} at {self.baudrate} baud.")
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")

    def read_loop(self):
        while self.running:
            try:
                line = self.serial_conn.readline().decode('utf-8').strip()
                if line:
                    parts = line.split(',')
                    if len(parts) == 2:
                        self.latest_sensor_value = int(parts[0])
                        self.latest_voltage = float(parts[1])
            except Exception as e:
                print(f"Error reading from Arduino: {e}")
            time.sleep(0.1)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        print("Arduino connection closed.")

    def get_sensor_value(self):
        return self.latest_sensor_value

    def get_voltage(self):
        return self.latest_voltage

# Singleton instance
arduino_interface = ArduinoInterface()

def start_arduino():
    arduino_interface.start()

def stop_arduino():
    arduino_interface.stop()

def get_sensor_value():
    return arduino_interface.get_sensor_value()

def get_voltage():
    return arduino_interface.get_voltage()
