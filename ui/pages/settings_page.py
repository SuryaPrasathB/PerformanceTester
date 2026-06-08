from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Slot
from ui.pages.ui_settings_page import Ui_SettingsPage
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QScrollArea, QFormLayout, QCheckBox, QLineEdit, QMessageBox


class SettingsPage(QWidget, Ui_SettingsPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        
        self.btn_toggle_theme.clicked.connect(self.main_window.toggle_theme)
        self.btn_connect_all.clicked.connect(self.device_manager.connect_all)
        self._init_hw_config_ui()
    def _init_hw_config_ui(self):
        self.hw_config_box = QGroupBox("Device Configuration")
        self.hw_config_layout = QVBoxLayout()
        self.hw_config_box.setLayout(self.hw_config_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll.setWidget(self.scroll_widget)
        self.hw_config_layout.addWidget(self.scroll)
        
        self.device_forms = []
        
        config = self.device_manager.config_service.get_config()
        devices = config.get("devices", [])
        
        for dev in devices:
            dev_group = QGroupBox(f"{dev.get('name', 'Unknown')} ({dev.get('type', 'Unknown')})")
            form = QFormLayout()
            
            inputs = {}
            for key, val in dev.items():
                if key in ['name', 'type']:
                    continue
                
                if isinstance(val, bool) or key == 'mock':
                    cb = QCheckBox()
                    cb.setChecked(bool(val))
                    form.addRow(f"{key}:", cb)
                    inputs[key] = cb
                else:
                    le = QLineEdit(str(val))
                    form.addRow(f"{key}:", le)
                    inputs[key] = le
                    
            dev_group.setLayout(form)
            self.scroll_layout.addWidget(dev_group)
            self.device_forms.append((dev.get('name'), dev.get('type'), inputs))
            
        self.btn_save_hw = QPushButton("Save Hardware Config")
        self.btn_save_hw.clicked.connect(self._save_hw_config)
        self.hw_config_layout.addWidget(self.btn_save_hw)
        
        # Insert it before the bottom spacer in the existing layout
        count = self.verticalLayout_settings.count()
        self.verticalLayout_settings.insertWidget(count - 1, self.hw_config_box)

    @Slot()
    def _save_hw_config(self):
        config_service = self.device_manager.config_service
        config = config_service.get_config()
        
        new_devices = []
        for name, dtype, inputs in self.device_forms:
            dev = {"name": name, "type": dtype}
            for key, widget in inputs.items():
                if isinstance(widget, QCheckBox):
                    dev[key] = widget.isChecked()
                else:
                    val = widget.text()
                    # Try to infer type
                    try:
                        dev[key] = int(val)
                    except ValueError:
                        try:
                            dev[key] = float(val)
                        except ValueError:
                            dev[key] = val
            new_devices.append(dev)
            
        config["devices"] = new_devices
        
        try:
            import json
            with open(config_service.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            QMessageBox.information(self, "Success", "Hardware configuration saved. Restart the application for changes to take effect fully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")

