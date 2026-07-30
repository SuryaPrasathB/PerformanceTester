from PySide6.QtWidgets import QWidget, QTableWidgetItem
from PySide6.QtCore import Slot, Qt, QPropertyAnimation, QEasingCurve, QTimer
from ui.pages.ui_test_page import Ui_TestPage

class TestPage(QWidget, Ui_TestPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window # Reference to main window for logging/state
        self.test_runner = None
        self.active_validation_rule = None
        
        self._setup_meter_profile_ui()
        self.refresh_meter_profiles()
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

        # Initial live data display
        self.lbl_live_data.setText("STATE: IDLE | V: -- V | I: -- A | PF: --")

        # Progress Animation Engine
        self.progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.is_milestone_anim = False
        self.dynamic_cards = []
        self.frame_graphs_container.hide()
        self.horizontalLayout_graphs.setAlignment(Qt.AlignCenter)

        # Create cycles container frame programmatically
        from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar
        from PySide6.QtCore import QSize
        
        self.frame_cycles_container = QFrame(self.widget_center_container)
        self.frame_cycles_container.setObjectName("frame_cycles_container")
        self.frame_cycles_container.setMinimumSize(QSize(16777215, 90))
        self.frame_cycles_container.setMaximumSize(QSize(16777215, 90))
        self.frame_cycles_container.setFrameShape(QFrame.StyledPanel)
        
        # Horizontal layout for the components
        self.horizontalLayout_cycles = QHBoxLayout(self.frame_cycles_container)
        self.horizontalLayout_cycles.setSpacing(20)
        self.horizontalLayout_cycles.setObjectName("horizontalLayout_cycles")
        self.horizontalLayout_cycles.setContentsMargins(20, 10, 20, 10)
        
        # Left side: Cycle Info Labels (Vertical)
        self.verticalLayout_cycle_info = QVBoxLayout()
        self.verticalLayout_cycle_info.setSpacing(4)
        self.verticalLayout_cycle_info.setObjectName("verticalLayout_cycle_info")
        
        self.lbl_cycle_header = QLabel("TEST CYCLE PROGRESS", self.frame_cycles_container)
        self.lbl_cycle_header.setObjectName("lbl_cycle_header")
        
        self.lbl_cycle_counter = QLabel("Cycle 0 of 0", self.frame_cycles_container)
        self.lbl_cycle_counter.setObjectName("lbl_cycle_counter")
        
        self.verticalLayout_cycle_info.addWidget(self.lbl_cycle_header)
        self.verticalLayout_cycle_info.addWidget(self.lbl_cycle_counter)
        self.horizontalLayout_cycles.addLayout(self.verticalLayout_cycle_info)
        
        # Center: Progress Bar
        self.cycle_progress_bar = QProgressBar(self.frame_cycles_container)
        self.cycle_progress_bar.setObjectName("cycle_progress_bar")
        self.cycle_progress_bar.setMinimumSize(QSize(0, 16))
        self.cycle_progress_bar.setMaximumSize(QSize(16777215, 16))
        self.cycle_progress_bar.setTextVisible(False)
        self.horizontalLayout_cycles.addWidget(self.cycle_progress_bar, stretch=1)
        
        # Right side: Percentage text
        self.lbl_cycle_percentage = QLabel("0%", self.frame_cycles_container)
        self.lbl_cycle_percentage.setObjectName("lbl_cycle_percentage")
        self.lbl_cycle_percentage.setMinimumSize(QSize(60, 0))
        self.lbl_cycle_percentage.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.horizontalLayout_cycles.addWidget(self.lbl_cycle_percentage)
        
        self.frame_cycles_container.hide()
        
        # Smooth Cycle Progress
        self.cycle_progress_anim = QPropertyAnimation(self.cycle_progress_bar, b"value")
        self.cycle_progress_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Insert into the vertical center layout right after the instructions card
        instr_idx = self.verticalLayout_center.indexOf(self.frame_instruction)
        self.verticalLayout_center.insertWidget(instr_idx + 1, self.frame_cycles_container)

        # Dynamic validation error label
        from PySide6.QtWidgets import QLabel
        self.lbl_validation_error = QLabel("", self.frame_instruction)
        self.lbl_validation_error.setObjectName("lbl_validation_error")
        self.lbl_validation_error.setAlignment(Qt.AlignCenter)
        self.lbl_validation_error.setStyleSheet("color: #EF4444; font-size: 14px; font-weight: bold; margin-top: 4px;")
        self.lbl_validation_error.hide()
        
        # Insert error label right below the input layout (before progress_bar)
        pbar_idx = self.verticalLayout_instr.indexOf(self.progress_bar)
        self.verticalLayout_instr.insertWidget(pbar_idx, self.lbl_validation_error)

    def _connect_signals(self):
        self.btn_start.clicked.connect(self.start_test)
        self.btn_stop.clicked.connect(self.toggle_pause_resume)
        self.btn_abort.clicked.connect(self.cancel_test)
        self.btn_emergency.clicked.connect(self.main_window.trigger_emergency_stop)
        self.input_instruction.returnPressed.connect(self.handle_return_pressed)
        self.input_instruction.textChanged.connect(self.validate_input)
        
    def _setup_meter_profile_ui(self):
        from PySide6.QtWidgets import QComboBox, QLabel, QLineEdit
        from services.profile_manager import ProfileManager
        
        self.lbl_meter_profile = QLabel("Meter Profile", self.frame_sidebar)
        self.lbl_meter_profile.setObjectName("lbl_section_title")
        
        self.cmb_meter_profile = QComboBox(self.frame_sidebar)
        
        self.input_serial_number = QLineEdit(self.frame_sidebar)
        self.input_serial_number.setPlaceholderText("Enter Meter Serial Number")
        self.input_serial_number.setStyleSheet("min-height: 28px; padding: 4px 16px;")
        
        self.verticalLayout_sidebar.insertWidget(0, self.lbl_meter_profile)
        self.verticalLayout_sidebar.insertWidget(1, self.cmb_meter_profile)
        self.verticalLayout_sidebar.insertWidget(2, self.input_serial_number)
        
        self.profile_manager = ProfileManager()
        self.cmb_meter_profile.currentIndexChanged.connect(self._on_meter_profile_changed)

    def refresh_meter_profiles(self):
        self.cmb_meter_profile.blockSignals(True)
        # Store current text/name if possible to re-select it
        current_name = self.cmb_meter_profile.currentText()
        self.cmb_meter_profile.clear()
        
        profiles = self.profile_manager.get_all_profiles()
        
        for profile in profiles:
            self.cmb_meter_profile.addItem(f"{profile.get('name')} ({profile.get('communication_mode')})", profile)
            
        self.cmb_meter_profile.blockSignals(False)
        
        # Try to restore previous selection
        index_to_select = 0
        for i in range(self.cmb_meter_profile.count()):
            if self.cmb_meter_profile.itemText(i) == current_name:
                index_to_select = i
                break
                
        if self.cmb_meter_profile.count() > 0:
            self.cmb_meter_profile.setCurrentIndex(index_to_select)
            self._on_meter_profile_changed(index_to_select)

    @Slot(int)
    def _on_meter_profile_changed(self, index):
        profile = self.cmb_meter_profile.currentData()
        if not profile:
            return
        mode = profile.get("communication_mode", "").lower()
        if mode:
            self.device_manager.switch_device_type("EnergyMeter1", mode)
 
    def _populate_tests(self):
        self.list_tests.clear()
        self.discovered_tests = {}
        
        # Use a static registry instead of filesystem auto-discovery.
        # Filesystem scanning fails in frozen PyInstaller builds because .py files
        # are compiled to bytecode inside the archive, not present as loose files.
        import re
        try:
            from core.test_definitions.test_registry import REGISTERED_TESTS
        except ImportError:
            self.main_window.append_log("ERROR", "Failed to import test registry.")
            return
            
        for test_class in REGISTERED_TESTS:
            name = test_class.__name__
            # Camel-case split for display (also splits after numbers like G2, G3)
            display_name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
            
            self.discovered_tests[name] = test_class
            self.list_tests.addItem(display_name)
            self.list_tests.item(self.list_tests.count()-1).setData(Qt.UserRole, name)
                    
        self.list_tests.setCurrentRow(0)

    @Slot()
    def start_test(self):
        if self.test_runner and self.test_runner.isRunning():
            return
            
        selected_items = self.list_tests.selectedItems()
        if not selected_items:
            self.main_window.append_log("WARNING", "No test selected.")
            return
            
        serial_number = self.input_serial_number.text().strip()
        if not serial_number:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Validation Error", "Please enter a Meter Serial Number before starting the test.")
            return
            
        test_class_name = selected_items[0].data(Qt.UserRole)
        
        from core.test_engine.test_context import TestContext
        from core.test_engine.test_runner import TestRunner
        context = TestContext(self.device_manager)
        
        context.meter_serial_number = serial_number
        
        selected_profile = self.cmb_meter_profile.currentData()
        if selected_profile:
            context.meter_profile = selected_profile
            
            # Apply dynamic DLMS settings to the driver before the test begins
            mode = selected_profile.get("communication_mode", "").lower()
            drv = self.device_manager.drivers.get("EnergyMeter1")
            
            if mode == "dlms" and drv and drv.__class__.__name__ == "DlmsDriver":
                dlms_settings = selected_profile.get("dlms_settings", {})
                if dlms_settings:
                    self.main_window.log_message(f"Applying DLMS profile settings to EnergyMeter1...")
                    drv.apply_profile_settings(dlms_settings)

        test_class = self.discovered_tests.get(test_class_name)
        if not test_class:
            self.main_window.append_log("ERROR", f"Test class {test_class_name} not found.")
            return
            
        test_instance = test_class()

        # Check if test requires PicoScope and if PicoScope is connected
        if getattr(test_instance, "requires_picoscope", False):
            pico_drv = self.device_manager.drivers.get("PicoScope1")
            if not pico_drv or not pico_drv.is_connected:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.critical(
                    self, 
                    "PicoScope Not Connected", 
                    f"The selected test ({test_instance.name if hasattr(test_instance, 'name') else test_class_name}) requires a PicoScope oscilloscope.\n\n"
                    "PicoScope is currently not connected. Please connect the PicoScope device before starting this test."
                )
                self.main_window.append_log("ERROR", f"Cannot start {test_class_name}: PicoScope is not connected.")
                return

        # Clear existing waveform cards
        if hasattr(self, 'dynamic_cards'):
            for card in self.dynamic_cards:
                self.horizontalLayout_graphs.removeWidget(card)
                card.deleteLater()
        self.dynamic_cards = []
        self.lbl_graphs_placeholder.show()
        self.frame_graphs_container.hide()
        self.frame_cycles_container.hide()

        self.test_runner = TestRunner(test_instance, context)
        
        self.test_runner.on_state_changed.connect(self.update_test_state)
        self.test_runner.on_log.connect(self.main_window.append_log)
        self.test_runner.on_data_update.connect(self.update_test_data)
        self.test_runner.finished.connect(self.handle_test_finished)
        self.test_runner.on_user_action_required.connect(self.prompt_user_action)
        self.test_runner.on_status_update.connect(self.update_status_text)
        self.test_runner.on_step_animate.connect(self.smart_step_animate)
        self.test_runner.on_cycle_update.connect(self.update_cycle_progress)
        self.test_runner.on_power_failure.connect(self.handle_power_failure)
        
        hw_service = self.test_runner.context.hardware_service
        if hw_service:
            hw_service.hardware_status_update.connect(self.main_window.update_hardware_status)
            hw_service.emergency_triggered.connect(self.main_window.handle_emergency_triggered)
            hw_service.waveform_captured.connect(self.add_waveform_card)
            
            # The hardware service initializes inside TestContext before we connect signals.
            # Manually trigger a UI update to clear any previous emergency state.
            self.main_window.update_hardware_status("System", "Initialization Complete")
            
        self.cmb_meter_profile.setEnabled(False)
        self.list_tests.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_abort.setEnabled(True)
        self.btn_stop.setText("Pause")
        self.update_status_text("Test Status: Running...")
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
            self.update_status_text("Test Status: Paused")
        elif current_state == TestState.PAUSED:
            self.test_runner.resume()
            self.btn_stop.setText("Pause")
            self.update_status_text("Test Status: Running...")
            if self.progress_anim.state() == QPropertyAnimation.State.Paused:
                self.progress_anim.resume()

    @Slot(str)
    def handle_power_failure(self, message: str):
        from PySide6.QtWidgets import QMessageBox
        self.update_status_text("Test Status: Paused (Power Cut)")
        self.btn_stop.setText("Resume")
        QMessageBox.warning(
            self,
            "Power Cut Detected",
            message
        )

    @Slot()
    def cancel_test(self):
        if self.test_runner:
            self.test_runner.cancel()
            self.btn_abort.setEnabled(False)
            self.update_status_text("Test Status: Aborting...")

    @Slot(str)
    def update_test_state(self, state_name: str):
        pass
        
    @Slot(dict)
    def update_test_data(self, data: dict):
        v = data.get("voltage", "--")
        i = data.get("current", "--")
        pf = data.get("power_factor", "--")
        state = data.get("state", "RUNNING")
        
        v_str = f"{v:.1f}" if isinstance(v, (int, float)) else str(v)
        
        is_g7 = False
        if self.test_runner and getattr(self.test_runner.test, "test_identifier", "").lower() == "g7":
            is_g7 = True
            
        if isinstance(i, (int, float)):
            if is_g7:
                i_ma = i * 1000.0
                i_str = f"{i_ma:.1f}mA"
            else:
                i_str = f"{i:.3f}A"
        else:
            i_str = f"{str(i)}mA" if is_g7 else f"{str(i)}A"
            
        pf_str = f"{pf:.2f}" if isinstance(pf, (int, float)) else str(pf)
        
        self.lbl_live_data.setText(f"STATE: {state} | V: {v_str}V | I: {i_str} | PF: {pf_str}")


        
    @Slot(str)
    def update_status_text(self, text: str):
        self.lbl_instruction.setStyleSheet("")
        
        is_dark = getattr(self.main_window, "current_theme", "light") == "dark"
        sec_color = "#94A3B8" if is_dark else "#64748B"
        title_color = "#38BDF8" if is_dark else "#2563EB"
        
        # Check if the test is running. If not, use simpler full text formatting
        if not (self.test_runner and self.test_runner.isRunning()):
            html = f"""
            <div align='center' style='line-height: 140%;'>
                <span style='font-size: 24px; color: {title_color}; font-weight: 600;'>{text}</span>
            </div>
            """
            self.lbl_instruction.setText(html)
            return
            
        # Parse status text into Title: Details
        if ":" in text:
            title, details = text.split(":", 1)
            title_text = title.strip().upper()
            details_text = details.strip()
        else:
            title_text = "ACTIVE OPERATION"
            details_text = text.strip()
            
        # Give countdown wait operations extra prominent styling
        if "WAIT" in title_text or "DELAY" in title_text:
            title_color = "#F59E0B" # Amber/Orange for waiting
            title_text = "COUNTDOWN DELAY"
            
        html = f"""
        <div align='center' style='line-height: 150%;'>
            <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
            <span style='font-size: 30px; color: {title_color}; font-weight: 800; letter-spacing: 0.5px;'>{details_text}</span>
        </div>
        """
        self.lbl_instruction.setText(html)

    @Slot()
    def handle_test_finished(self):
        self.lbl_live_data.setText("STATE: IDLE | V: -- V | I: -- A | PF: --")
        self.progress_anim.stop()
        self.cmb_meter_profile.setEnabled(True)
        self.list_tests.setEnabled(True)
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_abort.setEnabled(False)
        self.btn_done.hide()
        self.input_instruction.hide()
        self.progress_bar.setValue(100)
        self.frame_cycles_container.hide()
        self.cycle_progress_anim.stop()
        
        if not self.test_runner:
            is_dark = getattr(self.main_window, "current_theme", "light") == "dark"
            sec_color = "#94A3B8" if is_dark else "#64748B"
            html = f"""
            <div align='center' style='line-height: 140%;'>
                <span style='font-size: 14px; color: {sec_color}; font-weight: bold; letter-spacing: 1px;'>TEST SEQUENCE ENDED</span><br>
                <span style='font-size: 34px; color: #10B981; font-weight: 800; letter-spacing: 0.5px;'>COMPLETE</span>
            </div>
            """
            self.lbl_instruction.setText(html)
            self.lbl_instruction.setStyleSheet("")
            return
            
        from core.test_engine.state_machine import TestState
        state = self.test_runner.state_machine.get_state()
        serial = str(self.test_runner.context.meter_serial_number).strip() if self.test_runner.context.meter_serial_number else "UNKNOWN"
        
        is_dark = getattr(self.main_window, "current_theme", "light") == "dark"
        sec_color = "#94A3B8" if is_dark else "#64748B"
        text_color = "#F8FAFC" if is_dark else "#0F172A"
        
        # Determine result and styling
        if state == TestState.COMPLETE:
            is_success = self.test_runner.context.test_results.get("success", True)
            result = "PASS" if is_success else "FAIL"
            color = "#10B981" if is_success else "#EF4444"
        elif state == TestState.ERROR:
            failure_reason = getattr(self.test_runner, "failure_reason", "") or ""
            if self.test_runner.context.cancel_event.is_set() and "cancelled" in str(failure_reason).lower():
                result = "CANCELLED"
                color = "#F59E0B" # Amber/Orange
            else:
                result = "FAIL"
                color = "#EF4444" # Red
        else:
            result = "INCOMPLETE"
            color = "#64748B" # Slate
            
        calculated_pf_str = ""
        measured_curr_str = ""
        if self.test_runner and isinstance(self.test_runner.context.test_results, dict):
            test_id = getattr(self.test_runner.test, "test_identifier", "unknown").lower()
            if test_id != "g5":
                calc_pf = self.test_runner.context.test_results.get("calculated_pf")
                if calc_pf is not None:
                    calculated_pf_str = f"<br><span style='font-size: 16px; color: {text_color};'>Calculated PF: <span style='font-weight: bold; color: #10B981;'>{calc_pf:.3f}</span></span>"
                
                meas_curr = self.test_runner.context.test_results.get("measured_current")
                if meas_curr is not None:
                    measured_curr_str = f"<br><span style='font-size: 16px; color: {text_color};'>Measured Current: <span style='font-weight: bold; color: #F59E0B;'>{meas_curr:.1f} A</span></span>"
                
        failure_reason_str = ""
        if result != "PASS" and self.test_runner and getattr(self.test_runner, "failure_reason", None):
            reason = self.test_runner.failure_reason
            failure_reason_str = f"<br><br><span style='font-size: 14px; color: {sec_color};'>Reason: </span><span style='font-size: 14px; color: #EF4444;'>{reason}</span>"
        
        html = f"""
        <div align='center' style='line-height: 140%;'>
            <span style='font-size: 14px; color: {sec_color}; font-weight: bold; letter-spacing: 1px;'>TEST SEQUENCE ENDED</span><br>
            <span style='font-size: 34px; color: {color}; font-weight: 800; letter-spacing: 0.5px;'>{result}</span><br>
            <span style='font-size: 16px; color: {text_color};'>Meter Serial: <span style='font-weight: bold;'>{serial}</span></span>{calculated_pf_str}{measured_curr_str}{failure_reason_str}
        </div>
        """
        self.lbl_instruction.setText(html)
        self.lbl_instruction.setStyleSheet("")


    @Slot(str, bool)
    def prompt_user_action(self, message: str, requires_input: bool):
        self.lbl_instruction.setStyleSheet("") # Clear outcome color
        self.progress_anim.stop() # Freeze animation during user input
        
        if self.cycle_progress_anim.state() == QPropertyAnimation.State.Running:
            self.cycle_progress_anim.pause()
            self._cycle_anim_paused = True
        else:
            self._cycle_anim_paused = False
        
        is_dark = getattr(self.main_window, "current_theme", "light") == "dark"
        sec_color = "#EAB308" if is_dark else "#D97706" # Amber/Orange for alerts
        title_text = "USER INPUT REQUIRED" if requires_input else "ACTION REQUIRED"
        text_color = "#F8FAFC" if is_dark else "#0F172A"
        
        # Replace python newlines with HTML breaks since this is rendered as rich text
        formatted_message = message.replace('\n', '<br>')
        
        html_prompt = f"""
        <div align='center' style='line-height: 140%;'>
            <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
            <span style='font-size: 28px; color: {text_color}; font-weight: 800;'>{formatted_message}</span>
        </div>
        """
        self.lbl_instruction.setText(html_prompt)
        
        # Clear any existing dynamic buttons
        if hasattr(self, 'dynamic_buttons'):
            for btn in self.dynamic_buttons:
                self.horizontalLayout_input.removeWidget(btn)
                btn.deleteLater()
        self.dynamic_buttons = []
 
        if requires_input:
            if "U2 or U3" in message or "Select meter category" in message.lower():
                self.input_instruction.hide()
                self.btn_done.hide()
                
                html_cat = f"""
                <div align='center' style='line-height: 140%;'>
                    <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
                    <span style='font-size: 28px; color: {text_color}; font-weight: 800;'>Select Meter Category</span>
                </div>
                """
                self.lbl_instruction.setText(html_cat)
                
                from PySide6.QtWidgets import QPushButton
                btn_u2 = QPushButton("U2")
                btn_u2.setMinimumSize(120, 45)
                btn_u2.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #3B82F6; color: white; border-radius: 8px;")
                btn_u2.clicked.connect(lambda checked=False, val="U2": self.resolve_user_action(val))
                
                btn_u3 = QPushButton("U3")
                btn_u3.setMinimumSize(120, 45)
                btn_u3.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #3B82F6; color: white; border-radius: 8px;")
                btn_u3.clicked.connect(lambda checked=False, val="U3": self.resolve_user_action(val))
                
                idx = self.horizontalLayout_input.indexOf(self.btn_done)
                self.horizontalLayout_input.insertWidget(idx + 1, btn_u2)
                self.horizontalLayout_input.insertWidget(idx + 2, btn_u3)
                
                self.dynamic_buttons.extend([btn_u2, btn_u3])
            elif "RUN G7" in message:
                self.input_instruction.hide()
                self.btn_done.hide()
                
                html_cat = f"""
                <div align='center' style='line-height: 140%;'>
                    <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
                    <span style='font-size: 28px; color: {text_color}; font-weight: 800;'>{message}</span>
                </div>
                """
                self.lbl_instruction.setText(html_cat)
                
                from PySide6.QtWidgets import QPushButton
                btn_skip = QPushButton("Skip")
                btn_skip.setMinimumSize(120, 45)
                btn_skip.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #94A3B8; color: white; border-radius: 8px;")
                btn_skip.clicked.connect(lambda checked=False, val="Skip": self.resolve_user_action(val))
                
                btn_continue = QPushButton("Continue")
                btn_continue.setMinimumSize(120, 45)
                btn_continue.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #3B82F6; color: white; border-radius: 8px;")
                btn_continue.clicked.connect(lambda checked=False, val="Continue": self.resolve_user_action(val))
                
                idx = self.horizontalLayout_input.indexOf(self.btn_done)
                self.horizontalLayout_input.insertWidget(idx + 1, btn_skip)
                self.horizontalLayout_input.insertWidget(idx + 2, btn_continue)
                
                self.dynamic_buttons.extend([btn_skip, btn_continue])
            elif "pass or fail" in message.lower():
                self.input_instruction.hide()
                self.btn_done.hide()
                
                html_cat = f"""
                <div align='center' style='line-height: 140%;'>
                    <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
                    <span style='font-size: 28px; color: {text_color}; font-weight: 800;'>{message}</span>
                </div>
                """
                self.lbl_instruction.setText(html_cat)
                
                from PySide6.QtWidgets import QPushButton
                btn_pass = QPushButton("Pass")
                btn_pass.setMinimumSize(120, 45)
                btn_pass.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #10B981; color: white; border-radius: 8px;")
                btn_pass.clicked.connect(lambda checked=False, val="Pass": self.resolve_user_action(val))
                
                btn_fail = QPushButton("Fail")
                btn_fail.setMinimumSize(120, 45)
                btn_fail.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #EF4444; color: white; border-radius: 8px;")
                btn_fail.clicked.connect(lambda checked=False, val="Fail": self.resolve_user_action(val))
                
                idx = self.horizontalLayout_input.indexOf(self.btn_done)
                self.horizontalLayout_input.insertWidget(idx + 1, btn_pass)
                self.horizontalLayout_input.insertWidget(idx + 2, btn_fail)
                
                self.dynamic_buttons.extend([btn_pass, btn_fail])
            elif "review cycles" in message.lower():
                self.input_instruction.hide()
                self.btn_done.hide()
                
                html_cat = f"""
                <div align='center' style='line-height: 140%;'>
                    <span style='font-size: 13px; color: {sec_color}; font-weight: bold; letter-spacing: 1.5px;'>{title_text}</span><br>
                    <span style='font-size: 28px; color: {text_color}; font-weight: 800;'>{message}</span>
                </div>
                """
                self.lbl_instruction.setText(html_cat)
                
                from PySide6.QtWidgets import QPushButton
                btn_continue = QPushButton("Continue")
                btn_continue.setMinimumSize(120, 45)
                btn_continue.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #3B82F6; color: white; border-radius: 8px;")
                btn_continue.clicked.connect(lambda checked=False, val="Continue": self.resolve_user_action(val))
                
                idx = self.horizontalLayout_input.indexOf(self.btn_done)
                self.horizontalLayout_input.insertWidget(idx + 1, btn_continue)
                
                self.dynamic_buttons.extend([btn_continue])

                if hasattr(self, 'dynamic_cards'):
                    for card in self.dynamic_cards:
                        if hasattr(card, 'set_review_mode'):
                            card.set_review_mode(True)
            else:
                self.input_instruction.show()
                self.input_instruction.clear()
                self.input_instruction.setEnabled(True)
                self.btn_done.show()
                self.btn_done.setEnabled(True)
                
                # Active validation setup
                self.active_validation_rule = self.parse_validation_rules(message)
                self.validate_input()
                
                try:
                    if self.btn_done.receivers(self.btn_done.clicked) > 0:
                        self.btn_done.clicked.disconnect()
                except (TypeError, RuntimeError):
                    pass
                self.btn_done.clicked.connect(lambda: self.resolve_user_action())
        else:
            self.active_validation_rule = None
            self.lbl_validation_error.hide()
            self.set_input_validation_style(True)
            self.input_instruction.hide()
            self.btn_done.show()
            self.btn_done.setEnabled(True)
            try:
                if self.btn_done.receivers(self.btn_done.clicked) > 0:
                    self.btn_done.clicked.disconnect()
            except (TypeError, RuntimeError):
                pass
            self.btn_done.clicked.connect(lambda: self.resolve_user_action())

    @Slot()
    @Slot(str)
    def resolve_user_action(self, user_val=None):
        self.btn_done.hide()
        self.input_instruction.hide()
        self.lbl_validation_error.hide()
        self.set_input_validation_style(True)
        self.active_validation_rule = None
        
        if hasattr(self, 'dynamic_buttons'):
            for btn in self.dynamic_buttons:
                btn.hide()
                
        if hasattr(self, 'dynamic_cards'):
            for card in self.dynamic_cards:
                if hasattr(card, 'set_review_mode'):
                    card.set_review_mode(False)
                
        # Handle default parameter or boolean click value
        if user_val is None or isinstance(user_val, bool):
            user_val = self.input_instruction.text()
            
        if self.progress_anim.state() == QPropertyAnimation.State.Paused:
            self.progress_anim.resume() # Resume the active step animation
            
        if getattr(self, '_cycle_anim_paused', False):
            self.cycle_progress_anim.resume()
            self._cycle_anim_paused = False
            
        if self.test_runner:
            self.test_runner.resume_from_user(str(user_val))
            
    def handle_return_pressed(self):
        if self.btn_done.isEnabled() and self.btn_done.isVisible():
            self.btn_done.click()

    def parse_validation_rules(self, message: str):
        """Parses the message to extract validation rules."""
        import re
        message_lower = message.lower()
        
        # Look for range boundaries like "between 10-60 secs", "10 to 60", "10-60"
        range_match = re.search(r'between\s+(\d+(?:\.\d+)?)\s*(?:-|to|and)\s*(\d+(?:\.\d+)?)', message, re.IGNORECASE)
        if not range_match:
            range_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:-|to)\s*(\d+(?:\.\d+)?)', message, re.IGNORECASE)
            
        if range_match:
            try:
                min_val = float(range_match.group(1))
                max_val = float(range_match.group(2))
                return {
                    "type": "range",
                    "min": min(min_val, max_val),
                    "max": max(min_val, max_val),
                    "original_text": range_match.group(0)
                }
            except ValueError:
                pass
                
        if any(keyword in message_lower for keyword in ["energy", "value", "current", "voltage", "resistance", "limit", "time", "secs"]):
            if "serial number" not in message_lower:
                return {"type": "numeric"}
                
        return {"type": "non_empty"}

    @Slot()
    def validate_input(self):
        if not self.input_instruction.isVisible():
            return
            
        text = self.input_instruction.text().strip()
        rule = self.active_validation_rule
        
        if not rule:
            self.set_input_validation_style(True)
            self.lbl_validation_error.hide()
            self.btn_done.setEnabled(True)
            return

        is_valid = True
        error_msg = ""
        
        if not text:
            is_valid = False
            error_msg = "Input cannot be empty."
            # Do not show red border/error immediately on empty state if it's the initial prompt state
            self.set_input_validation_style(True)
            self.lbl_validation_error.hide()
            self.btn_done.setEnabled(False)
            return
        elif rule["type"] == "range":
            try:
                val = float(text)
                if val < rule["min"] or val > rule["max"]:
                    is_valid = False
                    error_msg = f"Value must be between {rule['min']} and {rule['max']}."
            except ValueError:
                is_valid = False
                error_msg = f"Please enter a valid number between {rule['min']} and {rule['max']}."
        elif rule["type"] == "numeric":
            try:
                val = float(text)
                if val < 0:
                    is_valid = False
                    error_msg = "Value must be a positive number."
            except ValueError:
                is_valid = False
                error_msg = "Please enter a valid number."
        elif rule["type"] == "non_empty":
            if not text:
                is_valid = False
                error_msg = "Please enter a value."
                
        if is_valid:
            self.set_input_validation_style(True)
            self.lbl_validation_error.hide()
            self.btn_done.setEnabled(True)
        else:
            self.set_input_validation_style(False)
            self.lbl_validation_error.setText(f"⚠️ {error_msg}")
            self.lbl_validation_error.show()
            self.btn_done.setEnabled(False)
            
            # Show tooltip popup near input field
            from PySide6.QtWidgets import QToolTip
            from PySide6.QtCore import QPoint
            tooltip_pos = self.input_instruction.mapToGlobal(QPoint(0, -self.input_instruction.height()))
            QToolTip.showText(tooltip_pos, f"<span style='color: #EF4444; font-weight: bold;'>Validation Error:</span><br>{error_msg}", self.input_instruction)

    def set_input_validation_style(self, is_valid: bool):
        is_dark = getattr(self.main_window, "current_theme", "light") == "dark"
        
        if is_valid:
            if self.input_instruction.text().strip():
                border_color = "#10B981"
                bg_color = "#ECFDF5" if not is_dark else "#062F21"
            else:
                border_color = "#6366F1" if is_dark else "#3B82F6"
                bg_color = "#1E293B" if is_dark else "#FFFFFF"
        else:
            border_color = "#EF4444"
            bg_color = "#FEF2F2" if not is_dark else "#451A1A"
            
        text_color = "#F8FAFC" if is_dark else "#0F172A"
        
        self.input_instruction.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 4px 16px;
                font-size: 16px;
                background-color: {bg_color};
                color: {text_color};
                min-height: 35px;
            }}
        """)

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

    @Slot(str, list, int, int)
    def add_waveform_card(self, name: str, data: list, timebase: int, range_val: int):
        """Appends a newly captured waveform card to the horizontal layout."""
        # Hide placeholder label when graphs start appearing
        self.lbl_graphs_placeholder.hide()
        
        # Determine current test identifier
        test_id = "unknown"
        if self.test_runner:
            test_id = getattr(self.test_runner.test, "test_identifier", "unknown").lower()
            
        from ui.widgets.waveform_card import WaveformCard
        card = WaveformCard(name, data, timebase, range_val, self.frame_graphs_container, test_id=test_id)
        card.override_requested.connect(self.handle_override_requested)
        card.redo_requested.connect(self.handle_redo_requested)
        
        # Helper to save full resolution graph
        def save_full_waveform_image():
            session_id = getattr(self.test_runner.context, "db_row_id", None) if self.test_runner else None
            if session_id:
                import os
                graphs_dir = "logs/graphs"
                os.makedirs(graphs_dir, exist_ok=True)
                safe_name = name.replace(" ", "_").lower()
                file_path = os.path.join(graphs_dir, f"session_{session_id}_{test_id}_{safe_name}.png")
                
                from ui.widgets.waveform_graph import WaveformGraph
                temp_graph = WaveformGraph()
                temp_graph.setData(data, None, timebase, range_val, test_id=test_id)
                temp_graph.calculated_pf = card.calculated_pf
                temp_graph.measured_current = card.measured_current
                temp_graph.pulse_duration = card.pulse_duration
                temp_graph.resize(950, 600)
                temp_graph.setAutoZoomEnabled(True)
                
                pm = temp_graph.grab()
                if pm and not pm.isNull():
                    pm.save(file_path)
                
                temp_graph.deleteLater()
                
        # Check if card with this name already exists
        for i, existing_card in enumerate(self.dynamic_cards):
            if existing_card.name == name:
                layout_index = self.horizontalLayout_graphs.indexOf(existing_card)
                self.horizontalLayout_graphs.removeWidget(existing_card)
                existing_card.deleteLater()
                if layout_index >= 0:
                    self.horizontalLayout_graphs.insertWidget(layout_index, card)
                else:
                    self.horizontalLayout_graphs.addWidget(card)
                self.dynamic_cards[i] = card
                self.frame_graphs_container.show()
                
                save_full_waveform_image()
                return
        
        # Limit the number of graphs to at most 3
        if len(self.dynamic_cards) >= 3:
            oldest_card = self.dynamic_cards.pop(0)
            self.horizontalLayout_graphs.removeWidget(oldest_card)
            oldest_card.deleteLater()
            
        self.frame_graphs_container.show()
            
        self.horizontalLayout_graphs.addWidget(card)
        self.dynamic_cards.append(card)
        
        save_full_waveform_image()

    @Slot(dict)
    def handle_override_requested(self, data: dict):
        if not self.test_runner:
            return
            
        test_id = data.get('test_id', 'unknown')
        pf = data.get('pf')
        curr = data.get('current')
        pixmap = data.get('pixmap')
        card_name = data.get('name', '')
        
        # Determine the 0-based index from card name (e.g., "Waveform 1" -> index 0)
        import re
        match = re.search(r'\d+', card_name)
        idx = int(match.group(0)) - 1 if match else -1
        
        # Update the list in the context so the average is recalculated
        results = self.test_runner.context.test_results
        
        if idx >= 0:
            if "pf_list" in results and idx < len(results["pf_list"]):
                results["pf_list"][idx] = pf
            if "measured_current_list" in results and idx < len(results["measured_current_list"]):
                results["measured_current_list"][idx] = curr
                
        # Recalculate average if lists exist, otherwise just use the overridden value
        if "pf_list" in results and len(results["pf_list"]) > 0:
            active_pfs = results["pf_list"]
            if test_id.lower() == "g6" and len(active_pfs) > 3:
                active_pfs = active_pfs[3:]
            results['calculated_pf'] = sum(active_pfs) / len(active_pfs)
        else:
            results['calculated_pf'] = pf
            
        if "measured_current_list" in results and len(results["measured_current_list"]) > 0:
            active_currs = results["measured_current_list"]
            if test_id.lower() == "g6" and len(active_currs) > 3:
                active_currs = active_currs[3:]
            results['measured_current'] = sum(active_currs) / len(active_currs)
        else:
            results['measured_current'] = curr
        
        # Save image
        if pixmap:
            import os
            graphs_dir = "logs/graphs"
            os.makedirs(graphs_dir, exist_ok=True)
            session_id = getattr(self.test_runner.context, 'db_row_id', None)
            if session_id:
                safe_name = card_name.replace(" ", "_").lower()
                # Overwrite the automatically generated image with the overridden one
                file_path = os.path.join(graphs_dir, f"session_{session_id}_{test_id}_{safe_name}.png")
                pixmap.save(file_path)
                
        # If the test is already complete, update the database
        from core.test_engine.state_machine import TestState
        if self.test_runner.state_machine.get_state() == TestState.COMPLETE:
            # Re-verify the test results with the new values
            if hasattr(self.test_runner, 'test') and hasattr(self.test_runner.test, 'verify'):
                self.test_runner.test.verify(self.test_runner.context)
            
            is_success = self.test_runner.context.test_results.get("success", True)
            outcome = "PASS" if is_success else "FAIL"
            self.test_runner._finalize_test_in_db(outcome)
            self.update_status_text(f"Override Saved & Result Updated to {outcome}!")
            
            # Revert to standard completion message after 3 seconds
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.handle_test_finished())
        else:
            old_html = self.lbl_instruction.text()
            self.update_status_text("Override Saved!")
            
            from PySide6.QtCore import QTimer
            QTimer.singleShot(3000, lambda: self.lbl_instruction.setText(old_html))

    @Slot(str)
    def handle_redo_requested(self, card_name: str):
        if not self.test_runner:
            return
            
        import re
        match = re.search(r'\d+', card_name)
        if match:
            # We assume card names are "Waveform 1", "Waveform 2", etc.
            cycle_idx = match.group(0)
            self.resolve_user_action(f"REDO:{cycle_idx}")
        else:
            if hasattr(self, 'main_window'):
                self.main_window.append_log("WARNING", f"Could not determine cycle index from '{card_name}'")

    @Slot(int, int)
    def update_cycle_progress(self, current: int, total: int):
        """Updates the active test cycle visualization panel."""
        if total > 0:
            self.frame_cycles_container.show()
            self.lbl_cycle_counter.setText(f"Cycle {current} of {total} (Running)")
            self.cycle_progress_bar.setRange(0, 100)
            
            target_val = int((current / total) * 100)
            
            if self.cycle_progress_anim.state() == QPropertyAnimation.State.Running:
                self.cycle_progress_anim.stop()
                
            self.cycle_progress_anim.setStartValue(self.cycle_progress_bar.value())
            self.cycle_progress_anim.setEndValue(target_val)
            self.cycle_progress_anim.setDuration(300) # 300ms smooth transition
            self.cycle_progress_anim.start()
            
            self.lbl_cycle_percentage.setText(f"{target_val}%")
        else:
            self.frame_cycles_container.hide()
            self.cycle_progress_anim.stop()
