import logging

class SafetyManager:
    """
    CRITICAL: Validates system before any operation and prevents unsafe conditions.
    """
    def __init__(self, plc_controller, config: dict):
        self.plc = plc_controller
        self.config = config.get("safety", {})
        self.logger = logging.getLogger(__name__)
        
        self.max_voltage = self.config.get("max_voltage_v", 300.0)
        self.max_current = self.config.get("max_current_a", 120.0)
        
        # Master flag to lock out the system after an emergency
        self.emergency_triggered = False

    def trigger_emergency_shutdown(self):
        """Halts all operations and locks out the system."""
        if not self.emergency_triggered:
            self.logger.critical("SAFETY MANAGER: EMERGENCY SHUTDOWN INITIATED!")
            self.emergency_triggered = True
            
        # Ensure outputs are disabled via PLC hard stop
        self.plc.emergency_stop()

    def reset_emergency(self):
        """Clears the emergency state. Should only be called via UI after manual resolution."""
        self.logger.info("SAFETY MANAGER: Emergency state reset manually.")
        self.emergency_triggered = False

    def pre_check(self, context) -> bool:
        """
        Validates system state BEFORE attempting any test step.
        Returns True if safe to proceed, False otherwise.
        """
        if self.emergency_triggered:
            self.logger.error("Pre-check failed: System is in EMERGENCY LOCKOUT state. Please reset via UI.")
            return False

        # Current setpoints from context
        requested_v = context.get_runtime_value("voltage", 0.0)
        requested_i = context.get_runtime_value("current", 0.0)

        # 1. Bounds checking
        if requested_v > self.max_voltage:
            self.logger.error(f"Pre-check failed: Requested voltage ({requested_v}V) exceeds absolute limit ({self.max_voltage}V).")
            return False

        if requested_i > self.max_current:
            self.logger.error(f"Pre-check failed: Requested current ({requested_i}A) exceeds absolute limit ({self.max_current}A).")
            return False

        # 2. Could check PLC connection status here
        if not self.plc.modbus_driver.is_connected:
            self.logger.error("Pre-check failed: PLC is not connected.")
            return False
            
        self.logger.debug("Safety pre-check passed.")
        return True

    def monitor_live(self, context) -> bool:
        """
        Continuously called during test execution to ensure no physical bounds 
        are exceeded dynamically (e.g. overcurrent spike from meter reading).
        """
        if self.emergency_triggered:
            return False

        # In a real environment, we'd read hardware directly if mapped:
        live_v = self.plc.read_input("voltage_monitor") if "voltage_monitor" in self.plc.registers else 0.0
        live_i = self.plc.read_input("current_monitor") if "current_monitor" in self.plc.registers else 0.0
        
        # For our mock/simulated context, we might also rely on the context variables
        ctx_v = context.get_runtime_value("voltage", 0.0)
        ctx_i = context.get_runtime_value("current", 0.0)

        # Check bounds
        if ctx_v > self.max_voltage + 10.0:  # Allow small margin before trip
            self.logger.critical(f"Live Monitor Trip: OVERVOLTAGE condition detected ({ctx_v}V).")
            self.trigger_emergency_shutdown()
            return False

        if ctx_i > self.max_current + 1.0:
            self.logger.critical(f"Live Monitor Trip: OVERCURRENT condition detected ({ctx_i}A).")
            self.trigger_emergency_shutdown()
            return False

        return True
