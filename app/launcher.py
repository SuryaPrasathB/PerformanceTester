import sys
from PySide6.QtWidgets import QApplication
from services.config_service import ConfigService
from services.logging_service import LoggingService
from core.device_manager import DeviceManager
from ui.main_window import MainWindow

class Launcher:
    """
    Launcher handles dependency injection, bootstrap, and UI wiring.
    """
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # 1. Initialize Services
        self.config_service = ConfigService()
        self.logging_service = LoggingService()
        self.logger = self.logging_service.get_logger()
        
        self.logger.info("Starting Meter Test System...")
        
        try:
            self.config_service.load_config()
            self.logger.info("Configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
        
        # 2. Initialize Core Logic
        self.device_manager = DeviceManager(self.config_service, self.logger)
        
        # 3. Initialize UI
        self.main_window = MainWindow(self.device_manager)
        
        # 4. Wire Logger to UI
        qt_emitter = self.logging_service.get_emitter()
        qt_emitter.log_message.connect(self.main_window.append_log)
        
    def run(self):
        """Shows the main window and executes the Qt application loop."""
        self.main_window.show()
        # Automatically trigger connect on start based on requirements (Attempt connections)
        self.device_manager.connect_all()
        return self.app.exec()
