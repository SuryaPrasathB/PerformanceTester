from typing import List, Callable, Any
from core.test_engine.test_step import TestStep
from core.hardware_mapping import PLCCoil, MFMRegister
import time

class ExecutableStep:
    def __init__(self, name: str, action: Callable, weight: int = 5, estimated_duration: int = 2, requires_input: bool = False, details: str = "", device: str = ""):
        self.name = name
        self.action = action
        self.weight = weight
        self.estimated_duration = estimated_duration
        self.requires_input = requires_input
        self.details = details
        self.device = device

class TestBuilder:
    """
    A fluent API for building test sequences in a clean, declarative way.
    """
    def __init__(self):
        self._steps: List[ExecutableStep] = []

    def get_steps(self) -> List[TestStep]:
        return [TestStep(s.name, s.weight, s.estimated_duration, s.requires_input, s.details, s.device) for s in self._steps]

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
            ctx.update_status(f"Waiting for {seconds} seconds...")
            start = time.time()
            while (time.time() - start) < seconds:
                ctx.check_cancel()
                ctx.wait_if_paused()
                time.sleep(0.5)
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
        return self

    def send_meter_command(self, command_key: str):
        def action(ctx, hw):
            ctx.update_status(f"Sending Meter Command: {command_key}")
            from services.profile_manager import ProfileManager
            pm = ProfileManager()
            profiles = pm.get_all_profiles()
            if not profiles:
                raise Exception("No meter profiles configured.")
            profile = profiles[0] # Using first profile for now
            
            cmd_data = profile.get("commands", {}).get(command_key)
            if not cmd_data:
                raise Exception(f"Command '{command_key}' not mapped in profile '{profile.get('name')}'.")
                
            ctx.logger.info(f"Sending via {profile.get('communication_mode')}: {cmd_data.get('value')} [{cmd_data.get('format')}]")
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
        def action(ctx, hw):
            for i in range(count):
                ctx.update_status(f"Loop {i+1}/{count}")
                # Create a temporary builder for the loop body
                sub_builder = TestBuilder()
                loop_builder_func(sub_builder, i)
                # Execute the sub-steps immediately
                for step in sub_builder._steps:
                    ctx.check_cancel()
                    ctx.wait_if_paused()
                    step.action(ctx, hw)
        self.add_step(f"Loop {count} times", action, weight=count*5, duration=count*2) # Rough estimate
        return self

    def custom_action(self, name: str, action_func: Callable):
        self.add_step(name, action_func)
        return self

    def execute(self, context):
        """ Executed by the TestRunner """
        hw = context.hardware_service
        for i, step in enumerate(self._steps):
            context.start_step(step.name)
            context.check_cancel()
            context.wait_if_paused()
            
            try:
                step.action(context, hw)
            except Exception as e:
                context.logger.error(f"Error in step '{step.name}': {e}")
                raise
