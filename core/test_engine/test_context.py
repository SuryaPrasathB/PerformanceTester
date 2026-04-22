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
        
        # Runtime values like voltage, current, PF, etc.
        self.runtime_values = {}
        
        # Store results and logs
        self.test_results = {}
        self.logger = logging.getLogger(__name__)
        
        # Synchronization events for thread-safe execution control
        self.pause_event = threading.Event()
        self.pause_event.set() # Set means "not paused", clear means "paused"
        
        self.cancel_event = threading.Event()
        
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
