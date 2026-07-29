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
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set Load to 240V Ic UPF", requires_input=False)
        
        # 2-4. Turn ON ACB -> Delay -> Turn ON Contactor
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
        # 6. Prompt user to enter initial Energy Value
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # Steps 7-10 repeated 3 times
        def loop_body(sub_builder: TestBuilder, idx: int):
            # 7. Close Meter Load Switch
            sub_builder.send_meter_command("close_load_switch")
            
            sub_builder.wait(5)
            # 8. Measure Current > 0
            sub_builder.measure_current(min_val=0.1, max_val=100.0)
            sub_builder.wait(5)
            
            # 9. Open Load Switch
            sub_builder.send_meter_command("open_load_switch")
            
            sub_builder.wait(5)
            # 10. Measure Current == 0
            sub_builder.measure_current(min_val=0.0, max_val=0.05)
            sub_builder.wait(5)
            
        builder.loop(3, loop_body)
        
        # 11. Prompt user to enter final Energy Value
        builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
        
        # 12. Show pass fail status & 13. Store Results
        builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 14-15. Turn OFF ACB and Contactor
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

    def _verify_and_store(self, ctx, hw):
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            
            # Simple threshold check
            threshold_percent = ctx.config.get("testing", {}).get("energy_diff_threshold_percent", 1.0)
            threshold_val = initial * (threshold_percent / 100.0)
            diff = abs(final - initial)
            if diff > threshold_val:
                ctx.logger.error(f"Test Failed: Energy difference ({diff}) > {threshold_percent}% threshold.")
            else:
                ctx.logger.info(f"Test Passed: Energy difference ({diff}) within threshold.")
            
            ctx.logger.info("Storing Results in DB...")
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
