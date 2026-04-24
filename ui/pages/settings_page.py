from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Slot
from ui.pages.ui_settings_page import Ui_SettingsPage

class SettingsPage(QWidget, Ui_SettingsPage):
    def __init__(self, device_manager, main_window):
        super().__init__()
        self.setupUi(self)
        self.device_manager = device_manager
        self.main_window = main_window
        
        self.btn_toggle_theme.clicked.connect(self.main_window.toggle_theme)
        self.btn_connect_all.clicked.connect(self.device_manager.connect_all)
