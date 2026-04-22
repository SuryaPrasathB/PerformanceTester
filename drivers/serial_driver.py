import serial
import time
from .base_driver import BaseDriver
import logging

class SerialDriver(BaseDriver):
    """
    Serial Driver for communicating with devices via serial ports using pyserial.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.port = config.get("port", "COM1")
        self.baudrate = config.get("baudrate", 9600)
        self.serial_conn = None

    def connect(self) -> bool:
        """Establishes connection to the serial device."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] Serial connected to {self.port} at {self.baudrate} baud.")
            self.is_connected = True
            return True
            
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            self.is_connected = self.serial_conn.is_open
            if self.is_connected:
                self.logger.info(f"Serial connected to {self.port} at {self.baudrate} baud.")
            return self.is_connected
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to Serial on {self.port}: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Closes the connection."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] Serial disconnected from {self.port}.")
            self.is_connected = False
            return True
            
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.is_connected = False
            self.logger.info(f"Serial disconnected from {self.port}.")
            return True
        return True

    def read_data(self, size: int = 1024) -> bytes:
        """Reads data from the serial device."""
        if self.mock_mode:
            self.logger.debug(f"[MOCK] Serial reading data from {self.port}.")
            time.sleep(0.1) # Simulate delay
            return b"MOCK_DATA"
            
        if not self.is_connected or not self.serial_conn:
            self.logger.error(f"Cannot read: Serial not connected to {self.port}.")
            return b""
            
        try:
            data = self.serial_conn.read(size)
            self.logger.debug(f"Read {len(data)} bytes from {self.port}.")
            return data
        except serial.SerialException as e:
            self.logger.error(f"Read error on {self.port}: {e}")
            return b""

    def write_data(self, data: bytes) -> bool:
        """Writes data to the serial device."""
        if self.mock_mode:
            self.logger.debug(f"[MOCK] Serial writing {len(data)} bytes to {self.port}.")
            time.sleep(0.1)
            return True
            
        if not self.is_connected or not self.serial_conn:
            self.logger.error(f"Cannot write: Serial not connected to {self.port}.")
            return False
            
        try:
            bytes_written = self.serial_conn.write(data)
            self.logger.debug(f"Wrote {bytes_written} bytes to {self.port}.")
            return True
        except serial.SerialException as e:
            self.logger.error(f"Write error on {self.port}: {e}")
            return False
