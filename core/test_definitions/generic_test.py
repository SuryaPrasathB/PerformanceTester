import time
from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_step import TestStep
from models.test_suite_model import TestSuiteModel

class GenericTest(BaseTest):
    """
    A dynamic test implementation that executes a sequence of steps 
    defined in a TestSuiteModel.
    """
    
    def __init__(self, suite_model: TestSuiteModel):
        self.suite_model = suite_model
        self.test_identifier = f"dynamic_{suite_model.id}"
        
    def get_steps(self) -> List[TestStep]:
        steps_list = []
        for step in self.suite_model.steps:
            if step.step_type == "REPEAT":
                start = step.parameters.get("start_step", 1) - 1
                end = step.parameters.get("end_step", 1) - 1
                iters = step.parameters.get("iterations", 1)
                
                # Ensure bounds are within range
                start = max(0, start)
                end = min(len(self.suite_model.steps) - 1, end)
                
                for _ in range(iters):
                    for sub_step in self.suite_model.steps[start:end+1]:
                        steps_list.append(TestStep(
                            name=sub_step.step_type.replace("_", " ").title(),
                            weight=sub_step.weight,
                            estimated_duration=sub_step.estimated_duration,
                            requires_input=(sub_step.step_type == "PROMPT_USER")
                        ))
            else:
                steps_list.append(TestStep(
                    name=step.step_type.replace("_", " ").title(),
                    weight=step.weight,
                    estimated_duration=step.estimated_duration,
                    requires_input=(step.step_type == "PROMPT_USER")
                ))
        return steps_list

    def setup(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Setup started.")
        # Basic initialization can be added here if needed

    def run(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Execution started.")
        hw = context.hardware_service

        for i, step_config in enumerate(self.suite_model.steps):
            if step_config.step_type == "REPEAT":
                start = step_config.parameters.get("start_step", 1) - 1
                end = step_config.parameters.get("end_step", 1) - 1
                iters = step_config.parameters.get("iterations", 1)
                
                start = max(0, start)
                end = min(len(self.suite_model.steps) - 1, end)
                
                for iter_num in range(iters):
                    context.logger.info(f"REPEAT loop: iteration {iter_num+1}/{iters}")
                    for sub_i, sub_step in enumerate(self.suite_model.steps[start:end+1]):
                        loop_prefix = f"Iter {iter_num+1}: "
                        # We use i + iter_num for uniqueness if needed in keys
                        step_key = f"loop_{i}_iter_{iter_num+1}_step_{start+sub_i}"
                        self._execute_step(step_key, sub_step, context, hw, loop_prefix)
            else:
                self._execute_step(f"step_{i}", step_config, context, hw)

    def _execute_step(self, step_key, step_config, context, hw, loop_prefix=""):
        step_name = step_config.step_type.replace("_", " ").title()
        context.start_step(step_name)
        
        # Execute logic based on step type
        stype = step_config.step_type.upper()
        params = step_config.parameters
        
        if stype == "SET_SOURCE":
            v = float(params.get("voltage", 0.0))
            i_val = float(params.get("current", 0.0))
            pf = float(params.get("pf", 1.0))
            context.update_status(f"{loop_prefix}Setting Source: {v}V, {i_val}A, PF: {pf}")
            hw.inject_signal(v, i_val, pf)
            
        elif stype == "TURN_LOAD":
            state = bool(params.get("state", False))
            context.update_status(f"{loop_prefix}Turning Load {'ON' if state else 'OFF'}")
            hw.control_load(state)
            
        elif stype == "WAIT":
            duration = float(params.get("duration_sec", 5.0))
            context.update_status(f"{loop_prefix}Waiting for {duration} seconds...")
            # Sleep in chunks to remain responsive to cancel/pause
            start_wait = time.time()
            while (time.time() - start_wait) < duration:
                context.check_cancel()
                context.wait_if_paused()
                time.sleep(0.5)
                
        elif stype == "READ_METER":
            regs = params.get("registers", [])
            context.update_status(f"{loop_prefix}Reading meter registers: {', '.join(regs)}")
            readings = hw.read_meter_registers(regs)
            context.update_runtime_value(f"{step_key}_readings", readings)
            
        elif stype == "PROMPT_USER":
            msg = params.get("message", "Please confirm to continue.")
            req_input = bool(params.get("requires_input", False))
            result = context.prompt_user_action(f"{loop_prefix}{msg}", requires_input=req_input)
            if req_input:
                context.update_runtime_value(f"{step_key}_user_input", result)
                
        elif stype == "WAIT_UNTIL_ZERO":
            threshold = float(params.get("threshold", 0.1))
            timeout = int(params.get("timeout_sec", 30))
            context.update_status(f"{loop_prefix}Waiting for current < {threshold}A...")
            success = hw.wait_for_current_zero(threshold=threshold, timeout_sec=timeout, context=context)
            if not success:
                raise Exception(f"Timeout waiting for current to reach zero.")

        # Check for generic pause/cancel between steps
        context.check_cancel()
        context.wait_if_paused()

    def verify(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Verification started.")
        # Logic for verification could also be dynamic, but for now we mark as success
        context.update_runtime_value("test_results", {"success": True, "details": "Sequence completed."})

    def cleanup(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Cleanup started.")
        hw = context.hardware_service
        if hw:
            hw.shutdown_all() # Safe shutdown
