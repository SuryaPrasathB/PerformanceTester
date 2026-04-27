import logging

class PLCController:
    """
    Control module for the PLC (Modbus RTU/TCP).
    Maps high-level logical hardware control to Modbus registers/coils.
    """
    def __init__(self, modbus_driver, config: dict):
        self.modbus_driver = modbus_driver
        self.config = config.get("plc", {})
        self.coils = self.config.get("coils", {})
        self.registers = self.config.get("registers", {})
        self.logger = logging.getLogger(__name__)
        
    def write_coil(self, address: int, value: bool) -> bool:
        """Raw write to a Modbus coil."""
        return self.modbus_driver.write_data(address=address, value=1 if value else 0)

    def read_coil(self, address: int) -> bool:
        """Raw read from a Modbus coil."""
        data = self.modbus_driver.read_data(address=address, count=1)
        return bool(data[0]) if data else False

    def write_register(self, address: int, value: int) -> bool:
        """Raw write to a Modbus holding register."""
        return self.modbus_driver.write_data(address=address, value=value)

    def read_register(self, address: int) -> int:
        """Raw read from a Modbus input/holding register."""
        data = self.modbus_driver.read_data(address=address, count=1)
        return data[0] if data else 0

    def connect(self) -> bool:
        """Ensures the underlying PLC modbus connection is active."""
        if not self.modbus_driver.is_connected:
            return self.modbus_driver.connect()
        return True

    def set_output(self, channel_name: str, state: bool) -> bool:
        """Sets a mapped coil output."""
        if channel_name not in self.coils:
            self.logger.error(f"Cannot set output: '{channel_name}' not defined in config.")
            return False
            
        coil_address = self.coils[channel_name]
        value = 1 if state else 0
        self.logger.info(f"PLC: Setting output '{channel_name}' (coil {coil_address}) to {state}")
        # Note: Depending on modbus library, write_coil might be separate from write_register.
        # Here we assume the modbus_driver write_data handles coils or we will use it for register.
        # We will assume write_data can be used, or driver needs write_coil method.
        # But modbus_driver only has write_data. Let's use it as is for now.
        return self.modbus_driver.write_data(address=coil_address, value=value)

    def read_input(self, channel_name: str) -> int:
        """Reads a mapped register input."""
        if channel_name not in self.registers:
            self.logger.error(f"Cannot read input: '{channel_name}' not defined in config.")
            return 0
            
        register_address = self.registers[channel_name]
        self.logger.debug(f"PLC: Reading input '{channel_name}' (register {register_address})")
        data = self.modbus_driver.read_data(address=register_address, count=1)
        if data and len(data) > 0:
            return data[0]
        return 0

    def emergency_stop(self) -> bool:
        """
        Hard stops all critical outputs immediately. 
        It prioritizes turning off relays and loads.
        """
        self.logger.critical("PLC EMERGENCY STOP INITIATED.")
        results = []
        for channel_name in ["relay_main", "load_on", "fault_trigger"]:
            if channel_name in self.coils:
                results.append(self.set_output(channel_name, False))
        
        return all(results)
