import sys
import os
import time
from PySide6.QtWidgets import QApplication, QSplashScreen, QProgressBar, QLabel
from PySide6.QtGui import QPixmap, QColor, QLinearGradient, QPainter, QBrush
from PySide6.QtCore import Qt, QSize

from services.config_service import ConfigService
from services.logging_service import LoggingService
from core.device_manager import DeviceManager
from services.database_service import DatabaseService

class PremiumSplashScreen(QSplashScreen):
    """A premium, modern splash screen with a custom background, title, progress bar, and status labels."""
    def __init__(self):
        # Create a nice canvas with a light gradient background
        splash_size = QSize(450, 300)
        pixmap = QPixmap(splash_size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw rounded rectangle background with light gradient
        gradient = QLinearGradient(0, 0, 0, splash_size.height())
        gradient.setColorAt(0.0, QColor("#ffffff"))
        gradient.setColorAt(1.0, QColor("#f1f5f9"))
        
        painter.setBrush(QBrush(gradient))
        
        # Thin border to make the light splash screen pop on light backgrounds
        from PySide6.QtGui import QPen
        border_pen = QPen(QColor("#e2e8f0"), 1.5)
        painter.setPen(border_pen)
        
        # Draw background rectangle (inset slightly by 1px to avoid clipping the border)
        painter.drawRoundedRect(1, 1, splash_size.width() - 2, splash_size.height() - 2, 12, 12)
        
        # Load and draw the app icon in the center (scaled)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "ui", "resources", "icons", "app_icon.png")
        icon_pixmap = QPixmap(icon_path)
        if not icon_pixmap.isNull():
            icon_size = 90
            x = (splash_size.width() - icon_size) // 2
            y = 35
            painter.setPen(Qt.NoPen)
            painter.drawPixmap(x, y, icon_pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
        painter.end()
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Add Title Label (Dark Text)
        self.title_label = QLabel(self)
        self.title_label.setGeometry(10, 145, splash_size.width() - 20, 30)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setText("PRO-PERF TEST SYSTEM")
        self.title_label.setStyleSheet("color: #0f172a; font-size: 16px; font-weight: bold; letter-spacing: 2px; font-family: 'Segoe UI', Arial;")
        
        # Add Status Message Label (Muted Text)
        self.status_label = QLabel(self)
        self.status_label.setGeometry(10, 190, splash_size.width() - 20, 20)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold; font-family: 'Segoe UI', Arial;")
        
        # Add Progress Bar (Light background)
        self.progress = QProgressBar(self)
        self.progress.setGeometry(30, 225, splash_size.width() - 60, 10)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0, 0, 0, 0.05);
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #06b6d4);
                border-radius: 5px;
            }
        """)

    def set_progress(self, val, message):
        self.progress.setValue(val)
        self.status_label.setText(message)
        # Force the UI to refresh
        QApplication.processEvents()

class Launcher:
    """
    Launcher handles dependency injection, bootstrap, and UI wiring.
    """
    def __init__(self):
        self.app = QApplication(sys.argv)
        
        # Initialize and show splash screen
        self.splash = PremiumSplashScreen()
        self.splash.show()
        
        self.splash.set_progress(10, "Starting Meter Test System...")
        time.sleep(0.3)
        
        # 1. Initialize Services
        self.config_service = ConfigService()
        
        if getattr(sys, 'frozen', False):
            base_log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'Pro-Perf', 'logs')
        else:
            base_log_dir = "logs"
            
        self.logging_service = LoggingService(base_log_dir)
        self.logger = self.logging_service.get_logger()
        
        self.splash.set_progress(30, "Connecting to Database...")
        time.sleep(0.3)
        
        db_config = self.config_service.get_database_config()
        self.database_service = DatabaseService(db_config, self.logger)
        try:
            self.database_service.connect()
        except Exception as e:
            self.logger.error(f"Failed to connect to MySQL: {e}")
        
        self.splash.set_progress(55, "Loading Configuration...")
        time.sleep(0.3)
        
        try:
            self.config_service.load_config()
            self.logger.info("Configuration loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
        
        self.splash.set_progress(75, "Initializing Device Manager...")
        time.sleep(0.3)
        
        # 2. Initialize Core Logic
        self.device_manager = DeviceManager(self.config_service, self.logger, self.database_service)
        
        self.splash.set_progress(90, "Loading User Interface...")
        time.sleep(0.3)
        
        # 3. Initialize UI
        from ui.main_window import MainWindow 
        self.main_window = MainWindow(self.device_manager)
        
        # 4. Wire Logger to UI
        qt_emitter = self.logging_service.get_emitter()
        qt_emitter.log_message.connect(self.main_window.append_log)
        
        self.splash.set_progress(100, "Done")
        time.sleep(0.2)
        
    def run(self):
        """Shows the main window and executes the Qt application loop."""
        self.main_window.showMaximized()
        self.splash.finish(self.main_window)
        # Automatically trigger connect on start based on requirements (Attempt connections)
        self.device_manager.connect_all()
        return self.app.exec()

