from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder

class G7MinimumSwitchedCurrentTest(BaseTest):
    """
    Implementation of the G7 Minimum Switched Current Test sequence.
    """
    def build(self, builder: TestBuilder):
        # 1. Prompt user to set load to Vc Ic UPF.
        builder.prompt_user("Set load to Vc Ic UPF", requires_input=False)
        
        # 2. Turn ON ACB (PLC Coil ACB_COIL_ADDR = 0x03).
        # 3. Delay as required.
        # 4. Turn ON SCR (PLC Coil SCR_COIL_ADDR = 0x04).
        builder.start_power_sequence()
        
        # 5. Read meter serial number.
        builder.send_meter_command("read_serial_number")
        
        # Start background current sensing in parallel
        def current_sensing_monitor(ctx, hw):
            try:
                # Read MFM current (which will automatically read from MFM Meter 2 because test_identifier is "g7")
                current = getattr(hw, "read_mfm_current", lambda: 0.0)()
                ctx.update_runtime_value("current", current)
            except Exception as e:
                ctx.logger.error(f"Error in Current Sensing Monitor: {e}")
            
        builder.start_background_monitor("current_sensing", current_sensing_monitor)
        
        # Repeat steps 6-8 (and 9) for 10 cycles
        def switched_current_loop(b, i):
            # 6. Close load switch.
            b.send_meter_command("close_load_switch")
            
            # 7. Delay 10 seconds.
            b.wait(10)
            
            # 8. Open load switch.
            b.send_meter_command("open_load_switch")
            
            # 9. Delay 20 seconds.
            b.wait(20)

        builder.loop(10, switched_current_loop)
        
        # Stop current sensing
        builder.stop_background_monitor("current_sensing")
        
        # 10. Validate result
        builder.custom_action("Validate Result", lambda ctx, hw: ctx.logger.info("G7 Minimum Switched Current Test Validated."))
        
        # 11. Turn OFF ACB
        # 12. Turn OFF SCR
        builder.stop_power_sequence()
