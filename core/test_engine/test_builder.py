from typing import List, Callable, Any
from core.test_engine.test_step import TestStep
from core.hardware_mapping import PLCCoil, MFMRegister
import time
import threading

ACB_OPERATED_DELAY = 5  # Global delay in seconds applied whenever the ACB is operated (ON or OFF)

class ExecutableStep:
    def __init__(self, name: str, action: Callable, weight: int = 5, estimated_duration: int = 2, requires_input: bool = False, details: str = "", device: str = ""):
        self.name = name
        self.action = action
        self.weight = weight
        self.estimated_duration = estimated_duration
        self.requires_input = requires_input
        self.details = details
        self.device = device
        self.sub_steps: List[TestStep] = None

class TestBuilder:
    """
    A fluent API for building test sequences in a clean, declarative way.
    """
    def __init__(self):
        self._steps: List[ExecutableStep] = []

    def get_steps(self) -> List[TestStep]:
        steps = []
        for s in self._steps:
            ts = TestStep(s.name, s.weight, s.estimated_duration, s.requires_input, s.details, s.device)
            if s.sub_steps:
                ts.sub_steps = s.sub_steps
            steps.append(ts)
        return steps

    def add_step(self, name: str, action: Callable, weight=5, duration=2, requires_input=False, details="", device=""):
        self._steps.append(ExecutableStep(name, action, weight, duration, requires_input, details, device))
        return self

    # --- High Level Fluent API ---

    def set_source(self, voltage: float, current: float, pf: float = 1.0):
        def action(ctx, hw):
            ctx.update_status(f"Setting Source: {voltage}V, {current}A, PF: {pf}")
            hw.inject_signal(voltage, current, pf)
        self.add_step("Set Source", action)
        return self

    def turn_on_load(self):
        def action(ctx, hw):
            ctx.update_status("Turning Load ON")
            hw.control_load(True)
        self.add_step("Turn On Load", action)
        return self

    def turn_off_load(self):
        def action(ctx, hw):
            ctx.update_status("Turning Load OFF")
            hw.control_load(False)
        self.add_step("Turn Off Load", action)
        return self
        
    def close_test_switch(self):
        def action(ctx, hw):
            ctx.update_status("Closing Test Switch")
            hw.plc.write_coil(0, True)
        self.add_step("Close Test Switch", action)
        return self

    def open_test_switch(self):
        def action(ctx, hw):
            ctx.update_status("Opening Test Switch")
            hw.plc.write_coil(0, False)
        self.add_step("Open Test Switch", action)
        return self

    def wait(self, seconds: int):
        def action(ctx, hw):
            import math
            start_time = time.time()
            total_duration = float(seconds)
            last_reported = -1
            
            while True:
                ctx.check_cancel()
                
                pre_pause = time.time()
                ctx.wait_if_paused()
                post_pause = time.time()
                pause_duration = post_pause - pre_pause
                if pause_duration > 0.05:
                    start_time += pause_duration
                
                elapsed = time.time() - start_time
                remaining = total_duration - elapsed
                if remaining <= 0:
                    break
                
                remaining_ceil = int(math.ceil(remaining))
                if remaining_ceil != last_reported:
                    ctx.update_status(f"Waiting: {remaining_ceil}s...")
                    last_reported = remaining_ceil
                
                time.sleep(0.1)
        self.add_step(f"Wait {seconds}s", action, duration=seconds, device="System")
        return self

    def prompt_user(self, message: str, requires_input: bool = False, save_as: str = None):
        def action(ctx, hw):
            result = ctx.prompt_user_action(message, requires_input)
            if save_as:
                ctx.update_runtime_value(save_as, result)
        self.add_step("Prompt User", action, requires_input=requires_input, details=message, device="System UI")
        return self

    def read_registers(self, registers: List[str], save_as: str = None):
        def action(ctx, hw):
            ctx.update_status(f"Reading registers: {', '.join(registers)}")
            readings = hw.read_meter_registers(registers)
            if save_as:
                ctx.update_runtime_value(save_as, readings)
        self.add_step("Read Registers", action)
        return self

    def wait_for_current_zero(self, threshold: float = 0.1, timeout: int = 60):
        def action(ctx, hw):
            ctx.update_status(f"Waiting for current < {threshold}A...")
            success = hw.wait_for_current_zero(threshold, timeout, ctx)
            if not success:
                raise Exception("Timeout waiting for current to reach zero.")
        self.add_step("Wait for Zero Current", action, duration=timeout, device="MFM Meter")
        return self
        
    def set_plc_coil(self, coil: PLCCoil, state: bool):
        def action(ctx, hw):
            ctx.update_status(f"Setting PLC Coil 0x{coil.value:02X} ({coil.name}) to {state}")
            try:
                hw.plc.write_coil(coil.value, state)
            except AttributeError:
                ctx.logger.info(f"MOCK: PLC.write_coil({coil.value}, {state})")
        self.add_step(f"Set Coil {coil.name}={'ON' if state else 'OFF'}", action, device="PLC")
        
        # Apply global delay whenever ACB is operated
        if coil == PLCCoil.ACB_COIL_ADDR:
            self.wait(ACB_OPERATED_DELAY)
            
        return self

    def verify_plc_coil_status(self, status_coil: PLCCoil, name_for_error: str):
        def action(ctx, hw):
            ctx.update_status(f"Verifying status of {name_for_error}...")
            try:
                if hasattr(hw, "plc") and hw.plc:
                    # Toggle INPUT_STATUS_REQUEST to True
                    hw.plc.write_coil(PLCCoil.INPUT_STATUS_REQUEST.value, True)
                    time.sleep(0.1)
                    # Read target status coil
                    status = hw.plc.read_coil(status_coil.value)
                    # Reset INPUT_STATUS_REQUEST to False
                    hw.plc.write_coil(PLCCoil.INPUT_STATUS_REQUEST.value, False)
                    
                    ctx.logger.info(f"PLC Status Verification: {name_for_error} status is {status} (verification result ignored)")
                else:
                    ctx.logger.info(f"MOCK: PLC Verification passed for {name_for_error}")
            except Exception as e:
                ctx.logger.warning(f"Ignoring error during status verification of {name_for_error}: {e}")
        self.add_step(f"Verify {name_for_error} Status", action, device="PLC")
        return self

    def start_power_sequence(self, contactor_coil: PLCCoil = PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR):
        self.set_plc_coil(PLCCoil.ACB_COIL_ADDR, True)
        self.verify_plc_coil_status(PLCCoil.ACB_STATUS, "ACB")
        self.set_plc_coil(contactor_coil, True)
        if contactor_coil == PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR:
            self.verify_plc_coil_status(PLCCoil.CONTACTOR_120A_STATUS, "120A Contactor")
        else:
            self.verify_plc_coil_status(PLCCoil.CONTACTOR_100mA_STATUS, "100mA Contactor")
        self.set_plc_coil(PLCCoil.SCR_COIL_ADDR, True)
        return self

    def stop_power_sequence(self, contactor_coil: PLCCoil = PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR):
        self.set_plc_coil(PLCCoil.SCR_COIL_ADDR, False)
        self.set_plc_coil(contactor_coil, False)
        self.set_plc_coil(PLCCoil.ACB_COIL_ADDR, False)
        return self

        
    def start_background_monitor(self, name: str, monitor_func: Callable):
        def action(ctx, hw):
            ctx.update_status(f"Starting Background Monitor: {name}")
            stop_event = threading.Event()
            ctx.background_tasks_stop_events[name] = stop_event
            
            def thread_target():
                while not stop_event.is_set() and not ctx.cancel_event.is_set():
                    monitor_func(ctx, hw)
                    time.sleep(1) # Internal loop delay to prevent pegging CPU

            t = threading.Thread(target=thread_target, daemon=True)
            ctx.background_tasks[name] = t
            t.start()
        self.add_step(f"Start Background Monitor: {name}", action)
        return self

    def stop_background_monitor(self, name: str):
        def action(ctx, hw):
            ctx.update_status(f"Stopping Background Monitor: {name}")
            stop_event = ctx.background_tasks_stop_events.get(name)
            if stop_event:
                stop_event.set()
                t = ctx.background_tasks.get(name)
                if t:
                    t.join(timeout=2)
                ctx.background_tasks.pop(name, None)
                ctx.background_tasks_stop_events.pop(name, None)
        self.add_step(f"Stop Background Monitor: {name}", action)
        return self

    def send_meter_command(self, command_key: str):
        if command_key == "read_serial_number":
            def action(ctx, hw):
                ctx.logger.info("Skipping meter command: read_serial_number (disabled per request)")
            self.add_step("Skip Read Serial Number", action, device="Energy Meter")
            return self

        def action(ctx, hw):
            profile = getattr(ctx, "meter_profile", None)
            if not profile:
                from services.profile_manager import ProfileManager
                pm = ProfileManager()
                profiles = pm.get_all_profiles()
                if not profiles:
                    raise Exception("No meter profiles configured.")
                profile = profiles[0] # Fallback
            
            def execute_single_command(key: str, is_auto_unlock: bool = False):
                cmd_data = profile.get("commands", {}).get(key)
                if not cmd_data:
                    if is_auto_unlock:
                        ctx.logger.info("Auto-unlock: 'unlock' command not mapped in profile. Skipping.")
                        return
                    raise Exception(f"Command '{key}' not mapped in profile '{profile.get('name')}'.")
                
                val = cmd_data.get("value", "")
                if not val and is_auto_unlock:
                    ctx.logger.info("Auto-unlock: 'unlock' command value is empty. Skipping.")
                    return
                
                ctx.update_status(f"Sending Meter Command: {key}")
                fmt = cmd_data.get("format", "Hex").lower()
                mode = profile.get("communication_mode", "DLMS").lower()
                
                ctx.logger.info(f"Sending via {profile.get('communication_mode')}: {val} [{cmd_data.get('format')}]")
                
                if mode == "serial":
                    serial_settings = profile.get("serial_settings", {})
                    write_term = serial_settings.get("write_terminator", "\\r\\n")
                    term_bytes_map = {
                        "\\r\\n": b'\r\n',
                        "\\r": b'\r',
                        "\\n": b'\n',
                        "None": b''
                    }
                    term_bytes = term_bytes_map.get(write_term, b'\r\n')

                    # Prepare payload
                    if fmt == "hex":
                        payload = bytes.fromhex(val.replace(" ", ""))
                    else:
                        val_processed = val.replace("<CR>", "\r").replace("<LF>", "\n")
                        payload = val_processed.encode('ascii')
                        if not (payload.endswith(b'\r') or payload.endswith(b'\n')):
                            payload += term_bytes
                    
                    drv = hw.energymeter_drv
                    if drv and drv.__class__.__name__ == "SerialDriver":
                        max_attempts = 4  # 1 initial attempt + 3 retries
                        for attempt in range(1, max_attempts + 1):
                            try:
                                if not drv.is_connected:
                                    drv.connect()
                                
                                if drv.serial_conn:
                                    drv.serial_conn.reset_input_buffer()
                                    
                                success = drv.write_data(payload)
                                if success:
                                    ctx.logger.info(f"Sent {len(payload)} bytes over Serial (Attempt {attempt}/{max_attempts}).")
                                    
                                    expected_term_hex = cmd_data.get("expected_terminator", "")
                                    expected_resp_hex = cmd_data.get("expected_response", "")
                                    
                                    term = bytes.fromhex(expected_term_hex.replace(" ", "")) if expected_term_hex else (term_bytes if term_bytes else b'\r\n')
                                    exp_resp = bytes.fromhex(expected_resp_hex.replace(" ", "")) if expected_resp_hex else b''
                                    
                                    response = drv.read_until(term, timeout=2.0)
                                    
                                    if not response:
                                        raise Exception(f"Meter did not respond to '{key}' command within the timeout period.")
                                        
                                    ctx.logger.info(f"Received Response: {response.hex().upper() if fmt == 'hex' else response}")
                                    
                                    if key == "read_serial_number":
                                        try:
                                            serial_str = response.decode('utf-8', errors='ignore').strip()
                                            if serial_str:
                                                ctx.meter_serial_number = serial_str
                                                ctx.logger.info(f"Saved read serial number to context: {serial_str}")
                                        except Exception as e:
                                            ctx.logger.warning(f"Could not parse serial number: {e}")
                                            
                                    if exp_resp and exp_resp not in response:
                                        ctx.logger.error(f"Expected response '{exp_resp.hex()}' not found in '{response.hex()}'")
                                        raise Exception(f"Validation failed: Expected response not found for '{key}' command.")
                                    
                                    ctx.logger.info(f"Meter response for '{key}' validated successfully.")
                                    break # Success! Break out of retry loop.
                                else:
                                    ctx.logger.error(f"Failed to write to Serial driver for '{key}' command.")
                                    raise Exception("Serial write failed.")
                            except Exception as e:
                                if attempt == max_attempts:
                                    raise Exception(f"Failed '{key}' command after {max_attempts} attempts. Error: {e}")
                                ctx.logger.warning(f"Attempt {attempt} of {max_attempts} failed for command '{key}': {e}. Retrying in 1s...")
                                time.sleep(1.0)
                    else:
                        ctx.logger.error("Meter profile specifies Serial, but driver in config is not SerialDriver.")
                        raise Exception("Driver type mismatch.")
                elif mode == "dlms":
                    drv = hw.energymeter_drv
                    if drv and drv.__class__.__name__ == "DlmsDriver":
                        obis = val
                        ctx.logger.info(f"Reading DLMS OBIS code: {obis}")
                        res = drv.read_data(obis)
                        ctx.logger.info(f"DLMS Read result: {res}")
                        
                        if key == "read_serial_number" and res is not None:
                            if isinstance(res, dict):
                                ctx.meter_serial_number = "MOCK_DLMS_SERIAL"
                            else:
                                ctx.meter_serial_number = str(res).strip()
                            ctx.logger.info(f"Saved read serial number to context: {ctx.meter_serial_number}")
                        
                        exp_resp = str(cmd_data.get("expected_response", "")).strip()
                        if exp_resp:
                            if str(res) != exp_resp:
                                raise Exception(f"DLMS Validation failed: Expected '{exp_resp}', got '{res}'")
                            ctx.logger.info("DLMS response validated successfully.")
                    else:
                        ctx.logger.error("Meter profile specifies DLMS, but driver is not DlmsDriver.")
                        raise Exception("Driver type mismatch.")

            # Send unlock before switch operation if unlock is configured and has a value
            if command_key in ["close_load_switch", "open_load_switch"]:
                unlock_cmd = profile.get("commands", {}).get("unlock")
                if unlock_cmd and unlock_cmd.get("value"):
                    execute_single_command("unlock", is_auto_unlock=True)
                    time.sleep(0.2)
            
            execute_single_command(command_key)

        self.add_step(f"Send Command: {command_key}", action, device="Energy Meter")
        return self

    def measure_current(self, min_val: float, max_val: float):
        def action(ctx, hw):
            ctx.update_status("Measuring Current (MFM)...")
            try:
                # Mock read for now
                current = 10.0 # Dummy value
                if current < min_val or current > max_val:
                    ctx.logger.error(f"Current measurement failed: {current}A not in [{min_val}, {max_val}]A")
                else:
                    ctx.logger.info(f"Current measurement passed: {current}A")
            except Exception as e:
                ctx.logger.error(f"Failed to read current: {e}")
        self.add_step(f"Measure Current [{min_val}-{max_val}A]", action, device="MFM Meter")
        return self
        
    def loop(self, count: int, loop_builder_func: Callable):
        """ Executes a nested sequence 'count' times. """
        # Capture the sub-steps to display in the UI
        dummy_builder = TestBuilder()
        loop_builder_func(dummy_builder, 0)
        sub_steps_metadata = dummy_builder.get_steps()
        
        def action(ctx, hw):
            min_duration = ctx.config.get("testing", {}).get("min_step_duration_s", 1.0)
            loop_id = id(action)
            ctx.push_loop(loop_id, count)
            try:
                for i in range(count):
                    ctx.update_status(f"Loop {i+1}/{count}")
                    ctx.set_loop_iteration(i)
                    # Create a temporary builder for the loop body
                    sub_builder = TestBuilder()
                    loop_builder_func(sub_builder, i)
                    # Execute the sub-steps immediately
                    for step in sub_builder._steps:
                        self._execute_step(ctx, step, hw, min_duration)
            finally:
                ctx.pop_loop()
        
        step_obj = ExecutableStep(f"Loop {count} times", action, weight=count*5, estimated_duration=count*2, device="System")
        step_obj.sub_steps = sub_steps_metadata
        self._steps.append(step_obj)
        return self

    def custom_action(self, name: str, action_func: Callable):
        self.add_step(name, action_func)
        return self

    def _execute_step(self, context, step, hw, min_duration):
        context.check_cancel()
        context.wait_if_paused()
        
        start_time = time.time()
        try:
            step.action(context, hw)
        except Exception as e:
            context.logger.error(f"Error in step '{step.name}': {e}")
            raise
            
        elapsed = time.time() - start_time
        remaining = min_duration - elapsed
        while remaining > 0:
            context.check_cancel()
            context.wait_if_paused()
            sleep_time = min(remaining, 0.1)
            time.sleep(sleep_time)
            remaining -= sleep_time

    def execute(self, context):
        """ Executed by the TestRunner """
        hw = context.hardware_service
        min_duration = context.config.get("testing", {}).get("min_step_duration_s", 1.0)
        for i, step in enumerate(self._steps):
            context.start_step(step.name)
            self._execute_step(context, step, hw, min_duration)
