from pymodbus.client import ModbusTcpClient
import time
from .base_driver import BaseDriver
import logging

class ModbusDriver(BaseDriver):
    """
    Modbus Driver for communicating with PLC or devices via Modbus TCP.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.ip = config.get("ip", "127.0.0.1")
        self.port = config.get("port", 502)
        self.client = None

    def connect(self) -> bool:
        """Establishes Modbus TCP connection."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] Modbus connected to {self.ip}:{self.port}.")
            self.is_connected = True
            return True

        try:
            self.client = ModbusTcpClient(self.ip, port=self.port)
            self.is_connected = self.client.connect()
            if self.is_connected:
                self.logger.info(f"Modbus connected to {self.ip}:{self.port}.")
            else:
                self.logger.error(f"Failed to connect to Modbus {self.ip}:{self.port}.")
            return self.is_connected
        except Exception as e:
            self.logger.error(f"Modbus connection exception on {self.ip}:{self.port} - {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Closes the Modbus connection."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] Modbus disconnected from {self.ip}:{self.port}.")
            self.is_connected = False
            return True

        if self.client:
            self.client.close()
            self.is_connected = False
            self.logger.info(f"Modbus disconnected from {self.ip}:{self.port}.")
        return True

    def read_data(self, address: int = 0, count: int = 1) -> list:
        """Reads holding registers from the Modbus device."""
        if self.mock_mode:
            # self.logger.debug(f"[MOCK] Modbus reading {count} registers from address {address} on {self.ip}:{self.port}.")
            time.sleep(0.1)
            return [0] * count

        if not self.is_connected or not self.client:
            self.logger.error(f"Cannot read: Modbus not connected to {self.ip}:{self.port}.")
            return []

        try:
            result = self.client.read_holding_registers(address=address, count=count)
            if result.isError():
                self.logger.error(f"Modbus read error on {self.ip}:{self.port}: {result}")
                return []
            self.logger.debug(f"Modbus read success from {self.ip}:{self.port}: {result.registers}")
            return result.registers
        except Exception as e:
            self.logger.error(f"Modbus read exception on {self.ip}:{self.port}: {e}")
            return []

    def write_data(self, address: int, value: int) -> bool:
        """Writes to a single holding register."""
        if self.mock_mode:
            # self.logger.debug(f"[MOCK] Modbus writing value {value} to address {address} on {self.ip}:{self.port}.")
            time.sleep(0.1)
            return True

        if not self.is_connected or not self.client:
            self.logger.error(f"Cannot write: Modbus not connected to {self.ip}:{self.port}.")
            return False

        try:
            result = self.client.write_register(address=address, value=value)
            if result.isError():
                self.logger.error(f"Modbus write error on {self.ip}:{self.port}: {result}")
                return False
            self.logger.debug(f"Modbus wrote {value} to address {address} on {self.ip}:{self.port}.")
            return True
        except Exception as e:
            self.logger.error(f"Modbus write exception on {self.ip}:{self.port}: {e}")
            return False
