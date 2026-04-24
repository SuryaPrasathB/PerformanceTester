from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot, Qt
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

    def _connect_signals(self):
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.toggle_pause_resume)
        self.btn_abort.clicked.connect(self.cancel_test)
        self.btn_emergency.clicked.connect(self.main_window.trigger_emergency_stop)
        
    def _populate_tests(self):
        self.list_tests.addItem("G2 Normal Operation Test")
        self.list_tests.setCurrentRow(0)

    @Slot()
    def start_test(self):
        if self.test_runner and self.test_runner.isRunning():
            return
            
        selected_items = self.list_tests.selectedItems()
        if not selected_items:
            self.main_window.append_log("WARNING", "No test selected.")
            return
            
        test_name = selected_items[0].text()
        if test_name == "G2 Normal Operation Test":
            from core.test_engine.test_context import TestContext
            from core.test_definitions.g2_normal_operation import G2NormalOperationTest
            from core.test_engine.test_runner import TestRunner
            
            context = TestContext(self.device_manager)
            test_instance = G2NormalOperationTest()
            self.test_runner = TestRunner(test_instance, context)
            
            self.test_runner.on_state_changed.connect(self.update_test_state)
            self.test_runner.on_log.connect(self.main_window.append_log)
            self.test_runner.on_data_update.connect(self.update_test_data)
            self.test_runner.finished.connect(self.on_test_finished)
            self.test_runner.on_user_action_required.connect(self.prompt_user_action)
            
            hw_service = self.test_runner.context.hardware_service
            if hw_service:
                hw_service.hardware_status_update.connect(self.main_window.update_hardware_status)
                hw_service.emergency_triggered.connect(self.main_window.on_emergency_triggered)
            
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
    def on_test_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_abort.setEnabled(False)
        self.btn_done.hide()
        self.input_instruction.hide()
        self.lbl_instruction.setText("Test Complete.")
        self.progress_bar.setValue(100)

    @Slot(str, bool)
    def prompt_user_action(self, message: str, requires_input: bool):
        self.lbl_instruction.setText(message)
        if requires_input:
            self.input_instruction.show()
            self.input_instruction.clear()
            self.input_instruction.setEnabled(True)
        else:
            self.input_instruction.hide()
        self.btn_done.show()
        self.btn_done.setEnabled(True)
        try: self.btn_done.clicked.disconnect()
        except: pass
        self.btn_done.clicked.connect(self.resolve_user_action)

    @Slot()
    def resolve_user_action(self):
        self.btn_done.hide()
        self.input_instruction.hide()
        user_val = self.input_instruction.text()
        if self.test_runner:
            self.test_runner.resume_from_user(user_val)
