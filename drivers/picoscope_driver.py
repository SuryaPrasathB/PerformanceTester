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
        self.no_of_values = 2500
        self.timebase = 13  # 10 * 2^13 ns = 81.92 us per sample -> ~204 ms total capture window

    def connect(self) -> bool:
        """Establishes connection to PicoScope."""
        if self.mock_mode:
            self.logger.info(f"[MOCK] PicoScope connected on port {self.port}.")
            self.handle = 999
            self.is_connected = True
            return True

        if not ps2000:
            self.logger.warning("PicoScope: ps2000.dll unavailable. Forcing Mock Mode connection.")
            self.mock_mode = True
            self.handle = 999
            self.is_connected = True
            return True

        self.logger.info(f"PicoScope: Connecting on {self.port}...")
        try:
            h = ps2000.ps2000_open_unit()
            if h > 0:
                self.handle = h
                self.is_connected = True
                self.logger.info(f"PicoScope: Connected successfully. Handle: {self.handle}")
                
                # Channel A enabled, DC coupling, 20V Range (constant 10)
                ps2000.ps2000_set_channel(self.handle, 0, 1, 1, 10)
                # Channel B disabled
                ps2000.ps2000_set_channel(self.handle, 1, 0, 1, 10)
                return True
            else:
                self.logger.error("PicoScope: Failed to open device unit. Falling back to Mock Mode.")
                self.mock_mode = True
                self.handle = 999
                self.is_connected = True
                return True
        except Exception as e:
            self.logger.error(f"PicoScope: Exception during connection: {e}. Falling back to Mock Mode.")
            self.mock_mode = True
            self.handle = 999
            self.is_connected = True
            return True

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

    def start_capture(self) -> bool:
        """Starts a block capture sequence."""
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
                # Disable hardware trigger (Auto-trigger immediately)
                ps2000.ps2000_set_trigger(self.handle, 5, 0, 0, 0, 0)
                
                time_indisposed_ms = c_int32(0)
                status = ps2000.ps2000_run_block(
                    self.handle, 
                    self.no_of_values, 
                    self.timebase, 
                    1, 
                    byref(time_indisposed_ms)
                )
                if status == 0:
                    self.logger.error("PicoScope: Failed to run block capture.")
                    self.is_capturing = False
                    return False
                self.logger.info(f"PicoScope: Block capture initiated. Time indisposed: {time_indisposed_ms.value}ms")
                return True
            except Exception as e:
                self.logger.error(f"PicoScope: Error starting block capture: {e}")
                self.is_capturing = False
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
                    if time.time() - start_wait > 0.5:
                        self.logger.warning("PicoScope: Timeout waiting for block ready status.")
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
                    buffer_a,
                    buffer_b,
                    None,
                    None,
                    byref(overflow),
                    self.no_of_values
                )
                
                if num_read > 0:
                    self.logger.info(f"PicoScope: Read {num_read} values from hardware buffer.")
                    
                    # Convert raw ADC values to voltage/current (RANGE_20V -> 20.0 V full scale)
                    range_volts = 20.0
                    max_adc = 32512.0
                    
                    scaled_data = []
                    for i in range(num_read):
                        # Calculate raw voltage
                        volt = (buffer_a[i] / max_adc) * range_volts
                        scaled_data.append(volt)
                    return scaled_data
                else:
                    self.logger.warning("PicoScope: Hardware buffer returned 0 values.")
                    return []
            except Exception as e:
                self.logger.error(f"PicoScope: Error retrieving waveform data: {e}")
                return []
        return []

    def _generate_mock_surge(self) -> list:
        """Generates a realistic 50Hz decaying short circuit current surge transient."""
        self.logger.debug("[MOCK] Generating transient current surge waveform.")
        data = []
        f = 50.0  # 50 Hz
        peak = 4500.0  # Peak Current in Amperes
        
        # 2500 samples at 81.92 us interval -> ~204.8 ms total duration
        interval_s = 0.00008192
        
        # Short circuit timing: starts at ~25ms, ends at ~45ms (20ms duration)
        sc_start = 0.025
        sc_end = 0.045
        
        for i in range(self.no_of_values):
            t = i * interval_s
            
            # AC sine wave component
            ac = peak * math.sin(2 * math.pi * f * t)
            
            # Decaying DC offset (asymmetrical short circuit transient)
            dc = peak * 0.7 * math.exp(-t / 0.012)
            
            val = ac + dc
            
            # Simulate contact opening and closing (20ms short-circuit duration)
            if sc_start <= t <= sc_end:
                # Smooth transients at boundaries
                fade_in = min(1.0, (t - sc_start) / 0.0015)
                fade_out = min(1.0, (sc_end - t) / 0.0015)
                current = val * fade_in * fade_out
            else:
                # Add background noise (leakage current)
                current = random.uniform(-3.0, 3.0)
                
            data.append(current)
            
        return data

    def read_data(self, address=0, count=1):
        return self.get_waveform()

    def write_data(self, address, value):
        return False
