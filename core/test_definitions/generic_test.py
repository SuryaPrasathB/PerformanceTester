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
        return [
            TestStep(
                name=step.step_type.replace("_", " ").title(),
                weight=step.weight,
                estimated_duration=step.estimated_duration,
                requires_input=(step.step_type == "PROMPT_USER")
            ) for step in self.suite_model.steps
        ]

    def setup(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Setup started.")
        # Basic initialization can be added here if needed

    def run(self, context):
        context.logger.info(f"Dynamic Test: {self.suite_model.name} - Execution started.")
        hw = context.hardware_service

        for i, step_config in enumerate(self.suite_model.steps):
            step_name = step_config.step_type.replace("_", " ").title()
            context.start_step(step_name)
            
            # Execute logic based on step type
            stype = step_config.step_type.upper()
            params = step_config.parameters
            
            if stype == "SET_SOURCE":
                v = float(params.get("voltage", 0.0))
                i_val = float(params.get("current", 0.0))
                pf = float(params.get("pf", 1.0))
                context.update_status(f"Setting Source: {v}V, {i_val}A, PF: {pf}")
                hw.inject_signal(v, i_val, pf)
                
            elif stype == "TURN_LOAD":
                state = bool(params.get("state", False))
                context.update_status(f"Turning Load {'ON' if state else 'OFF'}")
                hw.control_load(state)
                
            elif stype == "WAIT":
                duration = float(params.get("duration_sec", 5.0))
                context.update_status(f"Waiting for {duration} seconds...")
                # Sleep in chunks to remain responsive to cancel/pause
                start_wait = time.time()
                while (time.time() - start_wait) < duration:
                    context.check_cancel()
                    context.wait_if_paused()
                    time.sleep(0.5)
                    
            elif stype == "READ_METER":
                regs = params.get("registers", [])
                if isinstance(regs, str): regs = [r.strip() for r in regs.split(',') if r.strip()]
                context.update_status(f"Reading meter registers: {', '.join(regs)}")
                readings = hw.read_meter_registers(regs)
                context.update_runtime_value(f"step_{i}_readings", readings)

            elif stype == "READ_MFM_METER":
                regs = params.get("registers", [])
                if isinstance(regs, str): regs = [r.strip() for r in regs.split(',') if r.strip()]
                context.update_status(f"Reading MFM meter registers: {', '.join(regs)}")
                readings = hw.read_mfm_registers(regs)
                context.update_runtime_value(f"step_{i}_mfm_readings", readings)
                
            elif stype == "PROMPT_USER":
                msg = params.get("message", "Please confirm to continue.")
                req_input = bool(params.get("requires_input", False))
                result = context.prompt_user_action(msg, requires_input=req_input)
                if req_input:
                    context.update_runtime_value(f"step_{i}_user_input", result)
                    
            elif stype == "WAIT_UNTIL_ZERO":
                threshold = float(params.get("threshold", 0.1))
                timeout = int(params.get("timeout_sec", 30))
                context.update_status(f"Waiting for current < {threshold}A...")
                success = hw.wait_for_current_zero(threshold=threshold, timeout_sec=timeout, context=context)
                if not success:
                    raise Exception("Timeout waiting for current to reach zero.")

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
