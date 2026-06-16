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
    waveform_captured = Signal(str, list, int, int) # name, data, timebase, range

    def __init__(self, device_manager, config_service):
        super().__init__()
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        self.context = None
        
        # Pull global config dict
        self.config = {
            "plc": config_service.get_config().get("plc", {}),
            "safety": config_service.get_config().get("safety", {})
        }

        self.plc_drv = None
        self.energymeter_drv = None
        self.picoscope_drv = None
        self.mfm_drv = None
        self.mfm2_drv = None
        
        # Logical hardware controllers
        self.plc_controller = None
        self.load_controller = None
        self.safety_manager = None
        self.signal_injection = None
        
    @property
    def plc(self) -> PLCController:
        """Direct access to PLC controller."""
        return self.plc_controller

    @property
    def energymeter(self):
        """Direct access to the Energy Meter driver."""
        return self.energymeter_drv

    @property
    def mfm(self):
        """Direct access to the MFM (Multi-Function Meter) driver."""
        return self.mfm_drv

    @property
    def mfm2(self):
        """Direct access to the MFM Meter 2 driver (mA/G7 current)."""
        return self.mfm2_drv

    @property
    def picoscope(self):
        """Direct access to the PicoScope driver."""
        return self.picoscope_drv

    @property
    def source(self) -> SignalInjection:
        """Direct access to the Signal Injection / Power Source."""
        return self.signal_injection

    def initialize_all(self):
        """Builds all subcomponents based on available drivers in DeviceManager."""
        self.logger.info("Hardware Service: Initializing...")
        self.hardware_status_update.emit("System", "Initializing Hardware Subsystems...")
        
        # Link drivers dynamically from device_manager 
        self.plc_drv = self.device_manager.drivers.get("PLC1")
        self.energymeter_drv = self.device_manager.drivers.get("EnergyMeter1")
        self.picoscope_drv = self.device_manager.drivers.get("PicoScope1")
        self.mfm_drv = self.device_manager.drivers.get("MFMMeter1") # Using specific MFM Meter
        self.mfm2_drv = self.device_manager.drivers.get("MFMMeter2")
        self.waveform_counter = 0

        if self.energymeter_drv and not self.energymeter_drv.is_connected:
            self.logger.info("Hardware Service: Auto-connecting Energy Meter...")
            self.energymeter_drv.connect()
            
        if self.picoscope_drv and not self.picoscope_drv.is_connected:
            self.logger.info("Hardware Service: Auto-connecting PicoScope...")
            self.picoscope_drv.connect()

        if self.plc_drv:
            if not self.plc_drv.is_connected:
                self.logger.info("Hardware Service: Auto-connecting PLC...")
                self.plc_drv.connect()
            self.plc_controller = PLCController(self.plc_drv, self.config)
            self.load_controller = LoadController(self.plc_controller)
            self.safety_manager = SafetyManager(self.plc_controller, self.config)
        
        if self.mfm_drv:
            if not self.mfm_drv.is_connected:
                self.logger.info("Hardware Service: Auto-connecting MFM Meter 1...")
                self.mfm_drv.connect()
            # We also use the MFM driver for signal injection control if applicable
            self.signal_injection = SignalInjection(self.mfm_drv, self.config)
            
        if self.mfm2_drv:
            if not self.mfm2_drv.is_connected:
                self.logger.info("Hardware Service: Auto-connecting MFM Meter 2...")
                self.mfm2_drv.connect()
            
        self.hardware_status_update.emit("System", "Initialization Complete")

    def shutdown_all(self):
        """Safely powers down all active hardware."""
        self.logger.info("Hardware Service: System Shutdown.")
        if self.load_controller:
            self.load_controller.turn_load_off()
        if self.picoscope_drv:
            self.picoscope_drv.stop_capture()

    def start_waveform_capture(self):
        """Starts waveform capture block on PicoScope."""
        if self.picoscope_drv:
            self.logger.info("Hardware Service: Starting PicoScope capture...")
            self.picoscope_drv.start_capture()
        else:
            self.logger.warning("Hardware Service: Cannot start capture, PicoScope driver not linked.")

    def stop_waveform_capture(self, name: str = None):
        """Stops waveform capture, retrieves waveform data and emits captured signal."""
        self.waveform_counter += 1
        if name is None:
            name = f"Waveform {self.waveform_counter}"
            
        if self.picoscope_drv:
            self.logger.info(f"Hardware Service: Stopping PicoScope capture for '{name}'...")
            self.picoscope_drv.stop_capture()
            data = self.picoscope_drv.get_waveform()
            if data:
                timebase = self.picoscope_drv.timebase
                # RANGE_20V (index 10)
                voltage_range = 10 
                
                # Check for dual channels and calculate PF if not G5 Fault Current Making Capacity
                test_id = "unknown"
                if hasattr(self, 'context') and self.context:
                    test_id = getattr(self.context, "test_identifier", "unknown").lower()
                
                # Retrieve the number of points for logging
                num_points = len(data[0]) if (isinstance(data, list) and len(data) == 2 and isinstance(data[0], list)) else len(data)
                self.logger.info(f"Hardware Service: Emitting captured waveform '{name}' with {num_points} points. Test ID: {test_id}")
                
                if isinstance(data, list) and len(data) == 2 and isinstance(data[0], list):
                    if test_id != "g5":
                        try:
                            from core.waveform_analyzer import calculate_pulse_duration, calculate_pf_from_duration
                            duration_ms = calculate_pulse_duration(data[1], timebase)
                            if duration_ms > 0.0:
                                pf = calculate_pf_from_duration(duration_ms)
                                self.logger.info(f"Hardware Service: Calculated Power Factor from current waveform: {pf:.3f} (Duration: {duration_ms:.2f} ms)")
                                if hasattr(self, 'context') and self.context:
                                    self.context.update_runtime_value("power_factor", pf)
                                    if not isinstance(self.context.test_results, dict):
                                        self.context.test_results = {}
                                    self.context.test_results["calculated_pf"] = pf
                            else:
                                self.logger.info("Hardware Service: No current pulse detected, defaulting PF calculation to UPF.")
                        except Exception as e:
                            self.logger.error(f"Hardware Service: Error calculating Power Factor from waveform: {e}")
                            
                self.waveform_captured.emit(name, data, timebase, voltage_range)
            else:
                self.logger.warning("Hardware Service: PicoScope returned empty waveform data.")
        else:
            self.logger.warning("Hardware Service: Cannot stop capture, PicoScope driver not linked.")

    def get_meter_readings(self) -> dict:
        """Polls meter driver for current V, I, and Energy measurements."""
        if not self.energymeter_drv or not self.energymeter_drv.is_connected:
            self.logger.warning("Hardware Service: Meter not connected.")
            return {"voltage": 0.0, "current": 0.0}
            
        data = self.energymeter_drv.read_data()
        
        # Ensure data is a dictionary (Mock drivers might return a single value if not updated)
        if not isinstance(data, dict):
            if isinstance(data, (int, float)):
                 return {"voltage": 0.0, "current": float(data)}
            return {"voltage": 0.0, "current": 0.0}
            
        return data

    def read_meter_registers(self, register_list: list) -> dict:
        """
        Reads a list of memory registers from the meter.
        Supports both DLMS OBIS codes and Modbus addresses depending on the driver.
        """
        if not self.energymeter_drv or not self.energymeter_drv.is_connected:
            self.logger.error("Hardware Service: Meter driver unavailable or disconnected.")
            return {}

        results = {}
        for reg in register_list:
            results[reg] = self.energymeter_drv.read_data(reg)
        return results

    def read_mfm_registers(self, register_list: list) -> dict:
        """
        Reads arbitrary registers from the MFM meter.
        """
        if not self.mfm_drv or not self.mfm_drv.is_connected:
            self.logger.error("Hardware Service: MFM Meter driver unavailable or disconnected.")
            return {}

        results = {}
        for reg in register_list:
            results[reg] = self.mfm_drv.read_data(address=int(reg), count=1)
            # The modbus driver typically returns a list of values
            if isinstance(results[reg], list) and len(results[reg]) > 0:
                results[reg] = results[reg][0]
        return results

    def read_mfm_telemetry(self) -> dict:
        """
        Reads Voltage, Current, and Power Factor from the MFM Meter.
        During G7, current is read from MFM Meter 2, while voltage and PF are read from MFM Meter 1.
        """
        is_g7 = False
        if hasattr(self, 'context') and self.context:
            is_g7 = (getattr(self.context, "test_identifier", None) == "g7")

        drv_v_pf = self.mfm_drv
        drv_i = self.mfm2_drv if (is_g7 and self.mfm2_drv) else self.mfm_drv

        if not drv_v_pf or not drv_v_pf.is_connected:
            return {}
        try:
            from core.hardware_mapping import MFMRegister
            
            # Read voltage and PF from drv_v_pf
            v = 0.0
            pf = 1.0
            if hasattr(drv_v_pf, "read_float"):
                v = drv_v_pf.read_float(int(MFMRegister.VOLTAGE), function_code=4, swapped=True)
                pf = drv_v_pf.read_float(int(MFMRegister.PF), function_code=4, swapped=True)
            else:
                v_data = drv_v_pf.read_data(address=int(MFMRegister.VOLTAGE), count=1)
                pf_data = drv_v_pf.read_data(address=int(MFMRegister.PF), count=1)
                v = v_data[0] if v_data else 0.0
                pf = pf_data[0] if pf_data else 1.0

            # Read current from drv_i
            i = 0.0
            if drv_i and drv_i.is_connected:
                if hasattr(drv_i, "read_float"):
                    i = drv_i.read_float(int(MFMRegister.CURRENT), function_code=4, swapped=True)
                else:
                    i_data = drv_i.read_data(address=int(MFMRegister.CURRENT), count=1)
                    i = i_data[0] if i_data else 0.0

            return {
                "voltage": v,
                "current": i,
                "power_factor": pf,
                "active_power": v * i * pf
            }
        except Exception as e:
            self.logger.error(f"Error reading MFM telemetry: {e}")
        return {}

    def read_mfm_current(self) -> float:
        """
        Reads instantaneous current from the MFM meter.
        During G7, current is read from MFM Meter 2.
        """
        is_g7 = False
        if hasattr(self, 'context') and self.context:
            is_g7 = (getattr(self.context, "test_identifier", None) == "g7")

        drv_i = self.mfm2_drv if (is_g7 and self.mfm2_drv) else self.mfm_drv
        if not drv_i or not drv_i.is_connected:
            return 0.0
        try:
            from core.hardware_mapping import MFMRegister
            if hasattr(drv_i, "read_float"):
                return drv_i.read_float(int(MFMRegister.CURRENT), function_code=4, swapped=True)
            else:
                i_data = drv_i.read_data(address=int(MFMRegister.CURRENT), count=1)
                return i_data[0] if i_data else 0.0
        except Exception as e:
            self.logger.error(f"Error reading MFM current: {e}")
        return 0.0

    def wait_for_current_zero(self, threshold: float = 0.1, timeout_sec: int = 30, context=None) -> bool:
        """
        Monitors the meter current until it drops below the threshold or timeout occurs.
        """
        import time
        start_time = time.time()
        self.logger.info(f"Monitoring current until < {threshold}A (Timeout: {timeout_sec}s)")
        
        # Simulation for mock mode: gradually decrease current
        mock_sim_current = 5.0 
        
        while (time.time() - start_time) < timeout_sec:
            if context:
                context.check_cancel()
                context.wait_if_paused()

            readings = self.get_meter_readings()
            current = readings.get("current", 0.0)
            
            # If in mock mode, simulate current drop over time to allow test to progress
            if self.energymeter_drv and self.energymeter_drv.mock_mode:
                # Decrease mock current by 1A every 2 seconds
                elapsed = time.time() - start_time
                current = max(0.0, mock_sim_current - (elapsed * 0.5))
                self.logger.debug(f"[MOCK SIM] Current decaying: {current:.2f}A")
            
            if current < threshold:
                self.logger.info(f"Current reached zero-threshold: {current:.2f}A")
                return True
            
            time.sleep(1)
            
        self.logger.error("Timeout waiting for current to reach zero.")
        return False

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
