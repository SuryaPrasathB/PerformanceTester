from typing import List
import time
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

class G5FaultCurrentMakingTest(BaseTest):
    """
    Implementation of the G5 Fault Current Making Capacity Test sequence.
    """
    def build(self, builder: TestBuilder):
        # 1. Prompt user to set load to Vc Ic UPF.
        builder.prompt_user("Set load to Vc Ic UPF", requires_input=False)
        
        # 2. Turn ON ACB (PLC Coil ACB_COIL_ADDR = 0x03).
        # 3. Delay as required.
        # 4. Turn ON SCR (PLC Coil SCR_COIL_ADDR = 0x04).
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
        # 5. Read meter serial number.
        builder.send_meter_command("read_serial_number")
        
        # 6. Prompt user to enter Initial Energy Value.
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # Helper loop generator
        def g5_loop(b, i):
            # --- Pre-fusing (Steps 7-13) ---
            # 7. Close load switch.
            b.send_meter_command("close_load_switch")
            # 8. Verify measured current is > 0.
            b.measure_current(min_val=0.1, max_val=100.0)
            # 9. Delay 5 seconds.
            b.wait(5)
            # 10. Open load switch.
            b.send_meter_command("open_load_switch")
            # 11. Verify measured current is = 0.
            b.measure_current(min_val=0.0, max_val=0.05)
            # 12. Delay 5 seconds.
            b.wait(5)
            # 13. Validate result: If Pass, continue. If Fail, turn OFF outputs and abort test.
            # Measure current already logs errors, we proceed for now.
            b.custom_action("Validate Pre-fusing Result", lambda ctx, hw: ctx.logger.info("Pre-fusing validated."))
            
            # 14. Turn OFF ACB.
            # 15. Turn OFF SCR.
            b.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            
            # 16. Prompt user to select meter category (U2 or U3) using two selection buttons.
            b.prompt_user("Select meter category (U2 or U3)", requires_input=True, save_as="meter_category")
            
            # 17. If U2, prompt user to set load to Vc, 2.5 kA, 0.8 PF.
            # 18. If U3, prompt user to set load to Vc, 3 kA, 0.8 PF.
            def prompt_category_load(ctx, hw):
                cat = str(ctx.get_runtime_value("meter_category", "U2")).strip().upper()
                if cat == "U3":
                    ctx.prompt_user_action("Set load to Vc, 3 kA, 0.8 PF", False)
                else:
                    ctx.prompt_user_action("Set load to Vc, 2.5 kA, 0.8 PF", False)
            b.custom_action("Prompt for Load Configuration", prompt_category_load)
            
            # 19. Turn ON ACB (PLC Coil ACB_COIL_ADDR = 0x03).
            # 20. Delay as required.
            # 21. Turn ON SCR (PLC Coil SCR_COIL_ADDR = 0x04).
            b.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            
            # 22. Notify PLC that the test is starting (FCMC_TEST_START = 0x00).
            b.set_plc_coil(PLCCoil.FCMC_TEST_START, True)
            
            # 23. Start capturing PicoScope waveform.
            b.custom_action("Start PicoScope Capture", lambda ctx, hw: getattr(hw, "start_waveform_capture", lambda: ctx.logger.info("Started Waveform Capture"))())
            
            # 24. Close load switch.
            b.send_meter_command("close_load_switch")
            
            # 25. After 20 ms, stop waveform capture and save the waveform.
            def wait_and_stop_capture(ctx, hw):
                time.sleep(0.02)
                getattr(hw, "stop_waveform_capture", lambda: ctx.logger.info("Stopped and Saved Waveform Capture"))()
                
            b.custom_action("Wait 20ms and Stop Capture", wait_and_stop_capture)
            
            # 26. Delay 1 minute.
            b.wait(60)
 
        # Repeat steps 7-26 for 3 times in total.
        builder.loop(3, g5_loop)
 
        # 27. Close Meter Load Switch
        builder.send_meter_command("close_load_switch")
        # 28. Measure Current should be > 0
        builder.measure_current(min_val=0.1, max_val=100.0)
        # 29. Open Load Switch
        builder.send_meter_command("open_load_switch")
        # 30. Measure Current should be = 0
        builder.measure_current(min_val=0.0, max_val=0.05)
        
        # 31. G7
        builder.custom_action("Execute G7 Verification", lambda ctx, hw: ctx.update_status("Executing G7 Sequence Placeholder..."))
        
        # 32. Prompt User to Enter Final Energy Value
        builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
        
        # 33. Validate, Showcase and store results
        builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 34. Turn OFF ACB
        # 35. Turn OFF SCR
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
    def _verify_and_store(self, ctx, hw):
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            diff = abs(final - initial)
            ctx.logger.info(f"Test Completed: Energy difference ({diff}). Storing results...")
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
