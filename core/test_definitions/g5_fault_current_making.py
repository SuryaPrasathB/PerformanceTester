from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder

class G5FaultCurrentMakingUC2Test(BaseTest):
    """
    Implementation of the G5 Fault Current Making Capacity Test for UC2 Meters.
    Applies 2.5kA Fault Current.
    """
    def build(self, builder: TestBuilder):
        # 1. Setup Phase
        builder.close_test_switch()
        builder.wait(3) # Pre-fusing check
        
        # UC2 requires 2500A
        builder.set_source(voltage=240, current=2500.0, pf=0.8)

        # 2. Main Test Loop
        def fault_loop(b, i):
            b.turn_on_load()
            b.wait(1)
            b.open_test_switch()
            b.wait(1)
            b.turn_off_load()
            b.custom_action("Plot V-I Graph", lambda ctx, hw: ctx.update_status(f"Plotting V-I Graph for cycle {i+1}..."))
            b.wait(60)
            b.close_test_switch()

        builder.loop(3, fault_loop)
            
        # 3. Final Verification
        builder.set_source(voltage=240, current=10.0, pf=1.0)
        builder.turn_on_load()
        builder.wait(2)
        builder.turn_off_load()
        builder.custom_action("Execute G7 Verification", lambda ctx, hw: ctx.update_status("Executing G7 Sequence Placeholder..."))


class G5FaultCurrentMakingUC3Test(BaseTest):
    """
    Implementation of the G5 Fault Current Making Capacity Test for UC3 Meters.
    Applies 3.0kA Fault Current.
    """
    def build(self, builder: TestBuilder):
        # 1. Setup Phase
        builder.close_test_switch()
        builder.wait(3) # Pre-fusing check
        
        # UC3 requires 3000A
        builder.set_source(voltage=240, current=3000.0, pf=0.8)

        # 2. Main Test Loop
        def fault_loop(b, i):
            b.turn_on_load()
            b.wait(1)
            b.open_test_switch()
            b.wait(1)
            b.turn_off_load()
            b.custom_action("Plot V-I Graph", lambda ctx, hw: ctx.update_status(f"Plotting V-I Graph for cycle {i+1}..."))
            b.wait(60)
            b.close_test_switch()

        builder.loop(3, fault_loop)
            
        # 3. Final Verification
        builder.set_source(voltage=240, current=10.0, pf=1.0)
        builder.turn_on_load()
        builder.wait(2)
        builder.turn_off_load()
        builder.custom_action("Execute G7 Verification", lambda ctx, hw: ctx.update_status("Executing G7 Sequence Placeholder..."))
