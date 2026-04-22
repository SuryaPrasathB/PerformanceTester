from PySide6.QtCore import QObject, Signal
import logging

from hardware.plc_controller import PLCController
from hardware.load_controller import LoadController
from hardware.safety_manager import SafetyManager
from hardware.signal_injection import SignalInjection

class HardwareService(QObject):
    """
    Facade Layer orchestrating interactions between TestRunner and Physical Hardware.
    Isolates lower-level calls into generalized macros.
    Emits specific Qt Signals for UI status propagation.
    """
    hardware_status_update = Signal(str, str) # module, message
    safety_alert = Signal(str)
    emergency_triggered = Signal()

    def __init__(self, device_manager, config_service):
        super().__init__()
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        
        # Pull global config dict
        self.config = {
            "plc": config_service.get_config().get("plc", {}),
            "safety": config_service.get_config().get("safety", {})
        }

        self.plc_drv = None
        self.meter_drv = None
        self.picoscope_drv = None
        
        # Logical hardware controllers
        self.plc_controller = None
        self.load_controller = None
        self.safety_manager = None
        self.signal_injection = None

    def initialize_all(self):
        """Builds all subcomponents based on available drivers in DeviceManager."""
        self.logger.info("Hardware Service: Initializing...")
        self.hardware_status_update.emit("System", "Initializing Hardware Subsystems...")
        
        # Link drivers dynamically from device_manager 
        # (Assuming naming convention from device_config)
        self.plc_drv = self.device_manager.drivers.get("PLC1")
        self.meter_drv = self.device_manager.drivers.get("EnergyMeter1")
        self.picoscope_drv = self.device_manager.drivers.get("PicoScope1")
        # Sensor/Serial can also be mapped
        sensor_drv = self.device_manager.drivers.get("Sensor1")

        if self.plc_drv:
            self.plc_controller = PLCController(self.plc_drv, self.config)
            self.load_controller = LoadController(self.plc_controller)
            self.safety_manager = SafetyManager(self.plc_controller, self.config)
        
        if sensor_drv: # Assume we use the generic serial device to control injections
            self.signal_injection = SignalInjection(sensor_drv, self.config)
            
        self.hardware_status_update.emit("System", "Initialization Complete")

    def shutdown_all(self):
        """Safely powers down all active hardware."""
        self.logger.info("Hardware Service: System Shutdown.")
        if self.load_controller:
            self.load_controller.turn_load_off()
        if self.picoscope_drv:
            self.picoscope_drv.stop_capture()

    def get_meter_readings(self) -> dict:
        """Polls meter driver for current V, I, and Energy measurements."""
        if not self.meter_drv or not self.meter_drv.is_connected:
            self.logger.warning("Hardware Service: Meter not connected.")
            return {"voltage": 0.0, "current": 0.0}
            
        # In real logic, invoke DLMS driver methods directly
        # Example dummy fetch logic matching mock functionality
        data = self.meter_drv.read_data()
        
        # If mocked, simply fake some read data variation based on injection values
        # We will assume TestRunner updates Context, not this class directly.
        # But here we can fetch actual raw data from the driver.
        return data

    def control_load(self, turn_on: bool) -> bool:
        """Acts on the physical output relays safely."""
        if not self.load_controller:
            self.logger.error("Hardware Service: Load Controller unavailable.")
            return False
            
        if turn_on:
            return self.load_controller.turn_load_on()
        else:
            return self.load_controller.turn_load_off()

    def inject_signal(self, v: float, i: float, pf: float) -> bool:
        """Sends voltage and current vectors to power source."""
        if not self.signal_injection:
            self.logger.error("Hardware Service: Signal Injection unavailable.")
            return False
            
        self.signal_injection.set_voltage(v)
        self.signal_injection.set_current(i)
        self.signal_injection.set_pf(pf)
        return self.signal_injection.apply()

    def trigger_emergency_stop(self):
        """Handles emergency stop logic across all components."""
        self.emergency_triggered.emit() # Notify UI
        self.hardware_status_update.emit("Emergency", "STOP INITIATED")
        if self.safety_manager:
            self.safety_manager.trigger_emergency_shutdown()
        else:
            self.logger.critical("SAFETY MANAGER MISSING! Attempting raw load off.")
            if self.load_controller:
                self.load_controller.turn_load_off()
