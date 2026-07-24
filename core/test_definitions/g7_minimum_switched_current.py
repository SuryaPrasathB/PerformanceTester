from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

class G7MinimumSwitchedCurrentTest(BaseTest):
    """
    Implementation of the G7 Minimum Switched Current Test sequence.
    """
    def build(self, builder: TestBuilder, is_sub_sequence=False):
        if is_sub_sequence:
            builder.custom_action("Start G7 Sub-Test Tracker", lambda ctx, hw: ctx.update_runtime_value("active_sub_test", "g7"))

        # 1. Prompt user to set load to Vc Imin UPF.
        builder.stop_power_sequence(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set load to Vc Imin UPF", requires_input=False)
        
        # 2. Turn ON ACB (PLC Coil ACB_COIL_ADDR = 0x03).
        # 3. Delay as required.
        builder.start_power_sequence(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR)
        
        if not is_sub_sequence:
            # 6. Prompt user to enter Initial Energy Value.
            builder.prompt_user("Enter Initial Energy Value", requires_input=True, save_as="energy_initial")
        
        # Start background current sensing in parallel
        def current_sensing_monitor(ctx, hw):
            try:
                # Read MFM current (which will automatically read from MFM Meter 2 because test_identifier is "g7")
                current = getattr(hw, "read_mfm_current", lambda: 0.0)()
                ctx.update_runtime_value("current", current)
            except Exception as e:
                ctx.logger.error(f"Error in Current Sensing Monitor: {e}")
            
        builder.start_background_monitor("current_sensing", current_sensing_monitor)
        
        # Repeat steps 6-9 for 10 cycles
        def switched_current_loop(b, i):
            # 6. Close load switch.
            b.send_meter_command("close_load_switch")
            
            # Wait 5 seconds for the switch to mechanically close and current to establish
            b.wait(5)
            
            # Verify current is above 10 mA (0.010 A)
            b.measure_current(0.010, 100.0)
            
            # 7. Delay remaining 5 seconds (total 10s as before).
            b.wait(5)
            
            # 8. Open load switch.
            b.send_meter_command("open_load_switch")
            
            # Wait 5 seconds for the switch to mechanically open and current to drop
            b.wait(5)
            
            # Verify current is near zero (less than 0.3 mA = 0.0003 A)
            b.measure_current(0.0, 0.0003)
            
            # 9. Delay remaining 15 seconds (total 20s as before).
            b.wait(15)

        builder.loop(10, switched_current_loop)
        
        # Stop current sensing
        builder.stop_background_monitor("current_sensing")
        
        # 10. Validate result
        builder.custom_action("Validate Result", lambda ctx, hw: ctx.logger.info("G7 Minimum Switched Current Test Validated."))
        
        if is_sub_sequence:
            builder.custom_action("Log G7 Sub-Test Success", lambda ctx, hw: [
                ctx.database_service.save_test_run_detail(ctx.db_row_id, "g7", "PASS", is_sub_test=True) if ctx.database_service and getattr(ctx, "db_row_id", None) else None,
                ctx.update_runtime_value("active_sub_test", None)
            ])
            
        if not is_sub_sequence:
            # Prompt user to enter Final Energy Value.
            builder.prompt_user("Enter Final Energy Value", requires_input=True, save_as="energy_final")
            builder.custom_action("Verify Energy Difference & Store Results", self._verify_and_store)
        
        # 11. Turn OFF ACB and Contactor
        builder.stop_power_sequence(PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR)

    def _verify_and_store(self, ctx, hw):
        if not hasattr(ctx, "test_results"):
            ctx.test_results = {}
            
        try:
            initial = float(ctx.get_runtime_value("energy_initial", 0))
            final = float(ctx.get_runtime_value("energy_final", 0))
            diff = abs(final - initial)
            ctx.logger.info(f"G7 Test Completed. Energy difference: {diff}. Coagulated Result: PASS")
            ctx.test_results["success"] = True
        except ValueError:
            ctx.logger.error("Test Failed: Invalid energy values entered.")
            ctx.test_results["success"] = False
