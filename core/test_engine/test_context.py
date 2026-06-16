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
        if config is None and hasattr(device_manager, 'config_service') and device_manager.config_service:
            self.config = device_manager.config_service.get_config()
        else:
            self.config = config or {}
        
        # Phase 3 Hardware Integration
        from services.hardware_service import HardwareService
        self.hardware_service = HardwareService(self.device_manager, self.device_manager.config_service)
        self.hardware_service.context = self
        self.hardware_service.initialize_all()
        
        self.safety_manager = self.hardware_service.safety_manager
        
        # Database Integration
        self.database_service = self.device_manager.database_service
        self.meter_serial_number = ""
        self.db_row_id = None
        
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
        
        # We will inject callbacks here from TestRunner to emit signals safely
        self._prompt_callback = None
        self._status_callback = None
        self._progress_callback = None
        self._step_callback = None
        self._cycle_callback = None
        
        # Background Tasks
        self.background_tasks = {}
        self.background_tasks_stop_events = {}
        
        # Loop tracking stack to cache prompt actions on subsequent iterations
        self.loop_stack = []
        
    def check_cancel(self):
        """Checks if the test has been cancelled."""
        if self.cancel_event.is_set():
            self.stop_all_background_tasks()
            raise Exception("Test was cancelled.")
            
    def stop_all_background_tasks(self):
        for name, event in self.background_tasks_stop_events.items():
            event.set()
        self.background_tasks.clear()
        self.background_tasks_stop_events.clear()
            
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

    def push_loop(self, loop_id: int, total_loops: int = 1):
        """Pushes a new loop context onto the loop stack."""
        self.loop_stack.append({
            'loop_id': loop_id,
            'iteration': 0,
            'prompt_index': 0,
            'prompts_history': {},
            'total_loops': total_loops
        })
        if self._cycle_callback:
            self._cycle_callback(1, total_loops)

    def pop_loop(self):
        """Pops the topmost loop context off the loop stack."""
        if self.loop_stack:
            self.loop_stack.pop()
            if self._cycle_callback:
                if self.loop_stack:
                    outer = self.loop_stack[-1]
                    self._cycle_callback(outer['iteration'] + 1, outer['total_loops'])
                else:
                    self._cycle_callback(0, 0)

    def set_loop_iteration(self, iteration: int):
        """Sets the current iteration for the active loop, resetting the prompt index."""
        if self.loop_stack:
            self.loop_stack[-1]['iteration'] = iteration
            self.loop_stack[-1]['prompt_index'] = 0
            if self._cycle_callback:
                self._cycle_callback(iteration + 1, self.loop_stack[-1]['total_loops'])

    def prompt_user_action(self, instruction_text: str, requires_input: bool = False) -> str:
        """
        Halts test execution and prompts the UI for user interaction.
        Returns the user's string input if requested.
        
        If executing inside a loop (iteration > 0), reuses inputs cached from the first iteration.
        """
        if self.loop_stack:
            current_loop = self.loop_stack[-1]
            iteration = current_loop['iteration']
            prompt_idx = current_loop['prompt_index']
            
            if iteration > 0:
                cached_res = current_loop['prompts_history'].get(prompt_idx)
                if cached_res is not None:
                    self.logger.info(f"Loop iteration {iteration+1}: Skipping prompt '{instruction_text}' and using previous input: '{cached_res}'")
                    current_loop['prompt_index'] += 1
                    return cached_res
                else:
                    self.logger.warning(f"Loop iteration {iteration+1}: Expected cached prompt result at index {prompt_idx} but found none. Prompting user...")

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
        result = self.user_input_result
        
        if self.loop_stack:
            current_loop = self.loop_stack[-1]
            if current_loop['iteration'] == 0:
                current_loop['prompts_history'][current_loop['prompt_index']] = result
            current_loop['prompt_index'] += 1
            
        return result

    def update_status(self, message: str):
        """Sends a status commentary message to the UI."""
        self.logger.info(f"STATUS: {message}")
        if self._status_callback:
            self._status_callback(message)

    def update_progress(self, percentage: int):
        """Updates the test progress bar on the UI."""
        if self._progress_callback:
            self._progress_callback(percentage)

    def start_step(self, step_name: str):
        """Signals the start of a logical test step for smart progress tracking."""
        self.logger.info(f">>> STARTING STEP: {step_name}")
        if self._step_callback:
            self._step_callback(step_name)
