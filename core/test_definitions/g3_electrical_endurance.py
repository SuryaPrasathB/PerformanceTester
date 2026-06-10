from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder

class G3ElectricalEnduranceTest(BaseTest):
    """
    Implementation of the G3 Electrical Endurance Test sequence.
    Verifies the contact durability over 8000 switching operations.
    """
    def build(self, builder: TestBuilder):
        # 1. Setup Phase
        builder.prompt_user(
            "Enter the OFF delay duration (between 10 and 60 seconds):",
            requires_input=True,
            save_as="off_delay"
        )
        builder.read_registers(["Serial Number"], save_as="meter_serial")
        
        # Helper loop generator
        def make_cycles(pf):
            def cycle_logic(b, i):
                b.turn_on_load()
                b.wait(10)
                b.turn_off_load()
                
                # Fetch dynamically saved off delay, or default to 10
                b.custom_action("Wait Off Delay", lambda ctx, hw: b._delay(ctx, int(ctx.get_runtime_value("off_delay", 10))))
            return cycle_logic

        # 4000 Cycles at UPF
        builder.set_source(voltage=240, current=10.0, pf=1.0)
        builder.close_test_switch()
        # Note: 4000 is used for actual standard, may take a long time to run.
        builder.loop(4000, make_cycles(1.0))
        
        # 4000 Cycles at 0.5 PF
        builder.set_source(voltage=240, current=10.0, pf=0.5)
        builder.loop(4000, make_cycles(0.5))

        # Verification
        builder.turn_on_load()
        builder.wait(2)
        builder.turn_off_load()
        builder.wait(2)
        builder.custom_action("Execute G7 Verification", lambda ctx, hw: ctx.update_status("Executing G7 Sequence Placeholder..."))
        builder.open_test_switch()
