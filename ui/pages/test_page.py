from PySide6.QtWidgets import QWidget, QTableWidgetItem
from PySide6.QtCore import Slot, Qt, QPropertyAnimation, QEasingCurve
from ui.pages.ui_test_page import Ui_TestPage

class TestPage(QWidget, Ui_TestPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window # Reference to main window for logging/state
        self.test_runner = None
        
        self._populate_tests()
        self._connect_signals()
        
        # Initial state
        self.btn_done.setEnabled(False)
        self.btn_stop.setEnabled(False)
        self.btn_abort.setEnabled(False)
        self.input_instruction.hide()
        self.btn_done.hide()

        # Apply Premium Styling to Progress Bar
        self._apply_premium_styling()

        # Progress Animation Engine
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.is_milestone_anim = False

    def _connect_signals(self):
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.toggle_pause_resume)
        self.btn_abort.clicked.connect(self.cancel_test)
        self.btn_emergency.clicked.connect(self.main_window.trigger_emergency_stop)
        
    def _populate_tests(self):
        self.list_tests.clear()
        
        # Auto-discover tests
        import os
        import importlib
        import inspect
        from core.test_definitions.base_test import BaseTest
        
        test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "core", "test_definitions")
        self.discovered_tests = {}
        
        if not os.path.exists(test_dir):
            return
            
        for file in os.listdir(test_dir):
            if file.endswith(".py") and file != "__init__.py" and file != "base_test.py":
                module_name = f"core.test_definitions.{file[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and issubclass(obj, BaseTest) and obj is not BaseTest:
                            # Use class name nicely formatted
                            display_name = name.replace("Test", "").replace("([a-z])([A-Z])", r"\1 \2")
                            # basic naive camel case split
                            import re
                            display_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
                            
                            self.discovered_tests[name] = obj
                            self.list_tests.addItem(display_name)
                            self.list_tests.item(self.list_tests.count()-1).setData(Qt.UserRole, name)
                except Exception as e:
                    self.main_window.append_log("ERROR", f"Failed to load test from {file}: {e}")
                    
        self.list_tests.setCurrentRow(0)

    @Slot()
    def start_test(self):
        if self.test_runner and self.test_runner.isRunning():
            return
            
        selected_items = self.list_tests.selectedItems()
        if not selected_items:
            self.main_window.append_log("WARNING", "No test selected.")
            return
            
        test_class_name = selected_items[0].data(Qt.UserRole)
        
        from core.test_engine.test_context import TestContext
        from core.test_engine.test_runner import TestRunner
        context = TestContext(self.device_manager)

        test_class = self.discovered_tests.get(test_class_name)
        if not test_class:
            self.main_window.append_log("ERROR", f"Test class {test_class_name} not found.")
            return
            
        test_instance = test_class()

        self.test_runner = TestRunner(test_instance, context)
        
        self.test_runner.on_state_changed.connect(self.update_test_state)
        self.test_runner.on_log.connect(self.main_window.append_log)
        self.test_runner.on_data_update.connect(self.update_test_data)
        self.test_runner.finished.connect(self.handle_test_finished)
        self.test_runner.on_user_action_required.connect(self.prompt_user_action)
        self.test_runner.on_status_update.connect(self.lbl_instruction.setText)
        self.test_runner.on_step_animate.connect(self.smart_step_animate)
        
        hw_service = self.test_runner.context.hardware_service
        if hw_service:
            hw_service.hardware_status_update.connect(self.main_window.update_hardware_status)
            hw_service.emergency_triggered.connect(self.main_window.handle_emergency_triggered)
            
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_abort.setEnabled(True)
        self.btn_stop.setText("Pause")
        self.lbl_instruction.setText("Test running...")
        self.progress_bar.setValue(0)
        self.test_runner.start()

    @Slot()
    def toggle_pause_resume(self):
        if not self.test_runner: return
        from core.test_engine.state_machine import TestState
        current_state = self.test_runner.state_machine.get_state()
        if current_state == TestState.RUNNING:
            self.test_runner.pause()
            self.btn_stop.setText("Resume")
            self.lbl_instruction.setText("Test Paused.")
        elif current_state == TestState.PAUSED:
            self.test_runner.resume()
            self.btn_stop.setText("Pause")
            self.lbl_instruction.setText("Test running...")
            if self.progress_anim.state() == QPropertyAnimation.State.Paused:
                self.progress_anim.resume()

    @Slot()
    def cancel_test(self):
        if self.test_runner:
            self.test_runner.cancel()
            self.btn_abort.setEnabled(False)
            self.lbl_instruction.setText("Aborting...")

    @Slot(str)
    def update_test_state(self, state_name: str):
        pass
        
    @Slot(dict)
    def update_test_data(self, data: dict):
        v = data.get("voltage", "--")
        i = data.get("current", "--")
        pf = data.get("power_factor", "--")
        state = data.get("state", "RUNNING")
        self.lbl_live_data.setText(f"STATE: {state} | V: {v}V | I: {i}A | PF: {pf}")
        
    @Slot()
    def handle_test_finished(self):
        self.progress_anim.stop()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_abort.setEnabled(False)
        self.btn_done.hide()
        self.input_instruction.hide()
        self.lbl_instruction.setText("Test Complete.")
        self.progress_bar.setValue(100)

    @Slot(str, bool)
    def prompt_user_action(self, message: str, requires_input: bool):
        self.progress_anim.stop() # Freeze animation during user input
        self.lbl_instruction.setText(message)
        if requires_input:
            self.input_instruction.show()
            self.input_instruction.clear()
            self.input_instruction.setEnabled(True)
        else:
            self.input_instruction.hide()
        self.btn_done.show()
        self.btn_done.setEnabled(True)
        # Safely disconnect any previous connections to avoid multiple calls or warnings
        try:
            if self.btn_done.receivers(self.btn_done.clicked) > 0:
                self.btn_done.clicked.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.btn_done.clicked.connect(self.resolve_user_action)

    @Slot()
    def resolve_user_action(self):
        self.btn_done.hide()
        self.input_instruction.hide()
        user_val = self.input_instruction.text()
        if self.progress_anim.state() == QPropertyAnimation.State.Paused:
            self.progress_anim.resume() # Resume the active step animation
        if self.test_runner:
            self.test_runner.resume_from_user(user_val)

    @Slot(int, int, int)
    def smart_step_animate(self, start_val: int, end_val: int, duration_ms: int):
        """Performs a precise, metadata-driven animation for a logical test step."""
        if self.progress_anim.state() == QPropertyAnimation.State.Running:
            self.progress_anim.stop()
            
        self.progress_anim.setDuration(duration_ms)
        self.progress_anim.setStartValue(start_val)
        self.progress_anim.setEndValue(end_val)
        # Use Linear for background flows, InOutQuad for snappy transitions
        self.progress_anim.setEasingCurve(QEasingCurve.Type.Linear if duration_ms > 3000 else QEasingCurve.Type.InOutQuad)
        self.progress_anim.start()

    def _apply_premium_styling(self):
        """Applies advanced CSS for a high-fidelity look."""
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #CBD5E1;
                border-radius: 12px;
                background-color: #F1F5F9;
                text-align: center;
                color: transparent; /* Hide text for a cleaner look */
                height: 24px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3B82F6, stop:0.5 #60A5FA, stop:1 #3B82F6
                );
                border-radius: 10px;
                margin: 2px;
            }
        """)
        # Note: In a real app, we might add a QGraphicsDropShadowEffect here 
        # to the progress bar for the 'glow' mentioned by the user.
