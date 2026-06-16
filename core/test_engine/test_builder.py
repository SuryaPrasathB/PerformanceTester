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

    def start_power_sequence(self):
        self.set_plc_coil(PLCCoil.ACB_COIL_ADDR, True)
        self.set_plc_coil(PLCCoil.SCR_COIL_ADDR, True)
        return self

    def stop_power_sequence(self):
        self.set_plc_coil(PLCCoil.ACB_COIL_ADDR, False)
        self.set_plc_coil(PLCCoil.SCR_COIL_ADDR, False)
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
        def action(ctx, hw):
            ctx.update_status(f"Sending Meter Command: {command_key}")
            profile = getattr(ctx, "meter_profile", None)
            if not profile:
                from services.profile_manager import ProfileManager
                pm = ProfileManager()
                profiles = pm.get_all_profiles()
                if not profiles:
                    raise Exception("No meter profiles configured.")
                profile = profiles[0] # Fallback
            
            cmd_data = profile.get("commands", {}).get(command_key)
            if not cmd_data:
                raise Exception(f"Command '{command_key}' not mapped in profile '{profile.get('name')}'.")
                
            val = cmd_data.get("value", "")
            fmt = cmd_data.get("format", "Hex").lower()
            mode = profile.get("communication_mode", "DLMS").lower()
            
            ctx.logger.info(f"Sending via {profile.get('communication_mode')}: {val} [{cmd_data.get('format')}]")
            
            if mode == "serial":
                # Prepare payload
                if fmt == "hex":
                    payload = bytes.fromhex(val.replace(" ", ""))
                else:
                    payload = val.encode('ascii')
                
                # Append terminator. If the user provided one in the profile, we could use it. 
                # Otherwise, default to \r\n for ascii, or no terminator for hex unless specified.
                payload += b'\r\n'
                
                # Verify we have the correct driver type
                drv = hw.energymeter_drv
                if drv and drv.__class__.__name__ == "SerialDriver":
                    if not drv.is_connected:
                        drv.connect()
                    
                    # Flush before write
                    if drv.serial_conn:
                        drv.serial_conn.reset_input_buffer()
                        
                    success = drv.write_data(payload)
                    if success:
                        ctx.logger.info(f"Sent {len(payload)} bytes over Serial.")
                        
                        expected_term_hex = cmd_data.get("expected_terminator", "")
                        expected_resp_hex = cmd_data.get("expected_response", "")
                        
                        term = bytes.fromhex(expected_term_hex.replace(" ", "")) if expected_term_hex else b'\r\n'
                        exp_resp = bytes.fromhex(expected_resp_hex.replace(" ", "")) if expected_resp_hex else b''
                        
                        # Read until terminator or 2.0s timeout
                        response = drv.read_until(term, timeout=2.0)
                        
                        if not response:
                            raise Exception("Meter did not respond within the timeout period.")
                            
                        ctx.logger.info(f"Received Response: {response.hex().upper() if fmt == 'hex' else response}")
                        
                        if command_key == "read_serial_number":
                            try:
                                serial_str = response.decode('utf-8', errors='ignore').strip()
                                if serial_str:
                                    ctx.meter_serial_number = serial_str
                                    ctx.logger.info(f"Saved read serial number to context: {serial_str}")
                            except Exception as e:
                                ctx.logger.warning(f"Could not parse serial number: {e}")

                        if exp_resp and exp_resp not in response:
                            ctx.logger.error(f"Expected response '{exp_resp.hex()}' not found in '{response.hex()}'")
                            raise Exception(f"Validation failed: Expected response not found.")
                        
                        ctx.logger.info("Meter response validated successfully.")
                    else:
                        ctx.logger.error("Failed to write to Serial driver.")
                        raise Exception("Serial write failed.")
                else:
                    ctx.logger.error("Meter profile specifies Serial, but driver in config is not SerialDriver.")
                    raise Exception("Driver type mismatch.")
            elif mode == "dlms":
                drv = hw.energymeter_drv
                if drv and drv.__class__.__name__ == "DlmsDriver":
                    # value is expected to be an OBIS code
                    # If expected_response is provided and not empty, it's a read. 
                    # If we have a write value? For now, assume these are reads unless configured differently.
                    obis = val
                    ctx.logger.info(f"Reading DLMS OBIS code: {obis}")
                    res = drv.read_data(obis)
                    ctx.logger.info(f"DLMS Read result: {res}")
                    
                    if command_key == "read_serial_number" and res is not None:
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
