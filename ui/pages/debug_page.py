from PySide6.QtWidgets import (QWidget, QScrollArea, QFrame, QLabel, QPushButton,
                               QLineEdit, QComboBox, QGroupBox, QVBoxLayout,
                               QHBoxLayout, QGridLayout, QMessageBox, QTextEdit)
from PySide6.QtCore import Slot, Qt, QTimer, QThread, Signal
from ui.pages.ui_debug_page import Ui_DebugPage
from core.hardware_mapping import PLCCoil, MFMRegister
import threading
import time

class DebugPollWorker(QThread):
    data_polled = Signal(dict)

    def __init__(self, device_manager, parent=None):
        super().__init__(parent)
        self.device_manager = device_manager
        self._is_running = False
        self._lock = threading.Lock()

    def stop(self):
        with self._lock:
            self._is_running = False

    def run(self):
        self._is_running = True
        while True:
            with self._lock:
                if not self._is_running:
                    break
            
            try:
                # 1. Check if test running
                test_running = False
                parent_widget = self.parent()
                if parent_widget and hasattr(parent_widget, 'main_window') and parent_widget.main_window:
                    mw = parent_widget.main_window
                    if hasattr(mw, 'test_page') and mw.test_page.test_runner:
                        test_running = mw.test_page.test_runner.isRunning()

                data = {
                    "test_running": test_running,
                    "coil_states": {}
                }

                # 2. Poll PLC
                plc_driver = self.device_manager.drivers.get("PLC1")
                plc_connected = plc_driver and plc_driver.is_connected
                data["plc_connected"] = plc_connected
                if plc_connected:
                    for coil_enum in PLCCoil:
                        addr = int(coil_enum)
                        if hasattr(plc_driver, "read_coil"):
                            val = plc_driver.read_coil(address=addr)
                        else:
                            val_data = plc_driver.read_data(address=addr, count=1)
                            val = bool(val_data[0]) if val_data else False
                        data["coil_states"][coil_enum] = val

                # 3. Poll Energy Meter
                meter_driver = self.device_manager.drivers.get("EnergyMeter1")
                meter_connected = meter_driver and meter_driver.is_connected
                data["meter_connected"] = meter_connected
                if meter_connected and meter_driver.__class__.__name__ == "DlmsDriver":
                    data["meter_readings"] = meter_driver.read_data()

                # 4. Poll MFM Meter 1
                mfm1_driver = self.device_manager.drivers.get("MFMMeter1")
                mfm1_connected = mfm1_driver and mfm1_driver.is_connected
                data["mfm1_connected"] = mfm1_connected
                if mfm1_connected:
                    from core.hardware_mapping import MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
                    swap_v = (MFM_REGISTER_TYPES.get("VOLTAGE", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
                    swap_i = (MFM_REGISTER_TYPES.get("CURRENT", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
                    swap_pf = (MFM_REGISTER_TYPES.get("PF", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
                    
                    v, i, pf = 0.0, 0.0, 1.0
                    block_success = False
                    if not getattr(mfm1_driver, "mock_mode", False) and hasattr(mfm1_driver, "read_data") and hasattr(mfm1_driver, "read_float"):
                        try:
                            start_addr = int(MFMRegister.VOLTAGE)
                            if start_addr >= 40001:
                                start_addr = start_addr - 40001
                            elif start_addr >= 40000:
                                start_addr = start_addr - 40000
                            
                            regs = mfm1_driver.read_data(address=start_addr, count=6, function_code=MFM_FUNCTION_CODE)
                            if len(regs) >= 6:
                                import struct
                                packed_v = struct.pack('>HH', regs[1], regs[0]) if swap_v else struct.pack('>HH', regs[0], regs[1])
                                v = struct.unpack('>f', packed_v)[0]
                                
                                packed_i = struct.pack('>HH', regs[3], regs[2]) if swap_i else struct.pack('>HH', regs[2], regs[3])
                                i = struct.unpack('>f', packed_i)[0]
                                
                                packed_pf = struct.pack('>HH', regs[5], regs[4]) if swap_pf else struct.pack('>HH', regs[4], regs[5])
                                pf = struct.unpack('>f', packed_pf)[0]
                                block_success = True
                        except Exception:
                            pass
                            
                    if not block_success:
                        if hasattr(mfm1_driver, "read_float"):
                            v = mfm1_driver.read_float(int(MFMRegister.VOLTAGE), function_code=MFM_FUNCTION_CODE, swapped=swap_v)
                            i = mfm1_driver.read_float(int(MFMRegister.CURRENT), function_code=MFM_FUNCTION_CODE, swapped=swap_i)
                            pf = mfm1_driver.read_float(int(MFMRegister.PF), function_code=MFM_FUNCTION_CODE, swapped=swap_pf)
                        else:
                            v_data = mfm1_driver.read_data(address=int(MFMRegister.VOLTAGE), count=1)
                            i_data = mfm1_driver.read_data(address=int(MFMRegister.CURRENT), count=1)
                            pf_data = mfm1_driver.read_data(address=int(MFMRegister.PF), count=1)
                            v = v_data[0] if v_data else 0.0
                            i = i_data[0] if i_data else 0.0
                            pf = pf_data[0] if pf_data else 1.0
                    data["mfm1_readings"] = (v, i, pf)

                # 5. Poll MFM Meter 2
                mfm2_driver = self.device_manager.drivers.get("MFMMeter2")
                mfm2_connected = mfm2_driver and mfm2_driver.is_connected
                data["mfm2_connected"] = mfm2_connected
                if mfm2_connected:
                    from core.hardware_mapping import MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
                    swap_i = (MFM_REGISTER_TYPES.get("CURRENT", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
                    
                    v, i, pf = None, 0.0, None
                    try:
                        # MFMMeter2 is only for mA current sensing in G7, so we avoid querying Voltage and PF to prevent errors/timeouts
                        # Register 40001 is for current reading on MFMMeter2
                        if hasattr(mfm2_driver, "read_float"):
                            i = mfm2_driver.read_float(40001, function_code=MFM_FUNCTION_CODE, swapped=swap_i)
                        else:
                            i_data = mfm2_driver.read_data(address=40001, count=1)
                            i = i_data[0] if i_data else 0.0
                    except Exception:
                        pass
                    data["mfm2_readings"] = (v, i, pf)

                # 6. Poll PicoScope
                pico_driver = self.device_manager.drivers.get("PicoScope1")
                data["pico_connected"] = pico_driver and pico_driver.is_connected

                self.data_polled.emit(data)
            except Exception:
                pass

            # Sleep 1s in 100ms intervals
            for _ in range(10):
                time.sleep(0.1)
                with self._lock:
                    if not self._is_running:
                        break

class DebugPage(QWidget, Ui_DebugPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        self.is_active = False
        self.coil_states = {}
        self.coil_lockout_times = {}
        self.worker = None
        
        # Initialize default state for all coils
        for coil in PLCCoil:
            self.coil_states[coil] = False
            self.coil_lockout_times[coil] = 0
            
        # Build the custom interactive layout programmatically
        self.build_custom_ui()

    def set_active(self, active: bool):
        """Called by MainWindow when switching between dashboard tabs."""
        self.is_active = active
        if active:
            self.worker = DebugPollWorker(self.device_manager, self)
            self.worker.data_polled.connect(self.handle_poll_results)
            self.worker.start()
        else:
            if self.worker:
                self.worker.stop()
                self.worker.wait()
                self.worker = None

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
        self.create_mfm1_card()
        self.create_mfm2_card()
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
            (PLCCoil.SCR_COIL_ADDR, "SCR COIL"),
            (PLCCoil.ACB_COIL_ADDR, "ACB COIL"),
            (PLCCoil.CONTACTOR_100mA_LOAD_BANK_COIL_ADDR, "100mA CONTACTOR"),
            (PLCCoil.CONTACTOR_120A_LOAD_BANK_COIL_ADDR, "120A CONTACTOR"),
            (PLCCoil.FCMC_TEST_START, "FCMC START"),
            (PLCCoil.SCCC_TEST_START, "SCCC START"),
            (PLCCoil.FCMCT_ACK, "FCMCT ACK"),
            (PLCCoil.PRE_FUSING_MODE_COIL_ADDR, "PRE FUSING"),
            (PLCCoil.FAULT_INDICATION_BUZZER_COIL_ADDR, "BUZZER COIL"),
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
        
        # Grid/buttons container box
        self.meter_controls_box = QGroupBox("Meter Controls")
        controls_layout = QVBoxLayout(self.meter_controls_box)
        controls_layout.setSpacing(12)
        
        # Profile selector combobox
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(10)
        lbl_profile = QLabel("Select Profile:")
        lbl_profile.setStyleSheet("font-weight: bold; color: #475569; font-size: 13px;")
        
        self.cmb_meter_profile_debug = QComboBox()
        self.cmb_meter_profile_debug.setFixedWidth(250)
        self.cmb_meter_profile_debug.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                background-color: #FFFFFF;
                color: #1E293B;
                font-size: 13px;
                min-width: 200px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                selection-background-color: #EEF2FF;
                selection-color: #4338CA;
                color: #1E293B;
            }
            QComboBox::drop-down { border-left: 1px solid #CBD5E1; }
        """)
        
        # Populate profiles
        from services.profile_manager import ProfileManager
        pm = ProfileManager()
        profiles = pm.get_all_profiles()
        for p in profiles:
            self.cmb_meter_profile_debug.addItem(f"{p.get('name')} ({p.get('communication_mode')})", p)
            
        self.cmb_meter_profile_debug.currentIndexChanged.connect(self._on_meter_profile_changed_debug)
        
        profile_layout.addWidget(lbl_profile)
        profile_layout.addWidget(self.cmb_meter_profile_debug)
        profile_layout.addStretch()
        controls_layout.addLayout(profile_layout)
        
        # Horizontal layout for the buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.btn_load_switch_on = QPushButton("LOAD SWITCH ON")
        self.btn_load_switch_on.clicked.connect(lambda: self.send_meter_command_debug("close_load_switch"))
        
        self.btn_load_switch_off = QPushButton("LOAD SWITCH OFF")
        self.btn_load_switch_off.clicked.connect(lambda: self.send_meter_command_debug("open_load_switch"))
        
        self.btn_read_serial = QPushButton("Read Serial Number")
        self.btn_read_serial.clicked.connect(lambda: self.send_meter_command_debug("read_serial_number"))
        
        # Set styles for the buttons
        self.btn_load_switch_on.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_load_switch_off.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        self.btn_read_serial.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: #FFFFFF;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        
        buttons_layout.addWidget(self.btn_load_switch_on)
        buttons_layout.addWidget(self.btn_load_switch_off)
        buttons_layout.addWidget(self.btn_read_serial)
        buttons_layout.addStretch()
        
        controls_layout.addLayout(buttons_layout)
        
        # Result console
        lbl_console = QLabel("Result Output:")
        lbl_console.setStyleSheet("font-weight: bold; color: #94A3B8; font-size: 12px;")
        controls_layout.addWidget(lbl_console)
        
        self.txt_meter_console = QTextEdit()
        self.txt_meter_console.setReadOnly(True)
        self.txt_meter_console.setMaximumHeight(150)
        
        # Initial driver type configuration
        if self.cmb_meter_profile_debug.count() > 0:
            self._on_meter_profile_changed_debug(self.cmb_meter_profile_debug.currentIndex())
        
        controls_layout.addWidget(self.txt_meter_console)
        
        layout.addWidget(self.meter_controls_box)
        self.scroll_layout.addWidget(card)

    def create_mfm1_card(self):
        card, layout, header, self.lbl_mfm1_led, self.lbl_mfm1_status, self.btn_mfm1_connect = self.create_card_frame("3. MFM METER 1")
        self.btn_mfm1_connect.clicked.connect(lambda: self.toggle_device_connection("MFMMeter1"))
        
        # Instantaneous readings
        self.mfm1_readings_box = QGroupBox("Instantaneous Readings")
        readings_layout = QGridLayout(self.mfm1_readings_box)
        readings_layout.setSpacing(15)
        
        lbl_v = QLabel(f"Voltage (Reg {int(MFMRegister.VOLTAGE)}):")
        self.lbl_mfm1_val_v = QLabel("--- V")
        self.lbl_mfm1_val_v.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_i = QLabel(f"Current (Reg {int(MFMRegister.CURRENT)}):")
        self.lbl_mfm1_val_i = QLabel("--- A")
        self.lbl_mfm1_val_i.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        lbl_pf = QLabel(f"Power Factor (Reg {int(MFMRegister.PF)}):")
        self.lbl_mfm1_val_pf = QLabel("---")
        self.lbl_mfm1_val_pf.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        readings_layout.addWidget(lbl_v, 0, 0)
        readings_layout.addWidget(self.lbl_mfm1_val_v, 0, 1)
        readings_layout.addWidget(lbl_i, 0, 2)
        readings_layout.addWidget(self.lbl_mfm1_val_i, 0, 3)
        readings_layout.addWidget(lbl_pf, 0, 4)
        readings_layout.addWidget(self.lbl_mfm1_val_pf, 0, 5)
        
        layout.addWidget(self.mfm1_readings_box)
        
        # Modbus registers utility
        self.mfm1_utility_box = QGroupBox("Modbus Register Utility")
        modbus_layout = QVBoxLayout(self.mfm1_utility_box)
        
        input_layout = QHBoxLayout()
        self.le_mfm1_reg_addr = QLineEdit()
        self.le_mfm1_reg_addr.setPlaceholderText("Address (e.g. 256 or 0x0100)")
        
        self.le_mfm1_reg_count = QLineEdit()
        self.le_mfm1_reg_count.setPlaceholderText("Count (default 1)")
        
        self.le_mfm1_reg_val = QLineEdit()
        self.le_mfm1_reg_val.setPlaceholderText("Write Value")
        
        btn_reg_read = QPushButton("Read Register")
        btn_reg_read.clicked.connect(lambda: self.read_mfm_registers_specific("MFMMeter1"))
        
        btn_reg_write = QPushButton("Write Register")
        btn_reg_write.clicked.connect(lambda: self.write_mfm_registers_specific("MFMMeter1"))
        
        self.style_action_buttons(btn_reg_read, btn_reg_write)
        
        input_layout.addWidget(self.le_mfm1_reg_addr)
        input_layout.addWidget(self.le_mfm1_reg_count)
        input_layout.addWidget(self.le_mfm1_reg_val)
        input_layout.addWidget(btn_reg_read)
        input_layout.addWidget(btn_reg_write)
        modbus_layout.addLayout(input_layout)
        
        self.txt_mfm1_console = QTextEdit()
        self.txt_mfm1_console.setReadOnly(True)
        self.txt_mfm1_console.setMaximumHeight(100)
        
        modbus_layout.addWidget(self.txt_mfm1_console)
        layout.addWidget(self.mfm1_utility_box)
        self.scroll_layout.addWidget(card)

    def create_mfm2_card(self):
        card, layout, header, self.lbl_mfm2_led, self.lbl_mfm2_status, self.btn_mfm2_connect = self.create_card_frame("4. MFM METER 2")
        self.btn_mfm2_connect.clicked.connect(lambda: self.toggle_device_connection("MFMMeter2"))
        
        # Instantaneous readings
        self.mfm2_readings_box = QGroupBox("Instantaneous Readings")
        readings_layout = QGridLayout(self.mfm2_readings_box)
        readings_layout.setSpacing(15)
        
        lbl_i = QLabel("Current (Reg 40001):")
        self.lbl_mfm2_val_i = QLabel("--- A")
        self.lbl_mfm2_val_i.setStyleSheet("font-weight: bold; color: #38BDF8; font-size: 16px;")
        
        readings_layout.addWidget(lbl_i, 0, 0)
        readings_layout.addWidget(self.lbl_mfm2_val_i, 0, 1)
        
        layout.addWidget(self.mfm2_readings_box)
        
        # Modbus registers utility
        self.mfm2_utility_box = QGroupBox("Modbus Register Utility")
        modbus_layout = QVBoxLayout(self.mfm2_utility_box)
        
        input_layout = QHBoxLayout()
        self.le_mfm2_reg_addr = QLineEdit()
        self.le_mfm2_reg_addr.setPlaceholderText("Address (e.g. 256 or 0x0100)")
        
        self.le_mfm2_reg_count = QLineEdit()
        self.le_mfm2_reg_count.setPlaceholderText("Count (default 1)")
        
        self.le_mfm2_reg_val = QLineEdit()
        self.le_mfm2_reg_val.setPlaceholderText("Write Value")
        
        btn_reg_read = QPushButton("Read Register")
        btn_reg_read.clicked.connect(lambda: self.read_mfm_registers_specific("MFMMeter2"))
        
        btn_reg_write = QPushButton("Write Register")
        btn_reg_write.clicked.connect(lambda: self.write_mfm_registers_specific("MFMMeter2"))
        
        self.style_action_buttons(btn_reg_read, btn_reg_write)
        
        input_layout.addWidget(self.le_mfm2_reg_addr)
        input_layout.addWidget(self.le_mfm2_reg_count)
        input_layout.addWidget(self.le_mfm2_reg_val)
        input_layout.addWidget(btn_reg_read)
        input_layout.addWidget(btn_reg_write)
        modbus_layout.addLayout(input_layout)
        
        self.txt_mfm2_console = QTextEdit()
        self.txt_mfm2_console.setReadOnly(True)
        self.txt_mfm2_console.setMaximumHeight(100)
        
        modbus_layout.addWidget(self.txt_mfm2_console)
        layout.addWidget(self.mfm2_utility_box)
        self.scroll_layout.addWidget(card)

    def create_picoscope_card(self):
        card, layout, header, self.lbl_picoscope_led, self.lbl_picoscope_status, self.btn_picoscope_connect = self.create_card_frame("5. PICOSCOPE OSCILLOSCOPE")
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
                num_points = len(data[0]) if (isinstance(data, list) and len(data) == 2 and isinstance(data[0], list)) else len(data)
                self.txt_picoscope_console.append(f"<< Success: Captured {num_points} points.")
                from ui.widgets.waveform_card import WaveformCard
                timebase = pico_driver.timebase
                voltage_range = 10
                
                card = WaveformCard("Debug Capture", data, timebase, voltage_range, self, test_id="debug")
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
        if hasattr(self, 'btn_mfm1_connect'):
            self.btn_mfm1_connect.setStyleSheet(self.get_connect_button_style())
        if hasattr(self, 'btn_mfm2_connect'):
            self.btn_mfm2_connect.setStyleSheet(self.get_connect_button_style())
        if hasattr(self, 'btn_picoscope_connect'):
            self.btn_picoscope_connect.setStyleSheet(self.get_connect_button_style())
        
        # 2. Update consoles
        self.txt_meter_console.setStyleSheet(self.get_console_style())
        if hasattr(self, 'txt_mfm1_console'):
            self.txt_mfm1_console.setStyleSheet(self.get_console_style())
        if hasattr(self, 'txt_mfm2_console'):
            self.txt_mfm2_console.setStyleSheet(self.get_console_style())
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
        
        if hasattr(self, 'lbl_mfm1_led'):
            mfm1_driver = self.device_manager.drivers.get("MFMMeter1")
            self.update_connection_led(self.lbl_mfm1_led, self.lbl_mfm1_status, mfm1_driver and mfm1_driver.is_connected)
            
        if hasattr(self, 'lbl_mfm2_led'):
            mfm2_driver = self.device_manager.drivers.get("MFMMeter2")
            self.update_connection_led(self.lbl_mfm2_led, self.lbl_mfm2_status, mfm2_driver and mfm2_driver.is_connected)
        
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
        
        import time
        # Optimistic UI Update (Instantaneous Feedback)
        self.coil_states[coil_enum] = new_val
        self.coil_lockout_times[coil_enum] = time.time()
        self.update_coil_led(coil_enum, new_val)
        
        def write_task():
            try:
                if hasattr(plc_driver, "write_coil"):
                    success = plc_driver.write_coil(address=addr, value=new_val)
                else:
                    success = plc_driver.write_data(address=addr, value=1 if new_val else 0)
                    
                if success:
                    from PySide6.QtCore import QMetaObject, Qt, Q_ARG
                    QMetaObject.invokeMethod(self.main_window, "append_log", 
                                             Qt.QueuedConnection, 
                                             Q_ARG(str, "INFO"), 
                                             Q_ARG(str, f"Debug Screen: PLC coil {coil_enum.name} (0x{addr:02X}) set to {new_val}"))
                # If it fails, we don't show a blocking QMessageBox. 
                # The DebugPollWorker will automatically revert the UI state on its next poll cycle.
            except Exception as e:
                pass
                
        # Run write operation in a background thread to prevent UI blocking
        threading.Thread(target=write_task, daemon=True).start()

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
            
            if is_coil and hasattr(plc_driver, "read_coil"):
                val = plc_driver.read_coil(address=addr)
                self.lbl_plc_gen_result.setText(f"Result: {val}")
            else:
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
                val = val_str.lower() in ("true", "1", "on", "yes")
                if hasattr(plc_driver, "write_coil"):
                    success = plc_driver.write_coil(address=addr, value=val)
                else:
                    success = plc_driver.write_data(address=addr, value=1 if val else 0)
            else:
                val = int(val_str, 0)
                success = plc_driver.write_data(address=addr, value=val)
            self.lbl_plc_gen_result.setText("Result: Success" if success else "Result: Failed")
        except Exception as e:
            self.lbl_plc_gen_result.setText(f"Error: {e}")

    def _on_meter_profile_changed_debug(self, index):
        profile = self.cmb_meter_profile_debug.currentData()
        if profile:
            mode = profile.get("communication_mode", "DLMS").lower()
            self.device_manager.switch_device_type("EnergyMeter1", mode)
            if hasattr(self, 'txt_meter_console'):
                self.txt_meter_console.append(f">> Switched Energy Meter type to: {mode.upper()}")

    def send_meter_command_debug(self, command_key: str):
        profile = self.cmb_meter_profile_debug.currentData()
        if not profile:
            self.txt_meter_console.append("Error: No meter profile selected.")
            return

        # Send unlock before switch operation if unlock is configured and has a value
        if command_key in ["close_load_switch", "open_load_switch"]:
            unlock_cmd = profile.get("commands", {}).get("unlock")
            if unlock_cmd and unlock_cmd.get("value"):
                self.txt_meter_console.append(">> Auto-sending unlock command first...")
                self._execute_single_command_debug(profile, "unlock")
                time.sleep(0.2)
        
        self._execute_single_command_debug(profile, command_key)

    def _execute_single_command_debug(self, profile: dict, key: str):
        cmd_data = profile.get("commands", {}).get(key)
        if not cmd_data:
            self.txt_meter_console.append(f"Error: Command '{key}' not mapped in profile '{profile.get('name')}'.")
            return
            
        val = cmd_data.get("value", "")
        if not val:
            self.txt_meter_console.append(f"Error: Value for command '{key}' is empty.")
            return

        fmt = cmd_data.get("format", "Hex").lower()
        mode = profile.get("communication_mode", "DLMS").lower()
        
        self.txt_meter_console.append(f">> Sending Command '{key}' via {profile.get('communication_mode')}: {val} [{cmd_data.get('format')}]")
        
        drv = self.device_manager.drivers.get("EnergyMeter1")
        if not drv:
            self.txt_meter_console.append("Error: Energy Meter driver is unavailable.")
            return
            
        if not drv.is_connected:
            self.txt_meter_console.append(">> Energy Meter is disconnected. Attempting connection...")
            if not drv.connect():
                self.txt_meter_console.append("<< Error: Failed to connect to Energy Meter.")
                return
            self.txt_meter_console.append("<< Successfully connected to Energy Meter.")
            
        try:
            if mode == "serial":
                serial_settings = profile.get("serial_settings", {})
                write_term = serial_settings.get("write_terminator", "\\r\\n")
                term_bytes_map = {
                    "\\r\\n": b'\r\n',
                    "\\r": b'\r',
                    "\\n": b'\n',
                    "None": b''
                }
                term_bytes = term_bytes_map.get(write_term, b'\r\n')

                # Prepare payload
                if fmt == "hex":
                    payload = bytes.fromhex(val.replace(" ", ""))
                else:
                    val_processed = val.replace("<CR>", "\r").replace("<LF>", "\n")
                    payload = val_processed.encode('ascii')
                    if not (payload.endswith(b'\r') or payload.endswith(b'\n')):
                        payload += term_bytes
                
                if hasattr(drv, "serial_conn") and drv.serial_conn:
                    drv.serial_conn.reset_input_buffer()
                    
                success = drv.write_data(payload)
                if success:
                    expected_term_hex = cmd_data.get("expected_terminator", "")
                    expected_resp_hex = cmd_data.get("expected_response", "")
                    
                    term = bytes.fromhex(expected_term_hex.replace(" ", "")) if expected_term_hex else (term_bytes if term_bytes else b'\r\n')
                    exp_resp = bytes.fromhex(expected_resp_hex.replace(" ", "")) if expected_resp_hex else b''
                    
                    # Read response
                    response = drv.read_until(term, timeout=2.0)
                    if not response:
                        self.txt_meter_console.append("<< Error: Meter did not respond within timeout.")
                        return
                        
                    resp_str = response.hex().upper() if fmt == 'hex' else response.decode('utf-8', errors='ignore').strip()
                    self.txt_meter_console.append(f"<< Response: {resp_str}")
                    
                    if exp_resp and exp_resp not in response:
                        self.txt_meter_console.append(f"<< Error: Expected response '{exp_resp.hex()}' not found.")
                else:
                    self.txt_meter_console.append("<< Error: Failed to write serial data.")
            elif mode == "dlms":
                obis = val
                res = drv.read_data(obis)
                self.txt_meter_console.append(f"<< DLMS Result: {res}")
        except Exception as e:
            self.txt_meter_console.append(f"<< Error: {e}")

    def read_mfm_registers_specific(self, device_name: str):
        mfm_driver = self.device_manager.drivers.get(device_name)
        suffix = "1" if device_name == "MFMMeter1" else "2"
        console = getattr(self, f"txt_mfm{suffix}_console")
        le_addr = getattr(self, f"le_mfm{suffix}_reg_addr")
        le_count = getattr(self, f"le_mfm{suffix}_reg_count")
        
        if not mfm_driver or not mfm_driver.is_connected:
            console.append(f"{device_name} is disconnected.")
            return
        try:
            addr_str = le_addr.text().strip()
            if not addr_str: return
            addr = int(addr_str, 0)
            count = int(le_count.text().strip() or "1")
            
            console.append(f">> Read Reg: {addr} (count={count})")
            res = mfm_driver.read_data(address=addr, count=count)
            console.append(f"<< Value: {res}")
        except Exception as e:
            console.append(f"<< Error: {e}")

    def write_mfm_registers_specific(self, device_name: str):
        mfm_driver = self.device_manager.drivers.get(device_name)
        suffix = "1" if device_name == "MFMMeter1" else "2"
        console = getattr(self, f"txt_mfm{suffix}_console")
        le_addr = getattr(self, f"le_mfm{suffix}_reg_addr")
        le_val = getattr(self, f"le_mfm{suffix}_reg_val")
        
        if not mfm_driver or not mfm_driver.is_connected:
            console.append(f"{device_name} is disconnected.")
            return
        try:
            addr_str = le_addr.text().strip()
            val_str = le_val.text().strip()
            if not addr_str or not val_str: return
            addr = int(addr_str, 0)
            val = int(val_str, 0)
            
            console.append(f">> Write Reg: {addr} = {val}")
            success = mfm_driver.write_data(address=addr, value=val)
            console.append(f"<< Write result: {'Success' if success else 'Failed'}")
        except Exception as e:
            console.append(f"<< Error: {e}")

    @Slot(dict)
    def handle_poll_results(self, data: dict):
        if not self.is_active:
            return

        test_running = data.get("test_running", False)
        self.lbl_lock_status.setVisible(test_running)
        
        # Disable/Enable debug controls depending on test_running
        self.plc_grid_box.setEnabled(not test_running)
        self.plc_gen_box.setEnabled(not test_running)
        self.meter_controls_box.setEnabled(not test_running)
        if hasattr(self, 'mfm1_utility_box'):
            self.mfm1_utility_box.setEnabled(not test_running)
        if hasattr(self, 'mfm2_utility_box'):
            self.mfm2_utility_box.setEnabled(not test_running)
        if hasattr(self, 'picoscope_box'):
            self.picoscope_box.setEnabled(not test_running)
            self.btn_picoscope_connect.setEnabled(not test_running)
        self.btn_plc_connect.setEnabled(not test_running)
        self.btn_meter_connect.setEnabled(not test_running)
        if hasattr(self, 'btn_mfm1_connect'):
            self.btn_mfm1_connect.setEnabled(not test_running)
        if hasattr(self, 'btn_mfm2_connect'):
            self.btn_mfm2_connect.setEnabled(not test_running)

        # 2. Update PLC
        self.update_connection_led(self.lbl_plc_led, self.lbl_plc_status, data.get("plc_connected", False))
        
        import time
        current_time = time.time()
        for coil_enum, val in data.get("coil_states", {}).items():
            last_toggled = getattr(self, "coil_lockout_times", {}).get(coil_enum, 0)
            if current_time - last_toggled > 1.5:  # Lockout polling updates for 1.5s after toggle to prevent flicker
                self.update_coil_led(coil_enum, val)

        # 3. Update Energy Meter
        self.update_connection_led(self.lbl_meter_led, self.lbl_meter_status, data.get("meter_connected", False))

        # 4. Update MFM Meter 1
        if hasattr(self, 'lbl_mfm1_led'):
            self.update_connection_led(self.lbl_mfm1_led, self.lbl_mfm1_status, data.get("mfm1_connected", False))
        m1_vals = data.get("mfm1_readings")
        if m1_vals is not None:
            v, i, pf = m1_vals
            self.lbl_mfm1_val_v.setText(f"{v:.1f} V")
            self.lbl_mfm1_val_i.setText(f"{i:.3f} A")
            self.lbl_mfm1_val_pf.setText(f"{pf:.2f}")

        # 5. Update MFM Meter 2
        if hasattr(self, 'lbl_mfm2_led'):
            self.update_connection_led(self.lbl_mfm2_led, self.lbl_mfm2_status, data.get("mfm2_connected", False))
        m2_vals = data.get("mfm2_readings")
        if m2_vals is not None:
            v, i, pf = m2_vals
            if hasattr(self, "lbl_mfm2_val_i"):
                self.lbl_mfm2_val_i.setText(f"{i:.3f} A")

        # 6. Update PicoScope
        if hasattr(self, 'lbl_picoscope_led'):
            self.update_connection_led(self.lbl_picoscope_led, self.lbl_picoscope_status, data.get("pico_connected", False))
