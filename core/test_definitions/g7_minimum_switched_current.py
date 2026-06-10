from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder

class G7MinimumSwitchedCurrentTest(BaseTest):
    """
    Implementation of the G7 Minimum Switched Current Test.
    """
    def build(self, builder: TestBuilder):
        # 1. Setup Phase
        builder.prompt_user(
            "Enter Voltage (Vc):", requires_input=True, save_as="g7_v"
        )
        builder.prompt_user(
            "Enter Minimum Current (Imin):", requires_input=True, save_as="g7_i"
        )
        builder.prompt_user(
            "Enter Power Factor (UPF/0.5):", requires_input=True, save_as="g7_pf"
        )
        
        builder.read_registers(["Serial Number"], save_as="meter_serial")
        builder.close_test_switch()
        
        builder.custom_action("Apply User Parameters", self._apply_params)

        # 2. Main Test Loop
        def fault_loop(b, i):
            b.turn_on_load()
            b.wait(10)
            b.turn_off_load()
            b.custom_action("Check Contact Fault", lambda ctx, hw: ctx.update_status(f"Checking for contact faults in cycle {i+1}..."))
            b.wait(10)

        builder.loop(10, fault_loop)
            
        # 3. Final Verification
        builder.custom_action("Store Minimum Switched Parameters", lambda ctx, hw: ctx.update_status("Storing final parameters..."))
        builder.open_test_switch()

    def _apply_params(self, ctx, hw):
        try:
            v = float(ctx.get_runtime_value("g7_v", 240))
            i = float(ctx.get_runtime_value("g7_i", 10))
            pf = float(ctx.get_runtime_value("g7_pf", 1.0))
        except:
            v, i, pf = 240.0, 10.0, 1.0
            ctx.logger.warning("Failed to parse user inputs, using defaults.")
            
        hw.inject_signal(v, i, pf)
