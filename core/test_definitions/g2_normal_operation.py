from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

class G2NormalOperationTest(BaseTest):
    """
    Implementation of the G2 Normal Operation Test sequence.
    """
    def __init__(self):
        super().__init__()
        # Note: If name/desc are needed, they should be set as properties
        self.name = "G2 Normal Operation"
        self.description = "Verify basic operation and energy counting"

    def build(self, builder: TestBuilder):
        # 1. Prompt User to Set Load to 240V Ic UPF
        builder.prompt_user("Set Load to 240V Ic UPF", requires_input=False)
        
        # 2. Turn ON ACB
        builder.set_plc_coil(PLCCoil.ACB_COIL_ADDR, True)
        
        # 3. 2 sec Delay
        builder.wait(2)
        
        # 4. Turn ON SCR
        builder.set_plc_coil(PLCCoil.SCR_COIL_ADDR, True)
        
        # 5. Read Meter Serial Number
        builder.send_meter_command("read_serial_number")
        
        # 6. Prompt user to enter initial Energy Value
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # Steps 7-10 repeated 3 times
        def loop_body(sub_builder: TestBuilder, idx: int):
            # 7. Close Meter Load Switch
            sub_builder.send_meter_command("close_load_switch")
            
            # 8. Measure Current > 0
            sub_builder.measure_current(min_val=0.1, max_val=100.0)
            
            # 9. Open Load Switch
            sub_builder.send_meter_command("open_load_switch")
            
            # 10. Measure Current == 0
            sub_builder.measure_current(min_val=0.0, max_val=0.05)
            
        builder.loop(3, loop_body)
        
        # 11. Prompt user to enter final Energy Value
        builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
        
        # 12. Show pass fail status & 13. Store Results
        builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 14. Turn OFF ACB
        builder.set_plc_coil(PLCCoil.ACB_COIL_ADDR, False)
        
        # 15. Turn OFF SCR
        builder.set_plc_coil(PLCCoil.SCR_COIL_ADDR, False)

    def _verify_and_store(self, ctx, hw):
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            
            # Simple threshold check
            diff = abs(final - initial)
            if diff > (initial * 0.01): # > 1% diff
                ctx.logger.error(f"Test Failed: Energy difference ({diff}) > 1% threshold.")
            else:
                ctx.logger.info(f"Test Passed: Energy difference ({diff}) within threshold.")
            
            ctx.logger.info("Storing Results in DB...")
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
