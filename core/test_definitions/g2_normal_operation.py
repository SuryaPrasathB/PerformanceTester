import time
from core.test_definitions.base_test import BaseTest

class G2NormalOperationTest(BaseTest):
    """
    G2 Normal Operation Test:
    Simulates loading application (voltage/current/PF), reading meter values repeatedly,
    and simulating credit depletion over a specific cycle.
    """
    
    def setup(self, context):
        context.logger.info("G2 Normal Operation Test - Setup started.")
        
        # Initialize runtime values
        context.update_runtime_value("voltage", 230.0)
        context.update_runtime_value("current", 5.0)
        context.update_runtime_value("power_factor", 0.95)
        context.update_runtime_value("credit", 10.0) # start with 10 units of credit
        
        context.logger.info("G2 Normal Operation Test - Setup completed. Initialized voltage, current, PF, and credit.")

    def run(self, context):
        context.logger.info("G2 Normal Operation Test - Run started.")
        
        cycles_completed = 0
        max_cycles = 3
        
        while cycles_completed < max_cycles:
            context.wait_if_paused()
            context.check_cancel()
            
            # Read current credit
            current_credit = context.get_runtime_value("credit")
            
            # Simulate reading meter values repeatedly
            for _ in range(3):
                context.wait_if_paused()
                context.check_cancel()
                
                # Mock reading values
                voltage = context.get_runtime_value("voltage")
                current = context.get_runtime_value("current")
                
                context.logger.debug(f"Reading meter... V: {voltage}V, I: {current}A")
                time.sleep(1) # simulate delay
                
            # Deplete credit
            current_credit -= 3.33 # roughly deplete by 10 over 3 cycles
            if current_credit < 0:
                current_credit = 0.0
            context.update_runtime_value("credit", round(current_credit, 2))
            context.logger.info(f"Credit depleted. Current credit: {current_credit:.2f}")
            
            cycles_completed += 1
            context.logger.info(f"Completed cycle {cycles_completed}/{max_cycles}.")

        context.logger.info("G2 Normal Operation Test - Run completed.")

    def verify(self, context):
        context.logger.info("G2 Normal Operation Test - Verification started.")
        
        final_credit = context.get_runtime_value("credit")
        if final_credit > 0.1:
            context.logger.warning(f"Verification issue: Credit was not fully depleted. Final credit: {final_credit}")
            context.test_results["success"] = False
            context.test_results["reason"] = "Credit not fully depleted."
        else:
            context.logger.info("Verification passed: Credit was depleted correctly.")
            context.test_results["success"] = True

    def cleanup(self, context):
        context.logger.info("G2 Normal Operation Test - Cleanup started.")
        # Reset runtime values back to zero or default safe state
        context.update_runtime_value("voltage", 0.0)
        context.update_runtime_value("current", 0.0)
        context.logger.info("G2 Normal Operation Test - Cleanup completed.")
