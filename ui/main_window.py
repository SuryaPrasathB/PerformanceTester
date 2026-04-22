from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QTextEdit, QTableWidget, 
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QColor

class MainWindow(QMainWindow):
    """
    Main UI Window for the Meter Test System.
    """
    def __init__(self, device_manager):
        super().__init__()
        self.device_manager = device_manager
        
        self.setWindowTitle("Meter Test System")
        self.resize(800, 600)
        
        self._setup_ui()
        self._populate_devices()
        
    def _setup_ui(self):
        """Sets up the UI layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Device Status Panel ---
        status_label = QLabel("<b>Device Status Panel</b>")
        main_layout.addWidget(status_label)
        
        self.device_table = QTableWidget()
        self.device_table.setColumnCount(4)
        self.device_table.setHorizontalHeaderLabels(["Name", "Type", "Mock", "Status"])
        self.device_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.device_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.device_table)
        
        # --- Connect / Disconnect Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton("Connect All")
        self.btn_disconnect = QPushButton("Disconnect All")
        
        btn_layout.addWidget(self.btn_connect)
        btn_layout.addWidget(self.btn_disconnect)
        main_layout.addLayout(btn_layout)
        
        # --- Test Control / Status Panel ---
        test_panel_label = QLabel("<b>Test Control & Status Panel</b>")
        main_layout.addWidget(test_panel_label)

        test_control_layout = QHBoxLayout()
        self.btn_start_test = QPushButton("Start Test (G2)")
        self.btn_pause_resume = QPushButton("Pause")
        self.btn_cancel_test = QPushButton("Cancel Test")
        
        self.btn_pause_resume.setEnabled(False)
        self.btn_cancel_test.setEnabled(False)
        
        test_control_layout.addWidget(self.btn_start_test)
        test_control_layout.addWidget(self.btn_pause_resume)
        test_control_layout.addWidget(self.btn_cancel_test)
        main_layout.addLayout(test_control_layout)

        test_status_layout = QHBoxLayout()
        self.lbl_state = QLabel("State: IDLE")
        self.lbl_voltage = QLabel("Voltage: -- V")
        self.lbl_current = QLabel("Current: -- A")
        self.lbl_credit = QLabel("Credit: --")
        
        test_status_layout.addWidget(self.lbl_state)
        test_status_layout.addWidget(self.lbl_voltage)
        test_status_layout.addWidget(self.lbl_current)
        test_status_layout.addWidget(self.lbl_credit)
        main_layout.addLayout(test_status_layout)
        
        # --- Log Output Panel ---
        log_label = QLabel("<b>Log Output Panel</b>")
        main_layout.addWidget(log_label)
        
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(self.log_text_edit)
        
        # Wiring up UI actions to DeviceManager
        self.btn_connect.clicked.connect(self.device_manager.connect_all)
        self.btn_disconnect.clicked.connect(self.device_manager.disconnect_all)
        
        # Listen to DeviceManager signals to update UI
        self.device_manager.device_status_changed.connect(self.update_device_status)
        
        # Wire up test control buttons
        self.btn_start_test.clicked.connect(self.start_test)
        self.btn_pause_resume.clicked.connect(self.toggle_pause_resume)
        self.btn_cancel_test.clicked.connect(self.cancel_test)
        
        self.test_runner = None

    def _populate_devices(self):
        """Populates the device table with initial configurations."""
        devices = self.device_manager.get_devices()
        self.device_table.setRowCount(len(devices))
        
        for row, (name, model) in enumerate(devices.items()):
            name_item = QTableWidgetItem(name)
            type_item = QTableWidgetItem(model.type.upper())
            mock_item = QTableWidgetItem("Yes" if model.mock else "No")
            status_item = QTableWidgetItem("Disconnected")
            
            # Center text and color status
            for item in (name_item, type_item, mock_item, status_item):
                item.setTextAlignment(Qt.AlignCenter)
                
            status_item.setForeground(QColor("red"))
                
            self.device_table.setItem(row, 0, name_item)
            self.device_table.setItem(row, 1, type_item)
            self.device_table.setItem(row, 2, mock_item)
            self.device_table.setItem(row, 3, status_item)

    @Slot(str, str)
    def append_log(self, level: str, message: str):
        """Appends a new log message to the log panel."""
        color = "black"
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "DEBUG":
            color = "gray"
            
        html_msg = f'<span style="color:{color};">{message}</span><br>'
        self.log_text_edit.insertHtml(html_msg)
        
        # Scroll to bottom
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @Slot()
    def start_test(self):
        """Starts the G2 Normal Operation Test."""
        if self.test_runner and self.test_runner.isRunning():
            return
            
        from core.test_engine.test_context import TestContext
        from core.test_definitions.g2_normal_operation import G2NormalOperationTest
        from core.test_engine.test_runner import TestRunner
        
        context = TestContext(self.device_manager)
        test_instance = G2NormalOperationTest()
        self.test_runner = TestRunner(test_instance, context)
        
        # Connect signals
        self.test_runner.on_state_changed.connect(self.update_test_state)
        self.test_runner.on_log.connect(self.append_log)
        self.test_runner.on_data_update.connect(self.update_test_data)
        self.test_runner.finished.connect(self.on_test_finished)
        
        self.btn_start_test.setEnabled(False)
        self.btn_pause_resume.setEnabled(True)
        self.btn_cancel_test.setEnabled(True)
        self.btn_pause_resume.setText("Pause")
        
        self.test_runner.start()
        
    @Slot()
    def toggle_pause_resume(self):
        """Toggles between pause and resume states."""
        if not self.test_runner:
            return
            
        from core.test_engine.state_machine import TestState
        current_state = self.test_runner.state_machine.get_state()
        
        if current_state == TestState.RUNNING:
            self.test_runner.pause()
            self.btn_pause_resume.setText("Resume")
        elif current_state == TestState.PAUSED:
            self.test_runner.resume()
            self.btn_pause_resume.setText("Pause")
            
    @Slot()
    def cancel_test(self):
        """Cancels the currently running test."""
        if self.test_runner:
            self.test_runner.cancel()
            self.btn_cancel_test.setEnabled(False)
            
    @Slot(str)
    def update_test_state(self, state_name: str):
        """Updates the state label."""
        self.lbl_state.setText(f"State: {state_name}")
        
    @Slot(dict)
    def update_test_data(self, data: dict):
        """Updates the live values labels."""
        voltage = data.get("voltage", "--")
        current = data.get("current", "--")
        credit = data.get("credit", "--")
        
        self.lbl_voltage.setText(f"Voltage: {voltage} V")
        self.lbl_current.setText(f"Current: {current} A")
        self.lbl_credit.setText(f"Credit: {credit}")
        
    @Slot()
    def on_test_finished(self):
        """Handles post-test cleanup in the UI."""
        self.btn_start_test.setEnabled(True)
        self.btn_pause_resume.setEnabled(False)
        self.btn_cancel_test.setEnabled(False)
        self.btn_pause_resume.setText("Pause")

    @Slot(str, bool)
    def update_device_status(self, device_name: str, is_connected: bool):
        """Updates the status column for a specific device."""
        for row in range(self.device_table.rowCount()):
            item = self.device_table.item(row, 0)
            if item and item.text() == device_name:
                status_item = self.device_table.item(row, 3)
                if is_connected:
                    status_item.setText("Connected")
                    status_item.setForeground(QColor("green"))
                else:
                    status_item.setText("Disconnected")
                    status_item.setForeground(QColor("red"))
                break

    def closeEvent(self, event):
        """Ensure threads are cleaned up when window closes."""
        self.device_manager.cleanup()
        super().closeEvent(event)
