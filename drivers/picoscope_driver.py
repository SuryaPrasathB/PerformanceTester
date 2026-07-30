import random
import time
import math
import logging
import ctypes
from ctypes import byref, c_short, c_int32
from .base_driver import BaseDriver

import os

# Mappings for PicoScope 2000 Series (ps2000.dll)
ps2000 = None
# Search paths in order: system path/current dir, 64-bit SDK, 32-bit SDK
dll_search_paths = [
    "ps2000.dll",
    r"C:\Program Files\Pico Technology\SDK\lib\ps2000.dll",
    r"C:\Program Files (x86)\Pico Technology\SDK\lib\ps2000.dll"
]

for path in dll_search_paths:
    try:
        ps2000 = ctypes.windll.LoadLibrary(path)
        if ps2000:
            break
    except Exception:
        continue

if not ps2000:
    logging.getLogger("PicoScopeDriver").warning("Could not load ps2000.dll from system search paths or standard Pico SDK directories. Fallback to Mock Mode will be active.")

# Configure ctypes argtypes and restype if library loaded successfully
if ps2000:
    ps2000.ps2000_open_unit.restype = c_short
    
    ps2000.ps2000_close_unit.argtypes = [c_short]
    ps2000.ps2000_close_unit.restype = c_short
    
    ps2000.ps2000_set_channel.argtypes = [c_short, c_short, c_short, c_short, c_short]
    ps2000.ps2000_set_channel.restype = c_short
    
    ps2000.ps2000_run_block.argtypes = [c_short, c_int32, c_short, c_short, ctypes.POINTER(c_int32)]
    ps2000.ps2000_run_block.restype = c_short
    
    ps2000.ps2000_ready.argtypes = [c_short]
    ps2000.ps2000_ready.restype = c_short
    
    ps2000.ps2000_stop.argtypes = [c_short]
    ps2000.ps2000_stop.restype = c_short
    
    ps2000.ps2000_get_values.argtypes = [
        c_short, 
        ctypes.POINTER(c_short), 
        ctypes.POINTER(c_short), 
        ctypes.POINTER(c_short), 
        ctypes.POINTER(c_short), 
        ctypes.POINTER(c_short), 
        c_int32
    ]
    ps2000.ps2000_get_values.restype = c_short
    
    ps2000.ps2000_set_trigger.argtypes = [c_short, c_short, c_short, c_short, c_short, c_short]
    ps2000.ps2000_set_trigger.restype = c_short
    
    try:
        ps2000.ps2000SetAdvTriggerChannelDirections.argtypes = [c_short, c_int32, c_int32, c_int32, c_int32, c_int32]
        ps2000.ps2000SetAdvTriggerChannelDirections.restype = c_short
    except AttributeError:
        # Advanced trigger might not be available in older DLLs
        pass
        
    class PS2000_TRIGGER_CHANNEL_PROPERTIES(ctypes.Structure):
        _fields_ = [
            ("thresholdMajor", c_short),
            ("thresholdMinor", c_short),
            ("hysteresis", ctypes.c_ushort),
            ("channel", c_short),
            ("thresholdMode", c_short)
        ]

    class PS2000_TRIGGER_CONDITIONS(ctypes.Structure):
        _fields_ = [
            ("channelA", c_int32),
            ("channelB", c_int32),
            ("channelC", c_int32),
            ("channelD", c_int32),
            ("ext", c_int32),
            ("pwq", c_int32)
        ]

    try:
        ps2000.ps2000SetAdvTriggerChannelProperties.argtypes = [
            c_short, 
            ctypes.POINTER(PS2000_TRIGGER_CHANNEL_PROPERTIES), 
            c_short, 
            c_int32
        ]
        ps2000.ps2000SetAdvTriggerChannelProperties.restype = c_short
        
        ps2000.ps2000SetAdvTriggerChannelConditions.argtypes = [
            c_short, 
            ctypes.POINTER(PS2000_TRIGGER_CONDITIONS), 
            c_short
        ]
        ps2000.ps2000SetAdvTriggerChannelConditions.restype = c_short
    except AttributeError:
        pass
        
# Advanced Trigger Direction Constants
PS2000_ADV_NONE = 0
PS2000_ADV_RISING = 2
PS2000_ADV_FALLING = 3
PS2000_ADV_RISING_OR_FALLING = 4


