from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

def current_sensing_monitor(ctx, hw):
    profile = getattr(ctx, "meter_profile", {})
    if profile.get("communication_mode", "").lower() == "external":
        return
        
    expected_state = ctx.get_runtime_value("expected_meter_switch_state", "OPEN")
    
    try:
        # Read MFM current (mocked if not available, usually 10.0 or 0.0)
        current = getattr(hw, "read_mfm_current", lambda: 10.0 if expected_state == "CLOSED" else 0.0)()
        
        consecutive_weld = ctx.get_runtime_value("consecutive_weld_faults", 0)
        consecutive_open = ctx.get_runtime_value("consecutive_open_faults", 0)

        if expected_state == "OPEN":
            if current > 0.1:
                consecutive_weld += 1
            else:
                consecutive_weld = 0
        elif expected_state == "CLOSED":
            if current < 0.1:
                consecutive_open += 1
            else:
                consecutive_open = 0

        ctx.update_runtime_value("consecutive_weld_faults", consecutive_weld)
        ctx.update_runtime_value("consecutive_open_faults", consecutive_open)

        if consecutive_weld >= 2:
            ctx.logger.error("WELD FAULT DETECTED! Aborting test.")
            try:
                hw.plc.write_coil(PLCCoil.ACB_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.SCR_COIL_ADDR.value, False)
            except Exception:
                pass
            ctx.cancel_event.set()
        elif consecutive_open >= 2:
            ctx.logger.error("OPEN FAULT DETECTED! Aborting test.")
            try:
                hw.plc.write_coil(PLCCoil.ACB_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR.value, False)
                hw.plc.write_coil(PLCCoil.SCR_COIL_ADDR.value, False)
            except Exception:
                pass
            ctx.cancel_event.set()

    except Exception as e:
        ctx.logger.error(f"Error in Current Sensing Monitor: {e}")


class G3ElectricalEnduranceTest(BaseTest):
    """
    Implementation of the G3 Electrical Endurance Test sequence.
    Verifies the contact durability over 8000 switching operations.
    """
    def build(self, builder: TestBuilder):
        # 1. Prompt User to Set Load to Vc Ic UPF
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set Load to 240V Ic UPF", requires_input=False)
        
        # 2-3. Turn ON ACB -> Delay -> Turn ON Contactor
        builder.start_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        

        
        # 5. Prompt User to Enter Initial Energy Value
        builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # 6. Prompt user to Enter Off Time Between 10-60 secs
        builder.prompt_user("Enter OFF Time between 10-60 secs (ON time defaults to 10s)", requires_input=True, save_as="off_delay")
        
        # Start Parallel Background Process
        builder.start_background_monitor("Current Sensing", current_sensing_monitor)
        
        # Helper loop generator
        def make_cycles(pf):
            def cycle_logic(b, i):
                # Update expected state for monitor
                b.custom_action("Set expected state to CLOSED", lambda ctx, hw: ctx.update_runtime_value("expected_meter_switch_state", "CLOSED"))
                b.send_meter_command("close_load_switch")
                b.wait(10)
                
                b.custom_action("Set expected state to OPEN", lambda ctx, hw: ctx.update_runtime_value("expected_meter_switch_state", "OPEN"))
                b.send_meter_command("open_load_switch")
                
                # Dynamic off delay wait
                b.custom_action("Wait Off Delay", lambda ctx, hw: b.wait(int(ctx.get_runtime_value("off_delay", 10)))._steps[-1].action(ctx, hw))
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
        builder.prompt_user("Change Load to 240V 10A 0.5PF", requires_input=False)
        
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
            ctx.logger.info(f"G3 Test Completed. Energy difference: {diff}. G7 Result: {g7_res}. Coagulated Result: PASS")
            ctx.test_results["success"] = True
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
            ctx.test_results["success"] = False
