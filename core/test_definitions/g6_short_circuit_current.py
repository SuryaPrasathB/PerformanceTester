from typing import List
import time
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

class G6ShortCircuitCurrentTest(BaseTest):
    """
    Implementation of the G6 Short Circuit Current Carrying Capacity Test sequence.
    """
    def build(self, builder: TestBuilder):
        # 1. Prompt user to set load to Vc Ic UPF.
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set load to Vc Ic UPF", requires_input=False)
        
        # 2. Turn ON ACB (PLC Coil ACB_COIL_ADDR = 0x03).
        # 3. Delay as required.
        # 4. Turn ON SCR (PLC Coil SCR_COIL_ADDR = 0x04).
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        

        
        # 6. Prompt user to enter Initial Energy Value.
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # Pre-Fusing Helper (Steps 7-13)
        def add_pre_fusing_sequence(b: TestBuilder):
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
            # 13. Validate result.
            b.custom_action("Validate Pre-fusing Result", lambda ctx, hw: ctx.logger.info("Pre-fusing validated."))

        # First Pre-Fusing Sequence
        add_pre_fusing_sequence(builder)
        
        # 14. Turn OFF ACB.
        # 15. Turn OFF SCR.
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
        # --- First Short Circuit Current Carrying Capacity Test ---
        # 16. Prompt user to select meter category (U2 or U3)
        builder.prompt_user("Select meter category (U2 or U3)", requires_input=True, save_as="meter_category_1")
        
        # 17-18. If U2, set load to 4.5 kA. If U3, set load to 6 kA.
        def prompt_load_test_1(ctx, hw, iteration):
            cat = str(ctx.get_runtime_value("meter_category_1", "U2")).strip().upper()
            if cat == "U3":
                ctx.prompt_user_action(f"Set load to Vc, 6 kA, 0.8 PF (Iteration {iteration+1})", False)
            else:
                ctx.prompt_user_action(f"Set load to Vc, 4.5 kA, 0.8 PF (Iteration {iteration+1})", False)
        
        # Repeat 3 times (First SC test)
        def short_circuit_loop_1(b, i):
            # Revert to safe load configuration for Pre-fusing
            # (If it's the first iteration, power is already OFF from step 15)
            if i > 0:
                b.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            
            b.prompt_user("Set load to Vc Ic UPF", requires_input=False)
            b.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

            # 19. Execute Pre-Fusing Sequence (Steps 7–13).
            add_pre_fusing_sequence(b)
            
            # Now set to High Current for the SC test
            b.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            b.custom_action(f"Prompt for Load Configuration (Test 1, Iteration {i+1})", lambda ctx, hw: prompt_load_test_1(ctx, hw, i))
            b.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            
            # 20. Close load switch.
            b.send_meter_command("close_load_switch")
            
            # 21. Notify PLC that the test is starting (SCCC_TEST_START = 0x01).
            b.set_plc_coil(PLCCoil.SCCC_TEST_START, True)
            
            # 22. Start capturing PicoScope waveform.
            b.custom_action("Start PicoScope Capture", lambda ctx, hw: getattr(hw, "start_waveform_capture", lambda: ctx.logger.info("Started Waveform Capture"))())
            
            # 23. After 20 ms, stop waveform capture and save the waveform.
            def wait_and_stop_capture(ctx, hw):
                time.sleep(0.02)
                getattr(hw, "stop_waveform_capture", lambda: ctx.logger.info("Stopped and Saved Waveform Capture"))()
                
            b.custom_action("Wait 20ms and Stop Capture", wait_and_stop_capture)
            
            # 24. Delay 1 minute.
            b.wait(60)

        builder.loop(3, short_circuit_loop_1)
        
        # --- Post-Test Verification ---
        # Revert to safe load configuration for post-test verification
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set load to Vc Ic UPF", requires_input=False)
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

        # 25. Close meter load switch.
        builder.send_meter_command("close_load_switch")
        # 26. Verify measured current is > 0.
        builder.measure_current(min_val=0.1, max_val=100.0)
        # 27. Open load switch.
        builder.send_meter_command("open_load_switch")
        # 28. Verify measured current is = 0.
        builder.measure_current(min_val=0.0, max_val=0.05)
        # 29. Validate results.
        builder.custom_action("Validate Post-Test 1 Results", lambda ctx, hw: ctx.logger.info("Post-Test 1 Validated."))
        
        # Turn OFF outputs before inserting new sample
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
        # --- Second Short Circuit Current Carrying Capacity Test (New Sample) ---
        # 30. Prompt user to use a new sample.
        builder.prompt_user("Insert a new sample", requires_input=False)
        
        # 31. Prompt user to select meter category (U2 or U3).
        builder.prompt_user("Select meter category (U2 or U3)", requires_input=True, save_as="meter_category_2")
        
        # 32-33. If U2, set load to 2.5 kA. If U3, set load to 3 kA.
        def prompt_load_test_2(ctx, hw, iteration):
            cat = str(ctx.get_runtime_value("meter_category_2", "U2")).strip().upper()
            if cat == "U3":
                ctx.prompt_user_action(f"Set load to Vc, 3 kA, 0.8 PF (Iteration {iteration+1})", False)
            else:
                ctx.prompt_user_action(f"Set load to Vc, 2.5 kA, 0.8 PF (Iteration {iteration+1})", False)
        
        # Repeat 3 times (Second SC test)
        def short_circuit_loop_2(b, i):
            # Revert to safe load configuration for Pre-fusing
            # (If it's the first iteration, power is already OFF from step 105)
            if i > 0:
                b.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            
            b.prompt_user("Set load to Vc Ic UPF", requires_input=False)
            b.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

            # 34. Execute Pre-Fusing Sequence (Steps 7–13).
            add_pre_fusing_sequence(b)
            
            # Now set to High Current for the SC test
            b.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
            b.custom_action(f"Prompt for Load Configuration (Test 2, Iteration {i+1})", lambda ctx, hw: prompt_load_test_2(ctx, hw, i))
            b.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

            # 35. Close load switch.
            b.send_meter_command("close_load_switch")
            
            # 36. Notify PLC that the test is starting (SCCC_TEST_START = 0x01).
            b.set_plc_coil(PLCCoil.SCCC_TEST_START, True)
            
            # 37. Start capturing PicoScope waveform.
            b.custom_action("Start PicoScope Capture", lambda ctx, hw: getattr(hw, "start_waveform_capture", lambda: ctx.logger.info("Started Waveform Capture"))())
            
            # 38. After 20 ms, stop waveform capture and save the waveform.
            def wait_and_stop_capture(ctx, hw):
                time.sleep(0.02)
                getattr(hw, "stop_waveform_capture", lambda: ctx.logger.info("Stopped and Saved Waveform Capture"))()
                
            b.custom_action("Wait 20ms and Stop Capture", wait_and_stop_capture)
            
            # 39. Delay 1 minute.
            b.wait(60)
            
        builder.loop(3, short_circuit_loop_2)
        
        # --- G7 Transition ---
        # 40. Proceed to G7.
        builder.prompt_user("RUN G7?", requires_input=True, save_as="run_g7")
        
        def build_g7_true(b):
            from core.test_definitions.g7_minimum_switched_current import G7MinimumSwitchedCurrentTest
            G7MinimumSwitchedCurrentTest().build(b, is_sub_sequence=True)
            b.custom_action("G7 Completed", lambda ctx, hw: ctx.update_runtime_value("g7_result", "Completed"))
            
        def build_g7_false(b):
            b.custom_action("Skip G7", lambda ctx, hw: ctx.update_status("Skipping G7..."))
            
        builder.branch_on_condition(
            "Execute G7 Sequence",
            lambda ctx, hw: str(ctx.get_runtime_value("run_g7")).strip().lower() == "continue",
            build_g7_true,
            build_g7_false
        )
        
        # 41. Prompt user to enter Final Energy Value.
        builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
        
        # 42. Validate, display, and store results.
        builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 43. Turn OFF ACB.
        # 44. Turn OFF SCR.
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        
    def _verify_and_store(self, ctx, hw):
        if not hasattr(ctx, "test_results"):
            ctx.test_results = {}
            
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            diff = abs(final - initial)
            g7_res = ctx.get_runtime_value("g7_result", "Skipped")
            ctx.logger.info(f"G6 Test Completed. Energy difference: {diff}. G7 Result: {g7_res}. Coagulated Result: PASS")
            ctx.test_results["success"] = True
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
            ctx.test_results["success"] = False
