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
    on_user_action_required = Signal(str, bool)
    on_status_update = Signal(str)
    on_progress_update = Signal(int)
    on_step_animate = Signal(int, int, int) # start, end, duration_ms
    on_cycle_update = Signal(int, int) # current_cycle, total_cycles
    
    def __init__(self, test_instance: BaseTest, context: TestContext):
        super().__init__()
        self.test = test_instance
        self.context = context
        self.context.test_identifier = getattr(self.test, "test_identifier", "unknown")
        self.context._prompt_callback = self._emit_prompt
        self.context._status_callback = self.on_status_update.emit
        self.context._progress_callback = self.on_progress_update.emit
        self.context._step_callback = self._handle_step_started
        self.context._cycle_callback = self._emit_cycle
        self.state_machine = StateMachine()
        self.failure_reason = None
        
        self.step_ranges = {}
        self._initialize_progress_engine()
        
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
        outcome = "FAIL"
        
        try:
            # 1. INIT
            self.set_state(TestState.INIT)
            self.test.setup(self.context)
            
            # 2. RUNNING
            # Safety Pre-Check before transitioning
            if hasattr(self.context, 'safety_manager') and self.context.safety_manager:
                if not self.context.safety_manager.pre_check(self.context):
                    raise Exception("Safety Pre-Check failed. Aborting test.")
            
            self.set_state(TestState.RUNNING)
            
            # Start data emitter and live monitor
            import threading
            self.emitter_thread = threading.Thread(target=self._emit_data_loop, daemon=True)
            self.emitter_thread.start()
            
            self.test.run(self.context)
            
            # 3. VERIFY
            self.set_state(TestState.VERIFY)
            self.test.verify(self.context)
            
            # 4. COMPLETE
            self.set_state(TestState.COMPLETE)
            
            # Save outcomes
            is_success = self.context.test_results.get("success", True)
            outcome = "PASS" if is_success else "FAIL"
            if not is_success:
                self.failure_reason = self.context.test_results.get("failure_reason", "Test verification check failed.")

        except Exception as e:
            # ERROR handling
            self.failure_reason = str(e)
            if "cancelled" in str(e).lower() or self.context.cancel_event.is_set():
                self.logger.warning(f"Test cancelled: {str(e)}")
                outcome = "CANCELLED"
            else:
                self.logger.error(f"Test Error: {str(e)}")
                self.logger.error(traceback.format_exc())
                outcome = "FAIL"
            
                # Trigger hardware-level emergency stop on actual error
                if hasattr(self.context, 'hardware_service') and self.context.hardware_service:
                    self.logger.warning("Triggering Hardware Emergency Stop due to test error!")
                    self.context.hardware_service.trigger_emergency_stop()
                
            try:
                self.set_state(TestState.ERROR)
            except Exception as transition_error:
                 self.logger.error(f"Failed to transition to ERROR state: {transition_error}")

        finally:
            self._is_running = False
            
            # 5. DB proper closure: Save final result to database
            self._finalize_test_in_db(outcome)
            
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
        """Continuously emits the context's runtime values while test runs and monitors safety."""
        while self._is_running:
            try:
                # 1. Live Safety Monitor
                if hasattr(self.context, 'safety_manager') and self.context.safety_manager:
                    is_safe = self.context.safety_manager.monitor_live(self.context)
                    if not is_safe:
                        self.logger.critical("Live Monitor reported unsafe conditions! Cancelling test.")
                        self.cancel() # Break the main test thread
                
                # Poll MFM Telemetry and store in runtime_values
                hw = self.context.hardware_service
                if hw:
                    telemetry = hw.read_mfm_telemetry()
                    if telemetry:
                        if "voltage" in telemetry:
                            self.context.update_runtime_value("voltage", telemetry["voltage"])
                        if "current" in telemetry:
                            self.context.update_runtime_value("current", telemetry["current"])
                        if "power_factor" in telemetry:
                            self.context.update_runtime_value("power_factor", telemetry["power_factor"])
                        if "active_power" in telemetry:
                            self.context.update_runtime_value("active_power", telemetry["active_power"])
                        
                # 2. Update Data
                # Copy the dict to avoid race conditions
                current_data = dict(self.context.runtime_values)
                current_data["state"] = self.state_machine.get_state().name
                self.on_data_update.emit(current_data)
            except Exception:
                pass
            time.sleep(1.0)

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

    def _initialize_progress_engine(self):
        """Calculates percentage ranges for each test step based on metadata weights."""
        steps = self.test.get_steps()
        if not steps: return
        
        total_weight = sum(s.weight for s in steps)
        if total_weight == 0: return
        
        current_pos = 0.0
        for step in steps:
            # We allow multiple steps with same name (loops), so we store as a list
            step_width = (step.weight / total_weight) * 100
            range_info = (current_pos, current_pos + step_width, step.estimated_duration)
            
            if step.name not in self.step_ranges:
                self.step_ranges[step.name] = []
            self.step_ranges[step.name].append(range_info)
            
            current_pos += step_width
        
        self.step_execution_counts = {name: 0 for name in self.step_ranges}

    def _handle_step_started(self, step_name: str):
        """Processes a step-start notification and emits high-fidelity animation signals."""
        if step_name in self.step_ranges:
            occurence_idx = self.step_execution_counts[step_name]
            ranges = self.step_ranges[step_name]
            range_info = ranges[occurence_idx % len(ranges)]
            
            start_pct, end_pct, duration = range_info
            self.on_step_animate.emit(int(start_pct), int(end_pct), int(duration * 1000))
            
            self.step_execution_counts[step_name] += 1

    def _emit_prompt(self, msg: str, req_input: bool):
        """Helper to safely emit the user prompt from test context."""
        self.on_user_action_required.emit(msg, req_input)
        
    def _emit_cycle(self, current: int, total: int):
        """Helper to safely emit active loop cycle progress to the UI."""
        self.on_cycle_update.emit(current, total)
        
    def resume_from_user(self, user_input: str):
        """Called by UI when user finishes interaction."""
        self.context.user_input_result = user_input
        self.context.user_action_event.set()

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

    def _handle_database_session(self):
        """Resolves meter serial and database row to append/insert without interrupting prompt."""
        if not self.context.database_service:
            self.logger.warning("Database service not available. Skipping DB session management.")
            return

        serial = str(self.context.meter_serial_number).strip()
        if not serial:
            profile = getattr(self.context, "meter_profile", None)
            profile_name = profile.get("name") if profile else None
            serial = f"METER_{profile_name}" if profile_name else "UNKNOWN_METER"
            self.context.meter_serial_number = serial
            self.logger.warning(f"No serial number found in context. Using fallback: {serial}")
        
        test_type = getattr(self.test, "test_identifier", "unknown").lower()
        
        # Check for existing records
        existing_row_id = self.context.database_service.find_latest_incomplete_record(serial, test_type)
        
        if existing_row_id:
            # Automatically append to existing incomplete record
            self.context.db_row_id = existing_row_id
            self.logger.info(f"Automatically appending results to existing incomplete row ID: {existing_row_id} for meter {serial}")
        else:
            # Create new record
            self.context.db_row_id = self.context.database_service.create_new_record(serial)
            self.logger.info(f"Created new row ID: {self.context.db_row_id} for meter {serial}")

    def _finalize_test_in_db(self, outcome: str):
        """Ensures database row is resolved and updated with the final test outcome."""
        try:
            self._handle_database_session()
            if self.context.database_service and self.context.db_row_id:
                test_type = getattr(self.test, "test_identifier", "unknown").lower()
                valid_columns = ['g2', 'g3', 'g5', 'g6', 'g7']
                if test_type in valid_columns:
                    self.context.database_service.update_test_result(self.context.db_row_id, test_type, outcome)
                
                # Update overall results and failure reason
                self.context.database_service.update_test_result(self.context.db_row_id, "overall_results", outcome)
                if self.failure_reason:
                    self.context.database_service.update_test_result(self.context.db_row_id, "failure_reason", self.failure_reason)
                
                # Append measurements to reason so it reflects on the final PDF report
                pf = self.context.test_results.get('calculated_pf')
                curr = self.context.test_results.get('measured_current')
                details_text = []
                if pf is not None: details_text.append(f"PF: {pf:.3f}")
                if curr is not None: details_text.append(f"Current: {curr:.1f} A")
                
                final_reason = self.failure_reason or ""
                if details_text:
                    if final_reason: final_reason += " | "
                    final_reason += "Measurements: " + ", ".join(details_text)
                
                if not final_reason:
                    final_reason = None
                    
                # Check if a sub-test was active and failed
                active_sub = self.context.get_runtime_value("active_sub_test")
                if active_sub and outcome == "FAIL":
                    self.context.database_service.save_test_run_detail(
                        self.context.db_row_id, active_sub, "FAIL", final_reason, is_sub_test=True
                    )
                    self.context.update_runtime_value("active_sub_test", None)

                # Log this test run execution detail
                self.context.database_service.save_test_run_detail(
                    self.context.db_row_id, test_type, outcome, final_reason, is_sub_test=False
                )
                
                self.logger.info(f"Database record updated with final outcome: {outcome}")
        except Exception as e:
            self.logger.error(f"Error during database finalization: {e}")
