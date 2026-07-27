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
        builder.prompt_user("Set Load Vc, (2.5 / 3 / 4.5 / 6) kA, UPF. \nEnter Expected Peak Voltage (e.g. 2 for 1kA, 10 for 6kA):", requires_input=True, save_as="expected_peak_voltage")
        
        # Start Power Sequence (ACB -> Delay -> 120A Contactor, NO SCR)
        builder.set_plc_coil(PLCCoil.ACB_COIL_ADDR, True)
        builder.verify_plc_coil_status(PLCCoil.ACB_STATUS, "ACB")
 
        # 2. Close Load Switch
        builder.send_meter_command("close_load_switch")
        
        # 3. Configure PicoScope Range dynamically
        def configure_picoscope(ctx, hw):
            expected_v = float(ctx.get_runtime_value("expected_peak_voltage", 20.0))
            # Determine range index based on expected voltage
            if expected_v <= 1.0: range_idx = 6 # 1V
            elif expected_v <= 2.0: range_idx = 7 # 2V
            elif expected_v <= 5.0: range_idx = 8 # 5V
            elif expected_v <= 10.0: range_idx = 9 # 10V
            else: range_idx = 10 # 20V
            
            pico = hw.picoscope
            if pico:
                pico.set_channel_ranges(10, range_idx)
                ctx.logger.info(f"Dynamically set PicoScope Channel B to {range_idx} (+/- {expected_v}V)")
        builder.custom_action("Configure PicoScope Range", configure_picoscope)

        # 4. Start capturing PicoScope waveform with optional delay shift
        def start_pico_shifted(ctx, hw):
            delay = 0
            if hw.picoscope and hasattr(hw.picoscope, 'capture_delay_ms'):
                if getattr(hw.picoscope, 'trigger_mode', 'manual') != 'auto':
                    delay = hw.picoscope.capture_delay_ms
            
            if delay > 0:
                ctx.logger.info(f"Shifting capture start by {delay}ms...")
                time.sleep(delay / 1000.0)
                
            getattr(hw, "start_waveform_capture", lambda: ctx.logger.info("Started Waveform Capture"))()
            
        builder.custom_action("Start PicoScope Capture", start_pico_shifted)

        # 5. Notify PLC that the test is starting (using SCCC_TEST_START = 0x06)
        builder.set_plc_coil(PLCCoil.SCCC_TEST_START, True)
        
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
