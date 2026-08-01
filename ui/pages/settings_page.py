from PySide6.QtWidgets import QWidget, QPushButton, QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFormLayout, QCheckBox, QLineEdit, QMessageBox, QComboBox, QLabel
from PySide6.QtCore import Slot, Qt
from ui.pages.ui_settings_page import Ui_SettingsPage


class SettingsPage(QWidget, Ui_SettingsPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        
        self.frame_appearance.hide()
        self.btn_connect_all.clicked.connect(self._on_connect_all_clicked)
        
        # Wire DeviceManager signals for live feedback
        self.device_manager.hw_status_summary.connect(self._on_hw_summary)
        self.device_manager.device_status_changed.connect(self._on_device_status_changed)
        
        self._validate_buttons = {}  # device_name -> QPushButton (populated in _init_hw_config_ui)
        
        self._init_hw_config_ui()
    
    @Slot()
    def _on_connect_all_clicked(self):
        """Triggers connect_all with visual feedback on the button."""
        self.btn_connect_all.setText("Connecting...")
        self.btn_connect_all.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
        self.btn_connect_all.setEnabled(False)
        self.device_manager.connect_all()
    
    @Slot(str, bool)
    def _on_hw_summary(self, summary: str, all_ok: bool):
        """Updates the Connect All button when all connections are resolved."""
        self.btn_connect_all.setEnabled(True)
        if all_ok:
            self.btn_connect_all.setText("All Connected ✓")
            self.btn_connect_all.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold;")
        elif "Connecting" in summary:
            return  # Still in progress
        else:
            self.btn_connect_all.setText("Connect All HW")
            self.btn_connect_all.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
        
        # Reset style after 5 seconds
        from PySide6.QtCore import QTimer
        QTimer.singleShot(5000, self._reset_connect_btn_style)
    
    def _reset_connect_btn_style(self):
        self.btn_connect_all.setText("Connect All HW")
        self.btn_connect_all.setStyleSheet("")
    
    @Slot(str, bool)
    def _on_device_status_changed(self, device_name: str, success: bool):
        """Updates individual Validate buttons when connection status changes."""
        btn = self._validate_buttons.get(device_name)
        if btn:
            if success:
                btn.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold;")
                btn.setText("Connected")
            else:
                btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
                btn.setText("Failed")

    def _init_hw_config_ui(self):
        self.hw_config_box = QGroupBox("Device Configuration")
        self.hw_config_layout = QVBoxLayout()
        self.hw_config_box.setLayout(self.hw_config_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("scroll_widget")
        self.scroll_widget.setStyleSheet("#scroll_widget { background-color: transparent; }")
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(20)
        self.scroll.setWidget(self.scroll_widget)
        self.hw_config_layout.addWidget(self.scroll)
        
        self.device_forms = []
        
        config = self.device_manager.config_service.get_config()
        devices = config.get("devices", [])
        
        # Sort devices: PLC, Energy Meter, MFM Meter
        def get_order(dev):
            name = dev.get('name', '').lower()
            if 'plc' in name: return 0
            if 'energymeter' in name: return 1
            if 'mfmmeter' in name: return 2
            return 99
            
        devices = sorted(devices, key=get_order)
        
        row = 0
        
        # Headers
        headers = ["Device", "Configuration", "Action"]
        for i, text in enumerate(headers):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-weight: bold; color: #94A3B8; text-transform: uppercase; padding-bottom: 8px;")
            self.scroll_layout.addWidget(lbl, row, i)
        row += 1
        
        for dev in devices:
            original_name = dev.get('name', 'Unknown')
            if 'picoscope' in original_name.lower() or dev.get('type', '').lower() == 'picoscope':
                continue
                
            display_name = original_name[:-1] if original_name.endswith('1') else original_name
            device_type = dev.get('type', 'Unknown')
            
            lbl_dev = QLabel(display_name)
            lbl_dev.setStyleSheet("font-weight: bold;")
            lbl_dev.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            config_widget = QWidget()
            config_layout = QHBoxLayout(config_widget)
            config_layout.setContentsMargins(0, 0, 0, 0)
            config_layout.setSpacing(15)
            config_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            
            inputs = {}
            for key, val in dev.items():
                if key in ['name', 'type', 'mock']:
                    continue
                
                display_key = "IP" if key.lower() == 'ip' else key.capitalize()
                lbl_prop = QLabel(f"{display_key}:")
                lbl_prop.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                
                if key == 'port' and ('serial' in dev.get('type', '') or 'modbus' in dev.get('type', '') or 'dlms' in dev.get('type', '')):
                    import serial.tools.list_ports
                    cb = QComboBox()
                    available_ports = [port.device for port in serial.tools.list_ports.comports()]
                    current_val = str(val)
                    if current_val and current_val not in available_ports:
                        available_ports.append(current_val)
                    cb.addItems(available_ports)
                    cb.setCurrentText(current_val)
                    cb.setMinimumWidth(120)
                    input_widget = cb
                else:
                    le = QLineEdit(str(val))
                    le.setMinimumWidth(120)
                    le.setMaximumWidth(200)
                    input_widget = le
                    
                config_layout.addWidget(lbl_prop)
                config_layout.addWidget(input_widget)
                inputs[key] = input_widget
                
            config_layout.addStretch()
                
            btn_validate = QPushButton("Validate")
            btn_validate.setFixedWidth(120)
            btn_validate.clicked.connect(lambda checked=False, name=original_name, btn=btn_validate: self._validate_device(name, btn))
            self._validate_buttons[original_name] = btn_validate
            
            self.scroll_layout.addWidget(lbl_dev, row, 0, Qt.AlignmentFlag.AlignVCenter)
            self.scroll_layout.addWidget(config_widget, row, 1, Qt.AlignmentFlag.AlignVCenter)
            self.scroll_layout.addWidget(btn_validate, row, 2, Qt.AlignmentFlag.AlignVCenter)
            
            row += 1
            self.device_forms.append((original_name, dev.get('type'), inputs))
                
        self.scroll_layout.setColumnStretch(3, 1)
        self.scroll_layout.setRowStretch(row, 1)
            
        self.btn_save_hw = QPushButton("Save Hardware Config")
        self.btn_save_hw.clicked.connect(self._save_hw_config)
        self.hw_config_layout.addWidget(self.btn_save_hw)
        
        # Insert Report Config Box
        self.report_config_box = QGroupBox("Report Fields Configuration")
        self.report_config_layout = QVBoxLayout(self.report_config_box)
        self.report_config_layout.setSpacing(10)
        
        report_fields = config.get("testing", {}).get("report_fields", {
            "voltage_vrms": True,
            "current_apk": True,
            "duration_ms": True,
            "pf": True
        })
        
        self.chk_voltage = QCheckBox("Voltage (Vrms)")
        self.chk_voltage.setChecked(report_fields.get("voltage_vrms", True))
        self.chk_current = QCheckBox("Current (Apk)")
        self.chk_current.setChecked(report_fields.get("current_apk", True))
        self.chk_duration = QCheckBox("Duration (ms)")
        self.chk_duration.setChecked(report_fields.get("duration_ms", True))
        self.chk_pf = QCheckBox("Power Factor (PF)")
        self.chk_pf.setChecked(report_fields.get("pf", True))
        
        report_row1 = QHBoxLayout()
        report_row1.addWidget(self.chk_voltage)
        report_row1.addWidget(self.chk_current)
        report_row1.addStretch()
        
        report_row2 = QHBoxLayout()
        report_row2.addWidget(self.chk_duration)
        report_row2.addWidget(self.chk_pf)
        report_row2.addStretch()
        
        self.report_config_layout.addLayout(report_row1)
        self.report_config_layout.addLayout(report_row2)
        
        # Insert them before the bottom spacer in the existing layout
        count = self.verticalLayout_settings.count()
        self.verticalLayout_settings.insertWidget(count - 1, self.hw_config_box)
        self.verticalLayout_settings.insertWidget(count - 1, self.report_config_box)

    @Slot(str, object)
    def _validate_device(self, device_name, btn):
        driver = self.device_manager.drivers.get(device_name)
        if not driver:
            QMessageBox.warning(self, "Validation Failed", f"Driver for {device_name} not found.")
            return

        # Attempt to save current inputs in the UI so driver has the latest details?
        # The user has to click Save Hardware Config to commit to the file, but we could update driver config here.
        # For simplicity, we just use the current driver state, or the user should save first.

        if "plc" in device_name.lower():
            success = driver.connect()
            if success:
                btn.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold;")
                btn.setText("Connected")
            else:
                btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
                btn.setText("Failed")
        elif "mfm" in device_name.lower():
            success = driver.connect()
            if not success:
                btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
                btn.setText("Failed")
                return
            
            from core.hardware_mapping import MFMRegister, MFM_FUNCTION_CODE, MFM_REGISTER_TYPES
            try:
                # Use read_float helper if available
                if hasattr(driver, "read_float"):
                    swap_v = (MFM_REGISTER_TYPES.get("VOLTAGE", "SWAPPED_FLOAT") == "SWAPPED_FLOAT")
                    voltage = driver.read_float(address=int(MFMRegister.VOLTAGE), function_code=MFM_FUNCTION_CODE, swapped=swap_v)
                    btn.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold;")
                    btn.setText(f"V: {voltage:.1f}")
                else:
                    data = driver.read_data(address=int(MFMRegister.VOLTAGE), count=2)
                    if data and len(data) > 0:
                        # Fallback simple float decode or just check data exists
                        btn.setStyleSheet("background-color: #22C55E; color: white; font-weight: bold;")
                        btn.setText("Connected")
                    else:
                        btn.setStyleSheet("background-color: #F59E0B; color: white; font-weight: bold;")
                        btn.setText("No Data")
            except Exception as e:
                btn.setStyleSheet("background-color: #EF4444; color: white; font-weight: bold;")
                btn.setText("Error")
                self.main_window.append_log("ERROR", f"MFM Validation error: {e}")
        else:
            QMessageBox.information(self, "Validation", "Validation for this device will be implemented later.")

    @Slot()
    def _save_hw_config(self):
        config_service = self.device_manager.config_service
        config = config_service.get_config()
        
        forms_data = {name: (dtype, inputs) for name, dtype, inputs in self.device_forms}
        
        new_devices = []
        for d in config.get("devices", []):
            name = d.get("name")
            if name in forms_data:
                dtype, inputs = forms_data[name]
                dev = d.copy()
                dev["name"] = name
                dev["type"] = dtype
                for key, widget in inputs.items():
                    if isinstance(widget, QCheckBox):
                        dev[key] = widget.isChecked()
                    elif isinstance(widget, QComboBox):
                        dev[key] = widget.currentText()
                    else:
                        val = widget.text()
                        try:
                            dev[key] = int(val)
                        except ValueError:
                            try:
                                dev[key] = float(val)
                            except ValueError:
                                dev[key] = val
                new_devices.append(dev)
            else:
                new_devices.append(d.copy() if isinstance(d, dict) else d)
                
        existing_names = {d.get("name") for d in config.get("devices", []) if isinstance(d, dict)}
        for name, dtype, inputs in self.device_forms:
            if name not in existing_names:
                dev = {"name": name, "type": dtype}
                for key, widget in inputs.items():
                    if isinstance(widget, QCheckBox):
                        dev[key] = widget.isChecked()
                    elif isinstance(widget, QComboBox):
                        dev[key] = widget.currentText()
                    else:
                        val = widget.text()
                        try:
                            dev[key] = int(val)
                        except ValueError:
                            try:
                                dev[key] = float(val)
                            except ValueError:
                                dev[key] = val
                new_devices.append(dev)
            
        config["devices"] = new_devices
        
        # Save Report fields configuration
        if "testing" not in config:
            config["testing"] = {}
        if "report_fields" not in config["testing"]:
            config["testing"]["report_fields"] = {}
            
        config["testing"]["report_fields"]["voltage_vrms"] = self.chk_voltage.isChecked()
        config["testing"]["report_fields"]["current_apk"] = self.chk_current.isChecked()
        config["testing"]["report_fields"]["duration_ms"] = self.chk_duration.isChecked()
        config["testing"]["report_fields"]["pf"] = self.chk_pf.isChecked()
        
        try:
            import json
            with open(config_service.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            # Reload dynamically
            self.device_manager.reload_devices()
            
            # QMessageBox.information(self, "Success", "Hardware configuration saved and devices reloaded dynamically.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

