from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QLineEdit, 
                               QCheckBox, QPushButton, QLabel, QFrame, QMessageBox, QScrollArea)
from PySide6.QtCore import Slot, Qt
from ui.pages.ui_settings_page import Ui_SettingsPage

class SettingsPage(QWidget, Ui_SettingsPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        
        self.btn_toggle_theme.clicked.connect(self.main_window.toggle_theme)
        self.btn_connect_all.clicked.connect(self.device_manager.connect_all)
        
        self._build_device_config_ui()

    def _build_device_config_ui(self):
        # Create a container for device settings
        self.device_config_frame = QFrame()
        self.device_config_frame.setObjectName("frame_device_config")
        self.device_config_frame.setStyleSheet("""
            QFrame#frame_device_config {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.device_layout = QVBoxLayout(self.device_config_frame)
        
        lbl_title = QLabel("Device Configurations")
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
        self.device_layout.addWidget(lbl_title)
        
        self.device_inputs = {}
        
        devices = self.device_manager.config_service.get_devices()
        for dev in devices:
            dev_name = dev.get("name")
            dev_frame = QFrame()
            dev_frame.setStyleSheet("border-bottom: 1px solid #E2E8F0; padding-bottom: 5px;")
            form = QFormLayout(dev_frame)
            
            lbl_dev = QLabel(f"{dev_name} ({dev.get('type')})")
            lbl_dev.setStyleSheet("font-weight: bold; color: #475569;")
            form.addRow(lbl_dev)
            
            inputs = {}
            
            if "ip" in dev:
                ip_input = QLineEdit(dev["ip"])
                form.addRow("IP Address:", ip_input)
                inputs["ip"] = ip_input
                
            if "port" in dev:
                port_input = QLineEdit(str(dev["port"]))
                form.addRow("Port/COM:", port_input)
                inputs["port"] = port_input
                
            if "baudrate" in dev:
                baud_input = QLineEdit(str(dev["baudrate"]))
                form.addRow("Baudrate:", baud_input)
                inputs["baudrate"] = baud_input
                
            mock_checkbox = QCheckBox()
            mock_checkbox.setChecked(dev.get("mock", True))
            form.addRow("Mock Mode:", mock_checkbox)
            inputs["mock"] = mock_checkbox
            
            self.device_inputs[dev_name] = inputs
            self.device_layout.addWidget(dev_frame)
            
        self.btn_save_devices = QPushButton("Save Device Configurations")
        self.btn_save_devices.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        self.btn_save_devices.clicked.connect(self._save_device_configs)
        self.device_layout.addWidget(self.btn_save_devices)
        
        # Insert into the main layout before the bottom spacer
        index = self.verticalLayout_settings.count() - 1
        self.verticalLayout_settings.insertWidget(index, self.device_config_frame)

    @Slot()
    def _save_device_configs(self):
        config = self.device_manager.config_service.get_config()
        devices = config.get("devices", [])
        
        for dev in devices:
            dev_name = dev.get("name")
            if dev_name in self.device_inputs:
                inputs = self.device_inputs[dev_name]
                
                if "ip" in inputs:
                    dev["ip"] = inputs["ip"].text()
                if "port" in inputs:
                    # try to parse as int if possible, otherwise string (COM port)
                    val = inputs["port"].text()
                    dev["port"] = int(val) if val.isdigit() else val
                if "baudrate" in inputs:
                    dev["baudrate"] = int(inputs["baudrate"].text())
                if "mock" in inputs:
                    dev["mock"] = inputs["mock"].isChecked()
                    
        config["devices"] = devices
        success = self.device_manager.config_service.save_config(config)
        
        if success:
            QMessageBox.information(self, "Success", 
                "Device configurations saved successfully.\nPlease restart the application or reconnect hardware for changes to take effect.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save device configurations.")