class PicoScopeDriver(BaseDriver):
    """
    Driver interfacing with PicoScope 2000 Series oscilloscope using PicoSDK DLL.
    Includes high-fidelity mock waveform synthesis for offline testing.
    """
    def __init__(self, config: dict, logger: logging.Logger):
        super().__init__(config, logger)
        self.port = config.get("port", "USB")
        self.handle = 0
        self.is_capturing = False
        self.no_of_values = config.get("no_of_values", 2500)
        self.timebase = config.get("timebase", 14) # Changed to 14 for high resolution 1.3s window
        self.range_a_index = config.get("range_a_index", 10) # 10 = +/- 20V
        self.range_b_index = config.get("range_b_index", 10) # 10 = +/- 20V
        self.enable_channel_a = config.get("enable_channel_a", True)
        self.enable_channel_b = config.get("enable_channel_b", True)
        self.capture_delay_ms = config.get("capture_delay_ms", 0)
        self.fcmc_capture_delay_ms = config.get("fcmc_capture_delay_ms", 0)
        self.trigger_mode = config.get("trigger_mode", "manual")  # "auto" or "manual"
        self.trigger_threshold_adc = config.get("trigger_threshold_adc", 1000)
        self.use_window_trigger = config.get("use_window_trigger", False)
        self.pre_trigger_percent = config.get("pre_trigger_percent", 30)
        self.mock_mode = config.get("mock", False)

    def connect(self) -> bool:
        """Establishes connection to PicoScope."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] PicoScope connected on port {self.port}.")
            self.handle = 999
            self.is_connected = True
            return True

        if not ps2000:
            self.logger.warning("PicoScope: ps2000.dll unavailable. PicoScope is not connected.")
            self.is_connected = False
            return False

        self.logger.info(f"PicoScope: Connecting on {self.port}...")
        try:
            h = ps2000.ps2000_open_unit()
            if h > 0:
                self.handle = h
                self.is_connected = True
                self.logger.info(f"PicoScope: Connected successfully. Handle: {self.handle}")
                
                # Enable or Disable Channel A
                ps2000.ps2000_set_channel(self.handle, 0, 1 if self.enable_channel_a else 0, 1, self.range_a_index)
                # Enable or Disable Channel B
                ps2000.ps2000_set_channel(self.handle, 1, 1 if self.enable_channel_b else 0, 1, self.range_b_index)
                
                # Perform one-time setup of Advanced Window Trigger upon connection
                self.setup_advanced_trigger(force=True)
                return True
            else:
                self.logger.error("PicoScope: Failed to open device unit. PicoScope is not connected.")
                self.handle = 0
                self.is_connected = False
                return False
        except Exception as e:
            self.logger.error(f"PicoScope: Exception during connection: {e}. PicoScope is not connected.")
            self.handle = 0
            self.is_connected = False
            return False

    def disconnect(self) -> bool:
        """Closes the connection to PicoScope."""
        if self.mock_mode or self.handle == 999:
            self.logger.info("[MOCK] PicoScope disconnected.")
            self.is_connected = False
            self.handle = 0
            return True

        if self.handle > 0 and ps2000:
            try:
                ps2000.ps2000_stop(self.handle)
                ps2000.ps2000_close_unit(self.handle)
                self.logger.info("PicoScope: Disconnected successfully.")
            except Exception as e:
                self.logger.error(f"PicoScope: Error during disconnection: {e}")
            finally:
                self.handle = 0
                self.is_connected = False
        return True

    def setup_advanced_trigger(self, force: bool = False) -> bool:
        """Configures Advanced Window Trigger once per range setup, avoiding mode switching during captures."""
        if self.mock_mode or self.handle <= 0 or not ps2000:
            return True

        trigger_source = 1 if self.enable_channel_b else 0
        active_range_idx = self.range_b_index if trigger_source == 1 else self.range_a_index
        RANGE_MAP = {
            0: 0.01, 1: 0.02, 2: 0.05, 3: 0.1, 4: 0.2, 
            5: 0.5, 6: 1.0, 7: 2.0, 8: 5.0, 9: 10.0, 10: 20.0
        }
        active_range_v = RANGE_MAP.get(active_range_idx, 20.0)
        target_threshold_v = 0.5
        dynamic_adc_threshold = int((target_threshold_v / active_range_v) * 32512)
        pre_trig_delay = -abs(self.pre_trigger_percent)

        cache_key = (trigger_source, active_range_idx, dynamic_adc_threshold, pre_trig_delay)
        if not force and getattr(self, "_configured_trigger_key", None) == cache_key:
            return True

        self.logger.info(f"PicoScope: Configuring Advanced Window Trigger -> {target_threshold_v:.3f}V (ADC: {dynamic_adc_threshold}), Pre-Trigger: {abs(self.pre_trigger_percent)}% on Range: {active_range_v}V")
        
        try:
            if hasattr(ps2000, "ps2000SetAdvTriggerChannelProperties"):
                prop = PS2000_TRIGGER_CHANNEL_PROPERTIES()
                prop.thresholdMajor = dynamic_adc_threshold
                prop.thresholdMinor = -dynamic_adc_threshold
                prop.hysteresis = 256  # ~0.78% hysteresis
                prop.channel = trigger_source
                prop.thresholdMode = 1  # WINDOW

                auto_ms = 1000  # 1000 ms auto-trigger timeout

                # Set configured pre-trigger delay on active trigger channel
                t_status0 = ps2000.ps2000_set_trigger(self.handle, trigger_source, dynamic_adc_threshold, 0, pre_trig_delay, auto_ms)
                
                # Apply advanced trigger configuration
                t_status1 = ps2000.ps2000SetAdvTriggerChannelProperties(self.handle, ctypes.byref(prop), 1, auto_ms)

                cond = PS2000_TRIGGER_CONDITIONS()
                cond.channelA = 1 if trigger_source == 0 else 0
                cond.channelB = 1 if trigger_source == 1 else 0
                cond.channelC = 0
                cond.channelD = 0
                cond.ext = 0
                cond.pwq = 0
                t_status2 = ps2000.ps2000SetAdvTriggerChannelConditions(self.handle, ctypes.byref(cond), 1)

                dirA = 1 if trigger_source == 0 else 0
                dirB = 1 if trigger_source == 1 else 0
                t_status3 = ps2000.ps2000SetAdvTriggerChannelDirections(self.handle, dirA, dirB, 0, 0, 0)

                self._configured_trigger_key = cache_key
                self.logger.debug(f"PicoScope: Advanced trigger set up (base:{t_status0}, props:{t_status1}, conds:{t_status2}, dirs:{t_status3})")
            else:
                ps2000.ps2000_set_trigger(self.handle, trigger_source, self.trigger_threshold_adc, 0, pre_trig_delay, 1000)
                self._configured_trigger_key = cache_key
            return True
        except Exception as e:
            self.logger.error(f"PicoScope: Error configuring advanced trigger: {e}")
            return False

    def set_channel_ranges(self, range_a_index: int, range_b_index: int):
        """Dynamically reconfigures channel voltage ranges and updates trigger once."""
        self.range_a_index = range_a_index
        self.range_b_index = range_b_index
        if self.handle > 0 and ps2000:
            # Enable or Disable Channel A
            ps2000.ps2000_set_channel(self.handle, 0, 1 if self.enable_channel_a else 0, 1, self.range_a_index)
            # Enable or Disable Channel B
            ps2000.ps2000_set_channel(self.handle, 1, 1 if self.enable_channel_b else 0, 1, self.range_b_index)
            self.logger.info(f"PicoScope: Channel ranges updated. A:{range_a_index}, B:{range_b_index}")
            # Reconfigure advanced trigger for new scale
            self.setup_advanced_trigger(force=True)

    def start_capture(self) -> bool:
        """Starts a block capture sequence using pre-configured Advanced Window Trigger."""
        if not self.is_connected:
            self.logger.error("PicoScope: Cannot start capture, device not connected.")
            return False
            
        self.logger.info("PicoScope: Starting block capture...")
        self.is_capturing = True
        
        if self.mock_mode or self.handle == 999:
            self.capture_start_time = time.time()
            return True
            
        if ps2000:
            try:
                # Ensure trigger is configured for current hardware state
                self.setup_advanced_trigger()
                
                time_indisposed_ms = c_int32(0)
                status = ps2000.ps2000_run_block(
                    self.handle, 
                    self.no_of_values, 
                    self.timebase, 
                    1, 
                    byref(time_indisposed_ms)
                )

                if status == 0:
                    self.logger.error("PicoScope: ps2000_run_block failed.")
                    self.is_capturing = False
                    return False
                    
                self.logger.info(f"PicoScope: Block capture initiated. Time indisposed: {time_indisposed_ms.value}ms")
                return True
            except Exception as e:
                self.logger.error(f"PicoScope: Error starting block capture: {e}")
                self.is_capturing = False
                return False
        return False
        return False

    def stop_capture(self) -> bool:
        """Stops block capture."""
        if not self.is_capturing:
            return True
            
        self.logger.info("PicoScope: Capture stopped.")
        self.is_capturing = False
        
        if self.mock_mode or self.handle == 999:
            return True
            
        if self.handle > 0 and ps2000:
            try:
                # Wait for ready or timeout
                start_wait = time.time()
                while ps2000.ps2000_ready(self.handle) == 0:
                    time.sleep(0.005)
                    if time.time() - start_wait > 5.0:
                        self.logger.warning("PicoScope: Timeout waiting for block ready status (or trigger never occurred).")
                        break
                ps2000.ps2000_stop(self.handle)
            except Exception as e:
                self.logger.error(f"PicoScope: Error stopping capture: {e}")
        return True

    def get_waveform(self) -> list:
        """Returns captured waveform data."""
        if not self.is_connected:
            self.logger.warning("PicoScope: Not connected. Returning empty waveform.")
            return []
            
        if self.mock_mode or self.handle == 999:
            return self._generate_mock_surge()

        if self.handle > 0 and ps2000:
            try:
                buffer_a = (c_short * self.no_of_values)()
                buffer_b = (c_short * self.no_of_values)()
                overflow = c_short(0)
                
                num_read = ps2000.ps2000_get_values(
                    self.handle,
                    buffer_a if self.enable_channel_a else None,
                    buffer_b if self.enable_channel_b else None,
                    None,
                    None,
                    byref(overflow),
                    self.no_of_values
                )
                
                if num_read > 0:
                    self.logger.info(f"PicoScope: Read {num_read} values from hardware buffer.")
                    
                    # Convert raw ADC values to voltage/current
                    # PS2000 Range mapping: 
                    # 6=1V, 7=2V, 8=5V, 9=10V, 10=20V
                    RANGE_MAP = {
                        0: 0.01, 1: 0.02, 2: 0.05, 3: 0.1, 4: 0.2, 
                        5: 0.5, 6: 1.0, 7: 2.0, 8: 5.0, 9: 10.0, 10: 20.0
                    }
                    range_volts_a = RANGE_MAP.get(self.range_a_index, 20.0)
                    range_volts_b = RANGE_MAP.get(self.range_b_index, 20.0)
                    max_adc = 32512.0
                    
                    scaled_a = []
                    scaled_b = []
                    for i in range(num_read):
                        volt_a = (buffer_a[i] / max_adc) * range_volts_a
                        volt_b = (buffer_b[i] / max_adc) * range_volts_b
                        scaled_a.append(volt_a)
                        scaled_b.append(volt_b)
                    return [scaled_a, scaled_b]
                else:
                    self.logger.warning("PicoScope: Hardware buffer returned 0 values.")
                    return []
            except Exception as e:
                self.logger.error(f"PicoScope: Error retrieving waveform data: {e}")
                return []
        return []

    def _generate_mock_surge(self) -> list:
        """Generates a realistic 50Hz mains voltage and phase-cut current waveform."""
        self.logger.debug("[MOCK] Generating transient current surge waveform.")
        voltage_data = []
        current_data = []
        import math
        import random
        
        f = 50.0  # 50 Hz
        peak_current = 15.0  # Peak Current in Amperes
        peak_voltage = 230.0 * 1.414 # Peak Voltage in Volts
        
        # 2500 samples at 81.92 us interval -> ~204.8 ms total duration
        interval_s = 0.00008192
        
        # We need a varying PF for each mock capture.
        # Pick a random pulse duration between 5.0ms and 10.0ms.
        # UPF = 10ms (no cut).
        duration_ms = random.choice([5.0, 6.5, 8.0, 9.0, 10.0])
        cut_ms = 10.0 - duration_ms
        cut_s = cut_ms / 1000.0
        
        # Simulate trigger point at 20% of the buffer
        pre_trigger_samples = int(self.no_of_values * 0.2)
        
        for i in range(self.no_of_values):
            t = i * interval_s
            
            # Channel A: Voltage (continuous sine wave)
            val_v = peak_voltage * math.sin(2 * math.pi * f * t)
            voltage_data.append(val_v)
            
            # Channel B: Current
            if i < pre_trigger_samples:
                # Pre-trigger flatline (contactor open)
                current = random.uniform(-0.1, 0.1)
            else:
                # Post-trigger surge (contactor closed)
                # Offset t so the sine wave starts at the trigger point
                t_surge = (i - pre_trigger_samples) * interval_s
                
                # Only produce the surge for one half-cycle (10ms)
                if t_surge < 0.010:
                    half_cycle_t = t_surge
                    if half_cycle_t < cut_s:
                        current = random.uniform(-0.1, 0.1)
                    else:
                        current = peak_current * math.sin(2 * math.pi * f * t_surge)
                        current += random.uniform(-0.3, 0.3)
                else:
                    # Post-surge flatline
                    current = random.uniform(-0.1, 0.1)
                
            current_data.append(current)
            
        return [voltage_data, current_data]

    def read_data(self, address=0, count=1):
        return self.get_waveform()

    def write_data(self, address, value):
        return False
