from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import time
import threading
from .base_driver import BaseDriver
import logging

class ModbusDriver(BaseDriver):
    """
    Modbus Driver for communicating with PLC (TCP) or MFM (RTU Serial) via Modbus.
    """
    _shared_clients = {}
    _shared_locks = {}
    _client_refcounts = {}

    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.ip = config.get("ip", "127.0.0.1")
        # Port can be integer (TCP) or string (e.g. "COM1" for RTU)
        self.port = config.get("port", 502)
        
        # Connection params
        self.baudrate = config.get("baudrate", config.get("baud_rate", 9600))
        self.bytesize = config.get("bytesize", config.get("data_bits", 8))
        
        # Parity mapping (NONE, EVEN, ODD)
        parity_val = str(config.get("parity", "NONE")).upper()
        if parity_val in ("NONE", "N"):
            self.parity = "N"
        elif parity_val in ("EVEN", "E"):
            self.parity = "E"
        elif parity_val in ("ODD", "O"):
            self.parity = "O"
        else:
            self.parity = parity_val[0] if parity_val else "N"
            
        self.stopbits = config.get("stopbits", config.get("stop_bits", 1))
        
        # Timeout settings (timeout in json might be in ms, e.g. 1000ms, or standard seconds)
        timeout_ms = config.get("timeout_ms")
        if timeout_ms is not None:
            self.timeout = float(timeout_ms) / 1000.0
        else:
            self.timeout = config.get("timeout", 1.0)
            
        self.client = None
        self.is_serial = False
        self.slave_id = int(config.get("slave_id", config.get("slave", 1)))
        
        # 200ms Read Cache to prevent bombarding meter with requests from multiple threads
        self._cache = {}
        self._cache_duration = 0.200 # seconds
        
        # Determine if serial client based on port string format (e.g., COM1, /dev/ttyUSB0)
        if isinstance(self.port, str) and (self.port.upper().startswith("COM") or self.port.startswith("/dev/")):
            self.is_serial = True

        # Use shared lock if sharing serial port
        if self.is_serial:
            port_key = self.port.upper() if isinstance(self.port, str) else str(self.port)
            if port_key not in ModbusDriver._shared_locks:
                ModbusDriver._shared_locks[port_key] = threading.RLock()
            self._lock = ModbusDriver._shared_locks[port_key]
        else:
            self._lock = threading.RLock()

    def connect(self) -> bool:
        """Establishes Modbus TCP or Serial RTU connection."""
        with self._lock:
            if self.mock_mode:
                self.logger.info(f"[MOCK] Modbus connected. (Serial={self.is_serial}, port/ip={self.port}/{self.ip})")
                self.is_connected = True
                return True

            try:
                if self.is_serial:
                    port_key = self.port.upper() if isinstance(self.port, str) else str(self.port)
                    if port_key in ModbusDriver._shared_clients:
                        self.client = ModbusDriver._shared_clients[port_key]
                        ModbusDriver._client_refcounts[port_key] = ModbusDriver._client_refcounts.get(port_key, 0) + 1
                        self.is_connected = self.client.connected if hasattr(self.client, 'connected') else True
                        self.logger.info(f"Reusing shared Modbus RTU client on {self.port}.")
                        return self.is_connected
                    
                    self.logger.info(f"Connecting to Modbus RTU on {self.port} (Baud: {self.baudrate}, Parity: {self.parity})...")
                    self.client = ModbusSerialClient(
                        port=self.port,
                        baudrate=int(self.baudrate),
                        bytesize=int(self.bytesize),
                        parity=self.parity,
                        stopbits=int(self.stopbits),
                        timeout=float(self.timeout)
                    )
                    self.is_connected = self.client.connect()
                    if self.is_connected:
                        ModbusDriver._shared_clients[port_key] = self.client
                        ModbusDriver._client_refcounts[port_key] = 1
                        self.logger.info(f"Modbus RTU connected to {self.port}.")
                    else:
                        self.logger.error(f"Failed to connect to Modbus RTU on {self.port}.")
                else:
                    self.logger.info(f"Connecting to Modbus TCP on {self.ip}:{self.port}...")
                    self.client = ModbusTcpClient(self.ip, port=int(self.port), timeout=float(self.timeout))
                    self.is_connected = self.client.connect()
                    if self.is_connected:
                        self.logger.info(f"Modbus TCP connected to {self.ip}:{self.port}.")
                    else:
                        self.logger.error(f"Failed to connect to Modbus TCP on {self.ip}:{self.port}.")
                return self.is_connected
            except Exception as e:
                self.logger.error(f"Modbus connection exception on {self.port or self.ip}: {e}")
                self.is_connected = False
                return False

    def disconnect(self) -> bool:
        """Closes the Modbus connection."""
        with self._lock:
            if self.mock_mode:
                self.logger.info(f"[MOCK] Modbus disconnected. (Serial={self.is_serial})")
                self.is_connected = False
                return True

            if self.client:
                if self.is_serial:
                    port_key = self.port.upper() if isinstance(self.port, str) else str(self.port)
                    ref = ModbusDriver._client_refcounts.get(port_key, 0)
                    if ref > 1:
                        ModbusDriver._client_refcounts[port_key] = ref - 1
                        self.logger.info(f"Decremented shared client refcount on {self.port} to {ref - 1}. Client remains open.")
                    else:
                        self.client.close()
                        if port_key in ModbusDriver._shared_clients:
                            del ModbusDriver._shared_clients[port_key]
                        if port_key in ModbusDriver._client_refcounts:
                            del ModbusDriver._client_refcounts[port_key]
                        self.logger.info(f"Closed shared Modbus RTU client on {self.port}.")
                else:
                    self.client.close()
                    self.logger.info(f"Modbus disconnected.")
                self.is_connected = False
            # Clear cache upon disconnect
            self._cache.clear()
            return True

    def read_data(self, address: int = 0, count: int = 1, slave: int = None, function_code: int = 3) -> list:
        """Reads input or holding registers from the Modbus device."""
        if slave is None:
            slave = self.slave_id
        with self._lock:
            # Check cache
            key = ('data', address, count, slave, function_code)
            now = time.time()
            if key in self._cache:
                timestamp, cached_val = self._cache[key]
                if now - timestamp < self._cache_duration:
                    return cached_val

            if self.mock_mode:
                time.sleep(0.05)
                res = [0] * count
                self._cache[key] = (now, res)
                return res

            if not self.is_connected or not self.client:
                self.logger.error(f"Cannot read: Modbus not connected.")
                return []

            try:
                # function_code 4 means read input registers; otherwise default/3 means holding registers
                if function_code == 4:
                    result = self.client.read_input_registers(address=address, count=count, slave=slave)
                else:
                    result = self.client.read_holding_registers(address=address, count=count, slave=slave)
                    
                if result.isError():
                    self.logger.error(f"Modbus read error (FC={function_code}, addr={address}): {result}")
                    return []
                self.logger.debug(f"Modbus read success (FC={function_code}, addr={address}): {result.registers}")
                
                res_regs = result.registers
                self._cache[key] = (now, res_regs)
                return res_regs
            except Exception as e:
                self.logger.error(f"Modbus read exception (FC={function_code}, addr={address}): {e}")
                return []

    def write_data(self, address: int, value: int, slave: int = None) -> bool:
        """Writes to a single register (or coil if mapped)."""
        if slave is None:
            slave = self.slave_id
        with self._lock:
            # Clear read cache on any write to guarantee consistency
            self._cache.clear()
            
            if self.mock_mode:
                time.sleep(0.05)
                return True

            if not self.is_connected or not self.client:
                self.logger.error(f"Cannot write: Modbus not connected.")
                return False

            try:
                result = self.client.write_register(address=address, value=value, slave=slave)
                if result.isError():
                    self.logger.error(f"Modbus write error (addr={address}, val={value}): {result}")
                    return False
                self.logger.debug(f"Modbus wrote {value} to address {address}.")
                return True
            except Exception as e:
                self.logger.error(f"Modbus write exception (addr={address}, val={value}): {e}")
                return False

    def read_float(self, address: int, function_code: int = 4, swapped: bool = True, slave: int = None) -> float:
        """
        Reads two 16-bit registers (32-bit total) and decodes them as a float.
        """
        if slave is None:
            slave = self.slave_id
        with self._lock:
            # Check cache
            key = ('float', address, function_code, swapped, slave)
            now = time.time()
            if key in self._cache:
                timestamp, cached_val = self._cache[key]
                if now - timestamp < self._cache_duration:
                    return cached_val

            if self.mock_mode:
                import random
                time.sleep(0.02)
                # realistic simulator readings
                if address in (40001, 0):
                    res = 240.2 + random.uniform(-1.0, 1.0)
                elif address in (40003, 2):
                    res = 5.15 + random.uniform(-0.1, 0.1)
                elif address in (40005, 4):
                    res = 0.98 + random.uniform(-0.01, 0.01)
                else:
                    res = random.uniform(0.0, 100.0)
                self._cache[key] = (now, res)
                return res

            # Standard Modbus documentation offset mapping: 40001 -> index 0, 40003 -> index 2, etc.
            reg_addr = address
            if reg_addr >= 40001:
                reg_addr = reg_addr - 40001
            elif reg_addr >= 40000:
                reg_addr = reg_addr - 40000

            try:
                regs = self.read_data(address=reg_addr, count=2, slave=slave, function_code=function_code)
                if len(regs) < 2:
                    self.logger.warning(f"Could not read float from address {address}: expected 2 registers, got {len(regs)}")
                    return 0.0

                import struct
                if swapped:
                    packed = struct.pack('>HH', regs[1], regs[0])
                else:
                    packed = struct.pack('>HH', regs[0], regs[1])
                res_float = struct.unpack('>f', packed)[0]
                self._cache[key] = (now, res_float)
                return res_float
            except Exception as e:
                self.logger.error(f"Error reading float from address {address} (mapped to {reg_addr}): {e}")
                return 0.0

    def read_coil(self, address: int, slave: int = None) -> bool:
        """Reads a single coil (binary value) from the Modbus device."""
        if slave is None:
            slave = self.slave_id
        with self._lock:
            if self.mock_mode:
                time.sleep(0.01)
                if not hasattr(self, "_mock_coils"):
                    self._mock_coils = {}
                return self._mock_coils.get(address, False)

            if not self.is_connected or not self.client:
                self.logger.error("Cannot read coil: Modbus not connected.")
                return False

            try:
                result = self.client.read_coils(address=address, count=1, slave=slave)
                if result.isError():
                    self.logger.error(f"Modbus read coil error (addr={address}): {result}")
                    return False
                val = result.bits[0] if result.bits else False
                self.logger.debug(f"Modbus read coil (addr={address}): {val}")
                return val
            except Exception as e:
                self.logger.error(f"Modbus read coil exception (addr={address}): {e}")
                return False

    def write_coil(self, address: int, value: bool, slave: int = None) -> bool:
        """Writes a single coil (binary value) to the Modbus device."""
        if slave is None:
            slave = self.slave_id
        with self._lock:
            # Clear read cache on any write to guarantee consistency
            self._cache.clear()

            if self.mock_mode:
                time.sleep(0.01)
                if not hasattr(self, "_mock_coils"):
                    self._mock_coils = {}
                self._mock_coils[address] = value
                return True

            if not self.is_connected or not self.client:
                self.logger.error("Cannot write coil: Modbus not connected.")
                return False

            try:
                result = self.client.write_coil(address=address, value=value, slave=slave)
                if result.isError():
                    self.logger.error(f"Modbus write coil error (addr={address}, val={value}): {result}")
                    return False
                self.logger.debug(f"Modbus wrote coil {value} to address {address}.")
                return True
            except Exception as e:
                self.logger.error(f"Modbus write coil exception (addr={address}, val={value}): {e}")
                return False



