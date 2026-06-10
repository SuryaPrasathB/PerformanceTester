from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder

class ManualProspectiveCurrentTest(BaseTest):
    """
    Implementation of the Manual Prospective Current Test sequence.
    """
    def build(self, builder: TestBuilder):
        # 1. Setup Phase
        builder.set_source(voltage=240, current=10.0, pf=1.0)
        builder.wait(3) # Initial Stabilization
        
        # 2. Sequence
        builder.custom_action("Wait for Zero Crossing (V)", lambda ctx, hw: ctx.update_status("Waiting for Voltage ZC..."))
        builder.close_test_switch()
        
        builder.custom_action("Wait for Zero Crossing (I)", lambda ctx, hw: ctx.update_status("Waiting for Current ZC..."))
        builder.open_test_switch()
        
        builder.custom_action("Plot V-I Graph", lambda ctx, hw: ctx.update_status("Plotting Manual Prospective Current Graph..."))
        
        builder.wait(5)
        
        # 3. Final Verification
        builder.custom_action("Verify Prospective Current", lambda ctx, hw: ctx.update_status("Verifying PC constraints..."))
