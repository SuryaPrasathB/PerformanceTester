import logging
import time

class LoadController:
    """
    High-level abstraction over PLC for load control operations.
    Hides PLC complexity from test logic.
    """
    def __init__(self, plc_controller):
        self.plc = plc_controller
        self.logger = logging.getLogger(__name__)

    def turn_load_on(self) -> bool:
        """Turns the physical load on via the PLC."""
        self.logger.info("Load Controller: Turning load ON.")
        # Turn on main relay first, then load switch
        success_relay = self.plc.set_output("relay_main", True)
        time.sleep(0.1) # Stabilization delay
        success_load = self.plc.set_output("load_on", True)
        
        if not (success_relay and success_load):
            self.logger.error("Load Controller: Failed to turn load ON.")
            return False
        return True

    def turn_load_off(self) -> bool:
        """Turns the physical load off via the PLC."""
        self.logger.info("Load Controller: Turning load OFF.")
        # Turn off load switch first, then main relay
        success_load = self.plc.set_output("load_on", False)
        time.sleep(0.1)
        success_relay = self.plc.set_output("relay_main", False)
        
        return success_load and success_relay

    def apply_test_cycle(self, on_time: float, off_time: float) -> bool:
        """Applies a specific on/off test cycle."""
        self.logger.info(f"Load Controller: Starting test cycle ({on_time}s ON, {off_time}s OFF)")
        if not self.turn_load_on():
            return False
            
        time.sleep(on_time)
        
        if not self.turn_load_off():
            return False
            
        time.sleep(off_time)
        return True
