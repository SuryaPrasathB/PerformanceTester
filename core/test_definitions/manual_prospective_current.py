from typing import List
import time
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_builder import TestBuilder
from core.hardware_mapping import PLCCoil

class ManualProspectiveCurrentTest(BaseTest):
    """
    Implementation of the Manual Prospective Current Test sequence.
    """
    def build(self, builder: TestBuilder):
        # 1. Prompt User to set Load Vc, (2.5 / 3 / 4.5 / 6) kA, UPF
        builder.stop_power_sequence(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR)
        builder.prompt_user("Set Load Vc, (2.5 / 3 / 4.5 / 6) kA, UPF", requires_input=False)
        
        # Start Power Sequence (ACB -> Delay -> 120A Contactor, NO SCR)
        builder.set_plc_coil(PLCCoil.ACB_COIL_ADDR, True)
        builder.verify_plc_coil_status(PLCCoil.ACB_STATUS, "ACB")
        builder.set_plc_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR, True)
        builder.verify_plc_coil_status(PLCCoil.CONTACTOR_120A_STATUS, "120A Contactor")
        
        # 2. Close Load Switch
        builder.send_meter_command("close_load_switch")
        
        # 3. Notify PLC that the test is starting (using SCCC_TEST_START = 0x06)
        builder.set_plc_coil(PLCCoil.SCCC_TEST_START, True)
        
        # 4. Start capturing PicoScope waveform.
        builder.custom_action("Start PicoScope Capture", lambda ctx, hw: getattr(hw, "start_waveform_capture", lambda: ctx.logger.info("Started Waveform Capture"))())
        
        # 5. After 20 ms, stop waveform capture and save the waveform.
        def wait_and_stop_capture(ctx, hw):
            time.sleep(0.02)
            getattr(hw, "stop_waveform_capture", lambda: ctx.logger.info("Stopped and Saved Waveform Capture"))()
            
        builder.custom_action("Wait 20ms and Stop Capture", wait_and_stop_capture)
        
        # 7. Open Load Switch
        builder.send_meter_command("open_load_switch")
        
        # 6. Plot Graph (moved after load switch open)
        builder.custom_action("Plot Graph", lambda ctx, hw: ctx.update_status("Plotting Manual Prospective Current Graph..."))
        
        # Stop Power Sequence (Turn OFF ACB and Contactor)
        builder.set_plc_coil(PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR, False)
        builder.set_plc_coil(PLCCoil.ACB_COIL_ADDR, False)
