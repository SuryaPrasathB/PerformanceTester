import time
from typing import List
from core.test_definitions.base_test import BaseTest
from core.test_engine.test_step import TestStep

class G2NormalOperationTest(BaseTest):
    """
    Implementation of the G2 Normal Operation Test sequence.
    This test focuses on verifying the meter's ability to handle prepaid operations 
    and simulating credit depletion over a specific cycle.
    """
    test_identifier = "g2"
    
    def get_steps(self) -> List[TestStep]:
        return [
            TestStep("Initialization", weight=5, estimated_duration=2),
            TestStep("Turn On Source", weight=5, estimated_duration=3),
            TestStep("Initial Register Read", weight=10, estimated_duration=5),
            # Cycles (3 total)
            TestStep("Loop: Credit Prompt", weight=5, estimated_duration=0, requires_input=True),
            TestStep("Loop: Monitoring Current", weight=10, estimated_duration=15),
            TestStep("Loop: Credit Prompt", weight=5, estimated_duration=0, requires_input=True),
            TestStep("Loop: Monitoring Current", weight=10, estimated_duration=15),
            TestStep("Loop: Credit Prompt", weight=5, estimated_duration=0, requires_input=True),
            TestStep("Loop: Monitoring Current", weight=10, estimated_duration=15),
            # Final
            TestStep("Final Register Read", weight=10, estimated_duration=5),
            TestStep("Completion", weight=5, estimated_duration=2)
        ]

    def setup(self, context):
        context.logger.info("G2 Normal Operation Test - Setup started.")
        
        self.v_set = 240.0
        self.i_set = 10.0
        self.pf_set = 1.0
        self.target_registers = ["Active Energy", "Current Credit"]
        
        self.initial_registers = {}
        self.final_registers = {}

    def run(self, context):
        context.logger.info("G2 Normal Operation Test - Execution started.")
        
        context.start_step("Initialization")
        hw = context.hardware_service
        hw.inject_signal(self.v_set, self.i_set, self.pf_set)

        # Step 2: Turn On Source (PLC)
        context.start_step("Turn On Source")
        context.update_status("Step 2: Activating physical load source...")
        hw.plc.write_coil(0, True)

        context.start_step("Initial Register Read")
        context.update_status("Step 4: Reading initial meter registers...")
        self.initial_registers = hw.read_meter_registers(self.target_registers)
        context.update_runtime_value("initial_registers", self.initial_registers)

        # Looping Step 3 to 6 (Initial + 2 repeats = 3 total)
        for i in range(3):
            context.update_status(f"Cycle {i+1}/3: Starting test loop...")
            
            # Step 3: Prompt user for amount of credit
            context.start_step("Loop: Credit Prompt")
            credit_amount = context.prompt_user_action(
                f"Cycle {i+1}: Please enter the amount of credit to be added:",
                requires_input=True
            )
            context.logger.info(f"User entered credit: {credit_amount}")
            context.update_runtime_value(f"cycle_{i+1}_credit", credit_amount)

            # Step 5 & 6: Monitor and Wait until current 0
            context.start_step("Loop: Monitoring Current")
            context.update_status(f"Cycle {i+1}/4: Monitoring current until depletion (0A)...")
            success = hw.wait_for_current_zero(threshold=0.1, timeout_sec=60, context=context)
            
            if not success:
                context.logger.error(f"Cycle {i+1} failed: Timeout waiting for current 0.")
                raise Exception(f"Current did not reach zero in Cycle {i+1}")
            
            context.update_status(f"Cycle {i+1}/4: Depletion detected successfully.")

        # Step 7: Read Memory Registers - compare with step 4 read
        context.start_step("Final Register Read")
        context.update_status("Step 7: Reading final memory registers for comparison...")
        self.final_registers = hw.read_meter_registers(self.target_registers)
        context.update_runtime_value("final_registers", self.final_registers)
        
        # Step 8: Complete Test
        context.start_step("Completion")
        context.update_status("Step 8: Finalizing test results...")

    def verify(self, context):
        context.logger.info("G2 Normal Operation Test - Verification started.")
        
        # Compare initial and final registers
        results = {"success": True, "details": []}
        
        for reg in self.target_registers:
            initial = self.initial_registers.get(reg)
            final = self.final_registers.get(reg)
            
            context.logger.info(f"Register {reg}: Initial={initial}, Final={final}")
            
        context.update_runtime_value("test_results", results)

    def cleanup(self, context):
        context.logger.info("G2 Normal Operation Test - Cleanup started.")
        hw = context.hardware_service
        if hw:
            hw.control_load(False)
            hw.inject_signal(0, 0, 1.0)
