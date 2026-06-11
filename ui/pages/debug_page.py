from PySide6.QtWidgets import (QWidget, QScrollArea, QFrame, QLabel, QPushButton,
                               QLineEdit, QComboBox, QGroupBox, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QMessageBox, QTextEdit)
from PySide6.QtCore import Slot, Qt, QTimer
from ui.pages.ui_debug_page import Ui_DebugPage
from core.hardware_mapping import PLCCoil, MFMRegister

class DebugPage(QWidget, Ui_DebugPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        self.is_active = False
        self.coil_states = {}
        
        # Initialize default state for all coils
        for coil in PLCCoil:
            self.coil_states[coil] = False
            
        # Build the custom interactive layout programmatically
        self.build_custom_ui()
        
        # Setup polling QTimer (1000ms interval)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.poll_hardware)

    def set_active(self, active: bool):
        """Called by MainWindow when switching between dashboard tabs."""
        self.is_active = active
        if active:
            self.timer.start()
            self.poll_hardware()  # Force instant update
        else:
            self.timer.stop()

    def build_custom_ui(self):
        # Hide standard "Coming Soon" label
        if hasattr(self, 'label'):
            self.label.hide()
            
        # 1. Create a Scroll Area to fit all three sections beautifully
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scroll_content")
        self.scroll_content.setStyleSheet("#scroll_content { background-color: transparent; }")
        
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(20)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add Cards
        self.create_lock_indicator()
        self.create_plc_card()
        self.create_energy_meter_card()
        self.create_mfm_card()
        self.create_picoscope_card()
        
        self.scroll_area.setWidget(self.scroll_content)
        self.verticalLayout.addWidget(self.scroll_area)
        
        # Initial style application
        self.update_theme_styles()

    def create_lock_indicator(self):
        """Simple lock indicator if a test sequence is currently running."""
        self.lbl_lock_status = QLabel("⚠️ Test Active: Debug controls are locked to prevent hardware conflicts.")
        self.lbl_lock_status.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #F87171;
                background-color: #7F1D1D;
                border: 1px solid #B91C1C;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self.lbl_lock_status.hide()
        self.scroll_layout.addWidget(self.lbl_lock_status)

    def create_card_frame(self, title_text) -> tuple[QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLabel, QPushButton]:
        """Utility to generate a card frame with common header (Title, Status LED, Connect/Disconnect button)."""
        card = QFrame()
        # Setting objectName ensures it inherits background and border styles from standard theme QSS
        card.setObjectName("frame_settings")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        
        # Header layout
        header = QHBoxLayout()
        header.setSpacing(10)
        
        lbl_title = QLabel(title_text)
        lbl_title.setObjectName("lbl_section_title")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #38BDF8; letter-spacing: 0.5px;")
        
        header.addWidget(lbl_title)
        header.addStretch()
        
        # LED dot indicator
        lbl_led = QLabel()
        lbl_led.setFixedSize(12, 12)
        lbl_led.setStyleSheet("background-color: #475569; border-radius: 6px; border: 1px solid #334155;")
        
        lbl_status = QLabel("Offline")
        lbl_status.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 13px;")
        
        btn_connect = QPushButton("Connect")
        btn_connect.setFixedWidth(100)
        
        header.addWidget(lbl_led)
        header.addWidget(lbl_status)
        header.addWidget(btn_connect)
        
        card_layout.addLayout(header)
        
        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("border: 1px solid #334155;")
        card_layout.addWidget(sep)
        
        return card, card_layout, header, lbl_led, lbl_status, btn_connect

    def create_plc_card(self):
        card, layout, header, self.lbl_plc_led, self.lbl_plc_status, self.btn_plc_connect = self.create_card_frame("1. PLC CONTROLLER")
        self.btn_plc_connect.clicked.connect(lambda: self.toggle_device_connection("PLC1"))
        
        # Coils Grid
        self.plc_grid_box = QGroupBox("Coils Controls (Write Toggle)")
        grid_layout = QGridLayout(self.plc_grid_box)
        grid_layout.setSpacing(12)
        
        coils = [
            (PLCCoil.FCMC_TEST_START, "FCMC START"),
            (PLCCoil.SCCC_TEST_START, "SCCC START"),
            (PLCCoil.FCMCT_ACK, "FCMCT ACK"),
            (PLCCoil.ACB_COIL_ADDR, "ACB COIL"),
            (PLCCoil.SCR_COIL_ADDR, "SCR COIL"),
            (PLCCoil.PRE_FUSING_MODE_COIL_ADDR, "PRE FUSING"),
            (PLCCoil.PROS_CT_TEST_START, "PROS CT START"),
        ]
        
        self.coil_buttons = {}
        self.coil_leds = {}
        
        for idx, (coil, label_text) in enumerate(coils):
            row = idx // 3
            col = idx % 3
            
            # Channel cell container
            cell = QFrame()
            cell.setStyleSheet("background-color: transparent; border: none;")
            cell_layout = QHBoxLayout(cell)
            cell_layout.setContentsMargins(6, 4, 6, 4)
            cell_layout.setSpacing(8)
            
            led = QLabel()
            led.setFixedSize(12, 12)
            led.setStyleSheet("background-color: #475569; border-radius: 6px; border: 1px solid #334155;")
            self.coil_leds[coil] = led
            
            btn = QPushButton(f"{label_text} (0x{int(coil):02X})")
            btn.clicked.connect(lambda checked=False, c=coil: self.toggle_plc_coil(c))
            self.coil_buttons[coil] = btn
            
            cell_layout.addWidget(led)
            cell_layout.addWidget(btn)
            grid_layout.addWidget(cell, row, col)
            
        layout.addWidget(self.plc_grid_box)
        
        # General Read/Write Tool
        self.plc_gen_box = QGroupBox("General Read / Write Tool")
        gen_layout = QHBoxLayout(self.plc_gen_box)
        gen_layout.setSpacing(10)
        
        self.cmb_plc_gen_type = QComboBox()
        self.cmb_plc_gen_type.addItems(["Coil (Read/Write)", "Register (Read/Write)"])
        
        self.le_plc_gen_addr = QLineEdit()
        self.le_plc_gen_addr.setPlaceholderText("Address (e.g. 10 or 0x0A)")
        
        self.le_plc_gen_val = QLineEdit()
        self.le_plc_gen_val.setPlaceholderText("Value (for write)")
        
        btn_read = QPushButton("Read")
        btn_read.clicked.connect(self.read_plc_general)
        
        btn_write = QPushButton("Write")
        btn_write.clicked.connect(self.write_plc_general)
        
        self.lbl_plc_gen_result = QLabel("Result: ---")
        self.lbl_plc_gen_result.setStyleSheet("font-weight: bold; color: #38BDF8;")
        
        # Set custom styles for read/write buttons to highlight actions
        self.style_action_buttons(btn_read, btn_write)
        
        gen_layout.addWidget(self.cmb_plc_gen_type)
        gen_layout.addWidget(self.le_plc_gen_addr)
        gen_layout.addWidget(self.le_plc_gen_val)
        gen_layout.addWidget(btn_read)
        gen_layout.addWidget(btn_write)
        gen_layout.addWidget(self.lbl_plc_gen_result)
        
        layout.addWidget(self.plc_gen_box)
        self.scroll_layout.addWidget(card)

    def create_energy_meter_card(self):
        card, layout, header, self.lbl_meter_led, self.lbl_meter_status, self.btn_meter_connect = self.create_card_frame("2. ENERGY METER")
        self.btn_meter_connect.clicked.connect(lambda: self.toggle_device_connection("EnergyMeter1"))
        
        # Parameter Display
        self.meter_readings_box = QGroupBox("Live Parameter Values")
        readings_layout = QGridLayout(self.meter_readings_box)
        readings_layout.setSpacing(15)
        
        lbl_v = QLabel("Voltage L1:")
        self.lbl_meter_val_v = QLabel("--- V")
        self.lbl_meter_val_v.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_i = QLabel("Current L1:")
        self.lbl_meter_val_i = QLabel("--- A")
        self.lbl_meter_val_i.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_pf = QLabel("Power Factor:")
        self.lbl_meter_val_pf = QLabel("---")
        self.lbl_meter_val_pf.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_w = QLabel("Active Power:")
        self.lbl_meter_val_w = QLabel("--- W")
        self.lbl_meter_val_w.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        readings_layout.addWidget(lbl_v, 0, 0)
        readings_layout.addWidget(self.lbl_meter_val_v, 0, 1)
        readings_layout.addWidget(lbl_i, 0, 2)
        readings_layout.addWidget(self.lbl_meter_val_i, 0, 3)
        readings_layout.addWidget(lbl_pf, 1, 0)
        readings_layout.addWidget(self.lbl_meter_val_pf, 1, 1)
        readings_layout.addWidget(lbl_w, 1, 2)
        readings_layout.addWidget(self.lbl_meter_val_w, 1, 3)
        
        layout.addWidget(self.meter_readings_box)
        
        # DLMS Query Tool
        self.dlms_box = QGroupBox("DLMS OBIS Command Utility")
        dlms_layout = QVBoxLayout(self.dlms_box)
        
        input_layout = QHBoxLayout()
        self.le_meter_obis = QLineEdit()
        self.le_meter_obis.setPlaceholderText("OBIS Code (e.g. 0.0.96.1.0.255)")
        
        self.le_meter_obis_val = QLineEdit()
        self.le_meter_obis_val.setPlaceholderText("Write Value (optional)")
        
        btn_obis_read = QPushButton("Read OBIS")
        btn_obis_read.clicked.connect(self.read_energy_obis)
        
        btn_obis_write = QPushButton("Write OBIS")
        btn_obis_write.clicked.connect(self.write_energy_obis)
        
        self.style_action_buttons(btn_obis_read, btn_obis_write)
        
        input_layout.addWidget(self.le_meter_obis)
        input_layout.addWidget(self.le_meter_obis_val)
        input_layout.addWidget(btn_obis_read)
        input_layout.addWidget(btn_obis_write)
        dlms_layout.addLayout(input_layout)
        
        self.txt_meter_console = QTextEdit()
        self.txt_meter_console.setReadOnly(True)
        self.txt_meter_console.setMaximumHeight(100)
        
        dlms_layout.addWidget(self.txt_meter_console)
        layout.addWidget(self.dlms_box)
        self.scroll_layout.addWidget(card)

    def create_mfm_card(self):
        card, layout, header, self.lbl_mfm_led, self.lbl_mfm_status, self.btn_mfm_connect = self.create_card_frame("3. MFM METER")
        self.btn_mfm_connect.clicked.connect(lambda: self.toggle_device_connection("MFMMeter1"))
        
        # Instantaneous readings
        self.mfm_readings_box = QGroupBox("Instantaneous Readings")
        readings_layout = QGridLayout(self.mfm_readings_box)
        readings_layout.setSpacing(15)
        
        lbl_v = QLabel("Voltage L1 (0x0100):")
        self.lbl_mfm_val_v = QLabel("--- V")
        self.lbl_mfm_val_v.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_i = QLabel("Current L1 (0x0101):")
        self.lbl_mfm_val_i = QLabel("--- A")
        self.lbl_mfm_val_i.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_w = QLabel("Active Power (0x0102):")
        self.lbl_mfm_val_w = QLabel("--- W")
        self.lbl_mfm_val_w.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        readings_layout.addWidget(lbl_v, 0, 0)
        readings_layout.addWidget(self.lbl_mfm_val_v, 0, 1)
        readings_layout.addWidget(lbl_i, 0, 2)
        readings_layout.addWidget(self.lbl_mfm_val_i, 0, 3)
        readings_layout.addWidget(lbl_w, 0, 4)
        readings_layout.addWidget(self.lbl_mfm_val_w, 0, 5)
        
        layout.addWidget(self.mfm_readings_box)
        
        # Modbus registers utility
        self.mfm_utility_box = QGroupBox("Modbus Register Utility")
        modbus_layout = QVBoxLayout(self.mfm_utility_box)
        
        input_layout = QHBoxLayout()
        self.le_mfm_reg_addr = QLineEdit()
        self.le_mfm_reg_addr.setPlaceholderText("Address (e.g. 256 or 0x0100)")
        
        self.le_mfm_reg_count = QLineEdit()
        self.le_mfm_reg_count.setPlaceholderText("Count (default 1)")
        
        self.le_mfm_reg_val = QLineEdit()
        self.le_mfm_reg_val.setPlaceholderText("Write Value")
        
        btn_reg_read = QPushButton("Read Register")
        btn_reg_read.clicked.connect(self.read_mfm_registers)
        
        btn_reg_write = QPushButton("Write Register")
        btn_reg_write.clicked.connect(self.write_mfm_registers)
        
        self.style_action_buttons(btn_reg_read, btn_reg_write)
        
        input_layout.addWidget(self.le_mfm_reg_addr)
        input_layout.addWidget(self.le_mfm_reg_count)
        input_layout.addWidget(self.le_mfm_reg_val)
        input_layout.addWidget(btn_reg_read)
        input_layout.addWidget(btn_reg_write)
        modbus_layout.addLayout(input_layout)
        
        self.txt_mfm_console = QTextEdit()
        self.txt_mfm_console.setReadOnly(True)
        self.txt_mfm_console.setMaximumHeight(100)
        
        modbus_layout.addWidget(self.txt_mfm_console)
        layout.addWidget(self.mfm_utility_box)
        self.scroll_layout.addWidget(card)

    def create_picoscope_card(self):
        card, layout, header, self.lbl_picoscope_led, self.lbl_picoscope_status, self.btn_picoscope_connect = self.create_card_frame("4. PICOSCOPE OSCILLOSCOPE")
        self.btn_picoscope_connect.clicked.connect(lambda: self.toggle_device_connection("PicoScope1"))
        
        # PicoScope Utility
        self.picoscope_box = QGroupBox("PicoScope Capture Test")
        pico_layout = QVBoxLayout(self.picoscope_box)
        
        input_layout = QHBoxLayout()
        btn_capture = QPushButton("Trigger Test Capture")
        btn_capture.clicked.connect(self.trigger_picoscope_capture)
        
        # Styling for Trigger Test Capture button (using premium primary color)
        btn_capture.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        
        input_layout.addWidget(btn_capture)
        input_layout.addStretch()
        pico_layout.addLayout(input_layout)
        
        self.txt_picoscope_console = QTextEdit()
        self.txt_picoscope_console.setReadOnly(True)
        self.txt_picoscope_console.setMaximumHeight(100)
        
        pico_layout.addWidget(self.txt_picoscope_console)
        layout.addWidget(self.picoscope_box)
        self.scroll_layout.addWidget(card)

    def trigger_picoscope_capture(self):
        pico_driver = self.device_manager.drivers.get("PicoScope1")
        if not pico_driver or not pico_driver.is_connected:
            self.txt_picoscope_console.append("PicoScope is disconnected.")
            QMessageBox.warning(self, "Device Disconnected", "Please connect to PicoScope first.")
            return
            
        self.txt_picoscope_console.append(">> Starting block capture...")
        try:
            success = pico_driver.start_capture()
            if not success:
                self.txt_picoscope_console.append("<< Failed to start capture.")
                return
                
            self.txt_picoscope_console.append(">> Capture initiated. Retrieving waveform...")
            # If mock mode, start_capture returns immediately, but we might want a tiny delay so it feels realistic
            if pico_driver.mock_mode or pico_driver.handle == 999:
                import time
                time.sleep(0.1)
                
            pico_driver.stop_capture()
            data = pico_driver.get_waveform()
            if data:
                self.txt_picoscope_console.append(f"<< Success: Captured {len(data)} points.")
                from ui.widgets.waveform_card import WaveformCard
                timebase = pico_driver.timebase
                voltage_range = 10
                
                card = WaveformCard("Debug Capture", data, timebase, voltage_range, self)
                card.open_analysis_dialog()
            else:
                self.txt_picoscope_console.append("<< Failed: Empty waveform data returned.")
        except Exception as e:
            self.txt_picoscope_console.append(f"<< Error: {e}")

    def style_action_buttons(self, btn_read: QPushButton, btn_write: QPushButton):
        """Standard action buttons styling."""
        btn_read.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #3B82F6; }
        """)
        btn_write.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover { background-color: #10B981; }
        """)

    def get_connect_button_style(self) -> str:
        theme = getattr(self.main_window, "current_theme", "light")
        if theme == "dark":
            return """
                QPushButton {
                    background-color: #334155;
                    color: #F8FAFC;
                    border: 1px solid #475569;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 5px 12px;
                }
                QPushButton:hover { background-color: #475569; }
            """
        else:
            return """
                QPushButton {
                    background-color: #F1F5F9;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 5px 12px;
                }
                QPushButton:hover { background-color: #E2E8F0; }
            """

    def get_console_style(self) -> str:
        theme = getattr(self.main_window, "current_theme", "light")
        if theme == "dark":
            return """
                QTextEdit {
                    font-family: 'Cascadia Code', 'Consolas', monospace;
                    background-color: #0F172A;
                    color: #38BDF8;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    font-size: 13px;
                }
            """
        else:
            return """
                QTextEdit {
                    font-family: 'Cascadia Code', 'Consolas', monospace;
                    background-color: #F8FAFC;
                    color: #0369A1;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    font-size: 13px;
                }
            """

    def get_coil_style(self, val: bool) -> str:
        theme = getattr(self.main_window, "current_theme", "light")
        if val:
            return """
                QPushButton {
                    background-color: #10B981;
                    color: #FFFFFF;
                    border: 1px solid #34D399;
                    border-radius: 6px;
                    font-weight: 600;
                    padding: 8px;
                    text-align: left;
                }
                QPushButton:hover { background-color: #059669; }
            """
        else:
            if theme == "dark":
                return """
                    QPushButton {
                        background-color: #334155;
                        color: #94A3B8;
                        border: 1px solid #475569;
                        border-radius: 6px;
                        font-weight: 600;
                        padding: 8px;
                        text-align: left;
                    }
                    QPushButton:hover { background-color: #475569; color: #F8FAFC; }
                """
            else:
                return """
                    QPushButton {
                        background-color: #F1F5F9;
                        color: #64748B;
                        border: 1px solid #CBD5E1;
                        border-radius: 6px;
                        font-weight: 600;
                        padding: 8px;
                        text-align: left;
                    }
                    QPushButton:hover { background-color: #E2E8F0; color: #0F172A; }
                """

    def update_theme_styles(self):
        """Updates theme-dependent styles dynamically when changing dark/light mode."""
        # 1. Update general card styled buttons
        self.btn_plc_connect.setStyleSheet(self.get_connect_button_style())
        self.btn_meter_connect.setStyleSheet(self.get_connect_button_style())
        self.btn_mfm_connect.setStyleSheet(self.get_connect_button_style())
        if hasattr(self, 'btn_picoscope_connect'):
            self.btn_picoscope_connect.setStyleSheet(self.get_connect_button_style())
        
        # 2. Update consoles
        self.txt_meter_console.setStyleSheet(self.get_console_style())
        self.txt_mfm_console.setStyleSheet(self.get_console_style())
        if hasattr(self, 'txt_picoscope_console'):
            self.txt_picoscope_console.setStyleSheet(self.get_console_style())
        
        # 3. Update coil buttons and LEDs
        for coil_enum, val in self.coil_states.items():
            self.update_coil_led(coil_enum, val)
            
        # 4. Update device connection LEDs
        plc_driver = self.device_manager.drivers.get("PLC1")
        self.update_connection_led(self.lbl_plc_led, self.lbl_plc_status, plc_driver and plc_driver.is_connected)
        
        meter_driver = self.device_manager.drivers.get("EnergyMeter1")
        self.update_connection_led(self.lbl_meter_led, self.lbl_meter_status, meter_driver and meter_driver.is_connected)
        
        mfm_driver = self.device_manager.drivers.get("MFMMeter1")
        self.update_connection_led(self.lbl_mfm_led, self.lbl_mfm_status, mfm_driver and mfm_driver.is_connected)
        
        if hasattr(self, 'lbl_picoscope_led'):
            picoscope_driver = self.device_manager.drivers.get("PicoScope1")
            self.update_connection_led(self.lbl_picoscope_led, self.lbl_picoscope_status, picoscope_driver and picoscope_driver.is_connected)

    def toggle_device_connection(self, device_name: str):
        """Thread-safe toggle of connection using DeviceWorker slots."""
        driver = self.device_manager.drivers.get(device_name)
        if not driver: return
        
        worker = self.device_manager.workers.get(device_name)
        if not worker: return
        
        from PySide6.QtCore import QMetaObject, Qt
        if driver.is_connected:
            QMetaObject.invokeMethod(worker, "disconnect_device", Qt.QueuedConnection)
        else:
            QMetaObject.invokeMethod(worker, "connect_device", Qt.QueuedConnection)

    def update_connection_led(self, led_lbl: QLabel, text_lbl: QLabel, is_connected: bool):
        theme = getattr(self.main_window, "current_theme", "light")
        if is_connected:
            led_lbl.setStyleSheet("background-color: #10B981; border-radius: 6px; border: 1px solid #34D399;")
            text_lbl.setText("Connected")
            color = "#34D399" if theme == "dark" else "#059669"
            text_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 13px;")
        else:
            led_lbl.setStyleSheet("background-color: #EF4444; border-radius: 6px; border: 1px solid #F87171;")
            text_lbl.setText("Disconnected")
            color = "#F87171" if theme == "dark" else "#DC2626"
            text_lbl.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 13px;")

    def toggle_plc_coil(self, coil_enum):
        plc_driver = self.device_manager.drivers.get("PLC1")
        if not plc_driver or not plc_driver.is_connected:
            QMessageBox.warning(self, "Device Disconnected", "Please connect to PLC first.")
            return
            
        addr = int(coil_enum)
        current_val = self.coil_states.get(coil_enum, False)
        new_val = not current_val
        
        success = plc_driver.write_data(address=addr, value=1 if new_val else 0)
        if success:
            self.coil_states[coil_enum] = new_val
            self.update_coil_led(coil_enum, new_val)
            self.main_window.append_log("INFO", f"Debug Screen: PLC coil {coil_enum.name} (0x{addr:02X}) set to {new_val}")
        else:
            QMessageBox.critical(self, "Write Failed", f"Failed to write to PLC coil {coil_enum.name}.")

    def update_coil_led(self, coil_enum, val: bool):
        self.coil_states[coil_enum] = val
        led = self.coil_leds.get(coil_enum)
        btn = self.coil_buttons.get(coil_enum)
        theme = getattr(self.main_window, "current_theme", "light")
        
        if led:
            if val:
                led.setStyleSheet("background-color: #10B981; border-radius: 6px; border: 1px solid #34D399;")
            else:
                if theme == "dark":
                    led.setStyleSheet("background-color: #475569; border-radius: 6px; border: 1px solid #334155;")
                else:
                    led.setStyleSheet("background-color: #CBD5E1; border-radius: 6px; border: 1px solid #94A3B8;")
        
        if btn:
            label_text = btn.text().split(" (")[0]
            btn.setText(f"{label_text} (0x{int(coil_enum):02X})")
            btn.setStyleSheet(self.get_coil_style(val))

    def read_plc_general(self):
        plc_driver = self.device_manager.drivers.get("PLC1")
        if not plc_driver or not plc_driver.is_connected:
            self.lbl_plc_gen_result.setText("Disconnected")
            return
        try:
            addr_str = self.le_plc_gen_addr.text().strip()
            if not addr_str: return
            addr = int(addr_str, 0)
            is_coil = self.cmb_plc_gen_type.currentText().startswith("Coil")
            
            data = plc_driver.read_data(address=addr, count=1)
            if data and len(data) > 0:
                val = data[0]
                if is_coil:
                    val = bool(val)
                self.lbl_plc_gen_result.setText(f"Result: {val}")
            else:
                self.lbl_plc_gen_result.setText("No Response")
        except Exception as e:
            self.lbl_plc_gen_result.setText(f"Error: {e}")

    def write_plc_general(self):
        plc_driver = self.device_manager.drivers.get("PLC1")
        if not plc_driver or not plc_driver.is_connected:
            self.lbl_plc_gen_result.setText("Disconnected")
            return
        try:
            addr_str = self.le_plc_gen_addr.text().strip()
            val_str = self.le_plc_gen_val.text().strip()
            if not addr_str or not val_str: return
            addr = int(addr_str, 0)
            is_coil = self.cmb_plc_gen_type.currentText().startswith("Coil")
            
            if is_coil:
                val = 1 if val_str.lower() in ("true", "1", "on", "yes") else 0
            else:
                val = int(val_str, 0)
                
            success = plc_driver.write_data(address=addr, value=val)
            self.lbl_plc_gen_result.setText("Result: Success" if success else "Result: Failed")
        except Exception as e:
            self.lbl_plc_gen_result.setText(f"Error: {e}")

    def read_energy_obis(self):
        meter_driver = self.device_manager.drivers.get("EnergyMeter1")
        if not meter_driver or not meter_driver.is_connected:
            self.txt_meter_console.append("Meter is disconnected.")
            return
        try:
            obis = self.le_meter_obis.text().strip()
            if not obis: return
            self.txt_meter_console.append(f">> Read OBIS: {obis}")
            res = meter_driver.read_data(obis_code=obis)
            self.txt_meter_console.append(f"<< Value: {res}")
        except Exception as e:
            self.txt_meter_console.append(f"<< Error: {e}")

    def write_energy_obis(self):
        meter_driver = self.device_manager.drivers.get("EnergyMeter1")
        if not meter_driver or not meter_driver.is_connected:
            self.txt_meter_console.append("Meter is disconnected.")
            return
        try:
            obis = self.le_meter_obis.text().strip()
            val_str = self.le_meter_obis_val.text().strip()
            if not obis or not val_str: return
            self.txt_meter_console.append(f">> Write OBIS: {obis} = {val_str}")
            
            try:
                val = int(val_str)
            except ValueError:
                try:
                    val = float(val_str)
                except ValueError:
                    val = val_str
                    
            success = meter_driver.write_data(obis_code=obis, value=val)
            self.txt_meter_console.append(f"<< Write result: {'Success' if success else 'Failed'}")
        except Exception as e:
            self.txt_meter_console.append(f"<< Error: {e}")

    def read_mfm_registers(self):
        mfm_driver = self.device_manager.drivers.get("MFMMeter1")
        if not mfm_driver or not mfm_driver.is_connected:
            self.txt_mfm_console.append("MFM is disconnected.")
            return
        try:
            addr_str = self.le_mfm_reg_addr.text().strip()
            if not addr_str: return
            addr = int(addr_str, 0)
            count = int(self.le_mfm_reg_count.text().strip() or "1")
            
            self.txt_mfm_console.append(f">> Read Reg: {addr} (count={count})")
            res = mfm_driver.read_data(address=addr, count=count)
            self.txt_mfm_console.append(f"<< Value: {res}")
        except Exception as e:
            self.txt_mfm_console.append(f"<< Error: {e}")

    def write_mfm_registers(self):
        mfm_driver = self.device_manager.drivers.get("MFMMeter1")
        if not mfm_driver or not mfm_driver.is_connected:
            self.txt_mfm_console.append("MFM is disconnected.")
            return
        try:
            addr_str = self.le_mfm_reg_addr.text().strip()
            val_str = self.le_mfm_reg_val.text().strip()
            if not addr_str or not val_str: return
            addr = int(addr_str, 0)
            val = int(val_str, 0)
            
            self.txt_mfm_console.append(f">> Write Reg: {addr} = {val}")
            success = mfm_driver.write_data(address=addr, value=val)
            self.txt_mfm_console.append(f"<< Write result: {'Success' if success else 'Failed'}")
        except Exception as e:
            self.txt_mfm_console.append(f"<< Error: {e}")

    def poll_hardware(self):
        """Timer callback that reads device and registers state periodically."""
        if not self.is_active:
            return
            
        # 1. Concurrency Check: Check if any test sequence is running
        test_running = False
        if hasattr(self.main_window, 'test_page') and self.main_window.test_page.test_runner:
            test_running = self.main_window.test_page.test_runner.isRunning()
            
        self.lbl_lock_status.setVisible(test_running)
        
        # Disable/Enable debug controls depending on test_running
        self.plc_grid_box.setEnabled(not test_running)
        self.plc_grid_box.setEnabled(not test_running)
        self.plc_gen_box.setEnabled(not test_running)
        self.dlms_box.setEnabled(not test_running)
        self.mfm_utility_box.setEnabled(not test_running)
        if hasattr(self, 'picoscope_box'):
            self.picoscope_box.setEnabled(not test_running)
            self.btn_picoscope_connect.setEnabled(not test_running)
        self.btn_plc_connect.setEnabled(not test_running)
        self.btn_meter_connect.setEnabled(not test_running)
        self.btn_mfm_connect.setEnabled(not test_running)
        
        # 2. Poll PLC Connection & Coils
        plc_driver = self.device_manager.drivers.get("PLC1")
        plc_connected = plc_driver and plc_driver.is_connected
        self.update_connection_led(self.lbl_plc_led, self.lbl_plc_status, plc_connected)
        
        if plc_connected:
            try:
                for coil_enum in PLCCoil:
                    addr = int(coil_enum)
                    # Coil addresses are mapped as holding registers in modbus driver
                    data = plc_driver.read_data(address=addr, count=1)
                    val = bool(data[0]) if data else False
                    self.update_coil_led(coil_enum, val)
            except Exception as e:
                pass
                
        # 3. Poll Energy Meter
        meter_driver = self.device_manager.drivers.get("EnergyMeter1")
        meter_connected = meter_driver and meter_driver.is_connected
        self.update_connection_led(self.lbl_meter_led, self.lbl_meter_status, meter_connected)
        
        if meter_connected:
            try:
                # read_data without parameters fetches voltage and current readings dictionary
                readings = meter_driver.read_data()
                if isinstance(readings, dict):
                    v = readings.get("voltage", 0.0)
                    i = readings.get("current", 0.0)
                    pf = readings.get("power_factor", 1.0)
                    active_p = v * i * pf
                    
                    self.lbl_meter_val_v.setText(f"{v:.1f} V")
                    self.lbl_meter_val_i.setText(f"{i:.3f} A")
                    self.lbl_meter_val_pf.setText(f"{pf:.2f}")
                    self.lbl_meter_val_w.setText(f"{active_p:.1f} W")
                elif isinstance(readings, (int, float)):
                    self.lbl_meter_val_i.setText(f"{readings:.3f} A")
            except Exception as e:
                pass
                
        # 4. Poll MFM Meter
        mfm_driver = self.device_manager.drivers.get("MFMMeter1")
        mfm_connected = mfm_driver and mfm_driver.is_connected
        self.update_connection_led(self.lbl_mfm_led, self.lbl_mfm_status, mfm_connected)
        
        if mfm_connected:
            try:
                v_data = mfm_driver.read_data(address=int(MFMRegister.VOLTAGE_L1), count=1)
                i_data = mfm_driver.read_data(address=int(MFMRegister.CURRENT_L1), count=1)
                p_data = mfm_driver.read_data(address=int(MFMRegister.ACTIVE_POWER), count=1)
                
                v = v_data[0] if v_data else 0.0
                i = i_data[0] if i_data else 0.0
                p = p_data[0] if p_data else 0.0
                
                # Mock Mode realism
                if mfm_driver.mock_mode and v == 0.0:
                    v = 240.2
                    i = 5.1
                    p = v * i * 0.98
                    
                self.lbl_mfm_val_v.setText(f"{v:.1f} V")
                self.lbl_mfm_val_i.setText(f"{i:.3f} A")
                self.lbl_mfm_val_w.setText(f"{p:.1f} W")
            except Exception as e:
                pass
                
        # 5. Poll PicoScope
        if hasattr(self, 'lbl_picoscope_led'):
            pico_driver = self.device_manager.drivers.get("PicoScope1")
            pico_connected = pico_driver and pico_driver.is_connected
            self.update_connection_led(self.lbl_picoscope_led, self.lbl_picoscope_status, pico_connected)
