from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil
def _abort_test(ctx, hw, reason: str):
    try:
        from core.hardware_mapping import PLCCoil
        hw.plc.write_coil(PLCCoil.ACB_COIL_ADDR.value, False)
        hw.plc.write_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR.value, False)
        hw.plc.write_coil(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR.value, False)
        hw.plc.write_coil(PLCCoil.SCR_COIL_ADDR.value, False)
    except Exception:
        pass
    
    if not hasattr(ctx, "test_results"):
        ctx.test_results = {}
    ctx.test_results["success"] = False
    ctx.test_results["failure_reason"] = reason
    ctx.cancel_event.set()




class G3ElectricalEnduranceTest(BaseTest):
    """
    Implementation of the G3 Electrical Endurance Test sequence.
    Verifies the contact durability over 8000 switching operations.
    """
    def build(self, builder: TestBuilder):
        builder.custom_action("Initialize Fault Counters", lambda ctx, hw: (
            ctx.update_runtime_value("total_weld_fault_cycles", 0),
            ctx.update_runtime_value("total_open_fault_cycles", 0)
        ))
        
        # 1. Prompt User to Set Load to Vc Ic UPF
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set Load to Vc Ic UPF", requires_input=False)
        
        # 2-3. Turn ON ACB -> Delay -> Turn ON Contactor
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        

        
        # 5. Prompt User to Enter Initial Energy Value
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # 6. Prompt user to Enter Off Time Between 10-60 secs
        builder.prompt_user("Enter OFF Time between 10-60 secs (ON time defaults to 10s)", requires_input=True, save_as="off_delay")
        
        # Helper loop generator
        def make_cycles(pf):
            def cycle_logic(b, i):
                # 1. Close Load Switch
                b.send_meter_command("close_load_switch")
                
                # 2. Sequential Check for OPEN Fault (Current should be > 0.1A because switch is closed)
                def check_open_fault(ctx, hw):
                    profile = getattr(ctx, "meter_profile", {})
                    if profile.get("communication_mode", "").lower() == "external":
                        return
                        
                    import time
                    ignore_until = ctx.get_runtime_value("ignore_mfm_until", 0)
                    now = time.time()
                    if ignore_until > now:
                        delay = ignore_until - now
                        ctx.logger.info(f"Waiting {delay:.1f}s for MFM current to settle...")
                        time.sleep(delay)
                        
                    current = getattr(hw, "read_mfm_current", lambda: 10.0)()
                    if current < 0.1:
                        total = ctx.get_runtime_value("total_open_fault_cycles", 0) + 1
                        ctx.update_runtime_value("total_open_fault_cycles", total)
                        ctx.logger.warning(f"Open fault detected in cycle {i+1}. Current: {current}A. Total: {total}/3")
                        if total >= 3:
                            ctx.logger.error("3 OPEN FAULT CYCLES DETECTED! Aborting test.")
                            _abort_test(ctx, hw, "3 OPEN FAULT CYCLES DETECTED")
                b.custom_action("Check Open Fault", check_open_fault)
                
                # 3. Wait ON Time (10s)
                def dynamic_wait_on(ctx, hw):
                    import time
                    for s in range(10, 0, -1):
                        if ctx.cancel_event.is_set():
                            break
                        ctx.update_status(f"Waiting ON time: {s}s...")
                        time.sleep(1)
                b.custom_action("Wait ON Time", dynamic_wait_on)
                
                # 4. Open Load Switch
                b.send_meter_command("open_load_switch")
                
                # 5. Sequential Check for WELD Fault (Current should be < 0.1A because switch is open)
                def check_weld_fault(ctx, hw):
                    profile = getattr(ctx, "meter_profile", {})
                    if profile.get("communication_mode", "").lower() == "external":
                        return
                        
                    import time
                    ignore_until = ctx.get_runtime_value("ignore_mfm_until", 0)
                    now = time.time()
                    if ignore_until > now:
                        delay = ignore_until - now
                        ctx.logger.info(f"Waiting {delay:.1f}s for MFM current to settle...")
                        time.sleep(delay)
                        
                    current = getattr(hw, "read_mfm_current", lambda: 0.0)()
                    if current > 0.1:
                        total = ctx.get_runtime_value("total_weld_fault_cycles", 0) + 1
                        ctx.update_runtime_value("total_weld_fault_cycles", total)
                        ctx.logger.warning(f"Weld fault detected in cycle {i+1}. Current: {current}A. Total: {total}/3")
                        if total >= 3:
                            ctx.logger.error("3 WELD FAULT CYCLES DETECTED! Aborting test.")
                            _abort_test(ctx, hw, "3 WELD FAULT CYCLES DETECTED")
                b.custom_action("Check Weld Fault", check_weld_fault)
                
                # 6. Wait OFF Time (Dynamic off_delay)
                def dynamic_wait_off(ctx, hw):
                    delay = int(ctx.get_runtime_value("off_delay", 10))
                    import time
                    for s in range(delay, 0, -1):
                        if ctx.cancel_event.is_set():
                            break
                        ctx.update_status(f"Waiting OFF time: {s}s...")
                        time.sleep(1)
                b.custom_action("Wait OFF Time", dynamic_wait_off)
                
            return cycle_logic

        def is_external(ctx, hw):
            profile = getattr(ctx, "meter_profile", {})
            return profile.get("communication_mode", "").lower() == "external"

        def build_external_path(b):
            b.prompt_user("External Mode Detected. Start your external script now.", requires_input=False)
            b.wait_for_external_cycles(4000, threshold_current=0.5)

        def build_internal_path_upf(b):
            b.loop(4000, make_cycles(1.0))

        # 4000 Cycles at UPF
        builder.branch_on_condition("UPF Cycles", is_external, build_external_path, build_internal_path_upf)
        
        # 11. Prompt User to Change Load Vc Ic 0.5PF
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Change Load to Vc 10A 0.5PF", requires_input=False)
        
        def build_internal_path_pf(b):
            b.loop(4000, make_cycles(0.5))

        # 12-15. 4000 Cycles at 0.5 PF
        builder.branch_on_condition("0.5PF Cycles", is_external, build_external_path, build_internal_path_pf)

        # Stop Background Process
        builder.stop_background_monitor("Current Sensing")

        # 16-19. Verification
        builder.send_meter_command("close_load_switch")
        builder.measure_current(min_val=0.1, max_val=100.0)
        builder.send_meter_command("open_load_switch")
        builder.measure_current(min_val=0.0, max_val=0.05)
        
        # 20. G7
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
        
        # 21. Prompt User to Enter Final Energy Value
        builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
        
        # 22. Validate, Showcase and store results
        builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 23-24. Turn OFF ACB and Contactor
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)

    def _verify_and_store(self, ctx, hw):
        if not hasattr(ctx, "test_results"):
            ctx.test_results = {}
            
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            diff = abs(final - initial)
            g7_res = ctx.get_runtime_value("g7_result", "Skipped")
            weld_faults = ctx.get_runtime_value("total_weld_fault_cycles", 0)
            open_faults = ctx.get_runtime_value("total_open_fault_cycles", 0)
            
            ctx.test_results["energy_difference"] = diff
            ctx.test_results["g7_result"] = g7_res
            ctx.test_results["weld_faults"] = weld_faults
            ctx.test_results["open_faults"] = open_faults
            
            threshold_percent = ctx.config.get("testing", {}).get("energy_diff_threshold_percent", 1.0)
            threshold_val = initial * (threshold_percent / 100.0)
            
            if diff > threshold_val:
                ctx.logger.error(f"Test Failed: Energy diff {diff:.2f} exceeds {threshold_percent}% threshold.")
                ctx.test_results["success"] = False
                ctx.test_results["failure_reason"] = f"Energy diff > {threshold_percent}%"
            else:
                ctx.logger.info(f"G3 Test Completed. Energy diff: {diff:.2f}, Weld Faults: {weld_faults}, Open Faults: {open_faults}, G7: {g7_res}. Result: PASS")
                ctx.test_results["success"] = True
            
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
            ctx.test_results["success"] = False
            ctx.test_results["failure_reason"] = "Invalid energy values"
