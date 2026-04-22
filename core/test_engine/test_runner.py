from PySide6.QtCore import QThread, Signal
import traceback
import time
import logging

from core.test_engine.state_machine import StateMachine, TestState
from core.test_engine.test_context import TestContext
from core.test_definitions.base_test import BaseTest

class TestRunner(QThread):
    """
    Core engine that orchestrates test execution in a separate thread.
    Emits signals for state changes, logs, and data updates to keep UI responsive.
    """
    
    # Qt Signals for UI updates
    on_state_changed = Signal(str)
    on_log = Signal(str, str) # level, message
    on_data_update = Signal(dict)
    
    def __init__(self, test_instance: BaseTest, context: TestContext):
        super().__init__()
        self.test = test_instance
        self.context = context
        self.state_machine = StateMachine()
        
        # Override the context logger with a custom one that emits to the UI
        self._setup_logging()
        
        # Thread control loop flag for data emission
        self._is_running = False

    def _setup_logging(self):
        """Creates a custom logger for the context that emits signals."""
        class SignalHandler(logging.Handler):
            def __init__(self, signal):
                super().__init__()
                self.signal = signal
                
            def emit(self, record):
                msg = self.format(record)
                self.signal.emit(record.levelname, msg)
                
        logger = logging.getLogger("TestRunnerContext")
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()
            
        handler = SignalHandler(self.on_log)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        self.context.logger = logger
        self.logger = logger

    def set_state(self, new_state: TestState):
        """Updates internal state and emits signal."""
        self.state_machine.set_state(new_state)
        self.on_state_changed.emit(new_state.name)

    def run(self):
        """Main execution thread."""
        self._is_running = True
        
        try:
            # 1. INIT
            self.set_state(TestState.INIT)
            self.test.setup(self.context)
            
            # Start a background task or loop here to emit runtime data periodically
            # We can interleave the test execution and data emission, or emit from test.
            # But the test itself blocks this thread during `run()`. The UI can read via data updates.
            # To provide continuous data updates, we can wrap the test run, or let the test update 
            # runtime_values and we emit them. Since the test loop is single-threaded here, 
            # we will rely on a monitor thread, or let the test emit them, or we emit them 
            # periodically between test calls. A simple approach: start a timer thread.
            
            # 2. RUNNING
            self.set_state(TestState.RUNNING)
            
            # Start data emitter
            import threading
            self.emitter_thread = threading.Thread(target=self._emit_data_loop, daemon=True)
            self.emitter_thread.start()
            
            self.test.run(self.context)
            
            # 3. VERIFY
            self.set_state(TestState.VERIFY)
            self.test.verify(self.context)
            
            # 4. COMPLETE
            self.set_state(TestState.COMPLETE)

        except Exception as e:
            # ERROR handling
            if "cancelled" in str(e).lower():
                self.logger.warning(f"Test cancelled: {str(e)}")
            else:
                self.logger.error(f"Test Error: {str(e)}")
                self.logger.error(traceback.format_exc())
            
            try:
                self.set_state(TestState.ERROR)
            except Exception as transition_error:
                 self.logger.error(f"Failed to transition to ERROR state: {transition_error}")

        finally:
            self._is_running = False
            # CLEANUP (Must happen even on error)
            try:
                self.logger.info("Executing final cleanup...")
                self.test.cleanup(self.context)
            except Exception as e:
                self.logger.error(f"Error during cleanup: {str(e)}")
                
            # If we ended up in ERROR or COMPLETE, transition to IDLE is allowed.
            try:
                # Give UI a moment to process COMPLETE/ERROR before resetting to IDLE if needed,
                # or leave it as COMPLETE/ERROR so the user sees the final state.
                pass 
            except Exception:
                pass

    def _emit_data_loop(self):
        """Continuously emits the context's runtime values while test runs."""
        while self._is_running:
            try:
                # Copy the dict to avoid race conditions
                current_data = dict(self.context.runtime_values)
                self.on_data_update.emit(current_data)
            except Exception:
                pass
            time.sleep(0.5)

    def pause(self):
        """Pauses test execution."""
        if self.state_machine.get_state() == TestState.RUNNING:
            self.context.pause_event.clear()
            self.set_state(TestState.PAUSED)
            self.logger.info("Test paused.")

    def resume(self):
        """Resumes test execution."""
        if self.state_machine.get_state() == TestState.PAUSED:
            self.context.pause_event.set()
            self.set_state(TestState.RUNNING)
            self.logger.info("Test resumed.")

    def cancel(self):
        """Cancels test execution."""
        self.context.cancel_event.set()
        # Ensure it's not blocked by pause
        self.context.pause_event.set()
        self.logger.warning("Cancellation requested...")
        
        # If IDLE, just return (no thread running)
        if self.state_machine.get_state() == TestState.IDLE:
             return
             
        # The thread should catch the cancel_event in the test loop and raise Exception
