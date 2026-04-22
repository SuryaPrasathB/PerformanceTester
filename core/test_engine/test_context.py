import logging
import threading

class TestContext:
    """
    Shared runtime container for a test.
    Holds device_manager reference, config, runtime values, test results, 
    logger, and synchronization flags for pause/cancel support.
    """
    def __init__(self, device_manager, config=None):
        self.device_manager = device_manager
        self.config = config or {}
        
        # Phase 3 Hardware Integration
        from services.hardware_service import HardwareService
        self.hardware_service = HardwareService(self.device_manager, self.device_manager.config_service)
        self.hardware_service.initialize_all()
        
        self.safety_manager = self.hardware_service.safety_manager
        
        # Runtime values like voltage, current, PF, etc.
        self.runtime_values = {}
        
        # Store results and logs
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
        
        # Synchronization events for thread-safe execution control
        self.pause_event = threading.Event()
        self.pause_event.set() # Set means "not paused", clear means "paused"
        
        self.cancel_event = threading.Event()
        
        # User Interaction Event
        self.user_action_event = threading.Event()
        self.user_input_result = ""
        
        # We will inject a callback here from TestRunner to emit signals safely
        self._prompt_callback = None
        
    def check_cancel(self):
        """Checks if the test has been cancelled."""
        if self.cancel_event.is_set():
            raise Exception("Test was cancelled.")
            
    def wait_if_paused(self):
        """Blocks execution if the pause event is cleared."""
        # Wait until the flag is set. If already set, returns immediately.
        self.pause_event.wait()
        
    def update_runtime_value(self, key: str, value: any):
        """Updates a runtime value."""
        self.runtime_values[key] = value
        
    def get_runtime_value(self, key: str, default=None):
        """Gets a runtime value."""
        return self.runtime_values.get(key, default)

    def prompt_user_action(self, instruction_text: str, requires_input: bool = False) -> str:
        """
        Halts test execution and prompts the UI for user interaction.
        Returns the user's string input if requested.
        """
        self.logger.info(f"WAITING FOR USER: {instruction_text}")
        
        self.user_action_event.clear()
        self.user_input_result = ""
        
        if self._prompt_callback:
            self._prompt_callback(instruction_text, requires_input)
            
        # Block until user hits Done or test is cancelled
        # Check cancel loop to avoid deadlocks
        while not self.user_action_event.is_set():
            if self.cancel_event.is_set():
                raise Exception("Test was cancelled during user prompt.")
            self.user_action_event.wait(0.5)
            
        self.logger.info("USER ACTION COMPLETED/CONFIRMED.")
        return self.user_input_result
